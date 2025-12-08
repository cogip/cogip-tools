from typing import Annotated

import cv2
import typer


def cmd_charuco(
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
    """Display charuco board to check if is corresponds to the board used for calibration."""
    charuco_window_name = "Charuco Board"

    cv2.namedWindow(charuco_window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(charuco_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    board = cv2.aruco.CharucoBoard(
        (charuco_cols, charuco_rows),
        charuco_square_length,
        charuco_marker_length,
        aruco_dict,
    )
    board.setLegacyPattern(charuco_legacy)
    board_image = board.generateImage((charuco_cols * charuco_square_length, charuco_rows * charuco_square_length))
    cv2.imshow(charuco_window_name, board_image)
