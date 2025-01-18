from cogip.models.actuators import (
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorEnum,
    Servo,
    ServoEnum,
)
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from . import actions
from .avoidance.avoidance import AvoidanceStrategy
from .camp import Camp
from .pose import AdaptedPose, Pose
from .positions import StartPosition
from .properties import Properties
from .table import Table, TableEnum, tables


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """

    def __init__(self):
        self.properties = Properties()
        self.game_duration: int = 90 if self.properties.robot_id == 1 else 100
        self.minimum_score: int = 0
        self.camp = Camp()
        self.strategy = actions.Strategy.BackAndForth
        self._table = TableEnum.Game
        self.avoidance_strategy = AvoidanceStrategy.AvoidanceCpp
        self.reset()

    @property
    def table(self) -> Table:
        """
        Selected table.
        """
        return tables[self._table]

    @table.setter
    def table(self, new_table: TableEnum):
        self._table = new_table

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = self.minimum_score
        self.countdown = self.game_duration
        self.create_artifacts()
        self.create_fixed_obstacles()
        self.create_actuators_states()

    @property
    def default_controller(self) -> ControllerEnum:
        match self.strategy:
            case actions.Strategy.AngularSpeedTest:
                return ControllerEnum.ANGULAR_SPEED_TEST
            case actions.Strategy.LinearSpeedTest:
                return ControllerEnum.LINEAR_SPEED_TEST
            case _:
                return ControllerEnum.QUADPID

    def get_start_pose(self, n: StartPosition) -> Pose:
        """
        Define the possible start positions.
        Default positions for blue camp.
        """
        match n:
            case StartPosition.Top:
                return AdaptedPose(
                    x=1000 - 450 + self.properties.robot_width / 2,
                    y=-(1500 - 450 + self.properties.robot_length / 2),
                    O=90,
                )
            case StartPosition.Bottom:
                pose = AdaptedPose(
                    x=-785,
                    y=-1285,
                    O=90,
                )
                if self.camp.color == Camp.Colors.yellow and self.strategy == actions.Strategy.BackAndForth:
                    pose.O = 90
                return pose
            case StartPosition.Opposite:
                return AdaptedPose(
                    x=-450 / 2 + self.properties.robot_width / 2,
                    y=1500 - 450 + self.properties.robot_width / 2,
                    O=-90,
                )
            case StartPosition.PAMI2:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2,
                    y=-self.properties.robot_width / 2,
                    O=180,
                )
            case StartPosition.PAMI3:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_width / 2,
                    y=-33,
                    O=-90,
                )
            case StartPosition.PAMI4:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_width / 2,
                    y=-(450 - self.properties.robot_length / 2),
                    O=-90,
                )
            case StartPosition.PAMI2_TRAINING:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2 - 1000,
                    y=-self.properties.robot_width / 2,
                    O=180,
                )
            case StartPosition.PAMI3_TRAINING:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2 - 1000,
                    y=-450 / 2,
                    O=180,
                )
            case StartPosition.PAMI4_TRAINING:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_width / 2 - 1000,
                    y=-(450 - self.properties.robot_length / 2),
                    O=-90,
                )
            case _:
                return AdaptedPose()

    def get_available_start_poses(self) -> list[StartPosition]:
        """
        Get start poses available depending on camp and table.
        """
        start_pose_indices = []
        for p in StartPosition:
            pose = self.get_start_pose(p)
            if self.table.contains(pose):
                start_pose_indices.append(p)
        return start_pose_indices

    def create_artifacts(self):
        # Positions are related to the default camp blue.
        pass

    def create_fixed_obstacles(self):
        # Positions are related to the default camp blue.
        pass

    def create_actuators_states(self):
        self.servo_states: dict[ServoEnum, Servo] = {}
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[ServoEnum | PositionalActuatorEnum] = {}
