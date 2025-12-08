import logging
from pathlib import Path
from time import sleep
from typing import Annotated, Optional

import cv2
import typer
from linuxpy.video import device

from . import logger
from .arguments import CameraName, VideoCodec


def cmd_info(
    ctx: typer.Context,
    camera_name: Annotated[
        Optional[CameraName],  # noqa
        typer.Option(
            help="Name of the camera (all if not specified)",
            envvar="CAMERA_NAME",
        ),
    ] = None,
    camera_codec: Annotated[
        VideoCodec,
        typer.Option(
            help="Camera video codec",
            envvar="CAMERA_CODEC",
        ),
    ] = VideoCodec.yuyv.name,
    camera_width: Annotated[
        int,
        typer.Option(
            help="Camera frame width",
            envvar="CAMERA_WIDTH",
        ),
    ] = 640,
    camera_height: Annotated[
        int,
        typer.Option(
            help="Camera frame height",
            envvar="CAMERA_HEIGHT",
        ),
    ] = 480,
):
    """Get properties of connected cameras"""
    obj = ctx.ensure_object(dict)
    debug = obj.get("debug", False)

    if debug:
        logging.getLogger("linuxpy.video").setLevel(logging.DEBUG)
    else:
        logging.getLogger("linuxpy.video").setLevel(logging.INFO)

    if camera_name:
        if not Path(camera_name.val).exists():
            logger.error(f"Camera not found: {camera_name}")
            return
        camera = device.Device(camera_name.val)
        try:
            camera.open()
        except OSError:
            logger.error(f"Failed to open {camera_name.val}")
            return
        print_device_info(camera)
        camera.close()
        show_stream(camera_name, camera_codec, camera_width, camera_height)
        return

    for camera in device.iter_video_capture_devices():
        try:
            camera.open()
        except OSError:
            pass
        else:
            print_device_info(camera)
            camera.close()
            print()


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


def show_stream(name: CameraName, codec: VideoCodec, width: int, height: int):
    exit_key = 27  # Use this key (Esc) to exit stream display
    window_name = "Stream Preview - Press Esc to exit"

    cap = cv2.VideoCapture(str(name.val))

    fourcc = cv2.VideoWriter_fourcc(*codec.val)
    ret = cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    if not ret:
        logger.warning(f"Video codec {codec.val} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if not ret:
        logger.warning(f"Frame width {width} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not ret:
        logger.warning(f"Frame height {height} not supported")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning("Cannot read current frame.")
            sleep(0.2)
            continue

        cv2.imshow(window_name, frame)

        k = cv2.waitKey(1)
        if k == exit_key:
            break

    cap.release()
    cv2.destroyAllWindows()
