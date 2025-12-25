import signal
import time
from datetime import datetime
from multiprocessing import Queue
from pathlib import Path
from queue import Empty, Full
from threading import Thread
from time import sleep

import cv2
import polling2
import socketio

from cogip import logger
from cogip.tools.camera.arguments import CameraName, VideoCodec
from cogip.tools.camera.camera import Camera, RPiCamera, SimCamera, USBCamera
from .settings import Settings


class ExitSignal(Exception):
    pass


class CameraHandler:
    """
    Camera handler.

    Handle camera initialization.
    """

    _frame_rate: float = 10  # Number of images processed by seconds
    _exiting: bool = False  # Exit requested if True

    def __init__(self, frame_queue: Queue, stream_queue: Queue):
        """
        Class constructor.

        Create SocketIO client and connect to server.
        """
        self.settings = Settings()
        self.frame_queue = frame_queue
        self.stream_queue = stream_queue
        self.camera: Camera | None = None
        self.record_filename: Path | None = None
        self.record_writer: cv2.VideoWriter | None = None

        self.sio = socketio.Client(logger=False, engineio_logger=False, handle_sigint=False)
        self.register_sio_events()

        signal.signal(signal.SIGTERM, self.exit_handler)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        Thread(
            target=lambda: polling2.poll(
                self.sio_connect,
                step=1,
                ignore_exceptions=(socketio.exceptions.ConnectionError),
                poll_forever=True,
            ),
            daemon=True,
        ).start()

    @staticmethod
    def exit_handler(signum, frame):
        """
        Function called when TERM signal is received.
        """
        if CameraHandler._exiting:
            return
        CameraHandler._exiting = True
        raise ExitSignal()

    def sio_connect(self) -> bool:
        """
        Connect to SocketIO server.
        Returning True stops polling for connection to succeed.
        """
        if self._exiting:
            return True

        self.sio.connect(
            str(self.settings.socketio_server_url),
            namespaces=["/robotcam"],
        )
        return True

    def open_camera(self):
        """
        Initialize camera.
        """
        camera_name = CameraName[self.settings.camera_name]
        camera_codec = VideoCodec[self.settings.camera_codec]
        camera_path: Path = camera_name.val

        if not camera_path.exists():
            logger.error(f"Camera not found: {camera_path}")
            return

        if camera_name == CameraName.rpicam:
            CameraClass = RPiCamera
        elif camera_name == CameraName.simcam:
            CameraClass = SimCamera
        else:
            CameraClass = USBCamera
        self.camera = CameraClass(
            self.settings.id,
            camera_name,
            camera_codec,
            self.settings.camera_width,
            self.settings.camera_height,
            self.settings.stream_width,
            self.settings.stream_height,
        )

        self.camera.open()

    def close_camera(self) -> None:
        """
        Release camera device.
        """
        if self.camera:
            try:
                self.camera.close()
                logger.info("Camera handler: Camera closed.")
            except Exception as exc:  # noqa
                logger.info("Camera handler: Failed to release camera: {exc}")

        self.camera = None

    def camera_handler(self) -> None:
        """
        Read and process frames from camera.
        """
        interval = 1.0 / self._frame_rate

        try:
            while not self._exiting:
                start = time.time()

                if not self.camera:
                    self.open_camera()

                if not self.camera:
                    logger.warning("Camera handler: Failed to open camera, retry in 1s.")
                    sleep(1)
                    continue

                try:
                    self.process_image()
                except ExitSignal:
                    break
                except Exception as exc:
                    logger.warning(f"Unknown exception: {exc}")
                    self.close_camera()
                    sleep(1)
                    continue

                now = time.time()
                duration = now - start
                if duration > interval:
                    logger.warning(f"Function too long: {duration} > {interval}")
                else:
                    wait = interval - duration
                    time.sleep(wait)

        except ExitSignal:
            CameraHandler._exiting = True

        logger.info("Camera handler: Exiting.")

        self.close_camera()
        if self.sio.connected:
            self.sio.disconnect()

        if self.frame_queue:
            self.frame_queue.cancel_join_thread()
        if self.stream_queue:
            self.stream_queue.cancel_join_thread()

    def process_image(self) -> None:
        """
        Read one frame from camera, process it, send samples to cogip-server
        and generate image to stream.
        """
        image_main, image_stream = self.camera.read()
        if image_main is None:
            raise Exception("Camera handler: Cannot read frame.")

        # Encode the frame in JPEG format
        ret, encoded_image = cv2.imencode(".jpg", image_main, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        if not ret:
            raise Exception("Can't encode frame.")

        frame_data = encoded_image.tobytes()

        if self.frame_queue:
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except Empty:
                    pass
            try:
                self.frame_queue.put_nowait(frame_data)
            except Full:
                pass

        if image_stream is not None:
            ret, encoded_stream = cv2.imencode(".jpg", image_stream, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                stream_frame_data = encoded_stream.tobytes()

                if self.stream_queue:
                    if self.stream_queue.full():
                        try:
                            self.stream_queue.get_nowait()
                        except Exception:
                            pass
                    try:
                        self.stream_queue.put_nowait(stream_frame_data)
                    except Full:
                        pass

        if self.record_writer:
            if len(image_main.shape) == 2:
                image_record = cv2.cvtColor(image_main, cv2.COLOR_GRAY2BGR)
            else:
                image_record = image_main
            self.record_writer.write(image_record)

    def start_video_record(self):
        if self.record_writer:
            self.stop_video_record()
        records_dir = Path.home() / "records"
        records_dir.mkdir(exist_ok=True)
        # Keep only 20 last records
        for old_record in sorted(records_dir.glob("*.mp4"))[:-20]:
            old_record.unlink()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.record_filename = records_dir / f"robot{self.settings.id}_{timestamp}.mp4"

        logger.info(f"Start recording video in {self.record_filename}")
        self.record_writer = cv2.VideoWriter(
            str(self.record_filename),
            cv2.VideoWriter.fourcc(*"mp4v"),
            self._frame_rate,
            (self.settings.camera_width, self.settings.camera_height),
        )

    def stop_video_record(self):
        if self.record_writer:
            logger.info("Stop recording video")
            self.record_writer.release()
            self.record_filename = None
            self.record_writer = None

    def register_sio_events(self) -> None:
        @self.sio.event(namespace="/robotcam")
        def connect():
            """
            Callback on server connection.
            """
            polling2.poll(lambda: self.sio.connected is True, step=0.2, poll_forever=True)
            logger.info("Camera handler: connected to server")
            self.sio.emit("connected", namespace="/robotcam")

        @self.sio.event(namespace="/robotcam")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            logger.info("Camera handler: connection to server failed.")

        @self.sio.event(namespace="/robotcam")
        def disconnect():
            """
            Callback on server disconnection.
            """
            logger.info("Camera handler: disconnected from server")

        @self.sio.on("start_video_record", namespace="/robotcam")
        def start_video_record():
            self.start_video_record()

        @self.sio.on("stop_video_record", namespace="/robotcam")
        def stop_video_record():
            self.stop_video_record()
