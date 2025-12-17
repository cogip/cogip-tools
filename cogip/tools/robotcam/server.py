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
from cogip.models import CameraExtrinsicParameters, Pose, Vertex
from cogip.tools.camera.arguments import CameraName, VideoCodec
from cogip.tools.camera.camera import RPiCamera, USBCamera
from cogip.tools.camera.detect import (
    get_camera_position_in_robot,
    get_camera_position_on_table,
    get_solar_panel_positions,
)
from cogip.tools.camera.utils import (
    load_camera_extrinsic_params,
    load_camera_intrinsic_params,
    rotate_2d,
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

        self.detector = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100))

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
        def camera_calibration(x: float, y: float, angle: float) -> Vertex:
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
            table_camera_tvec, table_camera_angle = get_camera_position_on_table(
                table_markers,
                self.camera_matrix,
                self.dist_coefs,
            )

            # Compute camera position in robot if robot position is given
            camera_position = get_camera_position_in_robot(
                robot_pose,
                table_camera_tvec,
                table_camera_angle,
            )

            return camera_position

        @self.app.get("/solar_panels", status_code=200)
        def solar_panels(x: float, y: float, angle: float) -> dict[int, float]:
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
            marker_corners, marker_ids, rejected = self.detector.detectMarkers(dst)

            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

            # Record image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"robot{self.settings.id}-{timestamp}-panels"
            record_filename = self.records_dir / f"{basename}.jpg"
            cv2.imwrite(str(record_filename), frame)

            if marker_ids is None:
                return {}

            robot_pose = Pose(x=x, y=y, O=angle)

            # Keep solar panel markers only
            solar_panel_markers = [corners for id, corners in zip(marker_ids, marker_corners) if id[0] == 47]

            if len(solar_panel_markers) == 0:
                return {}

            panels = get_solar_panel_positions(
                solar_panel_markers,
                self.camera_matrix,
                self.dist_coefs,
                self.extrinsic_params,
                robot_pose,
            )

            return panels

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
            camera_tvec, camera_angle = get_camera_position_on_table(
                table_markers,
                self.camera_matrix,
                self.dist_coefs,
            )

            # Compute robot position on table
            delta_tvec = np.array([self.extrinsic_params.x, self.extrinsic_params.y])
            camera_tvec_rotated = rotate_2d(camera_tvec[0:2], -camera_angle)
            robot_tvec_rotated = camera_tvec_rotated + delta_tvec
            robot_tvec = rotate_2d(robot_tvec_rotated, camera_angle)
            camera_angle_degrees = np.rad2deg(camera_angle)
            logger.info(
                "Robot position: "
                f"X={robot_tvec[0]:.0f} Y={robot_tvec[1]:.0f} Z={camera_tvec[2]:.0f} Angle={camera_angle_degrees:.0f}"
            )
            return Pose(x=robot_tvec[0], y=robot_tvec[1], z=camera_tvec[2], O=camera_angle_degrees)
