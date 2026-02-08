from cogip import models

menu = models.ShellMenu(
    name="Planner",
    entries=[
        models.MenuEntry(cmd="game_wizard", desc="Wizard"),
        models.MenuEntry(cmd="choose_camp", desc="Choose camp"),
        models.MenuEntry(cmd="choose_strategy", desc="Choose strategy"),
        models.MenuEntry(cmd="choose_avoidance", desc="Choose avoidance"),
        models.MenuEntry(cmd="choose_table", desc="Choose table"),
        models.MenuEntry(cmd="choose_start_position", desc="Choose start position"),
        models.MenuEntry(cmd="play", desc="Play"),
        models.MenuEntry(cmd="stop", desc="Stop"),
        models.MenuEntry(cmd="next", desc="Next"),
        models.MenuEntry(cmd="reset", desc="Reset"),
        models.MenuEntry(cmd="config", desc="Configuration"),
        models.MenuEntry(cmd="scservos", desc="SC Servos"),
    ],
)

wizard_test_menu = models.ShellMenu(
    name="Wizard Test",
    entries=[
        models.MenuEntry(cmd="wizard_boolean", desc="Boolean"),
        models.MenuEntry(cmd="wizard_integer", desc="Integer"),
        models.MenuEntry(cmd="wizard_floating", desc="Float"),
        models.MenuEntry(cmd="wizard_str", desc="String"),
        models.MenuEntry(cmd="wizard_message", desc="Message"),
        models.MenuEntry(cmd="wizard_choice_integer", desc="Choice Integer"),
        models.MenuEntry(cmd="wizard_choice_floating", desc="Choice Float"),
        models.MenuEntry(cmd="wizard_choice_str", desc="Choice String"),
        models.MenuEntry(cmd="wizard_choice_str_group", desc="Choice String Group"),
        models.MenuEntry(cmd="wizard_select_integer", desc="Select Integer"),
        models.MenuEntry(cmd="wizard_select_floating", desc="Select Float"),
        models.MenuEntry(cmd="wizard_select_str", desc="Select String"),
        models.MenuEntry(cmd="wizard_camp", desc="Camp"),
        models.MenuEntry(cmd="wizard_camera", desc="Camera"),
        models.MenuEntry(cmd="wizard_score", desc="Score"),
    ],
)

cameras_menu = models.ShellMenu(
    name="Cameras",
    entries=[
        models.MenuEntry(cmd="cam_snapshot", desc="Snapshot"),
        models.MenuEntry(cmd="cam_camera_position", desc="Camera Position"),
    ],
)

robot_actuators_commands = [
    "actuators_init",
    # Lift 1 commands (10mm increments)
    "lift1_0",
    "lift1_10",
    "lift1_20",
    "lift1_30",
    "lift1_40",
    "lift1_50",
    "lift1_60",
    "lift1_70",
    "lift1_80",
    "lift1_90",
    "lift1_100",
    "lift1_110",
    # Lift 2 commands (10mm increments)
    "lift2_0",
    "lift2_10",
    "lift2_20",
    "lift2_30",
    "lift2_40",
    "lift2_50",
    "lift2_60",
    "lift2_70",
    "lift2_80",
    "lift2_90",
    "lift2_100",
    "lift2_110",
]


def _format_actuator_desc(cmd: str) -> str:
    """Format actuator command to readable description."""
    # lift1_5 -> "Lift 1: 5", actuators_init -> "Actuators Init"
    if cmd.startswith("lift"):
        # Extract lift number and position
        parts = cmd.split("_")
        lift_num = parts[0][-1]  # "1" or "2"
        position = parts[1] if len(parts) > 1 else "0"
        return f"Lift {lift_num}: {position}"
    return cmd.replace("_", " ").title()


robot_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[models.MenuEntry(cmd=f"act_{cmd}", desc=_format_actuator_desc(cmd)) for cmd in robot_actuators_commands],
)

robot_actuators_multi_commands = [
    # Lift 1 commands (10mm increments)
    "lift1_0",
    "lift1_10",
    "lift1_20",
    "lift1_30",
    "lift1_40",
    "lift1_50",
    "lift1_60",
    "lift1_70",
    "lift1_80",
    "lift1_90",
    "lift1_100",
    "lift1_110",
    # Lift 2 commands (10mm increments)
    "lift2_0",
    "lift2_10",
    "lift2_20",
    "lift2_30",
    "lift2_40",
    "lift2_50",
    "lift2_60",
    "lift2_70",
    "lift2_80",
    "lift2_90",
    "lift2_100",
    "lift2_110",
]

robot_actuators_multi_menu = models.ShellMenu(
    name="Actuators Multi",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=_format_actuator_desc(cmd)) for cmd in robot_actuators_multi_commands
    ],
)

pami_actuators_commands = []

pami_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in pami_actuators_commands
    ],
)
