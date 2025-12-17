import logging
from pathlib import Path
from time import sleep
from typing import Annotated, Optional

import cv2
import typer
from linuxpy.video import device

from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera


def cmd_info(
    ctx: typer.Context,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=0,
            help="Robot ID.",
            envvar=["ROBOT_ID", "CAMERA_ID"],
        ),
    ] = 1,
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
    ] = 1920,
    camera_height: Annotated[
        int,
        typer.Option(
            help="Camera frame height",
            envvar="CAMERA_HEIGHT",
        ),
    ] = 1080,
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

        if camera_name != CameraName.rpicam:
            camera = device.Device(camera_name.val)
            try:
                camera.open()
            except OSError:
                logger.error(f"Failed to open {camera_name.val}")
                return
            USBCamera.print_device_info(camera)
            camera.close()
        else:
            RPiCamera.print_device_info()

        show_stream(id, camera_name, camera_codec, camera_width, camera_height)
        return

    for camera in device.iter_video_capture_devices():
        try:
            camera.open()
        except OSError:
            pass
        else:
            USBCamera.print_device_info(camera)
            camera.close()
            print()


def show_stream(id: int, name: CameraName, codec: VideoCodec, width: int, height: int):
    exit_key = 27  # Use this key (Esc) to exit stream display
    window_name = "Stream Preview - Press Esc to exit"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if str(name.name).startswith("rpicam"):
        CameraClass = RPiCamera
    else:
        CameraClass = USBCamera
    camera = CameraClass(id, name, codec, width, height)

    camera.open()

    while True:
        frame, _ = camera.read()
        if frame is None:
            logger.warning("Cannot read current frame.")
            sleep(0.2)
            continue

        cv2.imshow(window_name, frame)

        k = cv2.waitKey(1)
        if k == exit_key:
            break

    camera.close()

    cv2.destroyAllWindows()
