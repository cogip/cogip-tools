from functools import lru_cache
from typing import Annotated, Optional

import cv2
import numpy as np
import typer
from cv2.typing import MatLike
from numpy.typing import ArrayLike

from cogip.models import Pose, Vertex
from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera
from .utils import (
    R_flip,
    load_camera_intrinsic_params,
    rotate_2d,
    rotation_matrix_to_euler_angles,
)

# Marker axes:
# - X: red
# - Y: green
# - Z: blue

marker_sizes: dict[int, float] = {
    # Blue robot markers
    1: 70.0,
    2: 70.0,
    3: 70.0,
    4: 70.0,
    5: 70.0,
    # Yellow robot markers
    6: 70.0,
    7: 70.0,
    8: 70.0,
    9: 70.0,
    10: 70.0,
    # Table markers
    20: 100.0,  # Back/Left    400/900
    21: 100.0,  # Back/Right   400/-900
    22: 100.0,  # Front/Left   -400/900
    23: 100.0,  # Front/Right  -400/-900
}

table_markers_positions = {
    20: {"x": 500, "y": 750},
    21: {"x": 500, "y": -750},
    22: {"x": -500, "y": 750},
    23: {"x": -500, "y": -750},
}

table_markers_tvecs = {n: np.array([t["x"], t["y"], 0]) for n, t in table_markers_positions.items()}

robot_width = 295.0
robot_length = 295.0


def marker_to_table_axes(tvec: ArrayLike, angle: int) -> tuple[ArrayLike, float]:
    return np.array([tvec[1], -tvec[0], tvec[2]]), -angle


def get_robot_position(n: int) -> Pose | None:
    """
    Define the possible start positions.
    """
    match n:
        case 1:  # Back left (yellow)
            return Pose(
                x=1000 - 450 + robot_width / 2,
                y=1500 - 450 + robot_width / 2,
                O=-90,
            )
        case 2:  # Front left (yellow)
            return Pose(
                x=-(1000 - 450 + robot_width / 2),
                y=1500 - 450 + robot_width / 2,
                O=-90,
            )
        case 3:  # Middle right (yellow)
            return Pose(
                x=robot_width / 2,
                y=-(1500 - 450 + robot_width / 2),
                O=90,
            )
        case 4:  # Back right (blue)
            return Pose(
                x=1000 - 450 + robot_width / 2,
                y=-(1500 - 450 + robot_width / 2),
                O=90,
            )
        case 5:  # Front right (blue)
            return Pose(
                x=-(1000 - 450 + robot_width / 2),
                y=-(1500 - 450 + robot_width / 2),
                O=90,
            )
        case 6:  # Middle left (blue)
            return Pose(
                x=robot_width / 2,
                y=-(1500 - 450 + robot_width / 2),
                O=90,
            )

    logger.error(f"Unknown robot position: {n}")

    return None


def cmd_detect(
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
    robot_position: Annotated[
        Optional[int],  # noqa
        typer.Option(
            help="Define the robot position",
            envvar="CAMERA_ROBOT_POSITION",
            min=1,
            max=6,
        ),
    ] = None,
):
    """Detect Aruco tags and estimate their positions"""
    exit_key = 27  # use this key (Esc) to exit before max_frames

    if not camera_name.val.exists():
        logger.error(f"Camera not found: {camera_name.val}")
        return

    if camera_name == CameraName.rpicam:
        CameraClass = RPiCamera
    else:
        CameraClass = USBCamera
    camera = CameraClass(id, camera_name, camera_codec, camera_width, camera_height)
    camera.open()

    # Load intrinsic parameters (mandatory)
    if not camera.intrinsic_params_filename.exists():
        logger.warning(f"Intrinsic parameters file not found: {camera.intrinsic_params_filename}")
        camera_matrix, dist_coefs = None, None
    else:
        camera_matrix, dist_coefs = load_camera_intrinsic_params(camera.intrinsic_params_filename)

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
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

    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    cv2.namedWindow("Marker Detection", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Marker Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        frame, stream_frame = camera.read()
        if frame is None:
            continue

        if len(frame.shape) == 2:
            dst = frame
        else:
            dst = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if stream_frame is None:
            if len(frame.shape) == 2:
                stream_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                stream_frame = frame

        # Detect marker corners
        marker_corners, marker_ids, _ = detector.detectMarkers(dst)

        # Classify detected markers by id and size
        corners_by_id = {}
        corners_by_size = {}
        if marker_ids is not None:
            for id, corners in zip(marker_ids, marker_corners):
                size = marker_sizes.get(id[0])
                if not size:
                    continue
                if id[0] not in corners_by_id:
                    corners_by_id[id[0]] = []
                corners_by_id[id[0]].append(corners)
                if size not in corners_by_size:
                    corners_by_size[size] = []
                corners_by_size[size].append((id[0], corners))

        if robot_position is not None and camera_matrix is not None and dist_coefs is not None:
            # Handle table markers
            table_markers = {
                id: corners[0]  # There can be only one marker of each id
                for id, corners in corners_by_id.items()
                if id in [20, 21, 22, 23]
            }
            handle_table_markers(
                table_markers,
                camera_matrix,
                dist_coefs,
                get_robot_position(robot_position),
            )

        if marker_ids is not None:
            # Draw all markers borders
            for i, corners in enumerate(marker_corners):
                cv2.polylines(stream_frame, [corners[0].astype(np.int32)], True, (255, 0, 255), 10)
                cv2.putText(
                    stream_frame,
                    str(marker_ids[i][0]),
                    tuple(corners[0][0].astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 0, 255),
                    2,
                )

            # Draw all markers axes
            if camera_matrix is not None and dist_coefs is not None:
                for id, corner in zip(marker_ids, marker_corners):
                    marker_id = id[0]
                    if marker_id not in marker_sizes:
                        logger.warning(f"Unknown marker found: {marker_id}")
                        continue

                    _, rvec, tvec = cv2.solvePnP(
                        get_marker_points(marker_sizes[marker_id]),
                        corner,
                        camera_matrix,
                        dist_coefs,
                        False,
                        cv2.SOLVEPNP_IPPE_SQUARE,
                    )
                    cv2.drawFrameAxes(stream_frame, camera_matrix, dist_coefs, rvec, tvec, 50, 5)

        cv2.imshow("Marker Detection", stream_frame)

        k = cv2.waitKey(1)
        if k == exit_key:
            break

    camera.close()


def handle_table_markers(
    markers: dict[int, MatLike],
    camera_matrix: MatLike,
    dist_coefs: MatLike,
    robot_position: Vertex | None,
):
    """Compute camera position on table and camera position in robot if robot position is given"""
    if len(markers) == 0:
        logger.debug("No table marker found, skip robot positioning.")
        return

    # Compute camera position on table
    table_camera_tvec, table_camera_angle = get_camera_position_on_table(
        markers,
        camera_matrix,
        dist_coefs,
    )

    # Compute camera position in robot if robot position is given
    if robot_position:
        get_camera_position_in_robot(
            robot_position,
            table_camera_tvec,
            table_camera_angle,
        )


@lru_cache
def get_marker_points(marker_size: float):
    """Get marker points matrix based on marker size, as used by cv2.solvePnP"""
    return np.array(
        [
            [-marker_size / 2, marker_size / 2, 0],
            [marker_size / 2, marker_size / 2, 0],
            [marker_size / 2, -marker_size / 2, 0],
            [-marker_size / 2, -marker_size / 2, 0],
        ],
        dtype=np.float32,
    )


def get_camera_position_on_table(
    table_markers: dict[int, MatLike],
    camera_matrix: MatLike,
    dist_coefs: MatLike,
) -> tuple[ArrayLike, float]:
    """
    Return a 3D NDArray of camera position and its rotation in radians
    in the table coordinate system.
    """
    tvecs = {}
    rvecs = {}
    distances = {}

    for id, corners in table_markers.items():
        # Get marker coordinates in the camera coordinate system
        _, rvec, tvec = cv2.solvePnP(
            get_marker_points(marker_sizes[id]),
            corners,
            camera_matrix,
            dist_coefs,
            False,
            cv2.SOLVEPNP_IPPE_SQUARE,
        )

        # Distance from the camera to the marker
        distance = np.sqrt(tvec[0] ** 2 + tvec[1] ** 2 + tvec[2] ** 2)

        # Keep the nearest marker for each id
        if id not in distances or distances[id] > distance:
            distances[id] = distance
            tvecs[id] = tvec
            rvecs[id] = rvec

    # Get nearest marker: sort by value (distance) in ascending order, and take first element key (id)
    marker_id, _ = sorted(distances.items(), key=lambda x: x[1])[0]
    marker_tvec = tvecs[marker_id][:, 0]
    marker_rvec = rvecs[marker_id][:, 0]
    marker_rvec_degrees = np.rad2deg(marker_rvec)

    logger.info(
        f"- Table marker {marker_id} position relative to camera coordinate system: "
        f"X={marker_tvec[0]:.0f} "
        f"Y={marker_tvec[1]:.0f} "
        f"Z={marker_tvec[2]:.0f} "
        f"roll={marker_rvec_degrees[0]:.0f} "
        f"pitch={marker_rvec_degrees[1]:.0f} "
        f"yaw={marker_rvec_degrees[2]:.0f}"
    )

    # Get camera coordinates relative to the marker in the marker axes
    R_ct = np.matrix(cv2.Rodrigues(marker_rvec)[0])
    R_tc = R_ct.T
    camera_tvec = -R_tc * np.matrix(marker_tvec).T  # 2D matrix: [[x], [y], [z]]
    camera_tvec = np.asarray(camera_tvec).flatten()  # 1D array: [x, y, z]
    camera_rvec = rotation_matrix_to_euler_angles(R_flip * R_tc)  # 1D array: [roll, pitch, yaw]
    camera_rvec_degrees = np.rad2deg(camera_rvec)

    logger.info(
        "- Camera position relative to the marker in the marker axes: "
        f"X={camera_tvec[0]:.0f} "
        f"Y={camera_tvec[1]:.0f} "
        f"Z={camera_tvec[2]:.0f} "
        f"Angle={camera_rvec_degrees[2]:.0f}"
    )

    # Get camera position relative to the marker in the table axes
    camera_tvec, camera_angle = marker_to_table_axes(camera_tvec, camera_rvec[2])
    camera_angle_degrees = np.degrees(camera_angle)
    logger.info(
        "- Camera position relative to the marker in the table axes: "
        f"X={camera_tvec[0]:.0f} "
        f"Y={camera_tvec[1]:.0f} "
        f"Z={camera_tvec[2]:.0f} "
        f"Angle={camera_angle_degrees:.0f}"
    )

    # Get camera position in the table coordinate system
    table_camera_tvec = camera_tvec + table_markers_tvecs[marker_id]

    logger.info(
        "- Camera position in table coordinate system: "
        f"X={table_camera_tvec[0]:.0f} "
        f"Y={table_camera_tvec[1]:.0f} "
        f"Z={table_camera_tvec[2]:.0f} "
        f"Angle={camera_angle_degrees:.0f}"
    )

    return (table_camera_tvec, camera_angle)


def get_camera_position_in_robot(
    robot_position: Vertex,
    table_camera_tvec: ArrayLike,
    table_camera_angle: float,
) -> Vertex:
    # If we know the real robot position on the table,
    # we can compute camera extrinsic parameters
    # (ie, the camera position relative to the robot center).
    # We consider that the camera is aligned with the robot on X axis.
    robot_tvec = np.array([robot_position.x, robot_position.y])

    camera_tvec_rotated = rotate_2d(table_camera_tvec[0:2], -table_camera_angle)
    robot_tvec_rotated = rotate_2d(robot_tvec, -table_camera_angle)
    relative_tvec = np.append(robot_tvec_rotated - camera_tvec_rotated, table_camera_tvec[2])
    logger.info(
        f"Camera extrinsic parameters: X={relative_tvec[0]:.0f} Y={relative_tvec[1]:.0f} Z={relative_tvec[2]:.0f}"
    )
    return Vertex(x=relative_tvec[0], y=relative_tvec[1], z=relative_tvec[2])
