from functools import lru_cache
from typing import Annotated, Optional

import cv2
import numpy as np
import typer
from cv2.typing import MatLike
from numpy.typing import ArrayLike

from cogip.models import CameraExtrinsicParameters, Pose
from . import logger
from .arguments import CameraName, VideoCodec
from .camera import RPiCamera, USBCamera
from .utils import (
    R_flip,
    decompose_transform_matrix,
    euler_angles_to_rotation_matrix,
    load_camera_intrinsic_params,
    make_transform_matrix,
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
    # Crates
    36: 30,  # blue hazelnut crates
    41: 30,  # empty crates
    47: 30,  # yellow hazelnut crates
}

table_markers_positions = {
    20: {"x": 400, "y": 900},
    21: {"x": 400, "y": -900},
    22: {"x": -400, "y": 900},
    23: {"x": -400, "y": -900},
}

table_markers_tvecs = {n: np.array([t["x"], t["y"], 0]) for n, t in table_markers_positions.items()}


robot_width = 295.0
robot_length = 295.0


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
    robot_position: Pose | None,
):
    """Compute camera position on table and camera position in robot if robot position is given"""
    if len(markers) == 0:
        logger.debug("No table marker found, skip robot positioning.")
        return

    # Compute camera position on table
    table_camera_tvec, table_camera_rvec_degrees = get_camera_position_on_table(
        markers,
        camera_matrix,
        dist_coefs,
    )

    # Compute camera position in robot if robot position is given
    if robot_position:
        get_camera_position_in_robot(
            robot_position,
            table_camera_tvec,
            table_camera_rvec_degrees,
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
) -> tuple[ArrayLike, ArrayLike]:
    """
    Return a 2-tuple of 3D NDArray of camera position and its rotation in degrees
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

    # Marker in Camera frame (from solvePnP)
    R_cm = cv2.Rodrigues(marker_rvec)[0]
    M_cm = make_transform_matrix(R_cm, marker_tvec)

    # Camera in Marker frame (inverse transformation)
    M_mc = np.linalg.inv(M_cm)

    # Rotation matrix from Marker frame to Table frame.
    # Marker frame (defined in get_marker_points): X Right, Y Up, Z Out (Up)
    # Table frame: X Up, Y Left, Z Up
    # Mapping: X_table = Y_marker, Y_table = -X_marker, Z_table = Z_marker
    R_tm = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    M_tm = make_transform_matrix(R_tm, table_markers_tvecs[marker_id])

    # Camera in Table frame
    M_tc = M_tm @ M_mc

    # Extract results
    R_tc, T_table = decompose_transform_matrix(M_tc)

    # Convert rotation matrix to Euler angles (degrees).
    # Apply R_flip (180 deg rotation around X) to match the convention expected
    # by rotation_matrix_to_euler_angles.
    camera_rvec = rotation_matrix_to_euler_angles(R_flip @ R_tc)
    camera_rvec_degrees = np.rad2deg(camera_rvec)

    logger.info(
        "- Camera position in table coordinate system: "
        f"X={T_table[0]:.0f} "
        f"Y={T_table[1]:.0f} "
        f"Z={T_table[2]:.0f} "
        f"Roll={camera_rvec_degrees[0]:.0f} "
        f"Pitch={camera_rvec_degrees[1]:.0f} "
        f"Yaw={camera_rvec_degrees[2]:.0f}"
    )

    return (T_table, camera_rvec_degrees)


def get_camera_position_in_robot(
    robot_position: Pose,
    table_camera_tvec: ArrayLike,
    table_camera_rvec: ArrayLike,
) -> CameraExtrinsicParameters:
    """
    Compute camera extrinsic parameters (position relative to robot center)
    using the known robot position on the table.
    """

    # Robot in Table frame (Transformation T_rt)
    robot_angle_rad = np.deg2rad(robot_position.O)
    R_rt = np.array(
        [
            [np.cos(robot_angle_rad), -np.sin(robot_angle_rad), 0],
            [np.sin(robot_angle_rad), np.cos(robot_angle_rad), 0],
            [0, 0, 1],
        ]
    )
    T_rt = np.array([robot_position.x, robot_position.y, 0])
    M_rt = make_transform_matrix(R_rt, T_rt)

    # Camera in Table frame (Transformation T_ct)
    # Reconstruct rotation matrix from Euler angles.
    # Note: table_camera_rvec was computed using R_flip * R_tc, so we reverse it here.
    R_ct_flipped = euler_angles_to_rotation_matrix(np.deg2rad(table_camera_rvec))
    R_ct = R_flip @ R_ct_flipped
    M_ct = make_transform_matrix(R_ct, table_camera_tvec)

    # Camera in Robot frame (Transformation T_cr)
    # M_cr = M_rt^(-1) * M_ct
    M_cr = np.linalg.inv(M_rt) @ M_ct

    # Extract results
    R_cr, T_cr = decompose_transform_matrix(M_cr)

    # Convert R_cr to Euler angles.
    # Apply R_flip again to maintain consistency with the storage convention.
    R_cr_flipped = R_flip @ R_cr
    rvec_cr = rotation_matrix_to_euler_angles(R_cr_flipped)
    rvec_cr_degrees = np.rad2deg(rvec_cr)

    logger.info(
        f"Camera extrinsic parameters: X={T_cr[0]:.0f} Y={T_cr[1]:.0f} Z={T_cr[2]:.0f} "
        f"Roll={rvec_cr_degrees[0]:.0f} Pitch={rvec_cr_degrees[1]:.0f} Yaw={rvec_cr_degrees[2]:.0f}"
    )
    return CameraExtrinsicParameters(
        x=T_cr[0],
        y=T_cr[1],
        z=T_cr[2],
        roll=rvec_cr_degrees[0],
        pitch=rvec_cr_degrees[1],
        yaw=rvec_cr_degrees[2],
        angle=rvec_cr_degrees[2],  # Backward compatibility
    )
