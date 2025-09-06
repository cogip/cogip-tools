from typing import TYPE_CHECKING

from cogip.tools.planner.actions.action import Action

if TYPE_CHECKING:
    from ..planner import Planner


class Strategy(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """

    def __init__(self, planner: "Planner"):
        super().__init__()
        self.planner = planner

    def get_next_action(self) -> Action | None:
        """
        Get a next action of the strategy.
        """
        sorted_actions = sorted(
            [action for action in self if not action.recycled and action.weight() > 0],
            key=lambda action: action.weight(),
        )

        if len(sorted_actions) == 0:
            return None

        action = sorted_actions[-1]
        self.remove(action)
        return action
