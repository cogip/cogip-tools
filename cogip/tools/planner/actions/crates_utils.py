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
    logger.info("take_crates: begin")
    lift_up_pose = 128
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
    duration = await lift_up(pose=lift_up_pose, speed=lift_speed)
    await asyncio.sleep(duration + 0.5)  # Extra time to wait for crates to stop moving

    # Close grips
    duration = await grips_close()
    await asyncio.sleep(duration)

    # Update context
    if side == "front":
        planner.game_context.front_free = False
    else:
        planner.game_context.back_free = False

    logger.info("take_crates: end")


async def turn_crates_in_camp_color(planner: "Planner", side: Literal["front", "back"]):
    """
    Turn the crates in the camp color if they are not already.
    """
    logger.info("turn_crates_in_camp_color: begin")
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
        scissors_open = functools.partial(actuators.front_scissors_open, planner, speed=scissors_speed)
        scissors_close = functools.partial(actuators.front_scissors_close, planner, speed=scissors_speed)
        axis_left_side_in = functools.partial(actuators.front_axis_left_side_in, planner, speed=axis_speed)
        axis_right_side_in = functools.partial(actuators.front_axis_right_side_in, planner, speed=axis_speed)
        axis_left_center_in = functools.partial(actuators.front_axis_left_center_in, planner, speed=axis_speed)
        axis_right_center_in = functools.partial(actuators.front_axis_right_center_in, planner, speed=axis_speed)
    else:
        logger.info("turn_crates_in_camp_color: back selected")
        crates_ids = planner.game_context.back_crates
        arms_open = functools.partial(actuators.back_arms_open, planner)
        arms_close = functools.partial(actuators.back_arms_close, planner)
        scissors_open = functools.partial(actuators.back_scissors_open, planner, speed=scissors_speed)
        scissors_close = functools.partial(actuators.back_scissors_close, planner, speed=scissors_speed)
        axis_left_side_in = functools.partial(actuators.back_axis_left_side_in, planner, speed=axis_speed)
        axis_right_side_in = functools.partial(actuators.back_axis_right_side_in, planner, speed=axis_speed)
        axis_left_center_in = functools.partial(actuators.back_axis_left_center_in, planner, speed=axis_speed)
        axis_right_center_in = functools.partial(actuators.back_axis_right_center_in, planner, speed=axis_speed)

    # Open arms
    duration = await arms_open()
    await asyncio.sleep(duration / 2)

    # Open scissors
    duration = await scissors_open()
    await asyncio.sleep(duration)

    # Turn bad crate outwards
    turn_funcs = [
        axis_left_side_in,
        axis_left_center_in,
        axis_right_center_in,
        axis_right_side_in,
    ]
    to_turn = [i for i, crate_id in enumerate(crates_ids) if crate_id == bad_crate_id]

    batches = []
    for i in to_turn:
        for batch in batches:
            # Check that the current crate is not adjacent to the last one added in this batch
            if batch[-1] != i - 1:
                batch.append(i)
                break
        else:
            batches.append([i])

    for batch in batches:
        duration = 0
        for i in batch:
            duration = await turn_funcs[i]()
        if duration > 0:
            await asyncio.sleep(duration)

    crates_ids[:] = [good_crate_id, good_crate_id, good_crate_id, good_crate_id]

    # Close scissors
    duration = await scissors_close()
    await asyncio.sleep(duration / 2)

    # Close arms
    duration = await arms_close()
    await asyncio.sleep(duration)

    # Update context
    crates_ids[:] = [good_crate_id, good_crate_id, good_crate_id, good_crate_id]

    logger.info("turn_crates_in_camp_color: end")


async def drop_crates(planner: "Planner", side: Literal["front", "back"]) -> Pose:
    """
    Drop the crates.
    """
    linear_speed_front = 10
    linear_speed_back = 20
    lift_speed_front = 25
    lift_speed_back = 20
    lift_wait_front = 1.5
    lift_wait_back = 2
    backward_distance_front = 200
    backward_distance_back = 300
    distance_to_move_before_lift_down_front = 2
    distance_to_move_before_lift_down_back = 1
    action_during_backward_end_event = asyncio.Event()

    if side == "front":
        linear_speed = linear_speed_front
        lift_speed = lift_speed_front
        lift_wait = lift_wait_front
        backward_distance = backward_distance_front
        distance_to_move_before_lift_down = distance_to_move_before_lift_down_front
        lift_init = functools.partial(actuators.front_lift_init, planner)
        lift_down = functools.partial(actuators.front_lift_down, planner)
        grips_open = functools.partial(actuators.front_grips_open, planner)
    else:
        linear_speed = linear_speed_back
        lift_speed = lift_speed_back
        lift_wait = lift_wait_back
        backward_distance = -backward_distance_back
        distance_to_move_before_lift_down = distance_to_move_before_lift_down_back
        lift_init = functools.partial(actuators.back_lift_init, planner)
        lift_down = functools.partial(actuators.back_lift_down, planner)
        grips_open = functools.partial(actuators.back_grips_open, planner)

    pose_current = planner.pose_current

    async def before_drop():
        logger.info("drop_crates: before_drop: begin")
        await turn_crates_in_camp_color(planner, side)

        # Open grips
        await grips_open()

        asyncio.create_task(action_during_backward(pose_current))

        logger.info("drop_crates: before_drop: end")

    async def after_drop():
        logger.info("drop_crates: after_drop: begin")

        await init_grips(planner, side)

        if action_during_backward_end_event.is_set():
            logger.info("drop_crates: after_drop: action_during_backward already ended")
        else:
            logger.info("drop_crates: after_drop: waiting for action_during_backward to end")
            await action_during_backward_end_event.wait()
            logger.info("drop_crates: after_drop: action_during_backward ended")

        # Update context
        if side == "front":
            planner.game_context.front_free = True
            planner.game_context.front_crates = [None, None, None, None]
        else:
            planner.game_context.back_free = True
            planner.game_context.back_crates = [None, None, None, None]

        logger.info("drop_crates: after_drop: end")

    async def action_during_backward(pose_current: models.Pose):
        logger.info("drop_crates: action_during_backward: begin")

        # Wait until the robot has started moving backward by checking the change in pose_current
        logger.info("drop_crates: action_during_backward: waiting for robot to start moving backward")
        while True:
            new_pose_current = planner.pose_current
            distance = math.dist((new_pose_current.x, new_pose_current.y), (pose_current.x, pose_current.y))
            if distance > distance_to_move_before_lift_down:
                break
            await asyncio.sleep(0.05)
        logger.info("drop_crates: action_during_backward: robot started moving backward")

        # Move lift down
        await lift_down(speed=lift_speed)
        await asyncio.sleep(lift_wait)

        # Re-init lift in case the lift got stuck on the ground and to prepare for the next lift up
        await lift_init()

        action_during_backward_end_event.set()
        logger.info("drop_crates: action_during_backward end")

    # Drop pose
    drop_pose = Pose(
        **get_relative_pose(pose_current, front_offset=-backward_distance).model_dump(),
        max_speed_linear=linear_speed,
        max_speed_angular=10,
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
