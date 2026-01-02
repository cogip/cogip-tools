import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any


class AsyncLoop:
    """
    This class creates a async task to execute a function in loop and wait after
    the function until the defined loop interval is reached.
    A warning is emitted if the function duration is longer than the loop
    interval.
    """

    def __init__(
        self,
        name: str,
        interval: float,
        func: Callable,
        logger: bool | logging.Logger = False,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ):
        """
        Class constructor.

        Arguments:
            name: Name to identify the thread in the logs
            interval: time between each iteration of the loop, in seconds
            func: function to execute in the loop
            logger: an optional custom logger
            args: arguments of the function
            kwargs: named arguments of the function
        """
        self._name = name
        self.interval = interval
        self._func = func
        self._args = args or []
        self._kwargs = kwargs or {}
        self._logger = logging.getLogger(f"AsyncLoop: {name}")
        self._task: asyncio.Task | None = None
        self.exit: bool = False

        if not isinstance(logger, bool):
            self._logger = logger
        else:
            if self._logger.level == logging.NOTSET:
                if logger:
                    self._logger.setLevel(logging.DEBUG)
                else:
                    self._logger.setLevel(logging.INFO)

    async def task(self) -> None:
        """
        Loop function executed in the task.
        """
        self._logger.info("Task started")

        try:
            while not self.exit:
                start = time.time()
                await self._func(*self._args, **self._kwargs)
                now = time.time()
                duration = now - start
                if duration > self.interval:
                    self._logger.warning(f"Function too long: {duration} > {self.interval}")
                else:
                    wait = self.interval - duration
                    await asyncio.sleep(wait)
        except asyncio.CancelledError:
            raise

    def start(self):
        if self._task:
            self._logger.warning("Already started")
            return

        self.exit = False
        self._task = asyncio.create_task(self.task(), name=self._name)

    async def stop(self):
        if not self._task:
            self._logger.warning("Not running")
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            self._logger.info("Task cancelled")

        self._task = None
