from __future__ import annotations
from enum import Enum


class ArgEnum(Enum):
    """
    This base class can be used to define Enum argument for Typer.
    It allows to use the Enum name of the enum in the command line arguments instead the Enum value.
    To get the Enum value, use `ArgEnum.val` property instead of `ArgEnum.value`.

    This workaround is explained here: https://github.com/tiangolo/typer/issues/151#issuecomment-1755370085.
    There is a pending merge request here: https://github.com/tiangolo/typer/pull/224.
    """

    def __init__(self, val):
        self.val = val

    @property
    def value(self):
        return self.name

    def __eq__(self, other: ArgEnum | int | str) -> bool:
        if isinstance(other, int | str):
            return self.val == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.val)
