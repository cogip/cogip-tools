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
    "bottom_grip_close",
    "bottom_grip_open",
    "top_grip_close",
    "top_grip_open",
    "bottom_lift_down",
    "bottom_lift_up",
    "top_lift_down",
    "top_lift_up",
    "cart_in",
    "cart_out",
    "cart_magnet_on",
    "cart_magnet_off",
    "arm_panel_open",
    "arm_panel_close",
    "bottom_grip_left_close",
    "bottom_grip_left_open",
    "bottom_grip_right_close",
    "bottom_grip_right_open",
    "top_grip_left_close",
    "top_grip_left_open",
    "top_grip_right_close",
    "top_grip_right_open",
    "cart_magnet_left_on",
    "cart_magnet_left_off",
    "cart_magnet_right_on",
    "cart_magnet_right_off",
]

robot_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in robot_actuators_commands
    ],
)

pami_actuators_commands = [
    "pami_arm_close",
    "pami_arm_open",
]

pami_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in pami_actuators_commands
    ],
)
