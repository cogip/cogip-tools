from cogip.models.actuators import (
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorEnum,
    Servo,
    ServoEnum,
)
from cogip.models.artifacts import (
    DropoffZone,
    DropoffZoneID,
    Planter,
    PlanterID,
    PlantSupply,
    PlantSupplyID,
    PotSupply,
    PotSupplyID,
    SolarPanels,
    SolarPanelsID,
)
from cogip.models.models import DynObstacleRect,DynRoundObstacle
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
        self.avoidance_strategy = AvoidanceStrategy.VisibilityRoadMapCpp
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
        #self.create_artifacts()
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
        Default positions for yellow camp.
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
                if self.camp.color == Camp.Colors.blue and self.strategy == actions.Strategy.GameSolarFirst:
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
        # Positions are related to the default camp yellow.
        self.plant_supplies: dict[PlantSupplyID, PlantSupply] = {}
        self.pot_supplies: dict[PotSupplyID, PotSupply] = {}
        self.dropoff_zones: dict[DropoffZoneID, DropoffZone] = {}
        self.planters: dict[PlanterID, Planter] = {}
        self.solar_panels: dict[SolarPanelsID, SolarPanels] = {}

        bb_radius = 125 + self.properties.robot_width / 2

        # Plant supplies
        plant_supply_positions = {
            PlantSupplyID.CenterTop: AdaptedPose(x=500, y=0),
            PlantSupplyID.CenterBottom: AdaptedPose(x=-500, y=0),
            PlantSupplyID.LocalTop: AdaptedPose(x=300, y=-500),
            PlantSupplyID.LocalBottom: AdaptedPose(x=-300, y=-500),
            PlantSupplyID.OppositeTop: AdaptedPose(x=300, y=500),
            PlantSupplyID.OppositeBottom: AdaptedPose(x=-300, y=500),
        }
        for id, pose in plant_supply_positions.items():
            plant_supply = PlantSupply(id=id, x=pose.x, y=pose.y, radius=125)
            self.plant_supplies[id] = plant_supply

        # Disable unused plant supplies
        self.plant_supplies[PlantSupplyID.OppositeTop].enabled = False
        self.plant_supplies[PlantSupplyID.OppositeBottom].enabled = False
        self.plant_supplies[PlantSupplyID.CenterTop].enabled = False

        #for plant_supply in self.plant_supplies.values():
        #    plant_supply.create_bounding_box(bb_radius, self.properties.obstacle_bb_vertices)

        # Pot supplies
        pot_supply_positions = {
            PotSupplyID.LocalTop: AdaptedPose(x=450 / 2 + 325 / 2, y=-1500 + 35, O=-90),
            PotSupplyID.LocalMiddle: AdaptedPose(x=-450 / 2 - 325 / 2, y=-1500 + 35, O=-90),
            PotSupplyID.LocalBottom: AdaptedPose(x=-1000 + 35, y=-500, O=180),
            PotSupplyID.OppositeTop: AdaptedPose(x=450 / 2 + 325 / 2, y=1500 - 35, O=90),
            PotSupplyID.OppositeMiddle: AdaptedPose(x=-450 / 2 - 325 / 2, y=1500 - 35, O=90),
            PotSupplyID.OppositeBottom: AdaptedPose(x=-1000 + 35, y=500, O=180),
        }
        for id, pose in pot_supply_positions.items():
            pot_supply = PotSupply(id=id, x=pose.x, y=pose.y, radius=125, angle=pose.O)
            self.pot_supplies[id] = pot_supply

        # Disable unused pot supplies
        self.pot_supplies[PotSupplyID.OppositeTop].enabled = False
        self.pot_supplies[PotSupplyID.OppositeMiddle].enabled = False
        self.pot_supplies[PotSupplyID.OppositeBottom].enabled = False

        #for pot_supply in self.pot_supplies.values():
        #    pot_supply.create_bounding_box(bb_radius, self.properties.obstacle_bb_vertices)

        # Drop-off zones
        dropoff_zone_positions = {
            DropoffZoneID.Top: AdaptedPose(x=1000 - 450 / 2, y=-1500 + 450 / 2),
            DropoffZoneID.Bottom: AdaptedPose(x=-1000 + 450 / 2, y=-1500 + 450 / 2),
            DropoffZoneID.Opposite: AdaptedPose(x=0, y=1500 - 450 / 2),
        }
        for id, pose in dropoff_zone_positions.items():
            self.dropoff_zones[id] = DropoffZone(id=id, x=pose.x, y=pose.y)

        # Planters
        planter_positions = {
            PlanterID.Top: AdaptedPose(x=1000, y=-1500 + 600 + 325 / 2, O=0),
            PlanterID.LocalSide: AdaptedPose(x=450 / 2 + 325 / 2, y=-1500, O=-90),
            PlanterID.OppositeSide: AdaptedPose(x=-450 / 2 - 325 / 2, y=1500, O=90),
            PlanterID.Test: AdaptedPose(x=-450 / 2 - 325 / 2, y=-1500, O=-90),
        }
        for id, pose in planter_positions.items():
            self.planters[id] = Planter(id=id, x=pose.x, y=pose.y, O=pose.O)

        # Solar panels
        solar_panels_positions = {
            SolarPanelsID.Local: AdaptedPose(x=-1000, y=-1000),
            SolarPanelsID.Shared: AdaptedPose(x=-1000, y=0),
        }
        for id, pose in solar_panels_positions.items():
            self.solar_panels[id] = SolarPanels(id=id, x=pose.x, y=pose.y)

    def create_fixed_obstacles(self):
        # Positions are related to the default camp yellow.
        self.fixed_obstacles: list[DynObstacleRect] = []

        pose = AdaptedPose(x=1000 - 300, y=1)
        #self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=450, length_y=450)]
        self.fixed_obstacles += [DynRoundObstacle(x=pose.x, y=pose.y, angle=0, radius=250)]
        #pose = AdaptedPose(x=1000 - 225, y=800)
        #self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=450, length_y=450)]

        #pose = AdaptedPose(x=1000 - 75, y=225)
        #self.fixed_obstacles += [DynObstacleRect(x=pose.x, y=pose.y, angle=0, length_x=150, length_y=450)]

        #for obstacle in self.fixed_obstacles:
        #    obstacle.create_bounding_box(self.properties.robot_width / 2)

    def create_actuators_states(self):
        self.servo_states: dict[ServoEnum, Servo] = {}
        self.positional_actuator_states: dict[PositionalActuatorEnum, PositionalActuator] = {}
        self.bool_sensor_states: dict[BoolSensorEnum, BoolSensor] = {id: BoolSensor(id=id) for id in BoolSensorEnum}
        self.emulated_actuator_states: set[ServoEnum | PositionalActuatorEnum] = {
            ServoEnum.LXSERVO_LEFT_CART,
            ServoEnum.LXSERVO_RIGHT_CART,
            ServoEnum.LXSERVO_ARM_PANEL,
            PositionalActuatorEnum.MOTOR_BOTTOM_LIFT,
            PositionalActuatorEnum.MOTOR_TOP_LIFT,
            PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_LEFT,
            PositionalActuatorEnum.ANALOGSERVO_BOTTOM_GRIP_RIGHT,
            PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_LEFT,
            PositionalActuatorEnum.ANALOGSERVO_TOP_GRIP_RIGHT,
            PositionalActuatorEnum.CART_MAGNET_LEFT,
            PositionalActuatorEnum.CART_MAGNET_RIGHT,
            PositionalActuatorEnum.ANALOGSERVO_PAMI,
            BoolSensorEnum.BOTTOM_GRIP_LEFT,
            BoolSensorEnum.BOTTOM_GRIP_RIGHT,
            BoolSensorEnum.TOP_GRIP_LEFT,
            BoolSensorEnum.TOP_GRIP_RIGHT,
            BoolSensorEnum.MAGNET_LEFT,
            BoolSensorEnum.MAGNET_RIGHT,
        }
