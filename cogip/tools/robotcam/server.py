import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from multiprocessing import Queue
from pathlib import Path
from queue import Empty
from threading import Thread

import cv2
import cv2.typing
import numpy as np
import systemd.daemon
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from uvicorn.main import Server as UvicornServer

from cogip import logger
from cogip.models import CameraExtrinsicParameters, Pose
from cogip.tools.camera.arguments import CameraName, VideoCodec
from cogip.tools.camera.camera import RPiCamera, SimCamera, USBCamera
from cogip.tools.camera.detect import (
    get_camera_position_in_robot,
    get_camera_position_on_table,
)
from cogip.tools.camera.utils import (
    R_flip,
    decompose_transform_matrix,
    euler_angles_to_rotation_matrix,
    extrinsic_params_to_matrix,
    load_camera_extrinsic_params,
    load_camera_intrinsic_params,
    make_transform_matrix,
)
from .settings import Settings


class CameraServer:
    """
    Camera web server.

    Handle FastAPI server to stream camera video and SocketIO client to send detected samples to server.
    """

    _exiting: bool = False  # True if Uvicorn server was ask to shutdown
    _original_uvicorn_exit_handler = UvicornServer.handle_exit

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application and SocketIO client.
        """
        self.settings = Settings()
        CameraServer._exiting = False

        self.frame_queue: Queue | None = None
        self.stream_queue: Queue | None = None
        self.last_frame: bytes | None = None
        self.last_stream_frame: bytes | None = None

        self.app = FastAPI(title="COGIP Robot Camera Streamer", lifespan=self.lifespan, debug=False)
        self.register_endpoints()

        UvicornServer.handle_exit = self.handle_exit

        self.records_dir = Path.home() / "records"
        self.records_dir.mkdir(exist_ok=True)
        # Keep only 100 last records
        for old_record in sorted(self.records_dir.glob("*.jpg"))[:-100]:
            old_record.unlink()

        if self.settings.camera_name == CameraName.rpicam.name:
            CameraClass = RPiCamera
        elif self.settings.camera_name == CameraName.simcam.name:
            CameraClass = SimCamera
        else:
            CameraClass = USBCamera
        self.camera = CameraClass(
            self.settings.id,
            CameraName[self.settings.camera_name],
            VideoCodec[self.settings.camera_codec],
            self.settings.camera_width,
            self.settings.camera_height,
            self.settings.stream_width,
            self.settings.stream_height,
        )

        # Load camera intrinsic parameters
        self.camera_matrix: cv2.typing.MatLike | None = None
        self.dist_coefs: cv2.typing.MatLike | None = None
        if not self.camera.intrinsic_params_filename.exists():
            logger.warning(f"Camera intrinsic parameters file not found: {self.camera.intrinsic_params_filename}")
        else:
            self.camera_matrix, self.dist_coefs = load_camera_intrinsic_params(self.camera.intrinsic_params_filename)

        # Load camera extrinsic parameters
        self.extrinsic_params: CameraExtrinsicParameters | None = None
        if not self.camera.extrinsic_params_filename.exists():
            logger.warning(f"Camera extrinsic parameters file not found: {self.camera.extrinsic_params_filename}")
        else:
            self.extrinsic_params = load_camera_extrinsic_params(self.camera.extrinsic_params_filename)

        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        parameters = cv2.aruco.DetectorParameters()

        # Speed optimizations
        # Use a single window size for adaptive thresholding to avoid multiple passes
        parameters.adaptiveThreshWinSizeMin = 13
        parameters.adaptiveThreshWinSizeMax = 13
        parameters.adaptiveThreshWinSizeStep = 1

        # Reduce accuracy of polygonal approximation (faster contour processing)
        parameters.polygonalApproxAccuracyRate = 0.05  # Default 0.03

        # Disable corner refinement if not strictly necessary (SUBPIX is slow)
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_NONE

        self.detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    def set_queues(self, frame_queue: Queue, stream_queue: Queue):
        self.frame_queue = frame_queue
        self.stream_queue = stream_queue

        # Start consumer thread
        self.consumer_thread = Thread(target=self.consume_queues, daemon=True)
        self.consumer_thread.start()

    def consume_queues(self):
        while not self._exiting:
            try:
                if self.frame_queue and not self.frame_queue.empty():
                    try:
                        self.last_frame = self.frame_queue.get_nowait()
                    except Empty:
                        pass

                if self.stream_queue and not self.stream_queue.empty():
                    try:
                        self.last_stream_frame = self.stream_queue.get_nowait()
                    except Empty:
                        pass

                time.sleep(0.01)
            except Exception:
                pass

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Handle application startup and shutdown events.
        """
        logger.info("Robotcam server starting up...")
        try:
            systemd.daemon.notify("READY=1")
            logger.info("Systemd notified: READY=1")
        except Exception as e:
            logger.error(f"Failed to notify systemd: {e}")

        yield

        logger.info("Robotcam server shutting down...")
        CameraServer._exiting = True
        if self.consumer_thread:
            self.consumer_thread.join()

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        CameraServer._exiting = True
        CameraServer._original_uvicorn_exit_handler(*args, **kwargs)

    async def camera_streamer(self):
        """
        Frame generator.
        Yield frames produced by [camera_handler][cogip.tools.robotcam.camera.CameraHandler.camera_handler].
        """
        while not self._exiting:
            if self.last_stream_frame:
                yield b"--frame\r\n"
                yield b"Content-Type: image/jpeg\r\n\r\n"
                yield self.last_stream_frame
                yield b"\r\n"

            await asyncio.sleep(0.1)

    def register_endpoints(self) -> None:
        @self.app.get("/")
        def index():
            """
            Camera stream.
            """
            stream = self.camera_streamer() if self.last_stream_frame else ""
            return StreamingResponse(stream, media_type="multipart/x-mixed-replace;boundary=frame")

        @self.app.get("/detect", status_code=200)
        def detect() -> list[dict]:
            start_time = time.time()
            if self.last_frame is None:
                raise HTTPException(status_code=503, detail="Camera not ready")

            jpg_as_np = np.frombuffer(self.last_frame, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=cv2.IMREAD_UNCHANGED)

            if len(frame.shape) == 2:
                dst = frame
            else:
                dst = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect marker corners
            marker_corners, marker_ids, _ = self.detector.detectMarkers(dst)

            results = []
            if marker_ids is not None:
                for id, corners in zip(marker_ids, marker_corners):
                    results.append({"id": int(id[0]), "corners": corners[0].tolist()})

            duration = time.time() - start_time
            logger.info(f"Detect endpoint took {duration:.3f}s")

            return results

        @self.app.get("/snapshot", status_code=200)
        def snapshot():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"robot{self.settings.id}-{timestamp}-snapshot"

            if self.last_frame is None:
                raise HTTPException(status_code=503, detail="Camera not ready")

            jpg_as_np = np.frombuffer(self.last_frame, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)

            record_filename = self.records_dir / f"{basename}.jpg"
            cv2.imwrite(str(record_filename), frame)

        @self.app.get("/camera_calibration", status_code=200)
        def camera_calibration(x: float, y: float, angle: float) -> CameraExtrinsicParameters:
            if self.last_frame is None:
                raise HTTPException(status_code=503, detail="Camera not ready")

            jpg_as_np = np.frombuffer(self.last_frame, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=cv2.IMREAD_UNCHANGED)

            if len(frame.shape) == 2:
                dst = frame
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                dst = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect marker corners
            marker_corners, marker_ids, _ = self.detector.detectMarkers(dst)

            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

            # Record image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"robot{self.settings.id}-{timestamp}-calibration"
            record_filename = self.records_dir / f"{basename}.jpg"
            cv2.imwrite(str(record_filename), frame)

            if marker_ids is None:
                raise HTTPException(status_code=404, detail="No marker found")

            robot_pose = Pose(x=x, y=y, O=angle)

            # Keep table markers only
            table_markers = {
                id[0]: corners for id, corners in zip(marker_ids, marker_corners) if id[0] in [20, 21, 22, 23]
            }

            if len(table_markers) == 0:
                raise HTTPException(status_code=404, detail="No table marker found")

            # Compute camera position on table
            table_camera_tvec, table_camera_rvec_degrees = get_camera_position_on_table(
                table_markers,
                self.camera_matrix,
                self.dist_coefs,
            )

            # Compute camera position in robot if robot position is given
            camera_position = get_camera_position_in_robot(
                robot_pose,
                table_camera_tvec,
                table_camera_rvec_degrees,
            )

            return camera_position

        @self.app.get("/robot_position", status_code=200)
        def robot_position() -> Pose:
            if self.last_frame is None:
                raise HTTPException(status_code=503, detail="Camera not ready")

            jpg_as_np = np.frombuffer(self.last_frame, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=cv2.IMREAD_UNCHANGED)

            if len(frame.shape) == 2:
                dst = frame
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                dst = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect marker corners
            marker_corners, marker_ids, _ = self.detector.detectMarkers(dst)

            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

            # Record image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"robot{self.settings.id}-{timestamp}-position"
            record_filename = self.records_dir / f"{basename}.jpg"
            cv2.imwrite(str(record_filename), frame)

            if marker_ids is None:
                raise HTTPException(status_code=404, detail="No marker found")

            # Keep table markers only
            table_markers = {
                id[0]: corners for id, corners in zip(marker_ids, marker_corners) if id[0] in [20, 21, 22, 23]
            }

            if len(table_markers) == 0:
                raise HTTPException(status_code=404, detail="No table marker found")

            if self.camera_matrix is None or self.dist_coefs is None:
                raise HTTPException(status_code=503, detail="Camera intrinsic parameters not loaded")

            # Compute camera position on table
            camera_tvec, camera_rvec_degrees = get_camera_position_on_table(
                table_markers,
                self.camera_matrix,
                self.dist_coefs,
            )

            # Compute robot position on table

            # 1. Camera in Table frame (Transformation T_ct)
            # Reconstruct rotation matrix from Euler angles (applying R_flip to match convention)
            R_ct_flipped = euler_angles_to_rotation_matrix(np.deg2rad(camera_rvec_degrees))
            R_ct = R_flip @ R_ct_flipped
            M_ct = make_transform_matrix(R_ct, camera_tvec)

            # 2. Camera in Robot frame (Transformation T_cr)
            M_cr = extrinsic_params_to_matrix(self.extrinsic_params)

            # 3. Robot in Table frame (Transformation T_rt)
            # M_rt = M_ct * M_cr^(-1)
            M_rt = M_ct @ np.linalg.inv(M_cr)

            # Extract results
            R_rt, T_rt = decompose_transform_matrix(M_rt)
            robot_angle_degrees = np.rad2deg(np.arctan2(R_rt[1, 0], R_rt[0, 0]))

            logger.info(
                f"Robot position: X={T_rt[0]:.0f} Y={T_rt[1]:.0f} Z={T_rt[2]:.0f} Angle={robot_angle_degrees:.0f}"
            )
            return Pose(x=T_rt[0], y=T_rt[1], z=T_rt[2], O=robot_angle_degrees)
