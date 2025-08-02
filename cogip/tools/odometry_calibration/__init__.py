import numpy as np

from cogip.utils.logger import Logger

from cogip.models import Pose

logger = Logger("cogip-odometry-calibration")

square_path_cw = [
    Pose(500 , 0, np.pi / 2),
    Pose(500, 500, np.pi),
    Pose(0, 500, -np.pi / 2),
    Pose(0, 0, 0),
]

square_path_ccw = [
    Pose(500 , 0, -np.pi / 2),
    Pose(500, -500, np.pi),
    Pose(0, -500, np.pi / 2),
    Pose(0, 0, 0),
]
