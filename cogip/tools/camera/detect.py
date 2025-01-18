from functools import lru_cache
from typing import Annotated, Optional

import cv2
import numpy as np
import typer
from cv2.typing import MatLike
from numpy.typing import ArrayLike

from cogip.models import CameraExtrinsicParameters, Pose, Vertex
from . import logger
from .arguments import CameraName, VideoCodec
from .utils import (
    R_flip,
    get_camera_extrinsic_params_filename,
    get_camera_intrinsic_params_filename,
    load_camera_extrinsic_params,
    load_camera_intrinsic_params,
    rotate_2d,
    rotation_matrix_to_euler_angles,
    wrap_to_pi,
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
    20: 100.0,  # Back/Left    500/750
    21: 100.0,  # Back/Right   500/-750
    22: 100.0,  # Front/Left   -500/750
    23: 100.0,  # Front/Right  -500/-750
}

table_markers_positions = {
    20: {"x": 500, "y": 750},
    21: {"x": 500, "y": -750},
    22: {"x": -500, "y": 750},
    23: {"x": -500, "y": -750},
}

table_markers_tvecs = {n: np.array([t["x"], t["y"], 0]) for n, t in table_markers_positions.items()}

solar_panels_positions = {
    1: Vertex(x=-1037, y=1225, z=104),
    2: Vertex(x=-1037, y=1000, z=104),
    3: Vertex(x=-1037, y=775, z=104),
    4: Vertex(x=-1037, y=225, z=104),
    5: Vertex(x=-1037, y=0, z=104),
    6: Vertex(x=-1037, y=-225, z=104),
    7: Vertex(x=-1037, y=-775, z=104),
    8: Vertex(x=-1037, y=-1000, z=104),
    9: Vertex(x=-1037, y=-1225, z=104),
}

solar_panels_tvecs = {n: np.array([v.x, v.y, v.z]) for n, v in solar_panels_positions.items()}

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

    logger.error("Unknown robot position: {n}")

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
    ] = 640,
    camera_height: Annotated[
        int,
        typer.Option(
            help="Camera frame height",
            envvar="CAMERA_HEIGHT",
        ),
    ] = 480,
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

    # Load intrinsic parameters (mandatory)
    intrinsic_params_filename = get_camera_intrinsic_params_filename(
        id, camera_name, camera_codec, camera_width, camera_height
    )

    if not intrinsic_params_filename.exists():
        logger.error(f"Intrinsic parameters file not found: {intrinsic_params_filename}")
        return

    camera_matrix, dist_coefs = load_camera_intrinsic_params(intrinsic_params_filename)

    # Load extrinsic parameters (optional)
    extrinsic_params_filename = get_camera_extrinsic_params_filename(
        id, camera_name, camera_codec, camera_width, camera_height
    )

    if not extrinsic_params_filename.exists():
        logger.warning(f"Extrinsic parameters file not found: {extrinsic_params_filename}")
        return

    extrinsic_params = load_camera_extrinsic_params(extrinsic_params_filename)

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    cap = cv2.VideoCapture(str(camera_name.val), apiPreference=cv2.CAP_V4L2)
    fourcc = cv2.VideoWriter_fourcc(*camera_codec.val)
    ret = cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    if not ret:
        logger.warning(f"Video codec {camera_codec.val} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    if not ret:
        logger.warning(f"Frame width {camera_width} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
    if not ret:
        logger.warning(f"Frame height {camera_height} not supported")

    cv2.namedWindow("Marker Detection", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_EXPANDED)

    while True:
        _, frame = cap.read()

        dst = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect marker corners
        marker_corners, marker_ids, _ = detector.detectMarkers(dst)

        # Draw detected markers
        cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

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

        # Handle solar panel markers
        solar_panel_markers = []
        if 47 in corners_by_id:
            solar_panel_markers = corners_by_id[47]
        get_solar_panel_positions(
            solar_panel_markers,
            camera_matrix,
            dist_coefs,
            extrinsic_params,
            get_robot_position(robot_position),
        )

        if marker_ids is not None:
            # Draw all markers borders
            cv2.aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

            # Draw all markers axes
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
                cv2.drawFrameAxes(frame, camera_matrix, dist_coefs, rvec, tvec, 50)

        cv2.imshow("Marker Detection", frame)

        k = cv2.waitKey(1)
        if k == exit_key:
            break


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


def get_solar_panel_positions(
    markers: list[list[ArrayLike]],
    camera_matrix: MatLike,
    dist_coefs: MatLike,
    extrinsic_params: CameraExtrinsicParameters,
    robot_position: Pose | None,
) -> dict[int, float]:
    """
    Compute position of solar panels relative to the table coordinate system
    """
    panels: dict[int, float] = {}

    if len(markers) == 0:
        logger.debug("No solar panel marker found.")
        return panels

    for i, corners in enumerate(markers):
        # Get marker coordinates in the camera coordinate system
        _, rvec, tvec = cv2.solvePnP(
            get_marker_points(marker_sizes[47]),
            corners,
            camera_matrix,
            dist_coefs,
            False,
            cv2.SOLVEPNP_IPPE_SQUARE,
        )
        marker_tvec = tvec[:, 0]
        marker_rvec = rvec[:, 0]
        marker_rvec_degrees = np.rad2deg(marker_rvec)
        logger.info(f"Solar panel marker {i}:")
        logger.info(
            f"- Position relative to camera coordinate system: "
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
        marker_camera_tvec = -R_tc * np.matrix(marker_tvec).T  # 2D matrix: [[x], [y], [z]]
        marker_camera_tvec = np.asarray(marker_camera_tvec).flatten()  # 1D array: [x, y, z]
        marker_camera_rvec = rotation_matrix_to_euler_angles(R_flip * R_tc)  # 1D array: [roll, pitch, yaw]

        # Use same axes as the table
        marker_camera_tvec[0], marker_camera_tvec[1] = marker_camera_tvec[1], marker_camera_tvec[0]
        marker_camera_rvec[2] = -marker_camera_rvec[2]

        marker_camera_rvec_degrees = np.rad2deg(marker_camera_rvec)

        logger.info(
            "- Camera position relative to the marker in the marker axes: "
            f"X={marker_camera_tvec[0]:.0f} "
            f"Y={marker_camera_tvec[1]:.0f} "
            f"Z={marker_camera_tvec[2]:.0f} "
            f"roll={marker_camera_rvec_degrees[0]:.0f} "
            f"pitch={marker_camera_rvec_degrees[1]:.0f} "
            f"yaw={marker_camera_rvec_degrees[2]:.0f}"
        )

        # Compute marker position relative to the camera in the robot axes
        hypot = np.hypot(marker_tvec[1], marker_tvec[2])

        angle_marker = np.arcsin(marker_tvec[1] / hypot)
        angle_camera = np.pi / 2 - marker_camera_rvec[0] + angle_marker

        dist_camera_to_marker_tvec = np.array(
            [
                hypot * np.cos(angle_camera),
                -marker_tvec[0],
                hypot * np.sin(angle_camera),
            ]
        )
        logger.info(
            "- Marker position relative to the camera in the robot axes: "
            f"X={dist_camera_to_marker_tvec[0]:.0f} "
            f"Y={dist_camera_to_marker_tvec[1]:.0f} "
            f"Z={dist_camera_to_marker_tvec[2]:.0f}"
        )

        # Compute marker position relative to the robot in the robot axes
        dist_robot_to_marker_tvec = np.array(
            [
                dist_camera_to_marker_tvec[0] - extrinsic_params.x,
                dist_camera_to_marker_tvec[1] - extrinsic_params.y,
                extrinsic_params.z - dist_camera_to_marker_tvec[2],
            ]
        )
        logger.info(
            "- Marker position relative to the robot in the robot axes: "
            f"X={dist_robot_to_marker_tvec[0]:.0f} "
            f"Y={dist_robot_to_marker_tvec[1]:.0f} "
            f"Z={dist_robot_to_marker_tvec[2]:.0f}"
        )

        if robot_position:
            # Compute solar panel angle in the table coordinate system
            panel_angle = wrap_to_pi(np.deg2rad(robot_position.O) - marker_camera_rvec[2])
            panel_angle_degrees = np.rad2deg(panel_angle)
            logger.info(f"- Angle in table the axes : {panel_angle_degrees:.0f} ({marker_camera_rvec[2]})")

            # Compute solar panel marker position  in the table coordinate system
            table_robot_rotated = rotate_2d(
                np.array([robot_position.x, robot_position.y]), -np.deg2rad(robot_position.O)
            )
            table_marker_rotated = table_robot_rotated + dist_robot_to_marker_tvec[0:2]
            table_marker_xy = rotate_2d(table_marker_rotated, np.deg2rad(robot_position.O))
            table_marker_tvec = np.array([table_marker_xy[0], table_marker_xy[1], dist_robot_to_marker_tvec[2]])

            logger.info(
                "- Marker position relative in the table coordinates: "
                f"X={table_marker_tvec[0]:.0f} "
                f"Y={table_marker_tvec[1]:.0f} "
                f"Z={table_marker_tvec[2]:.0f}"
            )

            # Find solar panel id
            for n, panel_tvec in solar_panels_tvecs.items():
                # Solar panel are separated by a minimum of 250 mm.
                # Considering the precision of the detection, a solar panel detected less than 60 mm around
                # its theoretical position is enough to identify a specific solar panel.
                maximum_detection_distance = 60
                if np.linalg.norm(panel_tvec - table_marker_tvec) < maximum_detection_distance:
                    panels[n] = panel_angle_degrees
                    break

    return panels


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
