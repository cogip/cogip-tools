from collections.abc import Awaitable, Callable
from typing import ClassVar, final

import socketio
from pydantic import field_validator

from cogip.models.models import PathPose
from .camp import Camp


class Pose(PathPose):
    """
    Pose class used in actions.
    A function can be executed before moving and an other once it is reached.
    """

    before_pose_func: Callable[[socketio.ClientNamespace], Awaitable[None]] | None = None
    intermediate_pose_func: Callable[[socketio.ClientNamespace], Awaitable[None]] | None = None
    after_pose_func: Callable[[socketio.ClientNamespace], Awaitable[None]] | None = None

    @final
    async def act_before_pose(self):
        """
        Function executed before the robot starts moving.
        """
        if self.before_pose_func:
            await self.before_pose_func()

    @final
    async def act_intermediate_pose(self):
        """
        Function executed once an intermediate pose is reached.
        """
        if self.intermediate_pose_func:
            await self.intermediate_pose_func()

    @final
    async def act_after_pose(self):
        """
        Function executed once the pose is reached.
        """
        if self.after_pose_func:
            await self.after_pose_func()

    @property
    def path_pose(self) -> PathPose:
        """
        Convert the pose into its parent class.
        """
        return PathPose(**self.model_dump())


class AdaptedPose(Pose):
    """
    Like a Pose, but its values are automatically adapted to selected camp
    during initialization.
    So to define static positions in actions, we can use this class to set pose related
    to the default camp, and if the camp changes, the pose will be adapted on reset.
    """

    _camp: ClassVar[Camp] = Camp()

    @field_validator("y")
    @classmethod
    def adapt_y(cls, v, **kwargs):
        """
        Validator to adapt Y depending on the camp at initialization.
        """
        return cls._camp.adapt_y(v)

    @field_validator("O")
    @classmethod
    def adapt_O(cls, v, **kwargs):
        """
        Validator to adapt the angle depending on the camp at initialization.
        """
        return cls._camp.adapt_angle(v)
