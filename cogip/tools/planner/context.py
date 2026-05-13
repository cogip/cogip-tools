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
            self.cursor_moved = False
            self.front_crates: list[int | None] = [None, None, None, None]
            self.back_crates: list[int | None] = [None, None, None, None]
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
        self.cursor_moved = False
        self.front_crates = [None, None, None, None]
        self.back_crates = [None, None, None, None]
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
        new_ctx.cursor_moved = self.cursor_moved
        new_ctx.front_crates = self.front_crates.copy()
        new_ctx.back_crates = self.back_crates.copy()
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
            enabled=self.shared_properties.robot_id != 2,
        )

        # Nest
        self.fixed_obstacles[FixedObstacleID.Nest] = FixedObstacle(
            x=775 if self.shared_properties.table == TableEnum.Game else -225,
            y=-1200,
            length=600,
            width=450,
            id=FixedObstacleID.Nest,
            enabled=self.shared_properties.robot_id == 2,
        )

        # Opposite Nest
        self.fixed_obstacles[FixedObstacleID.OppositeNest] = FixedObstacle(
            x=775,
            y=1200,
            length=600,
            width=450,
            id=FixedObstacleID.OppositeNest,
        )

        # Table
        # Width reduced by 40 mm vs the table's true span so the inflated east
        # edge (center.x + (width + robot_width)/2) leaves enough room for the
        # Ninja's pantry-deposit pose at x=620 to fall outside the obstacle.
        self.fixed_obstacles[FixedObstacleID.Table] = FixedObstacle(
            x=-225 if self.shared_properties.table == TableEnum.Game else -725,
            y=0 if self.shared_properties.table == TableEnum.Game else -750,
            length=3000 if self.shared_properties.table == TableEnum.Game else 1500,
            width=1510 if self.shared_properties.table == TableEnum.Game else 510,
            id=FixedObstacleID.Table,
            enabled=self.shared_properties.robot_id == 2,
        )

        # Ninja Area 1: rectangle (650..800, -450..-350), center (725, -400),
        # 150 x 100 mm. Holds nut crates the Ninja picks up; enabled during
        # transit so the avoidance routes around it, disabled by the pickup
        # action while the robot enters to collect.
        self.fixed_obstacles[FixedObstacleID.NinjaArea1] = FixedObstacle(
            x=725,
            y=-400,
            width=150,
            length=100,
            id=FixedObstacleID.NinjaArea1,
            enabled=self.shared_properties.robot_id == 2,
        )

        # Ninja Area 2: rectangle (700..850, -200..-100), center (775, -150),
        # 150 x 100 mm. Same role as NinjaArea1 for the upper crate location.
        self.fixed_obstacles[FixedObstacleID.NinjaArea2] = FixedObstacle(
            x=820,
            y=-200,
            width=140,
            length=100,
            id=FixedObstacleID.NinjaArea2,
            enabled=self.shared_properties.robot_id == 2,
        )

        # Ninja Deposit: zone where BuildGroup leaves the assembled nut crates,
        # initial corners (750, -150) and (500, -350) → displayed bbox of
        # 250 x 200 mm centered at (625, -250). Enlarged by 20% on each axis,
        # then widened 100 mm along y (east-west) → displayed bbox of
        # 300 x 340 mm. `planner.update_obstacles` inflates each fixed
        # obstacle by `robot_width = 160 mm`, so the raw width/length stored
        # here are shrunk by 160 mm to land the inflated bbox at the desired
        # size.
        # Disabled by default; enabled in BuildGroup `before_pose17` so the
        # avoidance routes around the released crates from then on, then
        # disabled again before PantryDeposit pose 5 dives into the area.
        self.fixed_obstacles[FixedObstacleID.NinjaDeposit] = FixedObstacle(
            x=675,
            y=-250,
            width=160,
            length=200,
            id=FixedObstacleID.NinjaDeposit,
            enabled=False,
        )

        # Ninja Drop Zone: raw rectangle 150 x 150 mm centered at (675, -700).
        # `length` (y / east-west) shrunk by 50 mm vs the initial 200 mm
        # spec. Represents the start-area crate stacks; enabled by default
        # so the avoidance routes around them, disabled once DropFour
        # finishes its first deposit (pose 1) and re-enabled by pose 6
        # before parking west of the zone.
        self.fixed_obstacles[FixedObstacleID.NinjaDropZone] = FixedObstacle(
            x=675,
            y=-700,
            width=150,
            length=100,
            id=FixedObstacleID.NinjaDropZone,
            enabled=self.shared_properties.robot_id == 2,
        )

        # Ninja Crates Zone: raw rectangle 150 x 150 mm centered at
        # (675, -710) — pose 8 raw y minus 75 mm. Holds 3 crates the Ninja
        # will pick up in a separate action. Disabled by default; enabled
        # by DropFour `after_pose9` once the shake/recul moves are done.
        self.fixed_obstacles[FixedObstacleID.NinjaCratesZone] = FixedObstacle(
            x=675,
            y=-790,
            width=150,
            length=150,
            id=FixedObstacleID.NinjaCratesZone,
            enabled=False,
        )

    def create_actuators_states(self):
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[PositionalActuatorEnum] = {}
