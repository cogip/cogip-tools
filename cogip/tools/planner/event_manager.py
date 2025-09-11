import asyncio
import traceback
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from . import logger

if TYPE_CHECKING:
    from .planner import Planner


class EventManager:
    """
    Manages asynchronous events and tasks for the Planner.
    """

    def __init__(self, planner: "Planner"):
        self.planner = planner
        self.blocked_event_task: asyncio.Task | None = None
        self.new_path_event_task: asyncio.Task | None = None
        self.countdown_task: asyncio.Task | None = None

    async def start_loops(self):
        """Start all async event loops."""
        self.blocked_event_task = asyncio.create_task(
            self.blocked_event_loop(),
            name="Planner: Task Blocked Event Watcher Loop",
        )
        self.new_path_event_task = asyncio.create_task(
            self.new_path_event_loop(),
            name="Planner: Task New Path Event Watcher Loop",
        )
        await self.countdown_start()

    async def stop_loops(self):
        """Stop all async event loops."""
        await self.countdown_stop()

        if self.blocked_event_task:
            self.blocked_event_task.cancel()
            try:
                await self.blocked_event_task
            except asyncio.CancelledError:
                logger.info("Planner: Task Blocked Event Watcher Loop stopped")
            except Exception as exc:
                logger.warning(f"Planner: Unexpected exception {exc}")
            self.blocked_event_task = None

        if self.new_path_event_task:
            self.new_path_event_task.cancel()
            try:
                await self.new_path_event_task
            except asyncio.CancelledError:
                logger.info("Planner: Task New Path Event Watcher Loop stopped")
            except Exception as exc:
                logger.warning(f"Planner: Unexpected exception {exc}")
                traceback.print_exc()
            self.new_path_event_task = None

    async def blocked_event_loop(self):
        """Watches for robot blocked events."""
        logger.info("Planner: Task Blocked Event Watcher Loop started")
        try:
            while True:
                await asyncio.to_thread(self.planner.shared_avoidance_blocked_lock.wait_update)
                if self.planner.sio.connected:
                    await self.planner.sio_ns.emit("brake")
                self.planner.blocked_counter += 1
                if self.planner.blocked_counter > 10:
                    self.planner.blocked_counter = 0
                    await self.planner.blocked()
        except asyncio.CancelledError:
            logger.info("Planner: Task Blocked Event Watcher Loop cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Task Blocked Event Watcher Loop: Unknown exception {exc}")
            traceback.print_exc()
            raise

    async def new_path_event_loop(self):
        """Watches for new path events."""
        logger.info("Planner: Task New Path Event Watcher Loop started")
        try:
            while True:
                await asyncio.to_thread(self.planner.shared_avoidance_path_lock.wait_update)
                self.planner.blocked_counter = 0
                if self.planner.pose_order:
                    await self.planner.pose_order.act_intermediate_pose()
        except asyncio.CancelledError:
            logger.info("Planner: Task New Path Event Watcher Loop cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Task New Path Event Watcher Loop: Unknown exception {exc}")
            traceback.print_exc()
            raise

    async def countdown_loop(self):
        """Manages the game countdown."""
        logger.info("Planner: Task Countdown started")
        try:
            self.planner.game_context.last_countdown = self.planner.game_context.countdown
            while True:
                await asyncio.sleep(0.2)

                if not self.planner.playing:
                    continue

                now = datetime.now(UTC)
                self.planner.game_context.countdown = (
                    self.planner.game_context.game_duration
                    - (now - self.planner.countdown_start_timestamp).total_seconds()
                )

                logger.info(f"Planner: countdown = {self.planner.game_context.countdown: 3.2f}")
                if (
                    self.planner.robot_id > 1
                    and self.planner.game_context.countdown < 15
                    and self.planner.game_context.last_countdown > 15
                ):
                    logger.info("Planner: countdown==15: start PAMI")
                    self.planner.pami_event.set()
                if (
                    self.planner.robot_id == 1
                    and self.planner.game_context.countdown < 7
                    and self.planner.game_context.last_countdown > 7
                ):
                    logger.info("Planner: countdown==7: force blocked")
                    asyncio.create_task(self.planner.blocked())
                if self.planner.game_context.countdown < 0 and self.planner.game_context.last_countdown > 0:
                    logger.info("Planner: countdown==0: final action")
                    await self.planner.final_action()
                if self.planner.game_context.countdown < -5 and self.planner.game_context.last_countdown > -5:
                    await self.planner.sio_ns.emit("stop_video_record")
                self.planner.game_context.last_countdown = self.planner.game_context.countdown
        except asyncio.CancelledError:
            logger.info("Planner: Task Countdown cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Planner: Unknown exception {exc}")
            raise

    async def countdown_start(self):
        """Starts the countdown task."""
        await self.countdown_stop()
        self.countdown_task = asyncio.create_task(self.countdown_loop())

    async def countdown_stop(self):
        """Stops the countdown task."""
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
