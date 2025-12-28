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

robot_front_actuators_commands = [
    "actuators_init",
    "front_lift_down",
    "front_lift_mid",
    "front_lift_up",
    "front_grip_left_side_open",
    "front_grip_left_side_close",
    "front_grip_left_center_open",
    "front_grip_left_center_close",
    "front_grip_right_center_open",
    "front_grip_right_center_close",
    "front_grip_right_side_open",
    "front_grip_right_side_close",
    "front_axis_left_side_out",
    "front_axis_left_side_in",
    "front_axis_left_center_out",
    "front_axis_left_center_in",
    "front_axis_right_center_out",
    "front_axis_right_center_in",
    "front_axis_right_side_out",
    "front_axis_right_side_in",
    "front_arm_left_open",
    "front_arm_left_close",
    "front_arm_right_open",
    "front_arm_right_close",
]

robot_front_actuators_menu = models.ShellMenu(
    name="Front Actuators",
    entries=[
        models.MenuEntry(
            cmd=f"act_{cmd}",
            desc=f"{cmd.replace('_', ' ').title()}",
        )
        for cmd in robot_front_actuators_commands
    ],
)

robot_back_actuators_commands = [
    "actuators_init",
    "back_lift_down",
    "back_lift_mid",
    "back_lift_up",
    "back_grip_left_side_open",
    "back_grip_left_side_close",
    "back_grip_left_center_open",
    "back_grip_left_center_close",
    "back_grip_right_center_open",
    "back_grip_right_center_close",
    "back_grip_right_side_open",
    "back_grip_right_side_close",
    "back_axis_left_side_out",
    "back_axis_left_side_in",
    "back_axis_left_center_out",
    "back_axis_left_center_in",
    "back_axis_right_center_out",
    "back_axis_right_center_in",
    "back_axis_right_side_out",
    "back_axis_right_side_in",
    "back_arm_left_open",
    "back_arm_left_close",
    "back_arm_right_open",
    "back_arm_right_close",
]

robot_back_actuators_menu = models.ShellMenu(
    name="Back Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in robot_back_actuators_commands
    ],
)

robot_actuators_multi_commands = [
    "front_arms_open",
    "front_arms_close",
    "front_grips_open",
    "front_grips_close",
    "front_lift_down",
    "front_lift_up",
    "back_arms_open",
    "back_arms_close",
    "back_grips_open",
    "back_grips_close",
    "back_lift_down",
    "back_lift_up",
]

robot_actuators_multi_menu = models.ShellMenu(
    name="Actuators Multi",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in robot_actuators_multi_commands
    ],
)

pami_actuators_commands = []

pami_actuators_menu = models.ShellMenu(
    name="Actuators",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}", desc=f"{cmd.replace('_', ' ').title()}") for cmd in pami_actuators_commands
    ],
)
