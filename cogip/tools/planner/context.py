from cogip.cpp.libraries.shared_memory import SharedProperties
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
from .pose import AdaptedPose
from .table import TableEnum


class GameContext:
    """
    A class recording the current game context.
    """

    def __init__(self, shared_properties: SharedProperties):
        self.shared_properties = shared_properties
        self.game_duration: int = 100
        self.minimum_score: int = 0
        self.reset()

        self.tribunes_in_robot = 0

    def reset(self):
        """
        Reset the context.
        """
        self.score = self.minimum_score
        self.countdown = self.game_duration
        self.last_countdown = self.game_duration
        self.tribunes_in_robot = 0
        self.create_artifacts()
        self.create_fixed_obstacles()
        self.create_actuators_states()

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
        if self.shared_properties.table == TableEnum.Training:
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge1].enabled = False
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge2].enabled = False
            self.opponent_construction_areas[ConstructionAreaID.OppositeSideLarge3].enabled = False

        # Tribunes
        for id, tribune in tribune_positions.items():
            adapted_pose = AdaptedPose(**tribune.model_dump())
            self.tribunes[id] = Tribune(**adapted_pose.model_dump(), id=id)

        if self.shared_properties.table == TableEnum.Training:
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
        if self.shared_properties.robot_id == 1:
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
            self.shared_properties.robot_id == 1
            and self.shared_properties.table == TableEnum.Training
            or self.shared_properties.robot_id == 5
        ):
            self.fixed_obstacles[FixedObstacleID.Ramp].enabled = False
            self.fixed_obstacles[FixedObstacleID.Scene].enabled = False
            self.fixed_obstacles[FixedObstacleID.Pami5Path].enabled = False

        if self.shared_properties.table == TableEnum.Training:
            for obstacle in self.fixed_obstacles.values():
                obstacle.x -= 1000

    def create_actuators_states(self):
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[PositionalActuatorEnum] = {}
