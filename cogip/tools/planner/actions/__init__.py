import importlib.util
import inspect
import sys
from enum import IntEnum
from pathlib import Path

from .. import logger
from .actions import Actions


def strip_action_name(name: str) -> str:
    if name.endswith("Actions"):
        return name[:-7]
    return name


actions_found = []

for path in Path(__file__).parent.glob("*.py"):
    if path.name == "__init__.py":
        continue
    module_name = path.stem
    module_path = path.resolve()

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError as e:
        logger.error(
            f"Import error in 'cogip/tools/planner/actions/{module_path.name}': "
            "Modules from the 'cogip.planner.actions' package cannot use relative import "
            "to allow dynamic discovery of Actions classes."
        )
        logger.error(e)
        sys.exit(1)

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Actions) and obj is not Actions:
            actions_found.append(obj)

sorted_actions = sorted(actions_found, key=lambda cls: cls.__name__)
actions_map = {strip_action_name(strategy.__name__): i + 1 for i, strategy in enumerate(sorted_actions)}

Strategy = IntEnum("Strategy", actions_map)

action_classes: dict[Strategy, Actions] = {
    strategy: actions_class for strategy, actions_class in zip(Strategy, sorted_actions)
}
