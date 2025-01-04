from PySide6 import QtCore

from cogip.entities.dynobstacle import DynCircleObstacleEntity, DynRectObstacleEntity
from cogip.entities.robot import RobotEntity
from cogip.models import Pose
from cogip.tools.monitor.mainwindow import MainWindow


class RobotManager(QtCore.QObject):
    def __init__(self, win: MainWindow):
        """
        Class constructor.

        Parameters:
            game_view: parent of the robots
        """
        super().__init__()
        self._win = win
        self._game_view = win.game_view
        self._robots: dict[int, RobotEntity] = dict()
        self._available_robots: dict[int, RobotEntity] = dict()
        self._rect_obstacles_pool: list[DynRectObstacleEntity] = []
        self._round_obstacles_pool: list[DynCircleObstacleEntity] = []
        self._sensors_emulation: dict[int, bool] = {}
        self._update_obstacles = QtCore.QTimer()
        self._update_obstacles.timeout.connect(self.update_obstacles)
        self._update_obstacles_interval = 50

    def add_robot(self, robot_id: int, virtual: bool = False) -> None:
        """
        Add a new robot.

        Parameters:
            robot_id: ID of the new robot
            virtual: whether the robot is virtual or not
        """
        if robot_id in self._robots:
            return

        if self._available_robots.get(robot_id) is None:
            robot = RobotEntity(robot_id, self._win, self._game_view.scene_entity)
            self._game_view.add_asset(robot)
            robot.setEnabled(False)
            self._available_robots[robot_id] = robot

        robot = self._available_robots.pop(robot_id)
        robot.setEnabled(True)
        self._robots[robot_id] = robot
        if self._sensors_emulation.get(robot_id, False):
            robot.start_sensors_emulation()

        if len(self._robots) == 1:
            self._update_obstacles.start(self._update_obstacles_interval)

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.

        Parameters:
            robot_id: ID of the robot to remove
        """
        robot = self._robots.pop(robot_id)
        robot.stop_sensors_emulation()
        robot.setEnabled(False)
        self._available_robots[robot_id] = robot
        if len(self._robots) == 0:
            self._update_obstacles.stop()

    def new_robot_pose_order(self, robot_id: int, new_pose: Pose) -> None:
        """
        Set the robot's new pose order.

        Arguments:
            robot_id: ID of the robot
            new_pose: new robot pose
        """
        robot = self._robots.get(robot_id)
        if robot:
            robot.new_robot_pose_order(new_pose)

    def start_sensors_emulation(self, robot_id: int) -> None:
        """
        Start timers triggering sensors update and sensors data emission.

        Arguments:
            robot_id: ID of the robot
        """
        self._sensors_emulation[robot_id] = True
        robot = self._robots.get(robot_id)
        if robot:
            robot.start_sensors_emulation()

    def stop_sensors_emulation(self, robot_id: int) -> None:
        """
        Stop timers triggering sensors update and sensors data emission.

        Arguments:
            robot_id: ID of the robot
        """
        self._sensors_emulation[robot_id] = False
        robot = self._robots.get(robot_id)
        if robot:
            robot.stop_sensors_emulation()

    def update_obstacles(self) -> None:
        """
        Qt Slot

        Display the dynamic obstacles detected by the robot.

        Reuse already created dynamic obstacles to optimize performance
        and memory consumption.
        """
        # Store new and already existing dyn obstacles
        current_rect_obstacles = []
        current_round_obstacles = []

        for robot_id in self._robots:
            robot = self._robots.get(robot_id)
            if robot.shared_circle_obstacles is not None:
                for circle_obstacle in robot.shared_circle_obstacles:
                    if len(self._round_obstacles_pool):
                        obstacle = self._round_obstacles_pool.pop(0)
                        obstacle.setEnabled(True)
                    else:
                        obstacle = DynCircleObstacleEntity(self._game_view.scene_entity)

                    obstacle.set_position(
                        x=circle_obstacle.center.x,
                        y=circle_obstacle.center.y,
                        radius=circle_obstacle.radius,
                    )
                    obstacle.set_bounding_box(circle_obstacle.bounding_box)

                    current_round_obstacles.append(obstacle)

            if robot.shared_rectangle_obstacles is not None:
                for rectangle_obstacle in robot.shared_rectangle_obstacles:
                    if len(self._rect_obstacles_pool):
                        obstacle = self._rect_obstacles_pool.pop(0)
                        obstacle.setEnabled(True)
                    else:
                        obstacle = DynRectObstacleEntity(self._game_view.scene_entity)

                    obstacle.set_position(
                        x=rectangle_obstacle.center.x,
                        y=rectangle_obstacle.center.y,
                        rotation=rectangle_obstacle.center.angle,
                    )
                    obstacle.set_size(length=rectangle_obstacle.length_y, width=rectangle_obstacle.length_x)
                    obstacle.set_bounding_box(rectangle_obstacle.bounding_box)

                    current_rect_obstacles.append(obstacle)

        # Disable remaining dyn obstacles
        while len(self._rect_obstacles_pool):
            dyn_obstacle = self._rect_obstacles_pool.pop(0)
            dyn_obstacle.setEnabled(False)
            current_rect_obstacles.append(dyn_obstacle)

        while len(self._round_obstacles_pool):
            dyn_obstacle = self._round_obstacles_pool.pop(0)
            dyn_obstacle.setEnabled(False)
            current_round_obstacles.append(dyn_obstacle)

        self._rect_obstacles_pool = current_rect_obstacles
        self._round_obstacles_pool = current_round_obstacles

    def disable_robots(self):
        """Disable all enabled robots."""
        for robot in self._robots.values():
            if robot.isEnabled():
                robot.setEnabled(False)
