import platform
from dataclasses import dataclass, field

from cogip import models
from cogip.utils.singleton import Singleton


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        robot_id:           Robot ID
        planner_sid:        Planner sid
        copilot_sid:        Copilot sid
        detector_sid:       Detector sid
        robotcam_sid:       Robotcam sid
        beacon_sid:         Beacon server sid
        monitor_sid:        Monitor sid
        tool_menus:         all registered tool menus
        current_tool_menu:  name of the currently selected tool menu
        shell_menu:         last received shell menu
        virtual:            Whether robot is virtual or not
        virtual_planner:    Whether planner is virtual or not
        virtual_detector:   Whether detector is virtual or not
    """

    robot_id: int | None = None
    planner_sid: str | None = None
    copilot_sid: str | None = None
    detector_sid: str | None = None
    robotcam_sid: str | None = None
    beacon_sid: str | None = None
    monitor_sid: str | None = None
    tool_menus: dict[str, models.ShellMenu] = field(default_factory=dict)
    current_tool_menu: str | None = None
    shell_menu: models.ShellMenu | None = None
    virtual = platform.machine() != "aarch64"
    virtual_planner = False
    virtual_detector = False
