from enum import IntEnum
from multiprocessing.managers import DictProxy

from cogip import models
from ..table import Table
from .visibility_road_map import visibility_road_map

from .. import logger
from cogip.cpp.avoidance import CppAvoidance,CppObstaclePolygon
from cogip.models import DynRoundObstacle, DynObstaclePolygon

import math

try:
    from .debug import DebugWindow
except ImportError:
    DebugWindow = bool


fixed_obstacles = []


class AvoidanceStrategy(IntEnum):
    Disabled = 0
    VisibilityRoadMapQuadPid = 1
    VisibilityRoadMapLinearPoseDisabled = 2
    StopAndGo = 3
    VisibilityRoadMapCpp = 4


class Avoidance:
    def __init__(self, table: Table, shared_properties: DictProxy):
        self.shared_properties = shared_properties
        self.visibility_road_map = VisibilityRoadMapWrapper(table, shared_properties)
        self.cpp_avoidance = CppAvoidance(CppObstaclePolygon([
            (table.x_min,table.y_min),
            (table.x_max,table.y_min),
            (table.x_max,table.y_max),
            (table.x_min,table.y_max),
            ]))
        self.last_robot_width: int = -1
        self.last_expand: int = -1

    def check_recompute(
            self,
            pose_current: models.PathPose,
            goal: models.PathPose
    ) -> bool:
        strategy = AvoidanceStrategy(self.shared_properties["avoidance_strategy"])
        match strategy:
            case AvoidanceStrategy.VisibilityRoadMapCpp:
                return self.cpp_avoidance.check_recompute(pose_current.x, pose_current.y, goal.x, goal.y)
            case _:
                return True

    def get_path(
        self,
        pose_current: models.PathPose,
        goal: models.PathPose,
        obstacles: models.DynObstacleList,
    ) -> list[models.PathPose]:
        strategy = AvoidanceStrategy(self.shared_properties["avoidance_strategy"])
        robot_width = self.shared_properties["robot_width"]
        match strategy:
            case AvoidanceStrategy.Disabled:
                path = [models.PathPose(**pose_current.model_dump()), goal.model_copy()]
            case AvoidanceStrategy.VisibilityRoadMapCpp:
                path = [models.PathPose(**pose_current.model_dump())]
                self.cpp_avoidance.clear_dynamic_obstacles()
                for obstacle in obstacles:
                    self.cpp_avoidance.add_dynamic_obstacle(obstacle._cython_obj)
                if self.cpp_avoidance.build_graph(pose_current.x, pose_current.y, goal.x, goal.y):
                    path = [models.PathPose(**pose_current.model_dump())]
                    for i in range(0, self.cpp_avoidance.get_path_size()):
                        pose = models.PathPose.from_cython(self.cpp_avoidance.get_path_pose(i))
                        pose.bypass_final_orientation = True
                        path.append(pose)
                    while len(path) > 1 and math.dist((path[1].x, path[1].y), (pose_current.x, pose_current.y)) < 10:
                        del path[1]
                    path.append(goal.model_copy())
            case _:
                expand = int(robot_width * self.shared_properties["obstacle_bb_margin"])
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
        self.fixed_obstacles: list[visibility_road_map.ObstaclePolygon] = []

    def set_properties(self, robot_width: int, expand: int):
        self.robot_width = robot_width
        self.expand = expand
        self.fixed_obstacles.clear()

        for obstacle in fixed_obstacles:
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle]))
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])

            self.fixed_obstacles.append(visibility_road_map.ObstaclePolygon(x_list, y_list, expand))

        if self.win:
            self.win.fixed_obstacles = self.fixed_obstacles[:]

        self.visibility_road_map = visibility_road_map.VisibilityRoadMap(
            x_min=self.table.x_min + robot_width / 2,
            x_max=self.table.x_max - robot_width / 2,
            y_min=self.table.y_min + robot_width / 2,
            y_max=self.table.y_max - robot_width / 2,
            fixed_obstacles=self.fixed_obstacles,
            win=self.win,
        )

    def get_path(
        self,
        start: models.PathPose,
        goal: models.PathPose,
        obstacles: models.DynObstacleList,
    ) -> list[models.PathPose]:
        if self.win:
            self.win.reset()
            self.win.point_start = start
            self.win.point_goal = goal.pose

        converted_obstacles = []

        for obstacle in obstacles:
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle.bb]))
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])
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
            path[0] = models.PathPose(**start.model_dump())

        return path
