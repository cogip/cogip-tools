import importlib.util
import inspect
import sys
from pathlib import Path

from cogip.utils.argenum import ArgEnum
from .. import logger
from .strategy import Strategy


def strip_action_name(name: str) -> str:
    if name.endswith("Strategy"):
        return name[:-8]
    return name


strategies_found = []

for path in Path(__file__).parent.glob("*.py"):
    if path.name == "__init__.py":
        continue
    module_name = path.stem
    module_path = path.resolve()

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError:
        logger.error(
            f"Import error in 'cogip/tools/planner/actions/{module_path.name}': "
            "Modules from the 'cogip.planner.actions' package cannot use relative import "
            "to allow dynamic discovery of Strategy classes."
        )
        sys.exit(1)

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Strategy) and obj is not Strategy:
            strategies_found.append(obj)

sorted_strategies = sorted(strategies_found, key=lambda cls: cls.__name__)
strategies_map = {strip_action_name(strategy.__name__): i + 1 for i, strategy in enumerate(sorted_strategies)}

StrategyEnum = ArgEnum("StrategyEnum", strategies_map)

strategy_classes: dict[StrategyEnum, Strategy] = {
    strategy: strategies_class for strategy, strategies_class in zip(StrategyEnum, sorted_strategies)
}
