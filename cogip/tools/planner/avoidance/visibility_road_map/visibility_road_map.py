"""

Visibility Road Map Planner

author: Atsushi Sakai (@Atsushi_twi)

"""

import math
from copy import deepcopy

import numpy as np

from .dijkstra_search import DijkstraSearch
from .geometry import Geometry

try:
    from ..debug import DebugWindow
except ImportError:
    DebugWindow = bool

from cogip.models import DynObstacle

class VisibilityRoadMap:
    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        fixed_obstacles: list["DynObstacle"] = [],
        win: DebugWindow | None = None,
    ):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.win = win

        self.fixed_nodes: list[DijkstraSearch.Node] = []

        for obstacle in fixed_obstacles:
            for coord in obstacle.bb():
                if coord.x < self.x_min or coord.x > self.x_max or coord.y < self.y_min or coord.y > self.y_max:
                    continue
                self.fixed_nodes.append(DijkstraSearch.Node(coord.x, coord.y))

    def planning(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        obstacles: list["DynObstacle"],
        max_distance: int,
    ):
        nodes = deepcopy(self.fixed_nodes)

        nodes.extend(self.generate_visibility_nodes(start_x, start_y, goal_x, goal_y, obstacles))

        filtered_nodes = []
        for node in nodes:
            if node.x == goal_x and node.y == goal_y:
                filtered_nodes.append(node)
                continue
            if math.dist((start_x, start_y), (node.x, node.y)) < max_distance:
                filtered_nodes.append(node)

        road_map_info = self.generate_road_map_info(filtered_nodes, obstacles)

        if self.win:
            self.plot_road_map(filtered_nodes, road_map_info)

        rx, ry = DijkstraSearch(self.win).search(
            start_x,
            start_y,
            goal_x,
            goal_y,
            [node.x for node in filtered_nodes],
            [node.y for node in filtered_nodes],
            road_map_info,
        )

        return rx, ry

    def generate_visibility_nodes(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        obstacles: list["DynObstacle"],
    ):
        # add start and goal as nodes
        nodes = [DijkstraSearch.Node(start_x, start_y), DijkstraSearch.Node(goal_x, goal_y, 0, None)]

        for obstacle in obstacles:
            for coord in obstacle.bb():
                if coord.x < self.x_min or coord.x > self.x_max or coord.y < self.y_min or coord.y > self.y_max:
                    continue
                nodes.append(DijkstraSearch.Node(coord.x, coord.y))

        if self.win:
            self.win.visibility_nodes = [(node.x, node.y) for node in nodes]
            self.win.update()

        return nodes

    def generate_road_map_info(self, nodes: list[DijkstraSearch.Node], obstacles: list["ObstaclePolygon"]) -> list[int]:
        road_map_info_list = []

        for target_node in nodes:
            road_map_info = []
            for node_id, node in enumerate(nodes):
                if np.hypot(target_node.x - node.x, target_node.y - node.y) <= 0.1:
                    continue

                is_valid = True
                for obstacle in obstacles:
                    if not obstacle.is_edge_valid(target_node.x, target_node.y, node.x, node.y):
                        is_valid = False
                        break
                if is_valid:
                    road_map_info.append(node_id)

            road_map_info_list.append(road_map_info)

        return road_map_info_list

    @staticmethod
    def is_edge_valid(target_node, node, obstacle):
        for i in range(len(obstacle.bb()) - 1):
            p1 = Geometry.Point(target_node.x, target_node.y)
            p2 = Geometry.Point(node.x, node.y)
            p3 = Geometry.Point(obstacle.bb()[i].x, obstacle.bb()[i].y)
            p4 = Geometry.Point(obstacle.bb()[i + 1].x, obstacle.bb()[i + 1].y)

            if Geometry.is_seg_intersect(p1, p2, p3, p4):
                return False

        return True

    def plot_road_map(self, nodes: list[DijkstraSearch.Node], road_map_info_list: list[int]):
        if not self.win:
            return

        self.win.road_map.clear()
        for i, node in enumerate(nodes):
            for index in road_map_info_list[i]:
                self.win.road_map.append((node.x, node.y, nodes[index].x, nodes[index].y))
        self.win.update()
