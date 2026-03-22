import asyncio
import functools
import math
from typing import TYPE_CHECKING, Literal

from cogip.cpp.libraries.models import MotionDirection
from cogip.models import models
from cogip.models.artifacts import Pantry, PantryID
from cogip.tools.planner import actuators, logger
from cogip.tools.planner.actions.utils import get_relative_pose
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


async def init_grips(planner: "Planner", side: Literal["front", "back"]):
    logger.info("init_grips: begin")
    scissors_speed = 1000
    axis_speed = 1000

    if side == "front":
        scissors_open = functools.partial(actuators.front_scissors_open, planner)
        scissors_close = functools.partial(actuators.front_scissors_close, planner)
        grips_close = functools.partial(actuators.front_grips_close, planner)
        axis_left_side_out = functools.partial(actuators.front_axis_left_side_out, planner)
        axis_right_side_out = functools.partial(actuators.front_axis_right_side_out, planner)
        axis_left_center_out = functools.partial(actuators.front_axis_left_center_out, planner)
        axis_right_center_out = functools.partial(actuators.front_axis_right_center_out, planner)
    else:
        scissors_open = functools.partial(actuators.back_scissors_open, planner)
        scissors_close = functools.partial(actuators.back_scissors_close, planner)
        grips_close = functools.partial(actuators.back_grips_close, planner)
        axis_left_side_out = functools.partial(actuators.back_axis_left_side_out, planner)
        axis_right_side_out = functools.partial(actuators.back_axis_right_side_out, planner)
        axis_left_center_out = functools.partial(actuators.back_axis_left_center_out, planner)
        axis_right_center_out = functools.partial(actuators.back_axis_right_center_out, planner)

    # Close grips
    await grips_close()

    # Open scissors
    duration = await scissors_open(speed=scissors_speed)
    await asyncio.sleep(duration)

    # Turn back grips outwards
    await axis_left_side_out(speed=axis_speed)
    duration = await axis_right_center_out(speed=axis_speed)
    await asyncio.sleep(duration)
    await axis_left_center_out(speed=axis_speed)
    duration = await axis_right_side_out(speed=axis_speed)
    await asyncio.sleep(duration)

    # Close scissors
    duration = await scissors_close(speed=scissors_speed)

    logger.info("init_grips: end")


async def take_crates(planner: "Planner", side: Literal["front", "back"]) -> bool:
    """
    Actions to take crates.
    """
    lift_speed = 100

    if side == "front":
        logger.info("take_crates: before_action: front selected")
        arms_close = functools.partial(actuators.front_arms_close, planner)
        lift_up = functools.partial(actuators.front_lift_up, planner)
        grips_open = functools.partial(actuators.front_grips_open, planner)
        grips_close = functools.partial(actuators.front_grips_close, planner)
    else:
        logger.info("take_crates: before_action: back selected")
        arms_close = functools.partial(actuators.back_arms_close, planner)
        lift_up = functools.partial(actuators.back_lift_up, planner)
        grips_open = functools.partial(actuators.back_grips_open, planner)
        grips_close = functools.partial(actuators.back_grips_close, planner)

    # Open grips
    await grips_open()

    # Close arms
    duration = await arms_close()
    await asyncio.sleep(duration)

    # Move lift up
    duration = await lift_up(speed=lift_speed)
    await asyncio.sleep(duration)

    # Close grips
    duration = await grips_close()
    await asyncio.sleep(duration)

    # Update context
    if side == "front":
        planner.game_context.front_free = False
    else:
        planner.game_context.back_free = False

    logger.info("take_crates: crates taken")


async def turn_crates_in_camp_color(planner: "Planner", side: Literal["front", "back"]):
    """
    Turn the crates in the camp color if they are not already.
    """
    axis_speed = 1000
    scissors_speed = 1000

    if Camp().color == Camp.Colors.blue:
        good_crate_id = 36
        bad_crate_id = 47
    else:
        good_crate_id = 47
        bad_crate_id = 36

    if side == "front":
        logger.info("turn_crates_in_camp_color: front selected")
        crates_ids = planner.game_context.front_crates
        arms_open = functools.partial(actuators.front_arms_open, planner)
        arms_close = functools.partial(actuators.front_arms_close, planner)
        scissors_open = functools.partial(actuators.front_scissors_open, planner)
        scissors_close = functools.partial(actuators.front_scissors_close, planner)
        axis_left_side_in = functools.partial(actuators.front_axis_left_side_in, planner)
        axis_right_side_in = functools.partial(actuators.front_axis_right_side_in, planner)
        axis_left_center_in = functools.partial(actuators.front_axis_left_center_in, planner)
        axis_right_center_in = functools.partial(actuators.front_axis_right_center_in, planner)
    else:
        logger.info("turn_crates_in_camp_color: back selected")
        crates_ids = planner.game_context.back_crates
        arms_open = functools.partial(actuators.back_arms_open, planner)
        arms_close = functools.partial(actuators.back_arms_close, planner)
        scissors_open = functools.partial(actuators.back_scissors_open, planner)
        scissors_close = functools.partial(actuators.back_scissors_close, planner)
        axis_left_side_in = functools.partial(actuators.back_axis_left_side_in, planner)
        axis_right_side_in = functools.partial(actuators.back_axis_right_side_in, planner)
        axis_left_center_in = functools.partial(actuators.back_axis_left_center_in, planner)
        axis_right_center_in = functools.partial(actuators.back_axis_right_center_in, planner)

    if bad_crate_id not in crates_ids:
        logger.warning("turn_crates_in_camp_color: No bad crate detected, skipping actuators execution")
        return

    # Open arms
    duration = await arms_open()
    await asyncio.sleep(duration / 2)

    # Open scissors
    duration = await scissors_open(speed=scissors_speed)
    await asyncio.sleep(duration)

    # Turn bad crate outwards
    duration = 0
    if crates_ids[0] == bad_crate_id:
        duration = await axis_left_side_in(speed=axis_speed)
    if crates_ids[2] == bad_crate_id:
        duration = await axis_right_center_in(speed=axis_speed)
    await asyncio.sleep(duration)
    duration = 0
    if crates_ids[1] == bad_crate_id:
        duration = await axis_left_center_in(speed=axis_speed)
    if crates_ids[3] == bad_crate_id:
        duration = await axis_right_side_in(speed=axis_speed)
    await asyncio.sleep(duration)

    # Close scissors
    duration = await scissors_close(speed=scissors_speed)
    await asyncio.sleep(duration / 2)

    # Close arms
    duration = await arms_close()
    await asyncio.sleep(duration)

    # Update context
    crates_ids[:] = [good_crate_id, good_crate_id, good_crate_id, good_crate_id]


async def drop_crates(planner: "Planner", side: Literal["front", "back"]) -> Pose:
    """
    Drop the crates.
    """
    linear_speed = 10
    angular_speed = 10
    lift_speed = 40
    backward_distance = 120
    if side == "back":
        backward_distance *= -1

    if side == "front":
        arms_open = functools.partial(actuators.front_arms_open, planner)
        arms_close = functools.partial(actuators.front_arms_close, planner)
        lift_down = functools.partial(actuators.front_lift_down, planner)
        lift_mid = functools.partial(actuators.front_lift_mid, planner)
        grips_open = functools.partial(actuators.front_grips_open, planner)
    else:
        arms_open = functools.partial(actuators.back_arms_open, planner)
        arms_close = functools.partial(actuators.back_arms_close, planner)
        lift_down = functools.partial(actuators.back_lift_down, planner)
        lift_mid = functools.partial(actuators.back_lift_mid, planner)
        grips_open = functools.partial(actuators.back_grips_open, planner)

    pose_current = planner.pose_current

    async def before_drop():
        logger.info("drop_crates: before_drop")
        await turn_crates_in_camp_color(planner, side)
        asyncio.create_task(action_during_backward(pose_current))

    async def after_drop():
        logger.info("drop_crates: after_drop")

        await init_grips(planner, side)

        # Update context
        if side == "front":
            planner.game_context.front_free = True
            planner.game_context.front_crates = [None, None, None, None]
        else:
            planner.game_context.back_free = True
            planner.game_context.back_crates = [None, None, None, None]

    async def action_during_backward(pose_current: models.Pose):
        logger.info("drop_crates: action_during_backward")

        # Open grips
        duration = await grips_open()
        await asyncio.sleep(duration)

        # Wait until the robot has started moving backward by checking the change in pose_current
        logger.info("drop_crates: action_during_backward: waiting for robot to start moving backward")
        while True:
            new_pose_current = planner.pose_current
            distance = math.dist((new_pose_current.x, new_pose_current.y), (pose_current.x, pose_current.y))
            if distance > 5:
                break
            await asyncio.sleep(0.05)
        logger.info("drop_crates: action_during_backward: robot started moving backward")

        # Move lift down
        duration = await lift_down(speed=lift_speed)
        await asyncio.sleep(duration)

        # Open arms
        duration = await arms_open()
        await asyncio.sleep(duration / 2)

        # Move lift mid at max speed
        duration = await lift_mid()
        await asyncio.sleep(duration / 2)

        # Close arms
        await arms_close()

        logger.info("drop_crates: action_during_backward end")

    # Drop pose
    drop_pose = Pose(
        **get_relative_pose(pose_current, front_offset=-backward_distance).model_dump(),
        max_speed_linear=linear_speed,
        max_speed_angular=angular_speed,
        motion_direction=MotionDirection.BIDIRECTIONAL,
        bypass_final_orientation=True,
        before_pose_func=before_drop,
        after_pose_func=after_drop,
    )

    logger.info(f"drop_crates: drop: x={drop_pose.x: 5.2f} y={drop_pose.y: 5.2f} O={drop_pose.O: 3.2f}°")

    return drop_pose


def shift_pantry_center_from_border(pantry: Pantry) -> tuple[float, float]:
    """
    Shift the pantry center coordinates from the border
    so its center becomes valid for avoidance.
    Only used for the inspect pose.
    """
    shift_value = 100
    x_shift_value = shift_value
    y_shift_value = Camp().adapt_y(shift_value)
    x = pantry.x
    y = pantry.y

    match pantry.id:
        case PantryID.LocalTop | PantryID.OppositeTop:
            x -= x_shift_value
        case PantryID.LocalSide:
            y += y_shift_value
        case PantryID.LocalBottom | PantryID.OppositeBottom | PantryID.MiddleBottom:
            x += x_shift_value
        case PantryID.OppositeSide:
            y -= y_shift_value

    return x, y
