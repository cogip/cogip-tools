import math
import time
from multiprocessing import Queue
from multiprocessing.managers import DictProxy

from cogip import models
from cogip.cpp.libraries.obstacles import ObstacleCircle as SharedObstacleCircle
from cogip.cpp.libraries.obstacles import ObstacleRectangle as SharedObstacleRectangle
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory
from .. import logger
from ..actions import Strategy
from ..table import Table
from .avoidance import Avoidance, AvoidanceStrategy


def avoidance_process(
    strategy: Strategy,
    table: Table,
    shared_properties: DictProxy,
    queue_sio: Queue,
):
    logger.info("Avoidance: process started")
    shared_memory = SharedMemory(f"cogip_{shared_properties["robot_id"]}")
    shared_data = shared_memory.get_data()
    shared_pose_current_lock = shared_memory.get_lock(LockName.PoseCurrent)
    shared_circle_obstacles = shared_memory.get_circle_obstacles()
    shared_rectangle_obstacles = shared_memory.get_rectangle_obstacles()
    shared_obstacles_lock = shared_memory.get_lock(LockName.Obstacles)

    avoidance = Avoidance(table, shared_properties)
    avoidance_path: list[models.PathPose] = []
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_properties["path_refresh_interval"] + 0.01

    while not shared_properties["exiting"]:
        queue_sio.put(("avoidance_path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))
        path_refresh_interval = shared_properties["path_refresh_interval"]

        now = time.time()
        duration = now - start
        if duration > path_refresh_interval:
            logger.warning(f"Avoidance: {duration:0.3f}ms > {path_refresh_interval:0.3f}ms")
        else:
            wait = path_refresh_interval - duration
            time.sleep(wait)
        start = time.time()

        avoidance_path = []

        pose_order = shared_properties["pose_order"]
        last_avoidance_pose_current = shared_properties["last_avoidance_pose_current"]
        if not pose_order:
            logger.debug("Avoidance: Skip path update (no pose order)")
            continue
        if not last_avoidance_pose_current:
            last_emitted_pose_order = None

        shared_pose_current_lock.start_reading()
        pose_current = models.PathPose(
            x=shared_data.pose_current.x,
            y=shared_data.pose_current.y,
            O=shared_data.pose_current.angle,
        )
        shared_pose_current_lock.finish_reading()
        pose_order = models.PathPose.model_validate(pose_order)

        if strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            logger.debug("Avoidance: Skip path update (speed test)")
            continue

        if last_avoidance_pose_current:
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
            if (
                last_avoidance_pose_current != (pose_current.x, pose_current.y)
                and (
                    dist := math.dist(
                        (pose_current.x, pose_current.y),
                        (last_avoidance_pose_current[0], last_avoidance_pose_current[1]),
                    )
                )
                < 20
            ):
                logger.debug(f"Avoidance: Skip path update (current pose too close: {dist:0.2f}mm)")
                continue

        # Create dynamic obstacles
        dyn_obstacles: list[SharedObstacleCircle | SharedObstacleRectangle] = []
        if shared_properties["avoidance_strategy"] != AvoidanceStrategy.Disabled:
            # Deep copy of obstacles to not block the shared memory
            shared_obstacles_lock.start_reading()
            for obstacle in shared_circle_obstacles:
                dyn_obstacles.append(SharedObstacleCircle(obstacle, deep_copy=True))
            for obstacle in shared_rectangle_obstacles:
                dyn_obstacles.append(SharedObstacleRectangle(obstacle, deep_copy=True))
            shared_obstacles_lock.finish_reading()

        if shared_properties["avoidance_strategy"] == AvoidanceStrategy.AvoidanceCpp:
            shared_properties["last_avoidance_pose_current"] = (pose_current.x, pose_current.y)

            # Recreate obstacles list
            avoidance.cpp_avoidance.clear_dynamic_obstacles()
            for obstacle in dyn_obstacles:
                avoidance.cpp_avoidance.add_dynamic_obstacle(obstacle)

            # Path is recomputed only if the pose order is reachable or an obstacle prevents
            # to reach next path pose.
            if (not avoidance.check_recompute(pose_current, pose_order) and last_emitted_pose_order != pose_order) \
                    or last_emitted_pose_order is None \
                    or avoidance.check_recompute(pose_current, last_emitted_pose_order):
                logger.info("Avoidance: compute path")
                path = avoidance.get_path(pose_current, pose_order, dyn_obstacles)
        else:
            if any([obstacle.is_point_inside(pose_current.x, pose_current.y) for obstacle in dyn_obstacles]):
                logger.debug("Avoidance: pose current in obstacle")
                path = []
            elif any([obstacle.is_point_inside(pose_order.x, pose_order.y) for obstacle in dyn_obstacles]):
                logger.debug("Avoidance: pose order in obstacle")
                path = []
            else:
                shared_properties["last_avoidance_pose_current"] = (pose_current.x, pose_current.y)

                if pose_current.x == pose_order.x and pose_current.y == pose_order.y:
                    # If the pose order is just a rotation from the pose current, the avoidance will not find any path,
                    # so set the path manually
                    logger.debug("Avoidance: rotation only")
                    path = [pose_current, pose_order]
                else:
                    path = avoidance.get_path(pose_current, pose_order, dyn_obstacles)

        if len(path) == 0:
            logger.debug("Avoidance: No path found")
            shared_properties["last_avoidance_pose_current"] = None
            last_emitted_pose_order = None
            queue_sio.put(("blocked", None))
            continue

        for p in path:
            p.allow_reverse = pose_order.allow_reverse

        if len(path) == 1:
            # Only one pose in path means the pose order is reached and robot is waiting next order,
            # so do nothing.
            logger.debug("Avoidance: len(path) == 1")
            continue

        if len(path) >= 2 and last_emitted_pose_order:
            dist_xy = math.dist((last_emitted_pose_order.x, last_emitted_pose_order.y), (path[1].x, path[1].y))
            dist_angle = abs(path[1].O - last_emitted_pose_order.O)
            if not path[1].bypass_final_orientation:
                if dist_xy < 20 and dist_angle < 5:
                    logger.debug(
                        f"Avoidance: Skip path update (new pose order too close: {dist_xy:0.2f}/{dist_angle:0.2f})"
                    )
                    continue
            else:
                if dist_xy < 20:
                    logger.debug(f"Avoidance: Skip path update (new pose order too close: {dist_xy:0.2f})")
                    continue

        if len(path) > 2:
            # Intermediate pose
            next_delta_x = path[2].x - path[1].x
            next_delta_y = path[2].y - path[1].y

            path[1].O = math.degrees(math.atan2(next_delta_y, next_delta_x))  # noqa
            path[1].allow_reverse = True

        avoidance_path = path[1:]
        new_pose_order = path[1]

        if last_emitted_pose_order == new_pose_order:
            logger.debug("Avoidance: ignore path update (last_emitted_pose_order == new_pose_order)")
            continue

        last_emitted_pose_order = new_pose_order.model_copy()

        logger.debug("Avoidance: Update path")
        queue_sio.put(("path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))
        queue_sio.put(("pose_order", new_pose_order.model_dump(exclude_defaults=True)))

    # Remove reference to shared memory data to trigger garbage collection
    shared_data = None
    shared_pose_current_lock = None
    shared_memory = None

    logger.info("Avoidance: process exited")
