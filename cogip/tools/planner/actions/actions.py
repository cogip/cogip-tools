from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action import Action

if TYPE_CHECKING:
    from ..planner import Planner


class Actions(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """

    def __init__(self, planner: "Planner"):
        super().__init__()
        self.planner = planner
