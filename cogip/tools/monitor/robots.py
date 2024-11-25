from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal

from cogip.entities.dynobstacle import DynCircleObstacleEntity, DynRectObstacleEntity
from cogip.entities.robot import RobotEntity
from cogip.models import DynObstacleList, DynObstacleRect, Pose
from cogip.widgets.gameview import GameView


class RobotManager(QtCore.QObject):
    """

    Attributes:
        sensors_emit_data_signal: Qt Signal emitting sensors data
    """

    sensors_emit_data_signal: qtSignal = qtSignal(int, list)

    def __init__(self, game_view: GameView):
        """
        Class constructor.

        Parameters:
            game_view: parent of the robots
        """
        super().__init__()
        self._game_view = game_view
        self._robots: dict[int, RobotEntity] = dict()
        self._available_robots: dict[int, RobotEntity] = dict()
        self._rect_obstacles_pool: list[DynRectObstacleEntity] = []
        self._round_obstacles_pool: list[DynCircleObstacleEntity] = []
        self._sensors_emulation: dict[int, bool] = {}

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
            robot = RobotEntity(robot_id, self._game_view.scene_entity)
            self._game_view.add_asset(robot)
            robot.sensors_emit_data_signal.connect(self.emit_sensors_data)
            robot.setEnabled(False)
            self._available_robots[robot_id] = robot

        robot = self._available_robots.pop(robot_id)
        robot.setEnabled(True)
        self._robots[robot_id] = robot
        if self._sensors_emulation.get(robot_id, False):
            robot.start_sensors_emulation()

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

    def new_robot_pose_current(self, robot_id: int, new_pose: Pose) -> None:
        """
        Set the robot's new pose current.

        Arguments:
            robot_id: ID of the robot
            new_pose: new robot pose
        """
        robot = self._robots.get(robot_id)
        if robot:
            robot.new_robot_pose_current(new_pose)

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
            robot.start_sensors_emulation()

    def emit_sensors_data(self, robot_id: int, data: list[int]) -> None:
        """
        Send sensors data to server.

        Arguments:
            robot_id: ID of the robot
            data: List of distances for each angle
        """
        self.sensors_emit_data_signal.emit(robot_id, data)

    def set_dyn_obstacles(self, dyn_obstacles: DynObstacleList) -> None:
        """
        Qt Slot

        Display the dynamic obstacles detected by the robot.

        Reuse already created dynamic obstacles to optimize performance
        and memory consumption.

        Arguments:
            dyn_obstacles: List of obstacles sent by the firmware through the serial port
        """
        # Store new and already existing dyn obstacles
        current_rect_obstacles = []
        current_round_obstacles = []

        for dyn_obstacle in dyn_obstacles:
            if isinstance(dyn_obstacle, DynObstacleRect):
                if len(self._rect_obstacles_pool):
                    obstacle = self._rect_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynRectObstacleEntity(self._game_view.scene_entity)

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, rotation=dyn_obstacle.angle)
                obstacle.set_size(length=dyn_obstacle.length_y, width=dyn_obstacle.length_x)
                #obstacle.set_bounding_box(dyn_obstacle.bb)

                current_rect_obstacles.append(obstacle)
            else:
                # Round obstacle
                if len(self._round_obstacles_pool):
                    obstacle = self._round_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynCircleObstacleEntity(self._game_view.scene_entity)

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, radius=dyn_obstacle.radius)
                #obstacle.set_bounding_box(dyn_obstacle.bb)

                current_round_obstacles.append(obstacle)

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
