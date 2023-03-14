from enum import IntEnum

from cogip import models
from .visibility_road_map import visibility_road_map
from .. import pose
from ..properties import Properties


borders = [
    models.Vertex(x=0, y=1000),
    models.Vertex(x=3000, y=1000),
    models.Vertex(x=3000, y=-1000),
    models.Vertex(x=0, y=-1000)
]

fixed_obstacles = [
    [
        models.Vertex(x=0, y=15),
        models.Vertex(x=300, y=15),
        models.Vertex(x=300, y=-15),
        models.Vertex(x=0, y=-15),
    ],
    [
        models.Vertex(x=3000 - 300, y=15),
        models.Vertex(x=3000, y=15),
        models.Vertex(x=3000, y=-15),
        models.Vertex(x=3000 - 300, y=-15),
    ],
    [
        models.Vertex(x=1500 - 150, y=-1000 + 30),
        models.Vertex(x=1500 + 150, y=-1000 + 30),
        models.Vertex(x=1500 + 150, y=-1000),
        models.Vertex(x=1500 - 150, y=-1000),
    ],
    [
        models.Vertex(x=1500 - 150, y=1000),
        models.Vertex(x=1500 + 150, y=1000),
        models.Vertex(x=1500 + 150, y=1000 - 30),
        models.Vertex(x=1500 - 150, y=1000 - 30),
    ]
]


class AvoidanceStrategy(IntEnum):
    Disabled = 0
    VisibilityRoadMap = 1


class Avoidance:
    def __init__(self, robot_id: int, properties: Properties):
        self.robot_id = robot_id
        self.properties = properties
        self.visibility_road_map = VisibilityRoadMapWrapper(robot_id, self.properties.plot)
        self.last_robot_width: int = -1
        self.last_expand: int = -1

    def get_path(
            self,
            pose_current: models.Pose,
            goal: pose.Pose,
            obstacles: models.DynObstacleList,
            strategy: AvoidanceStrategy = AvoidanceStrategy.Disabled) -> list[pose.Pose]:
        match strategy:
            case AvoidanceStrategy.VisibilityRoadMap:
                expand = int(self.properties.robot_width * self.properties.obstacle_bb_margin)
                if self.last_robot_width != self.properties.robot_width or self.last_expand != expand:
                    self.visibility_road_map.set_properties(self.properties.robot_width, expand)
                    self.last_robot_width = self.properties.robot_width
                    self.last_expand = expand
                return self.visibility_road_map.get_path(pose_current, goal, obstacles)
            case _:
                return [pose.Pose(**pose_current.dict()), goal.copy()]


class VisibilityRoadMapWrapper:
    def __init__(self, robot_id: int):
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

        self.visibility_road_map = visibility_road_map.VisibilityRoadMap(
            x_min=borders[0].x + robot_width / 2,
            x_max=borders[2].x - robot_width / 2,
            y_min=borders[2].y + robot_width / 2,
            y_max=borders[0].y - robot_width / 2,
            fixed_obstacles=self.fixed_obstacles
        )

    def get_path(
            self,
            start: models.Pose,
            goal: pose.Pose,
            obstacles: models.DynObstacleList) -> list[pose.Pose]:
        converted_obstacles = []

        for obstacle in obstacles:
            if not isinstance(obstacle, models.DynRoundObstacle):
                continue
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle.bb]))
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])
            converted_obstacles.append(visibility_road_map.ObstaclePolygon(
                x_list,
                y_list,
                self.expand
            ))

        # Compute path
        rx, ry = self.visibility_road_map.planning(
            start.x, start.y,
            goal.x, goal.y, converted_obstacles)

        # Convert computed path in the planner format
        path = [pose.Pose(x=x, y=y) for x, y in zip(rx, ry)]

        if len(path) == 1:
            # No path found, or start and goal are the same pose
            return []

        if len(path) > 1:
            # Replace first and last poses with original start and goal
            # to preserve the same properties (like orientation)
            path[-1] = goal.copy()
            path[0] = pose.Pose(**start.dict())

        return path
