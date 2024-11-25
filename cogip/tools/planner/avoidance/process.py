import math
import time
from multiprocessing import Queue
from multiprocessing.managers import DictProxy

from pydantic import TypeAdapter

from cogip import models
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
    avoidance = Avoidance(table, shared_properties)
    avoidance_path: list[models.PathPose] = []
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_properties["path_refresh_interval"] + 0.01

    path = []

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

        pose_current = shared_properties["pose_current"]
        pose_order = shared_properties["pose_order"]
        last_avoidance_pose_current = shared_properties["last_avoidance_pose_current"]
        if not pose_current:
            logger.debug("Avoidance: Skip path update (no pose current)")
            continue
        if not pose_order:
            logger.debug("Avoidance: Skip path update (no pose order)")
            continue
        if not last_avoidance_pose_current:
            last_emitted_pose_order = None

        pose_current = models.PathPose.model_validate(pose_current)
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
        if shared_properties["avoidance_strategy"] == AvoidanceStrategy.Disabled:
            dyn_obstacles = []
        else:
            dyn_obstacles = TypeAdapter(models.DynObstacleList).validate_python(shared_properties["obstacles"])

        #if len(path) == 0 or avoidance.check_recompute(pose_current, pose_order):
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

        logger.info("Avoidance: Update path")
        queue_sio.put(("path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))
        queue_sio.put(("pose_order", new_pose_order.model_dump(exclude_defaults=True)))

    logger.info("Avoidance: process exited")
