import shutil
from pathlib import Path
from typing import Annotated

import cv2
import cv2.typing
import typer

from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera


def cmd_capture(
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
        CameraName,
        typer.Option(
            help="Name of the camera",
            envvar="CAMERA_NAME",
        ),
    ] = CameraName.hbv.name,
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
    max_frames: Annotated[
        int,
        typer.Option(
            help="Maximum number of frames to read before exiting",
            envvar="CAMERA_MAX_FRAMES",
        ),
    ] = 120,
    capture_interval: Annotated[
        int,
        typer.Option(
            help="Capture an image every 'capture_interval' frames",
            envvar="CAMERA_CAPTURE_INTERVAL",
        ),
    ] = 10,
    charuco_rows: Annotated[
        int,
        typer.Option(
            help="Number of rows on the Charuco board",
            envvar="CAMERA_CHARUCO_ROWS",
        ),
    ] = 8,
    charuco_cols: Annotated[
        int,
        typer.Option(
            help="Number of columns on the Charuco board",
            envvar="CAMERA_CHARUCO_COLS",
        ),
    ] = 13,
    charuco_marker_length: Annotated[
        int,
        typer.Option(
            help="Length of an Aruco marker on the Charuco board (in mm)",
            envvar="CAMERA_CHARUCO_MARKER_LENGTH",
        ),
    ] = 23,
    charuco_square_length: Annotated[
        int,
        typer.Option(
            help="Length of a square in the Charuco board (in mm)",
            envvar="CAMERA_CHARUCO_SQUARE_LENGTH",
        ),
    ] = 30,
    charuco_legacy: Annotated[
        bool,
        typer.Option(
            help="Use Charuco boards compatible with OpenCV < 4.6",
            envvar="CAMERA_CHARUCO_LEGACY",
        ),
    ] = True,
):
    """Capture images to be used by the 'calibrate' command"""
    exit_key = 27  # use this key (Esc) to exit before max_frames
    captures_frames: list[cv2.typing.MatLike] = []  # Captured frames
    preview_window_name = "Detection Preview - Press Esc to exit"

    cv2.namedWindow(preview_window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(preview_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if not Path(camera_name.val).exists():
        logger.error(f"Camera not found: {camera_name.val}")
        return

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    board = cv2.aruco.CharucoBoard(
        (charuco_cols, charuco_rows),
        charuco_square_length,
        charuco_marker_length,
        aruco_dict,
    )
    board.setLegacyPattern(charuco_legacy)

    if camera_name == CameraName.rpicam:
        CameraClass = RPiCamera
    else:
        CameraClass = USBCamera
    camera = CameraClass(id, camera_name, camera_codec, camera_width, camera_height)
    camera.open()

    i = capture_interval
    while True:
        frame, stream_frame = camera.read()
        if frame is None:
            continue

        board_detector = cv2.aruco.CharucoDetector(board)

        k = cv2.waitKey(1)
        if k == exit_key:
            break
        elif i == 0:
            i = capture_interval
            captures_frames.append(frame)
            logger.info(f"Frame captured: {len(captures_frames)}")
            if len(captures_frames) == max_frames:
                break
        i -= 1

        _, _, marker_corners, marker_ids = board_detector.detectBoard(frame)
        cv2.aruco.drawDetectedMarkers(stream_frame, marker_corners, marker_ids)

        cv2.imshow(preview_window_name, stream_frame)

    camera.close()
    logger.info(f"Writing captured frames in: {camera.capture_path}")
    shutil.rmtree(camera.capture_path, ignore_errors=True)
    camera.capture_path.mkdir(parents=True, exist_ok=True)
    for n, frame in enumerate(captures_frames):
        filename = camera.capture_path / f"image_{n:03}.jpg"
        cv2.imwrite(str(filename), frame)
