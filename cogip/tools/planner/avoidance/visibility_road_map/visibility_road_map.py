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


class VisibilityRoadMap:
    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        win: DebugWindow | None = None,
    ):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.win = win

        self.fixed_nodes: list[DijkstraSearch.Node] = []

    def planning(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        obstacles: list["ObstaclePolygon"],
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
        obstacles: list["ObstaclePolygon"],
    ):
        # add start and goal as nodes
        nodes = [DijkstraSearch.Node(start_x, start_y), DijkstraSearch.Node(goal_x, goal_y, 0, None)]

        # add vertexes in configuration space as nodes
        for obstacle in obstacles:
            for vx, vy in zip(obstacle.cvx_list, obstacle.cvy_list):
                if vx < self.x_min or vx > self.x_max or vy < self.y_min or vy > self.y_max:
                    continue
                nodes.append(DijkstraSearch.Node(vx, vy))

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
                    if not self.is_edge_valid(target_node, node, obstacle):
                        is_valid = False
                        break
                if is_valid:
                    road_map_info.append(node_id)

            road_map_info_list.append(road_map_info)

        return road_map_info_list

    @staticmethod
    def is_edge_valid(target_node, node, obstacle):
        for i in range(len(obstacle.x_list) - 1):
            p1 = Geometry.Point(target_node.x, target_node.y)
            p2 = Geometry.Point(node.x, node.y)
            p3 = Geometry.Point(obstacle.x_list[i], obstacle.y_list[i])
            p4 = Geometry.Point(obstacle.x_list[i + 1], obstacle.y_list[i + 1])

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


class ObstaclePolygon:
    def __init__(self, x_list: list[float], y_list: list[float], expand_distance: float = 0.0):
        self.cvx_list = x_list
        self.cvy_list = y_list
        self.expand_distance = expand_distance
        self.x_list: list[float] = []
        self.y_list: list[float] = []

        self.calc_vertexes_in_configuration_space()
        self.x_list.append(self.x_list[0])
        self.y_list.append(self.y_list[0])
        self.cvx_list.pop(-1)
        self.cvy_list.pop(-1)

    def calc_vertexes_in_configuration_space(self):
        cvx_list = self.cvx_list[0:-1]
        cvy_list = self.cvy_list[0:-1]
        n_data = len(cvx_list)

        for index in range(n_data):
            offset_x, offset_y = self.calc_offset_xy(
                cvx_list[index - 1],
                cvy_list[index - 1],
                cvx_list[index],
                cvy_list[index],
                cvx_list[(index + 1) % n_data],
                cvy_list[(index + 1) % n_data],
            )
            self.x_list.append(offset_x)
            self.y_list.append(offset_y)

    def calc_offset_xy(self, px: float, py: float, x: float, y: float, nx: float, ny: float) -> tuple[float, float]:
        p_vec = math.atan2(y - py, x - px)
        n_vec = math.atan2(ny - y, nx - x)
        offset_vec = math.atan2(math.sin(p_vec) + math.sin(n_vec), math.cos(p_vec) + math.cos(n_vec)) + math.pi / 2.0
        offset_x = x - self.expand_distance * math.cos(offset_vec)
        offset_y = y - self.expand_distance * math.sin(offset_vec)
        return offset_x, offset_y
