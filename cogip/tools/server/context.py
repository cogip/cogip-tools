from dataclasses import dataclass, field
from typing import Literal

from bidict import bidict

from cogip import models
from cogip.utils.singleton import Singleton


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        copilot_sids:       map Copilot sid (str) to robot id (int)
        detector_sids:      map Detector sid (str) to robot id (int)
        detector_modes:     map robot id to Detector mode
        robotcam_sids:      map Robotcam sid (str) to robot id (int)
        tool_menus:         all registered tool menus
        current_tool_menu:  name of the currently selected tool menu
        shell_menu:         last received shell menu
        connected_robots:   list of robots already connected
        virtual_robots:     list of virtual robots connected
    """

    copilot_sids = bidict()
    detector_sids = bidict()
    detector_modes: dict[int, Literal["detection", "emulation"]] = field(default_factory=dict)
    robotcam_sids = bidict()
    tool_menus: dict[str, models.ShellMenu] = field(default_factory=dict)
    current_tool_menu: str | None = None
    shell_menu: dict[int, models.ShellMenu] = field(default_factory=dict)
    connected_robots: list[int] = field(default_factory=list)
    virtual_robots: list[int] = field(default_factory=list)
