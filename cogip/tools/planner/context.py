from cogip.models.actuators import (
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorEnum,
    Servo,
    ServoEnum,
)
from cogip.models.artifacts import (
    ConstructionArea,
    ConstructionAreaID,
    ConstructionAreaLarge,
    ConstructionAreaSmall,
    Tribune,
    TribuneID,
    construction_area_positions,
    tribune_positions,
)
from cogip.models.models import DynObstacleRect
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from . import actions
from .avoidance.avoidance import AvoidanceStrategy
from .camp import Camp
from .pose import AdaptedPose, Pose
from .positions import StartPosition
from .table import Table, TableEnum, tables


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """

    def __init__(self):
        from .properties import Properties

        self.properties = Properties()
        self.game_duration: int = 90 if self.properties.robot_id == 1 else 100
        self.minimum_score: int = 0
        self.camp = Camp()
        self.avoidance_strategy = AvoidanceStrategy.AvoidanceCpp
        self.reset()

    @property
    def table(self) -> Table:
        """
        Selected table.
        """
        return tables[self.properties.table]

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = self.minimum_score
        self.countdown = self.game_duration
        self.create_start_poses()
        self.create_artifacts()
        self.create_fixed_obstacles()
        self.create_actuators_states()

    @property
    def default_controller(self) -> ControllerEnum:
        match self.properties.strategy:
            case actions.Strategy.PidAngularSpeedTest:
                return ControllerEnum.ANGULAR_SPEED_TEST
            case actions.Strategy.PidLinearSpeedTest:
                return ControllerEnum.LINEAR_SPEED_TEST
            case _:
                return ControllerEnum.QUADPID

    def get_start_pose(self, n: StartPosition) -> Pose:
        """
        Define the possible start positions.
        Default positions for blue camp.
        """
        return self.start_poses.get(n, AdaptedPose())

    def create_start_poses(self):
        self.start_poses = {
            StartPosition.Bottom: AdaptedPose(
                x=-550 - self.properties.robot_length / 2,
                y=-100 - self.properties.robot_width / 2,
                O=0,
            ),
            StartPosition.Top: AdaptedPose(
                x=550 + self.properties.robot_length / 2,
                y=-900 - self.properties.robot_width / 2,
                O=180,
            ),
            StartPosition.Opposite: AdaptedPose(
                x=-350 + self.properties.robot_width / 2,
                y=1050 + self.properties.robot_length / 2,
                O=-90,
            ),
            StartPosition.PAMI2: AdaptedPose(
                x=550 + self.properties.robot_width * 0.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI3: AdaptedPose(
                x=550 + self.properties.robot_width * 1.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI4: AdaptedPose(
                x=550 + self.properties.robot_width * 2.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI5: AdaptedPose(
                x=550 + self.properties.robot_width * 3.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
        }

        # Adapt poses for training table
        if self.properties.table == TableEnum.Training:
            self.start_poses[StartPosition.Top].x -= 1000
            self.start_poses[StartPosition.PAMI2].x -= 1000
            self.start_poses[StartPosition.PAMI3].x -= 1000
            self.start_poses[StartPosition.PAMI4].x -= 1000
            self.start_poses[StartPosition.PAMI5].x -= 1000

    def get_available_start_poses(self) -> list[StartPosition]:
        """
        Get start poses available depending on camp and table.
        """
        start_pose_indices = []
        for p in StartPosition:
            if self.properties.robot_id == 1 and p not in [
                StartPosition.Top,
                StartPosition.Bottom,
                StartPosition.Opposite,
            ]:
                continue
            pose = self.get_start_pose(p)
            if self.table.contains(pose):
                start_pose_indices.append(p)
        return start_pose_indices

    def create_artifacts(self):
        # Positions are related to the default camp blue.
        self.construction_areas: dict[ConstructionAreaID, ConstructionArea] = {}
        self.opponent_construction_areas: dict[ConstructionAreaID, ConstructionArea] = {}
        self.tribunes: dict[TribuneID, Tribune] = {}

        # Construction areas
        for id, area in construction_area_positions.items():
            match id:
                case ConstructionAreaID.LocalBottomSmall | ConstructionAreaID.OppositeBottomSmall:
                    ConstructionAreaClass = ConstructionAreaSmall
                case _:
                    ConstructionAreaClass = ConstructionAreaLarge
            adapted_pose = AdaptedPose(**area.model_dump())
            self.construction_areas[id] = ConstructionAreaClass(**adapted_pose.model_dump(), id=id, enabled=False)
            self.opponent_construction_areas[id] = ConstructionAreaClass(
                x=adapted_pose.x,
                y=-adapted_pose.y,
                O=-adapted_pose.O,
                id=id,
            )

        for id, tribune in tribune_positions.items():
            adapted_pose = AdaptedPose(**tribune.model_dump())
            self.tribunes[id] = Tribune(**adapted_pose.model_dump(), id=id)

        if self.properties.table == TableEnum.Training:
            self.opponent_construction_areas[ConstructionAreaID.OppositeCenterLarge].enabled = False

    def create_fixed_obstacles(self):
        # Positions are related to the default camp blue.
        self.fixed_obstacles: list[DynObstacleRect] = []

        # Opponent starting area, ramp and scene.
        pose = AdaptedPose(x=775, y=750)
        self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=450, length_y=1500)]

        # Ramp and scene except for robot ID 5, the superstar.
        if self.properties.robot_id != 5:
            # Ramp
            pose = AdaptedPose(x=900, y=-650)
            self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=200, length_y=400)]

            # Scene
            pose = AdaptedPose(x=825, y=-225)
            self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=450, length_y=450)]

        # PAMIs starting area for robot ID 1, the main robot.
        if self.properties.robot_id == 1:
            pose = AdaptedPose(x=825, y=-1425)
            self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=450, length_y=150)]

    def create_actuators_states(self):
        self.servo_states: dict[ServoEnum, Servo] = {}
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[ServoEnum | PositionalActuatorEnum] = {}
