from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tools.planner.planner import Planner


class MockDummyClass:
    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return self

    def __setattr__(self, name, value):
        pass


def no_op(*args, **kwargs):
    pass


async def async_no_op(*args, **kwargs):
    pass


class MockAsyncioSleep:
    def __init__(self) -> None:
        self.total_sleep = 0

    async def __call__(self, seconds: int):
        self.total_sleep += seconds

    def reset(self):
        self.total_sleep = 0


class MockSCServos:
    def set(self, *args, **kwargs):
        pass


class MockSIO:
    async def emit(self, *args, **kwargs):
        pass


class MockPlanner:
    def __init__(self, planner: "Planner"):
        self.robot_id = planner.robot_id
        self.game_context = planner.game_context.deepcopy()
        self.pose_current = planner.pose_current.model_copy()
        self.shared_properties = planner.shared_properties
        self.scservos = MockSCServos()
        self.sio_ns = MockSIO()
