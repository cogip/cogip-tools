from pathlib import Path
from time import sleep
from typing import final

import cv2
import cv2.typing
from linuxpy.video import device

from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from . import logger
from .arguments import CameraName, VideoCodec


class Camera:
    def __init__(
        self,
        robot_id: int,
        name: CameraName,
        codec: VideoCodec,
        width: int,
        height: int,
        stream_width: int | None = None,
        stream_height: int | None = None,
    ):
        self.robot_id = robot_id
        self.name = name
        self.codec = codec
        self.width = width
        self.height = height
        self.stream_width = stream_width if stream_width else width
        self.stream_height = stream_height if stream_height else height

    def open(self):
        raise NotImplementedError()

    def read(self) -> tuple[cv2.typing.MatLike | None, cv2.typing.MatLike | None]:
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class USBCamera(Camera):
    def __init__(
        self,
        robot_id: int,
        name: CameraName,
        codec: VideoCodec,
        width: int,
        height: int,
        stream_width: int | None = None,
        stream_height: int | None = None,
    ):
        super().__init__(robot_id, name, codec, width, height, stream_width, stream_height)
        self.camera: cv2.VideoCapture | None = None
        params_path = Path(__file__).parent / "cameras" / str(robot_id)
        params_path /= f"{name.name}_{codec.name}_{width}x{height}"
        self.capture_path = params_path / "images"
        self.intrinsic_params_filename = params_path / "intrinsic_params.yaml"
        self.extrinsic_params_filename = params_path / "extrinsic_params.json"

    @final
    def open(self):
        self.close()
        self.camera = cv2.VideoCapture(str(self.name.val))

        fourcc = cv2.VideoWriter.fourcc(*self.codec.val)
        ret = self.camera.set(cv2.CAP_PROP_FOURCC, fourcc)
        if not ret:
            logger.warning(f"Video codec {self.codec.val} not supported")

        ret = self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if not ret:
            logger.warning(f"Frame width {self.width} not supported")

        ret = self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not ret:
            logger.warning(f"Frame height {self.height} not supported")

    @final
    def read(self) -> tuple[cv2.typing.MatLike | None, cv2.typing.MatLike | None]:
        ret, frame = self.camera.read()
        if not ret:
            return None, None

        if self.width != self.stream_width or self.height != self.stream_height:
            stream_frame = cv2.resize(frame, (self.stream_width, self.stream_height))
        else:
            stream_frame = frame

        return frame, stream_frame

    @final
    def close(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    @staticmethod
    def print_device_info(camera: device.Device):
        logger.info(f"Camera: {camera.filename} ({getattr(camera.info, 'card', 'N/A')})")

        logger.info("  - Frame sizes:")
        frame_sizes: set[tuple[device.PixelFormat, int, int]] = set()
        for frame_size in camera.info.frame_sizes:
            frame_size: device.FrameType
            frame_sizes.add((frame_size.pixel_format, frame_size.width, frame_size.height))

        for pixel_format, width, height in sorted(frame_sizes):
            logger.info(f"    - {pixel_format.name:>5s} - {width:4d} x {height:4d}")

        logger.info("  - Available controls:")
        for control in camera.controls.values():
            match type(control):
                case device.BooleanControl:
                    control: device.BooleanControl
                    logger.info(f"    - {control.name} - value={control.value} - default={control.default}")
                case device.IntegerControl:
                    control: device.IntegerControl
                    logger.info(
                        f"    - {control.name} - value={control.value} - default={control.default}"
                        f" - min={control.minimum} - max={control.maximum}"
                    )
                case device.MenuControl:
                    control: device.MenuControl
                    logger.info(f"    - {control.name} - value={control.value} - default={control.default}")
                    for key, value in control.data.items():
                        logger.info(f"      - {key}: {value}")

        logger.info("")


class RPiCamera(Camera):
    def __init__(
        self,
        robot_id: int,
        name: CameraName,
        codec: VideoCodec,
        width: int,
        height: int,
        stream_width: int | None = None,
        stream_height: int | None = None,
    ):
        super().__init__(robot_id, name, codec, width, height, stream_width, stream_height)
        # Detect camera type (imx219, imx296, etc.)
        self.camera_type = Path(name.val).read_text().partition(" ")[0]
        params_path = Path(__file__).parent / "cameras" / str(robot_id)
        params_path /= f"{name.name}-{self.camera_type}_{codec.name}_{width}x{height}"
        self.capture_path = params_path / "images"
        self.intrinsic_params_filename = params_path / "intrinsic_params.yaml"
        self.extrinsic_params_filename = params_path / "extrinsic_params.json"

    @final
    def open(self):
        # Import here to avoid dependency if RPiCamera is not used
        from picamera2 import Picamera2

        self.close()
        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={
                "format": "RGB888",
                "size": (self.width, self.height),
            },
            lores={
                "format": "YUV420",
                "size": (self.stream_width, self.stream_height),
            },
        )
        self.camera.configure(config)
        self.camera.start()
        sleep(1)  # Allow camera to warm up

    @final
    def read(self) -> tuple[cv2.typing.MatLike | None, cv2.typing.MatLike | None]:
        request = self.camera.capture_request()
        main = request.make_array("main")
        lores = request.make_array("lores")
        request.release()

        # main is RGB888 (for display)
        stream_frame = main

        # lores is YUV420 (for detection). Extract Y plane.
        frame = None
        if lores is not None and lores.shape[0] == self.stream_height * 3 // 2:
            frame = lores[: self.stream_height, : self.stream_width]

        return frame, stream_frame

    @final
    def close(self):
        if getattr(self, "camera", None) is not None:
            self.camera.close()
            self.camera = None

    @staticmethod
    def print_device_info():
        try:
            from picamera2 import Picamera2
        except ImportError:
            logger.error("picamera2 not installed")
            return

        try:
            picam2 = Picamera2()
        except Exception as e:
            logger.error(f"Failed to initialize Picamera2: {e}")
            return

        logger.info("RPiCamera:")

        # Sensor info
        props = picam2.camera_properties
        model = props.get("Model", "Unknown")
        logger.info(f"  - Model: {model}")

        logger.info("  - Sensor Modes:")
        for mode in picam2.sensor_modes:
            size = mode.get("size", (0, 0))
            fps = mode.get("fps", 0)
            logger.info(f"    - {size[0]} x {size[1]} @ {fps:.2f} fps")

        logger.info("  - Available controls:")
        for control_id, control_info in picam2.camera_controls.items():
            logger.info(f"    - {control_id}: {control_info}")

        picam2.close()
        logger.info("")


class SimCamera(Camera):
    def __init__(
        self,
        robot_id: int,
        name: CameraName,
        codec: VideoCodec,
        width: int,
        height: int,
        stream_width: int | None = None,
        stream_height: int | None = None,
    ):
        super().__init__(robot_id, name, codec, width, height, stream_width, stream_height)
        self.shared_memory: SharedMemory | None = None
        self.shared_sim_camera_data_lock: WritePriorityLock | None = None
        params_path = Path(__file__).parent / "cameras" / str(robot_id)
        params_path /= f"{name.name}_{codec.name}_{width}x{height}"
        self.capture_path = params_path / "images"
        self.intrinsic_params_filename = params_path / "intrinsic_params.yaml"
        self.extrinsic_params_filename = params_path / "extrinsic_params.json"

    @final
    def open(self):
        self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
        self.shared_sim_camera_data = self.shared_memory.get_sim_camera_data()
        self.shared_sim_camera_data_lock = self.shared_memory.get_lock(LockName.SimCameraData)

    @final
    def read(self) -> tuple[cv2.typing.MatLike | None, cv2.typing.MatLike | None]:
        # Copy and convert RGBA -> BGR for OpenCV
        self.shared_sim_camera_data_lock.start_reading()
        frame = cv2.cvtColor(self.shared_sim_camera_data, cv2.COLOR_RGBA2BGR)
        self.shared_sim_camera_data_lock.finish_reading()

        if self.width != self.stream_width or self.height != self.stream_height:
            stream_frame = cv2.resize(frame, (self.stream_width, self.stream_height))
        else:
            stream_frame = frame

        return frame, stream_frame

    @final
    def close(self):
        self.shared_sim_camera_data_lock = None
        self.shared_sim_camera_data = None
        self.shared_memory = None
