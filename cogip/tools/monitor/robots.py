from PySide6 import QtCore

from cogip.entities.dynobstacle import DynCircleObstacleEntity, DynRectObstacleEntity
from cogip.entities.robot import RobotEntity
from cogip.models import Pose, Vertex
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
        self._rect_obstacles_pool: list[DynRectObstacleEntity] = []
        self._round_obstacles_pool: list[DynCircleObstacleEntity] = []
        self._update_obstacles = QtCore.QTimer()
        self._update_obstacles.timeout.connect(self.update_obstacles)
        self._update_obstacles_interval = 100
        self.virtual_planner = False
        self.virtual_detector = False

    def add_robot(self, robot_id: int, virtual_planner: bool, virtual_detector: bool) -> None:
        """
        Add the robot.

        Parameters:
            robot_id: ID of the robot
            virtual_planner: whether the planner is virtual or not,
                if planner is virtual, use shared memory to get the robot current, pose order and obstacles.
            virtual_detector: whether the detector is virtual or not,
                if detector is virtual, detect virtual obstacles and write them in shared memory.
        """
        self.virtual_planner = virtual_planner
        self.virtual_detector = virtual_detector
        self.robot = RobotEntity(
            robot_id,
            self._win,
            self._game_view.scene_entity,
            virtual_planner=virtual_planner,
            virtual_detector=virtual_detector,
        )
        self._game_view.add_asset(self.robot)

        if virtual_planner:
            self._update_obstacles.start(self._update_obstacles_interval)

    def del_robot(self, robot_id: int = 0) -> None:
        """
        Remove a robot.

        Parameters:
            robot_id: ID of the robot to remove
        """
        if self.virtual_planner:
            self._update_obstacles.stop()
        self.robot.setParent(None)
        self.robot.delete_shared_memory()
        self.robot = None

    def new_robot_pose_order(self, new_pose: Pose) -> None:
        """
        Set the robot's new pose order.

        Arguments:
            new_pose: new robot pose
        """
        if self.robot:
            self.robot.new_robot_pose_order(new_pose)

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

        if self.robot:
            if self.robot.shared_circle_obstacles is not None:
                self.robot.shared_obstacles_lock.start_reading()
                for circle_obstacle in self.robot.shared_circle_obstacles:
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
                self.robot.shared_obstacles_lock.finish_reading()

            if self.robot.shared_rectangle_obstacles is not None:
                for rectangle_obstacle in self.robot.shared_rectangle_obstacles:
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

    def update_shared_obstacles(self, obstacles: list[Vertex]):
        if self.robot:
            self.robot.shared_monitor_obstacles_lock.start_writing()
            self.robot.shared_monitor_obstacles.clear()
            for obstacle in obstacles:
                self.robot.shared_monitor_obstacles.append(obstacle.x, obstacle.y)
            self.robot.shared_monitor_obstacles_lock.finish_writing()
