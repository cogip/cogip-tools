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

robot_actuators_commands = []

robot_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in robot_actuators_commands
    ],
)

pami_actuators_commands = []

pami_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in pami_actuators_commands
    ],
)
