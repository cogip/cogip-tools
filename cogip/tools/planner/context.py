from cogip.cpp.libraries.shared_memory import SharedProperties
from cogip.models.actuators import (
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorEnum,
)
from cogip.models.artifacts import (
    CollectionArea,
    CollectionAreaID,
    FixedObstacle,
    FixedObstacleID,
    Pantry,
    PantryID,
    collection_areas,
    pantries,
)
from cogip.tools.planner.pose import AdaptedPose
from cogip.tools.planner.table import TableEnum


class GameContext:
    """
    A class recording the current game context.
    """

    def __init__(self, shared_properties: SharedProperties, initialize: bool = True):
        self.shared_properties = shared_properties
        if initialize:
            self.minimum_score: int = 0
            self.game_duration: int = 100
            self.score = self.minimum_score
            self.front_free = True
            self.back_free = True
            self.collection_areas: dict[CollectionAreaID, CollectionArea] = {}
            self.pantries: dict[PantryID, Pantry] = {}
            self.fixed_obstacles: dict[FixedObstacleID, FixedObstacle] = {}
            self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
            self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {}
            self.emulated_actuator_states: set[PositionalActuatorEnum] = {}
            self.reset()

    def reset(self):
        """
        Reset the context.
        """
        self.score = self.minimum_score
        self.countdown = self.game_duration
        self.last_countdown = self.game_duration
        self.front_free = True
        self.back_free = True
        self.create_artifacts()
        self.create_fixed_obstacles()
        self.create_actuators_states()

    def deepcopy(self):
        """
        Return a deep copy of the GameContext instance.
        """
        new_ctx = GameContext(self.shared_properties, initialize=False)
        new_ctx.game_duration = self.game_duration
        new_ctx.minimum_score = self.minimum_score
        new_ctx.score = self.score
        new_ctx.front_free = self.front_free
        new_ctx.back_free = self.back_free
        new_ctx.countdown = self.countdown
        new_ctx.last_countdown = self.last_countdown
        new_ctx.fixed_obstacles = {k: v.model_copy() for k, v in self.fixed_obstacles.items()}
        new_ctx.collection_areas = {k: v.model_copy() for k, v in self.collection_areas.items()}
        new_ctx.pantries = {k: v.model_copy() for k, v in self.pantries.items()}
        return new_ctx

    def create_artifacts(self):
        self.collection_areas = {}
        for collection_area_id, values in collection_areas.items():
            x, y, angle, training = values
            enabled = self.shared_properties.table == TableEnum.Game or (
                self.shared_properties.table == TableEnum.Training and training
            )
            pose = AdaptedPose(x=x, y=y, O=angle)
            if angle is None:
                self.collection_areas[collection_area_id] = CollectionArea(
                    **pose.model_dump(include={"x", "y"}),
                    id=collection_area_id,
                    enabled=enabled,
                )
            else:
                self.collection_areas[collection_area_id] = CollectionArea(
                    **pose.model_dump(include={"x", "y", "O"}),
                    id=collection_area_id,
                    enabled=enabled,
                )

        self.pantries = {}
        for pantry_id, values in pantries.items():
            x, y, angle, training = values
            enabled = self.shared_properties.table == TableEnum.Game or (
                self.shared_properties.table == TableEnum.Training and training
            )
            pose = AdaptedPose(x=x, y=y, O=angle)
            if angle is None:
                self.pantries[pantry_id] = Pantry(
                    **pose.model_dump(include={"x", "y"}),
                    id=pantry_id,
                    enabled=enabled,
                )
            else:
                self.pantries[pantry_id] = Pantry(
                    **pose.model_dump(include={"x", "y", "O"}),
                    id=pantry_id,
                    enabled=enabled,
                )

        # We can consider that these pantries won't be used by the opponent robot
        if self.shared_properties.robot_id == 1:
            self.pantries[PantryID.LocalSide].enabled = False
            self.pantries[PantryID.LocalCenter].enabled = False
            self.pantries[PantryID.LocalBottom].enabled = False

        # Special case for nest, disabled on startup, special position on training table
        self.pantries[PantryID.Nest].enabled = False
        self.pantries[PantryID.Nest].x -= 1000
        self.pantries[PantryID.Nest].y -= 1050

    def create_fixed_obstacles(self):
        # Positions are related to the default camp blue.
        self.fixed_obstacles: dict[FixedObstacleID, FixedObstacle] = {}

        # Granary
        self.fixed_obstacles[FixedObstacleID.Granary] = FixedObstacle(
            x=775,
            y=0,
            length=1800,
            width=450,
            id=FixedObstacleID.Granary,
            enabled=self.shared_properties.robot_id != 5,
        )

        # Nest
        self.fixed_obstacles[FixedObstacleID.Nest] = FixedObstacle(
            **AdaptedPose(
                x=775 if self.shared_properties.table == TableEnum.Game else -225,
                y=-1200,
            ).model_dump(include={"x", "y"}),
            length=600,
            width=450,
            id=FixedObstacleID.Nest,
            enabled=self.shared_properties.robot_id == 5,
        )

        # Opposite Nest
        self.fixed_obstacles[FixedObstacleID.OppositeNest] = FixedObstacle(
            **AdaptedPose(x=775, y=1200).model_dump(include={"x", "y"}),
            length=600,
            width=450,
            id=FixedObstacleID.OppositeNest,
        )

        # Table
        self.fixed_obstacles[FixedObstacleID.Table] = FixedObstacle(
            x=-225 if self.shared_properties.table == TableEnum.Game else -725,
            y=0 if self.shared_properties.table == TableEnum.Game else -750,
            length=3000 if self.shared_properties.table == TableEnum.Game else 1500,
            width=1550 if self.shared_properties.table == TableEnum.Game else 550,
            id=FixedObstacleID.Table,
            enabled=self.shared_properties.robot_id == 5,
        )

    def create_actuators_states(self):
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[PositionalActuatorEnum] = {}
