from cogip.models.actuators import (
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorEnum,
)
from cogip.models.artifacts import (
    ConstructionArea,
    ConstructionAreaID,
    ConstructionAreaSmall,
    FixedObstacle,
    FixedObstacleID,
    Tribune,
    TribuneID,
    construction_area_positions,
    tribune_positions,
)
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
        self.game_duration: int = 100
        self.minimum_score: int = 0
        self.camp = Camp()
        self.avoidance_strategy = AvoidanceStrategy.AvoidanceCpp
        self.reset()

        self.tribunes_in_robot = 0

    @property
    def table(self) -> Table:
        """
        Selected table.
        """
        return tables[self.properties.table]

    @property
    def start_pose(self) -> Pose:
        """
        Start pose.
        """
        return self.start_poses[self.properties.start_position]

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = self.minimum_score
        self.countdown = self.game_duration
        self.last_countdown = self.game_duration
        self.tribunes_in_robot = 0
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
                x=550 + 100 * 0.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI3: AdaptedPose(
                x=550 + 100 * 1.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI4: AdaptedPose(
                x=550 + 100 * 2.5,
                y=-1350 - self.properties.robot_length / 2,
                O=90,
            ),
            StartPosition.PAMI5: AdaptedPose(
                x=550 + 100 * 3.5,
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

    def is_valid_start_position(self, position: StartPosition) -> bool:
        if self.properties.table == TableEnum.Training and position == StartPosition.Opposite:
            return False
        if self.properties.robot_id == 1 and position not in [
            StartPosition.Top,
            StartPosition.Bottom,
            StartPosition.Opposite,
        ]:
            return False
        return True

    def create_artifacts(self):
        # Positions are related to the default camp blue.
        self.construction_areas: dict[ConstructionAreaID, ConstructionArea] = {}
        self.opponent_construction_areas: dict[ConstructionAreaID, ConstructionArea] = {}
        self.tribunes: dict[TribuneID, Tribune] = {}

        # Construction areas
        for id, area in construction_area_positions.items():
            adapted_pose = AdaptedPose(**area.model_dump())
            self.construction_areas[id] = ConstructionAreaSmall(**adapted_pose.model_dump(), id=id, enabled=False)
            self.opponent_construction_areas[id] = ConstructionAreaSmall(
                x=adapted_pose.x,
                y=-adapted_pose.y,
                O=-adapted_pose.O,
                id=id,
            )

        self.opponent_construction_areas[ConstructionAreaID.LocalBottomLarge3].enabled = False
        self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge3].enabled = False
        if self.properties.table == TableEnum.Training:
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge1].enabled = False
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge2].enabled = False
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge3].enabled = False

        # Tribunes
        for id, tribune in tribune_positions.items():
            adapted_pose = AdaptedPose(**tribune.model_dump())
            self.tribunes[id] = Tribune(**adapted_pose.model_dump(), id=id)

        if self.properties.table == TableEnum.Training:
            self.tribunes[TribuneID.LocalTop] = self.tribunes[TribuneID.LocalTopTraining].model_copy(
                update={"id": TribuneID.LocalTop}
            )
            self.tribunes[TribuneID.LocalTop].x -= 73.0 / 2
            self.tribunes[TribuneID.LocalCenter].x -= 73.0 / 2
        del self.tribunes[TribuneID.LocalTopTraining]

    def create_fixed_obstacles(self):
        # Positions are related to the default camp blue.
        self.fixed_obstacles: dict[FixedObstacleID, FixedObstacle] = {}

        # Ramp
        self.fixed_obstacles[FixedObstacleID.Ramp] = FixedObstacle(
            **AdaptedPose(x=900, y=-650).model_dump(),
            length=400,
            width=200,
            id=FixedObstacleID.Ramp,
        )

        # Scene
        self.fixed_obstacles[FixedObstacleID.Scene] = FixedObstacle(
            **AdaptedPose(x=825, y=-225).model_dump(),
            length=450,
            width=450,
            id=FixedObstacleID.Scene,
        )

        # Pami 5 path
        self.fixed_obstacles[FixedObstacleID.Pami5Path] = FixedObstacle(
            **AdaptedPose(x=930, y=-1175).model_dump(),
            length=650,
            width=50,
            id=FixedObstacleID.Pami5Path,
        )

        # Opponent ramp
        self.fixed_obstacles[FixedObstacleID.OpponentRamp] = FixedObstacle(
            **AdaptedPose(x=900, y=650).model_dump(),
            length=400,
            width=200,
            id=FixedObstacleID.OpponentRamp,
        )

        # Opponent scene
        self.fixed_obstacles[FixedObstacleID.OpponentScene] = FixedObstacle(
            **AdaptedPose(x=825, y=225).model_dump(),
            length=450,
            width=450,
            id=FixedObstacleID.OpponentScene,
        )

        # Backstage
        self.fixed_obstacles[FixedObstacleID.Backstage] = FixedObstacle(
            **AdaptedPose(x=1000 - 450 / 2, y=-1500 + 150 + 450 / 2).model_dump(),
            length=450,
            width=450,
            enabled=False,
            id=FixedObstacleID.Backstage,
        )

        # PAMIs starting area for robot ID 1, the main robot.
        if self.properties.robot_id == 1:
            self.fixed_obstacles[FixedObstacleID.PamiStartArea] = FixedObstacle(
                **AdaptedPose(x=825, y=-1425).model_dump(),
                length=150,
                width=450,
                id=FixedObstacleID.PamiStartArea,
            )

            self.fixed_obstacles[FixedObstacleID.PitArea] = FixedObstacle(
                **AdaptedPose(x=375, y=-350).model_dump(),
                length=700,
                width=350,
                enabled=False,
                id=FixedObstacleID.PitArea,
            )

            self.fixed_obstacles[FixedObstacleID.OpponentPitArea] = FixedObstacle(
                **AdaptedPose(x=375, y=350).model_dump(),
                length=700,
                width=350,
                enabled=False,
                id=FixedObstacleID.OpponentPitArea,
            )

        if (
            self.properties.robot_id == 1
            and self.properties.table == TableEnum.Training
            or self.properties.robot_id == 5
        ):
            self.fixed_obstacles[FixedObstacleID.Ramp].enabled = False
            self.fixed_obstacles[FixedObstacleID.Scene].enabled = False
            self.fixed_obstacles[FixedObstacleID.Pami5Path].enabled = False

        if self.properties.table == TableEnum.Training:
            for obstacle in self.fixed_obstacles.values():
                obstacle.x -= 1000

    def create_actuators_states(self):
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[PositionalActuatorEnum] = {}
