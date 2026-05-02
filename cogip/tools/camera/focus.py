import sys
from typing import Annotated

import cv2
import typer

from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera


def cmd_focus(
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
    ] = CameraName.rpicam.name,
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
    ] = 728,
    camera_height: Annotated[
        int,
        typer.Option(
            help="Camera frame height",
            envvar="CAMERA_HEIGHT",
        ),
    ] = 544,
    zoom: Annotated[
        float,
        typer.Option(
            help="Digital zoom factor to apply to the center of the image",
            envvar="CAMERA_FOCUS_ZOOM",
        ),
    ] = 2.0,
    no_gui: Annotated[
        bool,
        typer.Option(
            "--no-gui",
            help="Run without displaying the video window (useful for SSH)",
        ),
    ] = False,
):
    """Help adjust the camera focus by calculating a sharpness score (Laplacian variance)."""
    if zoom < 1.0:
        logger.error("Zoom factor must be >= 1.0")
        return

    if camera_name == CameraName.rpicam:
        CameraClass = RPiCamera
    else:
        CameraClass = USBCamera

    camera = CameraClass(id, camera_name, camera_codec, camera_width, camera_height)
    camera.open()

    preview_window_name = "Focus Adjust - Press Esc to exit"
    if not no_gui:
        cv2.namedWindow(preview_window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(preview_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Starting focus loop. Press Ctrl+C (or Esc if GUI) to exit.", flush=True)

    try:
        while True:
            frame, stream_frame = camera.read()
            if stream_frame is None:
                continue

            h, w = stream_frame.shape[:2]

            # Apply digital zoom to center
            if zoom > 1.0:
                crop_w = int(w / zoom)
                crop_h = int(h / zoom)
                x1 = (w - crop_w) // 2
                y1 = (h - crop_h) // 2
                x2 = x1 + crop_w
                y2 = y1 + crop_h
                stream_frame = stream_frame[y1:y2, x1:x2]

                # Optionally resize back to original window size for better visibility
                stream_frame = cv2.resize(stream_frame, (w, h), interpolation=cv2.INTER_LINEAR)

            # Calculate sharpness score (Variance of Laplacian)
            gray = cv2.cvtColor(stream_frame, cv2.COLOR_BGR2GRAY) if len(stream_frame.shape) == 3 else stream_frame
            score = cv2.Laplacian(gray, cv2.CV_64F).var()

            if no_gui:
                # Print score cleanly on a single line
                sys.stdout.write(f"\rFocus Score: {score:10.2f}")
                sys.stdout.flush()
            else:
                # Display score on image
                text = f"Focus Score: {score:.2f}"
                cv2.putText(stream_frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                cv2.imshow(preview_window_name, stream_frame)

                k = cv2.waitKey(1)
                # Exit on Esc
                if k == 27:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        if no_gui:
            print()  # New line after the carriage return loop
        camera.close()
        if not no_gui:
            cv2.destroyAllWindows()
