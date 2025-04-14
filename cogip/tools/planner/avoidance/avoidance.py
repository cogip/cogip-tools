from enum import IntEnum
from multiprocessing.managers import DictProxy

from cogip import models
from cogip.cpp.libraries.avoidance import Avoidance as CppAvoidance
from cogip.cpp.libraries.models import Coords as SharedCoord
from cogip.cpp.libraries.models import CoordsList as SharedCoordList
from cogip.cpp.libraries.obstacles import ObstaclePolygon as SharedObstaclePolygon
from .. import logger
from ..table import Table


class AvoidanceStrategy(IntEnum):
    Disabled = 0
    StopAndGo = 1
    AvoidanceCpp = 2


class Avoidance:
    def __init__(self, table: Table, shared_properties: DictProxy):
        self.shared_properties = shared_properties
        border_coords = SharedCoordList()
        border_coords.append(table.x_min, table.y_min)
        border_coords.append(table.x_max, table.y_min)
        border_coords.append(table.x_max, table.y_max)
        border_coords.append(table.x_min, table.y_max)
        border_obstacle = SharedObstaclePolygon(border_coords, bounding_box_margin=0)
        self.cpp_avoidance = CppAvoidance(border_obstacle)

    def check_recompute(self, pose_current: models.PathPose, goal: models.PathPose) -> bool:
        strategy = AvoidanceStrategy(self.shared_properties["avoidance_strategy"])
        match strategy:
            case AvoidanceStrategy.AvoidanceCpp:
                return self.cpp_avoidance.check_recompute(
                    SharedCoord(x=pose_current.x, y=pose_current.y),
                    SharedCoord(x=goal.x, y=goal.y),
                )
            case _:
                return True

    def get_path(
        self,
        pose_current: models.PathPose,
        goal: models.PathPose,
    ) -> list[models.PathPose]:
        strategy = AvoidanceStrategy(self.shared_properties["avoidance_strategy"])
        match strategy:
            case AvoidanceStrategy.Disabled:
                path = [models.PathPose(**pose_current.model_dump()), goal.model_copy()]
            case _:
                path = [models.PathPose(**pose_current.model_dump())]
                res = self.cpp_avoidance.avoidance(
                    SharedCoord(pose_current.x, pose_current.y),
                    SharedCoord(goal.x, goal.y),
                )
                logger.debug(f"Avoidance: build graph success = {res}")
                if res:
                    for i in range(self.cpp_avoidance.get_path_size()):
                        shared_pose = self.cpp_avoidance.get_path_pose(i)
                        pose = models.PathPose(
                            x=shared_pose.x,
                            y=shared_pose.y,
                        )
                        pose.bypass_final_orientation = True
                        path.append(pose)

                    # Remove duplicates
                    path = [p for i, p in enumerate(path) if (p.x, p.y) not in {(p2.x, p2.y) for p2 in path[:i]}]

                    # Append final pose order
                    path.append(goal.model_copy())
                else:
                    path = []
                if strategy == AvoidanceStrategy.StopAndGo and len(path) > 2:
                    path = []
        return path
