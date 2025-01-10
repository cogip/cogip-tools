from enum import IntEnum
from multiprocessing.managers import DictProxy

from cogip import models
from cogip.cpp.libraries.avoidance import Avoidance as CppAvoidance
from cogip.cpp.libraries.models import Coords as SharedCoord
from cogip.cpp.libraries.models import CoordsList as SharedCoordList
from cogip.cpp.libraries.obstacles import ObstacleCircle as SharedObstacleCircle
from cogip.cpp.libraries.obstacles import ObstaclePolygon as SharedObstaclePolygon
from cogip.cpp.libraries.obstacles import ObstacleRectangle as SharedObstacleRectangle
from .. import logger
from ..table import Table
from .visibility_road_map import visibility_road_map

try:
    from .debug import DebugWindow
except ImportError:
    DebugWindow = bool


class AvoidanceStrategy(IntEnum):
    Disabled = 0
    VisibilityRoadMapQuadPid = 1
    VisibilityRoadMapLinearPoseDisabled = 2
    StopAndGo = 3
    AvoidanceCpp = 4


class Avoidance:
    def __init__(self, table: Table, shared_properties: DictProxy):
        self.shared_properties = shared_properties
        self.visibility_road_map = VisibilityRoadMapWrapper(table, shared_properties)
        self.last_robot_width: int = -1
        self.last_expand: int = -1
        border_coords = SharedCoordList()
        border_coords.append(table.x_min, table.y_min)
        border_coords.append(table.x_max, table.y_min)
        border_coords.append(table.x_max, table.y_max)
        border_coords.append(table.x_min, table.y_max)
        border_obstacle = SharedObstaclePolygon(border_coords, bounding_box_margin=0, bounding_box_points_number=0)
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
        obstacles: list[SharedObstacleCircle | SharedObstacleRectangle],
    ) -> list[models.PathPose]:
        strategy = AvoidanceStrategy(self.shared_properties["avoidance_strategy"])
        robot_width = self.shared_properties["robot_width"]
        match strategy:
            case AvoidanceStrategy.Disabled:
                path = [models.PathPose(**pose_current.model_dump()), goal.model_copy()]
            case AvoidanceStrategy.AvoidanceCpp:
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
            case _:
                expand = int(robot_width / 2 * self.shared_properties["obstacle_bb_margin"])
                if self.last_robot_width != robot_width or self.last_expand != expand:
                    self.visibility_road_map.set_properties(robot_width, expand)
                    self.last_robot_width = robot_width
                    self.last_expand = expand
                path = self.visibility_road_map.get_path(pose_current, goal, obstacles)
                if strategy == AvoidanceStrategy.StopAndGo and len(path) > 2:
                    path = []
        return path


class VisibilityRoadMapWrapper:
    def __init__(self, table: Table, shared_properties: DictProxy):
        if DebugWindow and shared_properties["plot"]:
            self.win = DebugWindow()
        else:
            self.win = None
        self.table = table
        self.shared_properties = shared_properties
        self.robot_width: int = 0

    def set_properties(self, robot_width: int, expand: int):
        self.robot_width = robot_width
        self.expand = expand

        self.visibility_road_map = visibility_road_map.VisibilityRoadMap(
            x_min=self.table.x_min + robot_width / 2,
            x_max=self.table.x_max - robot_width / 2,
            y_min=self.table.y_min + robot_width / 2,
            y_max=self.table.y_max - robot_width / 2,
            win=self.win,
        )

    def get_path(
        self,
        start: models.PathPose,
        goal: models.PathPose,
        obstacles: list[SharedObstacleCircle | SharedObstacleRectangle],
    ) -> list[models.PathPose]:
        if self.win:
            self.win.reset()
            self.win.point_start = start
            self.win.point_goal = goal.pose

        converted_obstacles = []

        for obstacle in obstacles:
            x_list: list[float] = []
            y_list: list[float] = []
            for point in obstacle.bounding_box:
                x_list.append(point.x)
                y_list.append(point.y)
            x_list.append(x_list[0])
            y_list.append(y_list[0])
            x_list.reverse()
            y_list.reverse()
            converted_obstacles.append(
                visibility_road_map.ObstaclePolygon(
                    x_list,
                    y_list,
                    self.expand,
                )
            )
        if self.win:
            self.win.dyn_obstacles.extend(converted_obstacles)
            self.win.update()

        # Compute path
        rx, ry = self.visibility_road_map.planning(
            start.x,
            start.y,
            goal.x,
            goal.y,
            converted_obstacles,
            self.shared_properties["max_distance"],
        )

        if self.win:
            self.win.path = [(x, y) for x, y in zip(rx, ry)]
            self.win.update()

        # Convert computed path in the planner format
        path = [models.PathPose(x=x, y=y) for x, y in zip(rx, ry)]

        if len(path) == 1:
            # No path found, or start and goal are the same pose
            return []

        if len(path) > 1:
            # Replace first and last poses with original start and goal
            # to preserve the same properties (like orientation)
            path[-1] = goal.model_copy()
            path[0] = start.model_copy()

        return path
