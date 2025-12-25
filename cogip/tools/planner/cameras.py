from typing import TYPE_CHECKING

import httpx

from cogip.models import CameraExtrinsicParameters, Pose
from . import logger
from .camp import Camp

if TYPE_CHECKING:
    from .planner import Planner


async def snapshot():
    camp = Camp().color.value
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8100/snapshots?camp={camp}")
            if response.status_code != 200:
                logger.warning(f"Request snapshot: Failed: {response.status_code}: {response.text}")
        except httpx.HTTPError as exc:
            logger.error(f"Request snapshot: HTTP Exception: {exc}")


async def calibrate_camera(planner: "Planner") -> CameraExtrinsicParameters | None:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + planner.robot_id
            queries = f"x={planner.pose_current.x}"
            queries += f"&y={planner.pose_current.y}"
            queries += f"&angle={planner.pose_current.O}"
            response = await client.get(f"http://robot{planner.robot_id}:{port}/camera_calibration?{queries}")
            if response.status_code != 200:
                logger.warning(f"Request camera_calibration: Failed: {response.status_code}: {response.text}")
                return None
            return CameraExtrinsicParameters.model_validate(response.json())
        except httpx.HTTPError as exc:
            logger.error(f"Request camera_calibration: HTTP Exception: {exc}")
            return None
        except Exception as exc:  # noqa
            logger.error(f"Request camera_calibration: Unknown exception: {exc}")
            return None


async def get_robot_position(planner: "Planner") -> Pose | None:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + planner.robot_id
            response = await client.get(f"http://robot{planner.robot_id}:{port}/robot_position")
            if response.status_code != 200:
                logger.warning(f"Request robot_position: Failed: {response.status_code}: {response.text}")
                return None
            return Pose.model_validate(response.json())
        except httpx.HTTPError as exc:
            logger.error(f"Request robot_position: HTTP Exception: {exc}")
            return None
        except Exception as exc:  # noqa
            logger.error(f"Request robot_position: Unknown exception: {exc}")
            return None
