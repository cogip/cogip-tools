import asyncio
import platform
import time
import traceback
from functools import partial
from multiprocessing import Manager, Process
from multiprocessing.managers import DictProxy
from typing import Any

import socketio
from gpiozero import Button
from gpiozero.pins.mock import MockFactory
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont
from pydantic import RootModel, TypeAdapter

from cogip import models
from cogip.models.actuators import ActuatorState
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.asyncloop import AsyncLoop
from cogip.utils.singleton import Singleton
from . import actuators, cameras, logger, pose, sio_events
from .actions import Strategy, action_classes, actions
from .avoidance.avoidance import AvoidanceStrategy
from .avoidance.process import avoidance_process
from .camp import Camp
from .context import GameContext
from .positions import StartPosition
from .properties import Properties
from .table import TableEnum
from .wizard import GameWizard


class Planner:
    """
    Main planner class.
    """

    def __init__(
        self,
        robot_id: int,
        server_url: str,
        robot_width: int,
        robot_length: int,
        obstacle_radius: int,
        obstacle_bb_margin: float,
        obstacle_bb_vertices: int,
        max_distance: int,
        obstacle_sender_interval: float,
        path_refresh_interval: float,
        plot: bool,
        starter_pin: int | None,
        oled_bus: int | None,
        oled_address: int | None,
        debug: bool,
    ):
        """
        Class constructor.

        Arguments:
            robot_id: Robot ID
            server_url: Socket.IO Server URL
            robot_width: Width of the robot (in mm)
            robot_length: Length of the robot (in mm)
            obstacle_radius: Radius of a dynamic obstacle (in mm)
            obstacle_bb_margin: Obstacle bounding box margin in percent of the radius
            obstacle_bb_vertices: Number of obstacle bounding box vertices
            max_distance: Maximum distance to take avoidance points into account (mm)
            obstacle_sender_interval: Interval between each send of obstacles to dashboards (in seconds)
            path_refresh_interval: Interval between each update of robot paths (in seconds)
            plot: Display avoidance graph in realtime
            starter_pin: GPIO pin connected to the starter
            oled_bus: PAMI OLED display i2c bus
            oled_address: PAMI OLED display i2c address
            debug: enable debug messages
        """
        self.robot_id = robot_id
        self.server_url = server_url
        self.oled_bus = oled_bus
        self.oled_address = oled_address
        self.debug = debug

        # We have to make sure the Planner is the first object calling the constructor
        # of the Properties singleton
        if Properties in Singleton._instance:
            raise RuntimeError("Properties class must not be initialized before this point.")
        self.properties = Properties(
            robot_id=robot_id,
            robot_width=robot_width,
            robot_length=robot_length,
            obstacle_radius=obstacle_radius,
            obstacle_bb_margin=obstacle_bb_margin,
            obstacle_bb_vertices=obstacle_bb_vertices,
            max_distance=max_distance,
            obstacle_sender_interval=obstacle_sender_interval,
            path_refresh_interval=path_refresh_interval,
            plot=plot,
        )
        self.virtual = platform.machine() != "aarch64"
        self.retry_connection = True
        self.sio = socketio.AsyncClient(logger=False)
        self.sio_ns = sio_events.SioEvents(self)
        self.sio.register_namespace(self.sio_ns)
        self.game_context = GameContext()
        self.process_manager = Manager()
        self.sio_receiver_queue = asyncio.Queue()
        self.sio_emitter_queue = self.process_manager.Queue()
        self.action: actions.Action | None = None
        self.actions = action_classes.get(self.game_context.strategy, actions.Actions)(self)
        self.obstacles: models.DynObstacleList = []
        self.obstacles_sender_loop = AsyncLoop(
            "Obstacles sender loop",
            obstacle_sender_interval,
            self.send_obstacles,
            logger=self.debug,
        )
        self._pose_current: models.Pose | None = None
        self._pose_order: pose.Pose | None = None
        self.pose_reached: bool = True
        self.avoidance_path: list[pose.Pose] = []
        self.blocked_counter: int = 0
        self.controller = self.game_context.default_controller
        self.game_wizard = GameWizard(self)
        self.start_position: StartPosition | None = None
        available_start_poses = self.game_context.get_available_start_poses()
        if available_start_poses:
            self.start_position = available_start_poses[(self.robot_id - 1) % len(available_start_poses)]
        self.sio_receiver_task: asyncio.Task | None = None
        self.sio_emitter_task: asyncio.Task | None = None
        self.countdown_task: asyncio.Task | None = None

        self.shared_properties: DictProxy = self.process_manager.dict(
            {
                "robot_id": self.robot_id,
                "exiting": False,
                "avoidance_strategy": self.game_context.avoidance_strategy,
                "pose_current": {},
                "pose_order": {},
                "last_avoidance_pose_current": {},
                "obstacles": [],
                "path_refresh_interval": path_refresh_interval,
                "robot_width": robot_width,
                "obstacle_radius": obstacle_radius,
                "obstacle_bb_vertices": obstacle_bb_vertices,
                "obstacle_bb_margin": obstacle_bb_margin,
                "max_distance": max_distance,
                "plot": plot,
            }
        )
        self.avoidance_process: Process | None = None

        if starter_pin:
            self.starter = Button(
                starter_pin,
                pull_up=False,
                bounce_time=None,
            )
        else:
            self.starter = Button(
                17,
                pull_up=True,
                pin_factory=MockFactory(),
            )

        self.starter.when_pressed = partial(self.sio_emitter_queue.put, ("starter_changed", True))
        self.starter.when_released = partial(self.sio_emitter_queue.put, ("starter_changed", False))

        if self.oled_bus and self.oled_address:
            self.oled_serial = i2c(port=self.oled_bus, address=self.oled_address)
            self.oled_device = sh1106(self.oled_serial)
            self.oled_font = ImageFont.truetype("DejaVuSansMono.ttf", 9)
            self.oled_image = canvas(self.oled_device)
            self.oled_update_loop = AsyncLoop(
                "OLED display update loop",
                0.5,
                self.update_oled_display,
                logger=self.debug,
            )

    async def connect(self):
        """
        Connect to SocketIO server.
        """
        self.retry_connection = True
        try:
            await self.try_connect()
            await self.sio.wait()
        except asyncio.CancelledError:
            self.process_manager.shutdown()

    async def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while self.retry_connection:
            try:
                await self.sio.connect(self.server_url, namespaces=["/planner"])
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    async def start(self):
        """
        Start sending obstacles list.
        """
        logger.info("Planner: start")
        self.shared_properties["exiting"] = False
        await self.soft_reset()
        await self.set_pose_start(self.game_context.get_start_pose(self.start_position).pose)
        await self.set_controller(self.game_context.default_controller, True)
        self.sio_receiver_task = asyncio.create_task(
            self.task_sio_receiver(),
            name="Robot: Task SIO Receiver",
        )
        self.sio_emitter_task = asyncio.create_task(
            self.task_sio_emitter(),
            name="Robot: Task SIO Emitter",
        )
        await self.sio_ns.emit("starter_changed", self.starter.is_pressed)
        await self.sio_ns.emit("game_reset")
        await self.countdown_start()
        self.obstacles_sender_loop.start()
        if self.oled_bus and self.oled_address:
            self.oled_update_loop.start()

        self.avoidance_process = Process(
            target=avoidance_process,
            args=(
                self.game_context.strategy,
                self.game_context.table,
                self.shared_properties,
                self.sio_emitter_queue,
            ),
        )
        self.avoidance_process.start()

    async def stop(self):
        """
        Stop running tasks.
        """
        logger.info("Planner: stop")

        self.shared_properties["exiting"] = True

        await self.sio_ns.emit("stop_video_record")

        await self.countdown_stop()

        await self.obstacles_sender_loop.stop()
        if self.oled_bus and self.oled_address:
            await self.oled_update_loop.stop()

        if self.sio_emitter_task:
            self.sio_emitter_task.cancel()
            try:
                await self.sio_emitter_task
            except asyncio.CancelledError:
                logger.info("Planner: Task SIO Emitter stopped")
            except Exception as exc:
                logger.warning(f"Planner: Unexpected exception {exc}")
        self.sio_emitter_task = None

        if self.sio_receiver_task:
            self.sio_receiver_task.cancel()
            try:
                await self.sio_receiver_task
            except asyncio.CancelledError:
                logger.info("Planner: Task SIO Receiver stopped")
            except Exception as exc:
                logger.warning(f"Planner: Unexpected exception {exc}")
        self.sio_receiver_task = None

        if self.avoidance_process and self.avoidance_process.is_alive():
            self.avoidance_process.join()
            self.avoidance_process = None

    async def reset(self):
        """
        Reset planner, context, robots and actions.
        """
        await self.stop()
        await self.start()

    async def soft_reset(self):
        """
        Only reset context and actions.
        """
        self.game_context.reset()
        self.actions = action_classes.get(self.game_context.strategy, actions.Actions)(self)
        await self.set_pose_start(self.game_context.get_start_pose(self.start_position).pose)

    async def task_sio_emitter(self):
        logger.info("Planner: Task SIO Emitter started")
        try:
            while True:
                name, value = await asyncio.to_thread(self.sio_emitter_queue.get)
                match name:
                    case "avoidance_path":
                        self.avoidance_path = [pose.Pose.model_validate(m) for m in value]
                    case "blocked":
                        if self.sio.connected:
                            await self.sio_ns.emit("brake")
                        self.blocked_counter += 1
                        if self.blocked_counter > 10:
                            self.blocked_counter = 0
                            await self.blocked()
                    case "path":
                        if self.pose_order:
                            await self.pose_order.act_intermediate_pose()
                        if len(value) == 1:
                            # Final pose
                            new_controller = ControllerEnum.QUADPID
                        else:
                            # Intermediate pose
                            match self.game_context.avoidance_strategy:
                                case AvoidanceStrategy.Disabled | AvoidanceStrategy.VisibilityRoadMapQuadPid:
                                    new_controller = ControllerEnum.QUADPID
                                case AvoidanceStrategy.VisibilityRoadMapLinearPoseDisabled | AvoidanceStrategy.VisibilityRoadMapCpp:
                                    new_controller = ControllerEnum.LINEAR_POSE_DISABLED
                        await self.set_controller(new_controller)
                        if self.sio.connected:
                            await self.sio_ns.emit(name, value)
                    case "pose_order":
                        self.blocked_counter = 0
                        if self.sio.connected:
                            await self.sio_ns.emit(name, value)
                    case "starter_changed":
                        await self.starter_changed(value)
                    case _:
                        if self.sio.connected:
                            await self.sio_ns.emit(name, value)
                self.sio_emitter_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Planner: Task SIO Emitter cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Task SIO Emitter: Unknown exception {exc}")
            traceback.print_exc()
            raise

    async def task_sio_receiver(self):
        logger.info("Planner: Task SIO Receiver started")
        try:
            while True:
                func = await self.sio_receiver_queue.get()
                await func
                self.sio_receiver_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Planner: Task SIO Receiver cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Task SIO Receiver: Unknown exception {exc}")
            traceback.print_exc()
            raise

    async def countdown_loop(self):
        logger.info("Planner: Task Countdown started")
        try:
            last_now = time.time()
            last_countdown = self.game_context.countdown
            while True:
                await asyncio.sleep(0.5)
                now = time.time()
                self.game_context.countdown -= now - last_now
                logger.debug(f"Planner: countdown = {self.game_context.countdown}")
                if self.game_context.playing and self.game_context.countdown < 15 and last_countdown > 15:
                    logger.debug("Planner: countdown==15: force blocked")
                    await self.sio_receiver_queue.put(self.blocked())
                if self.game_context.playing and self.game_context.countdown < 0 and last_countdown > 0:
                    logger.debug("Planner: countdown==0: final action")
                    await self.final_action()
                if self.game_context.countdown < -5 and last_countdown > -5:
                    await self.sio_ns.emit("stop_video_record")
                last_now = now
                last_countdown = self.game_context.countdown
        except asyncio.CancelledError:
            logger.info("Planner: Task Countdown cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Unknown exception {exc}")
            raise

    async def countdown_start(self):
        await self.countdown_stop()
        self.countdown_task = asyncio.create_task(self.countdown_loop())

    async def countdown_stop(self):
        if self.countdown_task is None:
            return

        self.countdown_task.cancel()
        try:
            await self.countdown_task
        except asyncio.CancelledError:
            logger.info("Planner: Task Countdown stopped")
        except Exception as exc:
            logger.warning(f"Planner: Unexpected exception {exc}")

        self.countdown_task = None

    async def final_action(self):
        if not self.game_context.playing:
            return
        self.game_context.playing = False
        await self.sio_ns.emit("game_end")
        await self.sio_ns.emit("score", self.game_context.score)

    async def starter_changed(self, pushed: bool):
        if not self.virtual:
            await self.sio_ns.emit("starter_changed", pushed)

    async def set_controller(self, new_controller: ControllerEnum, force: bool = False):
        if self.controller == new_controller and not force:
            return
        self.controller = new_controller
        await self.sio_ns.emit("set_controller", self.controller.value)

    async def set_pose_start(self, pose_start: models.Pose):
        """
        Set the start position of the robot for the next game.
        """
        self.action = None
        self.pose_current = pose_start.model_copy()
        self.pose_order = None
        self.pose_reached = True
        self.avoidance_path = []
        await self.sio_ns.emit("pose_start", pose_start.model_dump())

    def set_pose_current(self, pose: models.Pose) -> None:
        """
        Set current pose of a robot.
        """
        self.pose_current = models.Pose.model_validate(pose)

    @property
    def pose_current(self) -> models.Pose:
        return self._pose_current

    @pose_current.setter
    def pose_current(self, new_pose: models.Pose):
        self._pose_current = new_pose
        self.shared_properties["pose_current"] = new_pose.model_dump(exclude_unset=True)

    @property
    def pose_order(self) -> pose.Pose | None:
        return self._pose_order

    @pose_order.setter
    def pose_order(self, new_pose: pose.Pose | None):
        self._pose_order = new_pose
        if new_pose is None:
            self.shared_properties["pose_order"] = None
        else:
            self.shared_properties["pose_order"] = new_pose.path_pose.model_dump(exclude_unset=True)

    async def set_pose_reached(self):
        """
        Set pose reached for a robot.
        """
        logger.debug("Planner: set_pose_reached()")

        logger.info(f"Planner: Intermediate {len(self.avoidance_path)}")
        if len(self.avoidance_path) > 1:
            # The pose reached is intermediate, do nothing.
            return

        # Set pose reached
        self.avoidance_path = []
        if not self.pose_reached and (pose_order := self.pose_order):
            self.pose_order = None
            await pose_order.act_after_pose()
        else:
            self.pose_order = None

        self.pose_reached = True
        if (action := self.action) and len(self.action.poses) == 0:
            self.action = None
            await action.act_after_action()

        if not self.game_context.playing:
            return

        await self.next_pose()

    async def next_pose_in_action(self):
        if self.action and len(self.action.poses) > 0:
            pose_order = self.action.poses.pop(0)
            self.pose_order = None
            await pose_order.act_before_pose()
            self.blocked_counter = 0
            self.pose_order = pose_order

            if self.game_context.strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
                await self.sio_ns.emit("pose_order", self.pose_order.pose.model_dump())

    async def next_pose(self):
        """
        Select the next pose for a robot.
        """
        logger.debug("Planner: next_pose()")
        try:
            # Get and set new pose
            self.pose_reached = False
            await self.next_pose_in_action()

            # If no pose left in current action, get and set new action
            if not self.pose_order and (new_action := self.get_action()):
                await self.set_action(new_action)
                if not self.pose_order:
                    await self.sio_receiver_queue.put(self.set_pose_reached())
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Unknown exception {exc}")
            traceback.print_exc()
            raise

    def get_action(self) -> actions.Action | None:
        """
        Get a new action for a robot.
        Simply choose next action in the list for now.
        """
        sorted_actions = sorted(
            [action for action in self.actions if not action.recycled and action.weight() > 0],
            key=lambda action: action.weight(),
        )

        if len(sorted_actions) == 0:
            return None

        action = sorted_actions[-1]
        self.actions.remove(action)
        return action

    async def set_action(self, action: "actions.Action"):
        """
        Set current action.
        """
        logger.debug(f"Planner: set action '{action.name}'")
        self.pose_order = None
        self.action = action
        await self.action.act_before_action()
        await self.next_pose_in_action()

    async def blocked(self):
        """
        Function called when a robot cannot find a path to go to the current pose of the current action
        """
        if (current_action := self.action) and current_action.interruptable:
            logger.debug("Planner: blocked")
            if new_action := self.get_action():
                await self.set_action(new_action)
            await current_action.recycle()
            self.actions.append(current_action)
            if not self.pose_order:
                await self.sio_receiver_queue.put(self.set_pose_reached())

    def create_dyn_obstacle(
        self,
        center: models.Vertex,
        radius: float | None = None,
        bb_radius: float | None = None,
    ) -> models.DynRoundObstacle:
        """
        Create a dynamic obstacle.

        Arguments:
            center: center of the obstacle
            radius: radius of the obstacle, use the value from global properties if not specified
            bb_radius: radius of the bounding box
        """
        if radius is None:
            radius = self.properties.obstacle_radius

        if bb_radius is None:
            bb_radius = radius + self.properties.robot_width / 2

        obstacle = models.DynRoundObstacle(
            x=center.x, y=center.y,angle=0,
            radius=radius
        )

        return obstacle

    def set_obstacles(self, obstacles: list[models.Vertex]) -> None:
        """
        Store obstacles detected by a robot sent by Detector.
        Add bounding box and radius.
        """
        table = self.game_context.table
        if self.robot_id == 1:
            bb_radius = self.properties.obstacle_radius + self.properties.robot_length / 2

            self.obstacles = [
                self.create_dyn_obstacle(obstacle, bb_radius)
                for obstacle in obstacles
                if table.contains(obstacle, self.properties.obstacle_radius)
            ]
        else:
            # In case of PAMI, the detected obstacle is at the front the real obstacle
            # instead of at its center.
            # Since we use a specific avoidance strategy that only needs to know the path
            # is intersecting the obstacle, the radius can be reduced to the minimum to create
            # a bounding box.
            self.obstacles = [
                self.create_dyn_obstacle(obstacle, radius=10, bb_radius=10)
                for obstacle in obstacles
                if table.contains(obstacle)
            ]
        #self.obstacles += [p for p in self.game_context.plant_supplies.values() if p.enabled and table.contains(p)]
        #self.obstacles += [p for p in self.game_context.pot_supplies.values() if p.enabled and table.contains(p)]
        self.obstacles += [p for p in self.game_context.fixed_obstacles if table.contains(p)]

        self.shared_properties["obstacles"] = [
            obstacle.model_dump(exclude_defaults=True) for obstacle in self.obstacles
        ]

    async def send_obstacles(self):
        await self.sio_ns.emit("obstacles", [o.model_dump(exclude_defaults=True) for o in self.obstacles])

    async def update_oled_display(self):
        try:
            text = (
                f"{'Connected' if self.sio.connected else 'Not connected': <20}"
                f"{'▶' if self.game_context.playing else '◼'}\n"
                f"Camp: {self.game_context.camp.color.name}\n"
                f"Strategy: {self.game_context.strategy.name}\n"
                f"Pose: {self.pose_current.x},{self.pose_current.y},{self.pose_current.O}\n"
                f"Countdown: {self.game_context.countdown:.2f}"
            )
            with self.oled_image as draw:
                draw.rectangle([(0, 0), (128, 64)], fill="black", outline="black")
                draw.multiline_text(
                    (1, 0),
                    text,
                    fill="white",
                    font=self.oled_font,
                )
        except Exception as exc:
            logger.warning(f"Planner: OLED display update loop: Unknown exception {exc}")
            traceback.print_exc()

    async def command(self, cmd: str):
        """
        Execute a command from the menu.
        """
        if cmd.startswith("wizard_"):
            await self.cmd_wizard_test(cmd)
            return

        if cmd.startswith("act_"):
            await self.cmd_act(cmd)
            return

        if cmd.startswith("cam_"):
            await self.cmd_cam(cmd)
            return

        if cmd == "config":
            # Get JSON Schema
            schema = TypeAdapter(Properties).json_schema()
            # Add namespace in JSON Schema
            schema["namespace"] = "/planner"
            # Add current values in JSON Schema
            for prop, value in RootModel[Properties](self.properties).model_dump().items():
                schema["properties"][prop]["value"] = value
            # Send config
            await self.sio_ns.emit("config", schema)
            return

        if cmd == "game_wizard":
            await self.game_wizard.start()
            return

        if not (cmd_func := getattr(self, f"cmd_{cmd}", None)):
            logger.warning(f"Unknown command: {cmd}")
            return

        await cmd_func()

    def update_config(self, config: dict[str, Any]) -> None:
        """
        Update a Planner property with the value sent by the dashboard.
        """
        self.properties.__setattr__(name := config["name"], value := config["value"])
        if name in self.shared_properties:
            self.shared_properties[name] = value
        match name:
            case "obstacle_sender_interval":
                self.obstacles_sender_loop.interval = self.properties.obstacle_sender_interval
            case "robot_width" | "obstacle_bb_vertices":
                self.game_context.create_artifacts()
                self.game_context.create_fixed_obstacles()

    async def cmd_play(self):
        """
        Play command from the menu.
        """
        if self.game_context.playing:
            return

        self.game_context.countdown = self.game_context.game_duration
        self.game_context.playing = True
        await self.sio_ns.emit("start_video_record")
        await self.sio_receiver_queue.put(self.set_pose_reached())

    async def cmd_stop(self):
        """
        Stop command from the menu.
        """
        self.game_context.playing = False
        await self.sio_ns.emit("stop_video_record")

    async def cmd_next(self):
        """
        Next command from the menu.
        Ignored if current pose is not reached for all robots.
        """
        if self.game_context.playing:
            return

        # Check that pose_reached is set
        if not self.pose_reached:
            return

        await self.sio_receiver_queue.put(self.next_pose())

    async def cmd_reset(self):
        """
        Reset command from the menu.
        """
        await self.reset()
        await self.sio_ns.emit("cmd_reset")

    async def cmd_choose_camp(self):
        """
        Choose camp command from the menu.
        Send camp wizard message.
        """
        await self.sio_ns.emit(
            "wizard",
            {
                "name": "Choose Camp",
                "type": "camp",
                "value": self.game_context.camp.color.name,
            },
        )

    async def cmd_choose_strategy(self):
        """
        Choose strategy command from the menu.
        Send strategy wizard message.
        """
        await self.sio_ns.emit(
            "wizard",
            {
                "name": "Choose Strategy",
                "type": "choice_str",
                "choices": [e.name for e in Strategy],
                "value": self.game_context.strategy.name,
            },
        )

    async def cmd_choose_avoidance(self):
        """
        Choose avoidance strategy command from the menu.
        Send avoidance strategy wizard message.
        """
        await self.sio_ns.emit(
            "wizard",
            {
                "name": "Choose Avoidance",
                "type": "choice_str",
                "choices": [e.name for e in AvoidanceStrategy],
                "value": self.game_context.avoidance_strategy.name,
            },
        )

    async def cmd_choose_start_position(self):
        """
        Choose start position command from the menu.
        Send start position wizard message.
        """
        if self.start_position is None:
            await self.sio_ns.emit(
                "wizard",
                {
                    "name": "Error",
                    "type": "message",
                    "value": "No start position available with this Camp/Table",
                },
            )
        else:
            await self.sio_ns.emit(
                "wizard",
                {
                    "name": "Choose Start Position",
                    "type": "choice_integer",
                    "choices": [p.name for p in self.game_context.get_available_start_poses()],
                    "value": self.start_position.name,
                },
            )

    async def cmd_choose_table(self):
        """
        Choose table command from the menu.
        Send table wizard message.
        """
        await self.sio_ns.emit(
            "wizard",
            {
                "name": "Choose Table",
                "type": "choice_str",
                "choices": [e.name for e in TableEnum],
                "value": self.game_context._table.name,
            },
        )

    async def wizard_response(self, message: dict[str, Any]):
        """
        Handle wizard response sent from the dashboard.
        """
        if (value := message["value"]) is None:
            return

        match name := message.get("name"):
            case "Choose Camp":
                new_camp = Camp.Colors[value]
                if self.game_context.camp.color == new_camp:
                    return
                if self.game_context._table == TableEnum.Training and new_camp == Camp.Colors.blue:
                    logger.warning("Wizard: only yellow camp is authorized on training table")
                    return
                self.game_context.camp.color = new_camp
                await self.soft_reset()
                logger.info(f"Wizard: New camp: {self.game_context.camp.color.name}")
            case "Choose Strategy":
                new_strategy = Strategy[value]
                if self.game_context.strategy == new_strategy:
                    return
                self.game_context.strategy = new_strategy
                await self.soft_reset()
                logger.info(f"Wizard: New strategy: {self.game_context.strategy.name}")
            case "Choose Avoidance":
                new_strategy = AvoidanceStrategy[value]
                if self.game_context.avoidance_strategy == new_strategy:
                    return
                self.game_context.avoidance_strategy = new_strategy
                self.shared_properties["avoidance_strategy"] = new_strategy
                logger.info(f"Wizard: New avoidance strategy: {self.game_context.avoidance_strategy.name}")
            case "Choose Start Position":
                start_position = StartPosition[value]
                self.start_position = start_position
                await self.soft_reset()
            case "Choose Table":
                new_table = TableEnum[value]
                if self.game_context.table == new_table:
                    return
                if self.game_context.camp.color == Camp.Colors.blue and new_table == TableEnum.Training:
                    logger.warning("Wizard: training table is not supported with blue camp")
                    await self.sio_ns.emit(
                        "wizard",
                        {
                            "name": "Error",
                            "type": "message",
                            "value": "Training table is not supported with blue camp",
                        },
                    )
                    return
                self.game_context.table = new_table
                self.shared_properties["table"] = new_table
                await self.soft_reset()
                logger.info(f"Wizard: New table: {self.game_context._table.name}")
            case game_wizard_response if game_wizard_response.startswith("Game Wizard"):
                await self.game_wizard.response(message)
            case wizard_test_response if wizard_test_response.startswith("Wizard Test"):
                logger.info(f"Wizard test response: {name} = {value}")
            case _:
                logger.warning(f"Wizard: Unknown type: {name}")

    async def cmd_wizard_test(self, cmd: str):
        match cmd:
            case "wizard_boolean":
                message = {
                    "name": "Wizard Test Boolean",
                    "type": "boolean",
                    "value": True,
                }
            case "wizard_integer":
                message = {
                    "name": "Wizard Test Integer",
                    "type": "integer",
                    "value": 42,
                }
            case "wizard_floating":
                message = {
                    "name": "Wizard Test Float",
                    "type": "floating",
                    "value": 66.6,
                }
            case "wizard_str":
                message = {
                    "name": "Wizard Test String",
                    "type": "str",
                    "value": "cogip",
                }
            case "wizard_message":
                message = {
                    "name": "Wizard Test Message",
                    "type": "message",
                    "value": "Hello Robot!",
                }
            case "wizard_choice_integer":
                message = {
                    "name": "Wizard Test Choice Integer",
                    "type": "choice_integer",
                    "choices": [1, 2, 3],
                    "value": 2,
                }
            case "wizard_choice_floating":
                message = {
                    "name": "Wizard Test Choice Float",
                    "type": "choice_floating",
                    "choices": [1.1, 2.2, 3.3],
                    "value": 2.2,
                }
            case "wizard_choice_str":
                message = {
                    "name": "Wizard Test Choice String",
                    "type": "choice_str",
                    "choices": ["one", "two", "tree"],
                    "value": "two",
                }
            case "wizard_select_integer":
                message = {
                    "name": "Wizard Test Select Integer",
                    "type": "select_integer",
                    "choices": [1, 2, 3],
                    "value": [1, 3],
                }
            case "wizard_select_floating":
                message = {
                    "name": "Wizard Test Select Float",
                    "type": "select_floating",
                    "choices": [1.1, 2.2, 3.3],
                    "value": [1.1, 3.3],
                }
            case "wizard_select_str":
                message = {
                    "name": "Wizard Test Select String",
                    "type": "select_str",
                    "choices": ["one", "two", "tree"],
                    "value": ["one", "tree"],
                }
            case "wizard_camp":
                message = {
                    "name": "Wizard Test Camp",
                    "type": "camp",
                    "value": "yellow",
                }
            case "wizard_camera":
                message = {
                    "name": "Wizard Test Camera",
                    "type": "camera",
                }
            case "wizard_score":
                await self.sio_ns.emit("score", 100)
                return
            case _:
                logger.warning(f"Wizard test unsupported: {cmd}")
                return

        await self.sio_ns.emit("wizard", message)

    async def cmd_act(self, cmd: str):
        _, _, command = cmd.partition("_")
        func = getattr(actuators, command)
        await func(self)

    async def cmd_cam(self, cmd: str):
        _, _, command = cmd.partition("_")
        match command:
            case "snapshot":
                await cameras.snapshot()
            case "camera_position":
                await self.get_camera_position()

    async def get_camera_position(self):
        if camera_position := await cameras.calibrate_camera(self):
            logger.info(
                f"Planner: Camera position in robot:"
                f" X={camera_position.x:.0f} Y={camera_position.y:.0f} Z={camera_position.z:.0f}"
            )
        else:
            logger.info("Planner: No table marker found")

    async def update_actuator_state(self, actuator_state: ActuatorState):
        # actuators_states = getattr(self.game_context, f"{actuator_state.kind.name}_states")
        # actuators_states[actuator_state.id] = actuator_state
        # if not self.virtual and actuator_state.id in self.game_context.emulated_actuator_states:
        #     self.game_context.emulated_actuator_states.remove(actuator_state.id)
        pass
