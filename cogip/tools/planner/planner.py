import asyncio
import platform
import re
import time
import traceback
from functools import partial
from multiprocessing import Manager, Process
from multiprocessing.managers import DictProxy
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import socketio
from colorzero import Color
from gpiozero import RGBLED, Button, OutputDevice
from gpiozero.pins.mock import MockFactory
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from numpy.typing import NDArray
from PIL import ImageFont
from pydantic import RootModel, TypeAdapter

from cogip import models
from cogip.cpp.libraries.models import CircleList as SharedCircleList
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.obstacles import ObstacleCircleList as SharedObstacleCircleList
from cogip.cpp.libraries.obstacles import ObstacleRectangleList as SharedObstacleRectangleList
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.models.actuators import ActuatorState
from cogip.models.artifacts import ConstructionArea
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
from .scservos import SCServoEnum, SCServos
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
        obstacle_updater_interval: float,
        path_refresh_interval: float,
        starter_pin: int | None,
        led_red_pin: int | None,
        led_green_pin: int | None,
        led_blue_pin: int | None,
        flag_motor_pin: int | None,
        oled_bus: int | None,
        oled_address: int | None,
        bypass_detector: bool,
        scservos_port: Path | None,
        scservos_baud_rate: int,
        disable_fixed_obstacles: bool,
        table: TableEnum,
        strategy: Strategy,
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
            obstacle_updater_interval: Interval between each send of obstacles to dashboards (in seconds)
            path_refresh_interval: Interval between each update of robot paths (in seconds)
            starter_pin: GPIO pin connected to the starter
            led_red_pin: GPIO pin connected to the red LED
            led_green_pin: GPIO pin connected to the green LED
            led_blue_pin: GPIO pin connected to the blue LED
            flag_motor_pin: GPIO pin connected to the flag motor
            oled_bus: PAMI OLED display i2c bus
            oled_address: PAMI OLED display i2c address
            bypass_detector: Use perfect obstacles from monitor instead of detected obstacles by Lidar
            scservos_port: SC Servos serial port
            scservos_baud_rate: SC Servos baud rate (usually 921600 or 1000000)
            disable_fixed_obstacles: Disable fixed obstacles. Useful to work on Lidar obstacles and avoidance
            table: Default table on startup
            strategy: Default strategy on startup
            debug: enable debug messages
        """
        self.robot_id = robot_id
        self.server_url = server_url
        self.oled_bus = oled_bus
        self.oled_address = oled_address
        self.scservos_port = scservos_port
        self.scservos_baud_rate = scservos_baud_rate
        self.debug = debug

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_lock: WritePriorityLock | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_table_limits: NDArray | None = None
        self.shared_detector_obstacles: SharedCircleList | None = None
        self.shared_detector_obstacles_lock: WritePriorityLock | None = None
        self.shared_monitor_obstacles: SharedCircleList | None = None
        self.shared_monitor_obstacles_lock: WritePriorityLock | None = None
        self.shared_circle_obstacles: SharedObstacleCircleList | None = None
        self.shared_rectangle_obstacles: SharedObstacleRectangleList | None = None
        self.shared_obstacles_lock: WritePriorityLock | None = None
        self.create_shared_memory()

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
            obstacle_updater_interval=obstacle_updater_interval,
            path_refresh_interval=path_refresh_interval,
            bypass_detector=bypass_detector,
            disable_fixed_obstacles=disable_fixed_obstacles,
            table=table,
            strategy=strategy,
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
        self.actions = action_classes.get(self.properties.strategy, actions.Actions)(self)
        self.obstacles_updater_loop = AsyncLoop(
            "Obstacles updater loop",
            obstacle_updater_interval,
            self.update_obstacles,
            logger=self.debug,
        )
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
        self.scservos = SCServos(self.scservos_port, scservos_baud_rate)

        self.shared_properties: DictProxy = self.process_manager.dict(
            {
                "robot_id": self.robot_id,
                "exiting": False,
                "avoidance_strategy": self.game_context.avoidance_strategy,
                "new_pose_order": None,
                "pose_order": None,
                "last_avoidance_pose_current": None,
                "path_refresh_interval": path_refresh_interval,
                "robot_width": robot_width,
                "obstacle_radius": obstacle_radius,
                "obstacle_bb_vertices": obstacle_bb_vertices,
                "obstacle_bb_margin": obstacle_bb_margin,
                # table_margin is the half of the max robot size,
                # increase of 20% to not touch the borders during rotations.
                "table_margin": max(self.properties.robot_length, self.properties.robot_width) / 1.8,
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

        if led_red_pin and led_green_pin and led_blue_pin:
            self.led = RGBLED(
                led_red_pin,
                led_green_pin,
                led_blue_pin,
                initial_value=(1, 0, 0),
            )
        else:
            self.led = Mock()

        if flag_motor_pin:
            self.flag_motor = OutputDevice(flag_motor_pin)
        else:
            self.flag_motor = Mock()

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

    def create_shared_memory(self):
        if self.shared_memory is None:
            self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
            self.shared_pose_current_lock = self.shared_memory.get_lock(LockName.PoseCurrent)
            self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
            self.shared_table_limits = self.shared_memory.get_table_limits()
            self.shared_detector_obstacles = self.shared_memory.get_detector_obstacles()
            self.shared_detector_obstacles_lock = self.shared_memory.get_lock(LockName.DetectorObstacles)
            self.shared_monitor_obstacles = self.shared_memory.get_monitor_obstacles()
            self.shared_monitor_obstacles_lock = self.shared_memory.get_lock(LockName.MonitorObstacles)
            self.shared_circle_obstacles = self.shared_memory.get_circle_obstacles()
            self.shared_rectangle_obstacles = self.shared_memory.get_rectangle_obstacles()
            self.shared_obstacles_lock = self.shared_memory.get_lock(LockName.Obstacles)

    def delete_shared_memory(self):
        if self.shared_memory is not None:
            self.shared_obstacles_lock = None
            self.shared_rectangle_obstacles = None
            self.shared_circle_obstacles = None
            self.shared_monitor_obstacles_lock = None
            self.shared_monitor_obstacles = None
            self.shared_detector_obstacles_lock = None
            self.shared_detector_obstacles = None
            self.shared_table_limits = None
            self.shared_pose_current_buffer = None
            self.shared_pose_current_lock = None
            self.shared_memory = None

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

    @property
    def pose_current(self) -> models.Pose:
        """
        Get the current pose of the robot.
        """
        pose = self.shared_pose_current_buffer.last
        return models.Pose(x=pose.x, y=pose.y, O=pose.angle)

    async def start(self):
        """
        Start sending obstacles list.
        """
        logger.info("Planner: start")
        self.create_shared_memory()
        self.shared_properties["exiting"] = False
        await self.soft_reset()
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
        self.obstacles_updater_loop.start()
        if self.oled_bus and self.oled_address:
            self.oled_update_loop.start()

        self.avoidance_process = Process(
            target=avoidance_process,
            args=(
                self.properties.strategy,
                self.shared_properties,
                self.sio_emitter_queue,
            ),
        )
        self.avoidance_process.start()

        await actuators.actuators_init(self)

    async def stop(self):
        """
        Stop running tasks.
        """
        logger.info("Planner: stop")

        self.shared_properties["exiting"] = True

        await self.sio_ns.emit("stop_video_record")

        await self.countdown_stop()

        await self.obstacles_updater_loop.stop()
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

        self.delete_shared_memory()

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
        await self.set_controller(self.game_context.default_controller, True)
        self.shared_table_limits[0] = self.game_context.table.x_min
        self.shared_table_limits[1] = self.game_context.table.x_max
        self.shared_table_limits[2] = self.game_context.table.y_min
        self.shared_table_limits[3] = self.game_context.table.y_max
        self.flag_motor.off()
        self.actions = action_classes.get(self.properties.strategy, actions.Actions)(self)
        available_start_poses = self.game_context.get_available_start_poses()
        if available_start_poses and self.start_position not in available_start_poses:
            self.start_position = available_start_poses[(self.robot_id - 1) % len(available_start_poses)]
        await self.set_pose_start(self.game_context.get_start_pose(self.start_position).pose)

    async def task_sio_emitter(self):
        logger.info("Planner: Task SIO Emitter started")
        try:
            while True:
                name, value = await asyncio.to_thread(self.sio_emitter_queue.get)
                logger.info(f"Planner: Task SIO emitter: {name} {value}")
                match name:
                    case "nop":
                        pass
                    case "blocked":
                        if self.sio.connected:
                            await self.sio_ns.emit("brake")
                        self.blocked_counter += 1
                        if self.blocked_counter > 10:
                            self.blocked_counter = 0
                            await self.blocked()
                    case "path":
                        self.blocked_counter = 0
                        self.avoidance_path = [pose.PathPose.model_validate(m) for m in value]
                        if self.pose_order:
                            await self.pose_order.act_intermediate_pose()
                        if len(value) == 1:
                            # Final pose
                            new_controller = ControllerEnum.QUADPID
                        else:
                            # Intermediate pose
                            match self.game_context.avoidance_strategy:
                                case AvoidanceStrategy.Disabled | AvoidanceStrategy.AvoidanceCpp:
                                    new_controller = ControllerEnum.QUADPID
                        await self.set_controller(new_controller)
                        if self.sio.connected:
                            logger.info(f"Task SIO Emitter: Planner: Send pose order: {value[0]}")
                            await self.sio_ns.emit("pose_order", value[0])
                            pose_current = self.pose_current
                            await self.sio_ns.emit(
                                "path",
                                [pose_current.model_dump(exclude_defaults=True, mode="json")] + value,
                            )
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
                logger.info(f"Planner: SIO Task received: {func}")
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
                    logger.info("Planner: countdown==15: force blocked")
                    await self.sio_receiver_queue.put(self.blocked())
                if self.game_context.playing and self.game_context.countdown < 0 and last_countdown > 0:
                    logger.info("Planner: countdown==0: final action")
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
        self.flag_motor.on()
        self.pose_order = None

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
        self.pose_order = None
        self.pose_reached = True
        self.avoidance_path = []

        # When the firmware receives a pose start, it does not send its updated pose current,
        # so do it here.
        self.shared_pose_current_buffer.push(pose_start.x, pose_start.y, pose_start.O)
        await self.sio_ns.emit("pose_start", pose_start.model_dump())

    @property
    def pose_order(self) -> pose.Pose | None:
        return self._pose_order

    @pose_order.setter
    def pose_order(self, new_pose: pose.Pose | None):
        logger.info(f"Planner: pose_order={new_pose.path_pose if new_pose else None}")
        self._pose_order = new_pose
        if new_pose is None:
            self.shared_properties["new_pose_order"] = None
            self.shared_properties["pose_order"] = None
        else:
            self.shared_properties["new_pose_order"] = new_pose.path_pose.model_dump(exclude_unset=True)
        self.shared_properties["last_avoidance_pose_current"] = None

    async def set_pose_reached(self):
        """
        Set pose reached for a robot.
        """
        logger.info("Planner: set_pose_reached()")

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

    async def set_intermediate_pose_reached(self):
        """
        Set pose reached for a robot.
        """
        logger.info("Planner: set_intermediate_pose_reached()")

        # The pose reached is intermediate, just force path recompute.
        self.shared_properties["last_avoidance_pose_current"] = None

    async def next_pose_in_action(self):
        if self.action and len(self.action.poses) > 0:
            pose_order = self.action.poses.pop(0)
            self.pose_order = None
            await pose_order.act_before_pose()
            self.blocked_counter = 0
            self.pose_order = pose_order

            if self.properties.strategy in [Strategy.PidLinearSpeedTest, Strategy.PidAngularSpeedTest]:
                await self.sio_ns.emit("pose_order", self.pose_order.path_pose.model_dump())

    async def next_pose(self):
        """
        Select the next pose for a robot.
        """
        logger.info("Planner: next_pose()")
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
        logger.info(f"Planner: set action '{action.name}'")
        self.pose_order = None
        self.action = action
        await self.action.act_before_action()
        await self.next_pose_in_action()

    async def blocked(self):
        """
        Function called when a robot cannot find a path to go to the current pose of the current action
        """
        if (current_action := self.action) and current_action.interruptable:
            logger.info("Planner: blocked")
            if new_action := self.get_action():
                await self.set_action(new_action)
            await current_action.recycle()
            self.actions.append(current_action)
            if not self.pose_order:
                await self.sio_receiver_queue.put(self.set_pose_reached())

    async def update_obstacles(self):
        table = self.game_context.table
        try:
            margin = self.properties.obstacle_bb_margin * self.properties.robot_length / 2
            if self.properties.bypass_detector:
                shared_obstacles = self.shared_monitor_obstacles
                shared_lock = self.shared_monitor_obstacles_lock
            else:
                shared_obstacles = self.shared_detector_obstacles
                shared_lock = self.shared_detector_obstacles_lock
            shared_lock.start_reading()
            self.shared_obstacles_lock.start_writing()
            self.shared_circle_obstacles.clear()
            self.shared_rectangle_obstacles.clear()

            # Add dynamic obstacles
            for detector_obstacle in shared_obstacles:
                if not table.contains(detector_obstacle, margin):
                    continue
                if self.robot_id == 1:
                    radius = self.properties.obstacle_radius
                else:
                    radius = detector_obstacle.radius
                radius += self.properties.robot_length / 2
                self.shared_circle_obstacles.append(
                    x=detector_obstacle.x,
                    y=detector_obstacle.y,
                    angle=0,
                    radius=radius,
                    bounding_box_margin=margin,
                    bounding_box_points_number=self.properties.obstacle_bb_vertices,
                )
            shared_lock.finish_reading()

            if not self.properties.disable_fixed_obstacles:
                if self.robot_id == 1:
                    # Add artifact obstacles
                    construction_areas: list[ConstructionArea] = list(
                        self.game_context.construction_areas.values()
                    ) + list(self.game_context.opponent_construction_areas.values())
                    for construction_area in construction_areas:
                        if not construction_area.enabled:
                            continue
                        if not table.contains(construction_area, margin):
                            continue
                        self.shared_rectangle_obstacles.append(
                            x=construction_area.x,
                            y=construction_area.y,
                            angle=construction_area.O,
                            length_x=construction_area.length + self.properties.robot_width,
                            length_y=construction_area.width + self.properties.robot_width,
                            bounding_box_margin=margin,
                            id=construction_area.id.value,
                        )
                    for tribune in self.game_context.tribunes.values():
                        if not tribune.enabled:
                            continue
                        if not table.contains(tribune, margin):
                            continue
                        self.shared_rectangle_obstacles.append(
                            x=tribune.x,
                            y=tribune.y,
                            angle=tribune.O,
                            length_x=tribune.width + self.properties.robot_width,
                            length_y=tribune.length + self.properties.robot_width,
                            bounding_box_margin=margin,
                            id=tribune.id.value,
                        )

                # Add fixed obstacles
                for fixed_obstacle in self.game_context.fixed_obstacles.values():
                    if not fixed_obstacle.enabled:
                        continue
                    if not table.contains(fixed_obstacle, margin):
                        continue
                    self.shared_rectangle_obstacles.append(
                        x=fixed_obstacle.x,
                        y=fixed_obstacle.y,
                        angle=0,
                        length_x=fixed_obstacle.width + self.properties.robot_width,
                        length_y=fixed_obstacle.length + self.properties.robot_width,
                        bounding_box_margin=margin,
                        id=fixed_obstacle.id.value,
                    )

            self.shared_obstacles_lock.finish_writing()
            self.shared_obstacles_lock.post_update()
        except Exception as exc:
            logger.warning(f"Planner: update_obstacles: Unknown exception {exc}")
            traceback.print_exc()

    async def update_oled_display(self):
        try:
            pose_current = self.pose_current
            text = (
                f"{'Connected' if self.sio.connected else 'Not connected': <20}"
                f"{'▶' if self.game_context.playing else '◼'}\n"
                f"Camp: {self.game_context.camp.color.name}\n"
                f"Strategy: {self.properties.strategy.name}\n"
                f"Pose: {pose_current.x},{pose_current.y},{pose_current.O}\n"
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
            schema["sio_event"] = "config_updated"
            # Add current values in JSON Schema
            for prop, value in RootModel[Properties](self.properties).model_dump(mode="json").items():
                schema["properties"][prop]["value"] = value
            # Send config
            await self.sio_ns.emit("config", schema)
            return

        if cmd == "scservos":
            # Get JSON Schema
            schema = self.scservos.get_schema()
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
            case "obstacle_updater_interval":
                self.obstacles_updater_loop.interval = self.properties.obstacle_updater_interval
            case "robot_width" | "obstacle_bb_vertices":
                self.game_context.create_artifacts()
                self.game_context.create_fixed_obstacles()

    async def update_scservo(self, servo: dict[str, Any]) -> None:
        """
        Update a SC Servo with the value sent by the dashboard.
        """
        self.scservos.set(SCServoEnum[servo["name"]], servo["value"])

    async def cmd_play(self):
        """
        Play command from the menu.
        """
        logger.info("Planner: cmd_play()")
        if self.game_context.playing:
            return

        await self.sio_ns.emit("start_countdown", self.game_context.game_duration)

        self.game_context.countdown = self.game_context.game_duration
        self.game_context.playing = True
        self.led.color = Color("blue")

        await self.sio_ns.emit("start_video_record")
        await self.sio_receiver_queue.put(self.set_pose_reached())

    async def cmd_stop(self):
        """
        Stop command from the menu.
        """
        logger.info("Planner: cmd_stop()")
        self.game_context.playing = False
        await self.sio_ns.emit("stop_video_record")

    async def cmd_next(self):
        """
        Next command from the menu.
        Ignored if current pose is not reached for all robots.
        """
        logger.info("Planner: cmd_next()")
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
        logger.info("Planner: cmd_reset()")
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
        choices: list[tuple[str, str, str]] = []  # list of (category, value, name). Name can be used for display.
        for strategy in Strategy:
            split = re.findall(r"[A-Z][a-z]*|[a-z]+|[0-9]+", strategy.name)
            choices.append((strategy.name, split[0], " ".join(split)))
        await self.sio_ns.emit(
            "wizard",
            {
                "name": "Choose Strategy",
                "type": "choice_str",
                "choices": choices,
                "value": self.properties.strategy.name,
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
                "value": self.properties.table.name,
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
                if self.properties.table == TableEnum.Training and new_camp == Camp.Colors.yellow:
                    logger.warning("Wizard: only blue camp is authorized on training table")
                    return
                self.game_context.camp.color = new_camp
                await self.soft_reset()
                logger.info(f"Wizard: New camp: {self.game_context.camp.color.name}")
            case "Choose Strategy":
                new_strategy = Strategy[value]
                if self.properties.strategy == new_strategy:
                    return
                self.properties.strategy = new_strategy
                await self.soft_reset()
                logger.info(f"Wizard: New strategy: {self.properties.strategy.name}")
            case "Choose Avoidance":
                new_strategy = AvoidanceStrategy[value]
                if self.game_context.avoidance_strategy == new_strategy:
                    return
                self.game_context.avoidance_strategy = new_strategy
                self.shared_properties["avoidance_strategy"] = new_strategy
                logger.info(f"Wizard: New avoidance strategy: {self.game_context.avoidance_strategy.name}")
            case "Choose Start Position":
                self.start_position = StartPosition[value]
                await self.soft_reset()
            case "Choose Table":
                new_table = TableEnum[value]
                if self.game_context.table == new_table:
                    return
                if self.game_context.camp.color == Camp.Colors.yellow and new_table == TableEnum.Training:
                    logger.warning("Wizard: training table is not supported with yellow camp")
                    await self.sio_ns.emit(
                        "wizard",
                        {
                            "name": "Error",
                            "type": "message",
                            "value": "Training table is not supported with yellow camp",
                        },
                    )
                    return
                self.properties.table = new_table
                self.shared_table_limits[0] = self.game_context.table.x_min
                self.shared_table_limits[1] = self.game_context.table.x_max
                self.shared_table_limits[2] = self.game_context.table.y_min
                self.shared_table_limits[3] = self.game_context.table.y_max
                self.shared_properties["table"] = new_table
                await self.soft_reset()
                logger.info(f"Wizard: New table: {self.properties.table.name}")
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
                    "choices": ["one", "two", "three"],
                    "value": "two",
                }
            case "wizard_choice_str_group":
                message = {
                    "name": "Wizard Test Choice String",
                    "type": "choice_str",
                    "choices": [
                        ("one", "Group A", "One"),
                        ("two", "Group A", "Two"),
                        ("three", "Group B", "Three"),
                    ],
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
                    "value": "blue",
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
