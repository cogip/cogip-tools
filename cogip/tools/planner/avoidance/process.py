import logging
import math
import os
import time

from cogip import models
from cogip.cpp.libraries.obstacles import ObstacleCircle as SharedObstacleCircle
from cogip.cpp.libraries.obstacles import ObstacleRectangle as SharedObstacleRectangle
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory
from cogip.utils.logger import Logger
from ..actions import Strategy
from .avoidance import Avoidance, AvoidanceStrategy


def avoidance_process(robot_id: int):
    logger = Logger("cogip-avoidance", enable_cpp=True)
    if os.getenv("AVOIDANCE_DEBUG") not in [None, False, "False", "false", 0, "0", "no", "No"]:
        logger.setLevel(logging.DEBUG)

    logger.info("Avoidance: process started")
    shared_memory = SharedMemory(f"cogip_{robot_id}")
    shared_memory_properties = shared_memory.get_properties()
    shared_pose_current_buffer = shared_memory.get_pose_current_buffer()
    shared_pose_current_lock = shared_memory.get_lock(LockName.PoseCurrent)
    shared_circle_obstacles = shared_memory.get_circle_obstacles()
    shared_rectangle_obstacles = shared_memory.get_rectangle_obstacles()
    shared_obstacles_lock = shared_memory.get_lock(LockName.Obstacles)
    shared_avoidance_pose_order = shared_memory.get_avoidance_pose_order()
    shared_avoidance_blocked_lock = shared_memory.get_lock(LockName.AvoidanceBlocked)
    shared_avoidance_path = shared_memory.get_avoidance_path()
    shared_avoidance_path_lock = shared_memory.get_lock(LockName.AvoidancePath)
    avoidance = Avoidance(shared_memory_properties)
    pose_order: models.PathPose | None = None
    last_pose_current: models.Pose | None = None
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_memory_properties.path_refresh_interval + 0.01

    while not shared_memory.avoidance_exiting:
        path_refresh_interval = shared_memory_properties.path_refresh_interval
        now = time.time()
        duration = now - start
        if duration > path_refresh_interval:
            logger.warning(f"Avoidance: {duration:0.3f}ms > {path_refresh_interval:0.3f}ms")
        else:
            wait = path_refresh_interval - duration
            time.sleep(wait)
        start = time.time()

        # Check if new pose order has been computed
        if shared_memory.avoidance_has_new_pose_order:
            pose_order = models.PathPose.from_shared(shared_avoidance_pose_order)
            logger.info(f"Avoidance: New pose order received: {pose_order}")
            shared_memory.avoidance_has_pose_order = True
            shared_memory.avoidance_has_new_pose_order = False
            last_pose_current = None
            last_emitted_pose_order = None

        # Check if pose order is available
        if not shared_memory.avoidance_has_pose_order or not pose_order:
            logger.debug("Avoidance: Skip path update (no pose order)")
            last_pose_current = None
            last_emitted_pose_order = None
            continue

        # Get current pose
        shared_pose_current_lock.start_reading()
        shared_pose_current = shared_pose_current_buffer.last
        pose_current = models.PathPose.from_shared(shared_pose_current)
        shared_pose_current_lock.finish_reading()

        if shared_memory_properties.strategy in [Strategy.PidLinearSpeedTest.val, Strategy.PidAngularSpeedTest.val]:
            logger.debug("Avoidance: Skip path update (speed test)")
            continue

        if last_pose_current:
            # Check if pose order is far enough from current pose
            dist_xy = math.dist((pose_current.x, pose_current.y), (pose_order.x, pose_order.y))
            dist_angle = abs(pose_current.O - pose_order.O)
            if dist_xy < 20 and dist_angle < 5:
                logger.debug(
                    "Avoidance: Skip path update "
                    f"(pose current and order too close: {dist_xy:0.2f}mm {dist_angle:0.2f}°)"
                )
                continue

            # Check if robot has moved enough since the last avoidance path was computed
            if (last_pose_current.x, last_pose_current.y) != (pose_current.x, pose_current.y) and (
                dist := math.dist(
                    (pose_current.x, pose_current.y),
                    (last_pose_current.x, last_pose_current.y),
                )
            ) < 20:
                logger.debug(f"Avoidance: Skip path update (current pose too close: {dist:0.2f}mm)")
                continue

        # Create dynamic obstacles
        dyn_obstacles: list[SharedObstacleCircle | SharedObstacleRectangle] = []
        if shared_memory_properties.avoidance_strategy != AvoidanceStrategy.Disabled.val:
            # Deep copy of obstacles to not block the shared memory
            shared_obstacles_lock.start_reading()
            for obstacle in shared_circle_obstacles:
                dyn_obstacles.append(SharedObstacleCircle(obstacle, deep_copy=True))
            for obstacle in shared_rectangle_obstacles:
                dyn_obstacles.append(SharedObstacleRectangle(obstacle, deep_copy=True))
            shared_obstacles_lock.finish_reading()

        if shared_memory_properties.avoidance_strategy == AvoidanceStrategy.AvoidanceCpp.val:
            # Recreate obstacles list
            avoidance.cpp_avoidance.clear_dynamic_obstacles()
            for obstacle in dyn_obstacles:
                avoidance.cpp_avoidance.add_dynamic_obstacle(obstacle)

            # Path is recomputed only if the pose order is reachable or an obstacle prevents
            # to reach next path pose.
            if (
                (
                    (not avoidance.check_recompute(pose_current, pose_order) and robot_id == 1)
                    and last_emitted_pose_order != pose_order
                )
                or last_emitted_pose_order is None
                or avoidance.check_recompute(pose_current, last_emitted_pose_order)
            ):
                logger.info("Avoidance: compute path")
                path = avoidance.get_path(pose_current, pose_order)
        else:
            if any([obstacle.is_point_inside(pose_current.x, pose_current.y) for obstacle in dyn_obstacles]):
                logger.info("Avoidance: pose current in obstacle")
                path = []
            elif any([obstacle.is_point_inside(pose_order.x, pose_order.y) for obstacle in dyn_obstacles]):
                logger.info("Avoidance: pose order in obstacle")
                path = []
            else:
                if pose_current.x == pose_order.x and pose_current.y == pose_order.y:
                    # If the pose order is just a rotation from the pose current, the avoidance will not find any path,
                    # so set the path manually
                    logger.debug("Avoidance: rotation only")
                    path = [pose_current.model_copy(), pose_order.model_copy()]
                else:
                    path = avoidance.get_path(pose_current, pose_order)

        if len(path) == 0:
            logger.debug("Avoidance: No path found")
            last_pose_current = None
            last_emitted_pose_order = None
            shared_avoidance_blocked_lock.post_update()
            continue

        last_pose_current = pose_current.pose

        for p in path:
            p.allow_reverse = pose_order.allow_reverse
            p.timeout_ms = pose_order.timeout_ms
            p.max_speed_linear = pose_order.max_speed_linear
            p.max_speed_angular = pose_order.max_speed_angular

        if len(path) == 1:
            # Only one pose in path means the pose order is reached and robot is waiting next order,
            # so do nothing.
            logger.debug("Avoidance: len(path) == 1")
            continue

        if len(path) >= 2 and last_emitted_pose_order:
            dist_xy = math.dist((last_emitted_pose_order.x, last_emitted_pose_order.y), (path[1].x, path[1].y))
            if not path[1].bypass_final_orientation:
                dist_angle = abs(path[1].O - last_emitted_pose_order.O)
                if dist_xy < 20 and dist_angle < 5:
                    logger.debug(
                        f"Avoidance: Skip path update (new pose order too close: {dist_xy:0.2f}/{dist_angle:0.2f})"
                    )
                    continue
            else:
                if dist_xy < 20:
                    logger.debug(f"Avoidance: Skip path update (new pose order too close: {dist_xy:0.2f})")
                    continue

        if last_emitted_pose_order == path[1]:
            logger.debug("Avoidance: ignore path update (last_emitted_pose_order == path[1])")
            continue

        if shared_memory.avoidance_has_new_pose_order:
            logger.debug("Avoidance: ignore path update (new pose order has been received)")
            continue

        logger.info("Avoidance: Update path")
        last_emitted_pose_order = path[1].model_copy()
        shared_avoidance_path_lock.start_writing()
        shared_avoidance_path.clear()
        for pose in path[1:]:
            shared_avoidance_path.append()
            shared_pose = shared_avoidance_path[shared_avoidance_path.size() - 1]
            pose.to_shared(shared_pose)
        shared_avoidance_path_lock.finish_writing()
        shared_avoidance_path_lock.post_update()

    # Remove reference to shared memory data to trigger garbage collection
    shared_avoidance_path_lock = None
    shared_avoidance_path = None
    shared_avoidance_blocked_lock = None
    shared_avoidance_pose_order = None
    shared_circle_obstacles = None
    shared_rectangle_obstacles = None
    shared_obstacles_lock = None
    shared_pose_current_lock = None
    shared_pose_current_buffer = None
    shared_memory_properties = None
    shared_memory = None

    logger.info("Avoidance: process exited")
