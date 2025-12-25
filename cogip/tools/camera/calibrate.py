from typing import Annotated

import cv2
import cv2.aruco
import cv2.typing
import typer

from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera
from .utils import save_camera_intrinsic_params


def cmd_calibrate(
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
    """Calibrate camera using images captured by the 'capture' command"""
    obj = ctx.ensure_object(dict)
    debug = obj.get("debug", False)

    if camera_name == CameraName.rpicam:
        CameraClass = RPiCamera
    else:
        CameraClass = USBCamera
    camera = CameraClass(id, camera_name, camera_codec, camera_width, camera_height)

    if not camera.capture_path.exists():
        logger.error(f"Captured images directory not found: {camera.capture_path}")
        return

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    board = cv2.aruco.CharucoBoard(
        (charuco_cols, charuco_rows),
        charuco_square_length,
        charuco_marker_length,
        aruco_dict,
    )
    board.setLegacyPattern(charuco_legacy)

    captured_images = list(camera.capture_path.glob("image_*.jpg"))
    if (nb_img := len(captured_images)) < 10:
        logger.error(f"Not enough images: {nb_img} < 10")
        return

    object_points = []
    image_points: list[cv2.typing.MatLike] = []

    board_detector = cv2.aruco.CharucoDetector(board)

    for im in sorted(captured_images)[0:]:
        frame = cv2.imread(str(im))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        char_corners, char_ids, _, _ = board_detector.detectBoard(gray)
        if char_corners is None or len(char_corners) == 0:
            logger.info(f"{im}: KO")
            continue

        frame_obj_points, frame_img_points = board.matchImagePoints(char_corners, char_ids)

        if len(frame_obj_points) < 4:
            logger.info(f"{im}: KO (not enough points: {len(frame_obj_points)})")
            continue

        logger.info(f"{im}: OK ({len(frame_obj_points)} points)")
        object_points.append(frame_obj_points)
        image_points.append(frame_img_points)

        if debug:
            cv2.aruco.drawDetectedCornersCharuco(frame, char_corners, char_ids)
            cv2.imshow("img", frame)
            cv2.waitKey(1000)

    ret, camera_matrix, dist_coefs, _, _ = cv2.calibrateCamera(
        object_points,
        image_points,
        (camera_width, camera_height),
        None,
        None,
    )

    logger.debug(f"Camera calibration status: {ret}")
    logger.debug("- camera matrix:")
    logger.debug(camera_matrix)
    logger.debug("- dist coefs:")
    logger.debug(dist_coefs)

    save_camera_intrinsic_params(camera_matrix, dist_coefs, camera.intrinsic_params_filename)
    logger.info(f"Calibration parameters stored in: {camera.intrinsic_params_filename}")
