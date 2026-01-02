from pathlib import Path

import cv2
import cv2.typing
import numpy as np
from numpy.typing import ArrayLike

from cogip.models import CameraExtrinsicParameters

#
# Utility functions to handle rotation matrices
#

# 180 deg rotation matrix around the X axis
R_flip = np.zeros((3, 3), dtype=np.float32)
R_flip[0, 0] = 1.0
R_flip[1, 1] = -1.0
R_flip[2, 2] = -1.0


def is_rotation_matrix(R):
    """
    Checks if a matrix is a valid rotation matrix

    Source: https://www.learnopencv.com/rotation-matrix-to-euler-angles/
    """
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    ident = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(ident - shouldBeIdentity)
    return n < 1e-6


def rotation_matrix_to_euler_angles(R):
    """
    Calculates rotation matrix to euler angles.
    The result is the same as MATLAB except the order
    of the euler angles (x and z are swapped).

    Source: https://www.learnopencv.com/rotation-matrix-to-euler-angles/
    """
    assert is_rotation_matrix(R)

    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])


def euler_angles_to_rotation_matrix(theta: ArrayLike) -> cv2.typing.MatLike:
    """
    Calculates rotation matrix from euler angles.

    Arguments:
        theta: Euler angles in radians (roll, pitch, yaw)
    """
    R_x = np.array(
        [
            [1, 0, 0],
            [0, np.cos(theta[0]), -np.sin(theta[0])],
            [0, np.sin(theta[0]), np.cos(theta[0])],
        ]
    )

    R_y = np.array(
        [
            [np.cos(theta[1]), 0, np.sin(theta[1])],
            [0, 1, 0],
            [-np.sin(theta[1]), 0, np.cos(theta[1])],
        ]
    )

    R_z = np.array(
        [
            [np.cos(theta[2]), -np.sin(theta[2]), 0],
            [np.sin(theta[2]), np.cos(theta[2]), 0],
            [0, 0, 1],
        ]
    )

    R = np.dot(R_z, np.dot(R_y, R_x))

    return R


def make_transform_matrix(R: ArrayLike, t: ArrayLike) -> np.ndarray:
    """Create a 4x4 transformation matrix from rotation matrix and translation vector."""
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = np.asarray(t).flatten()
    return M


def decompose_transform_matrix(M: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Decompose a 4x4 transformation matrix into rotation matrix and translation vector."""
    return M[:3, :3].copy(), M[:3, 3].copy()


def extrinsic_params_to_matrix(params: CameraExtrinsicParameters) -> np.ndarray:
    """Convert camera extrinsic parameters to a 4x4 transformation matrix."""
    rvec_degrees = np.array([params.roll, params.pitch, params.yaw])
    R_flipped = euler_angles_to_rotation_matrix(np.deg2rad(rvec_degrees))
    R = R_flip @ R_flipped
    t = np.array([params.x, params.y, params.z])
    return make_transform_matrix(R, t)


#
# Utility functions to handle calibration parameters
#


def save_camera_intrinsic_params(camera_matrix: cv2.typing.MatLike, dist_coefs: cv2.typing.MatLike, path: Path):
    """Save the camera matrix and the distortion coefficients to given path/file."""
    cv_file = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", camera_matrix)
    cv_file.write("D", dist_coefs)
    cv_file.release()


def load_camera_intrinsic_params(path: Path) -> tuple[cv2.typing.MatLike, cv2.typing.MatLike]:
    """Loads camera matrix and distortion coefficients."""
    cv_file = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    camera_matrix = cv_file.getNode("K").mat()
    dist_coefs = cv_file.getNode("D").mat()
    cv_file.release()
    return camera_matrix, dist_coefs


def save_camera_extrinsic_params(params: CameraExtrinsicParameters, path: Path):
    """Save the camera position relative to robot center to given path/file."""
    path.write_text(params.model_dump_json(indent=2))


def load_camera_extrinsic_params(path: Path) -> CameraExtrinsicParameters:
    """Loads camera position relative to robot center."""
    return CameraExtrinsicParameters.model_validate_json(path.read_text())
