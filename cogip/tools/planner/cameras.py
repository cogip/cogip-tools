from typing import TYPE_CHECKING

import httpx

from cogip.models import Pose, Vertex
from . import logger
from .camp import Camp

if TYPE_CHECKING:
    from .robot import Robot


async def snapshot():
    camp = Camp().color.value
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8100/snapshots?camp={camp}")
            if response.status_code != 200:
                logger.warning(f"Request snapshot: Failed: {response.status_code}: {response.text}")
        except httpx.HTTPError as exc:
            logger.error(f"Request snapshot: HTTP Exception: {exc}")


async def calibrate_camera(robot: "Robot") -> Vertex | None:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + robot.robot_id
            queries = f"x={robot.pose_current.x}"
            queries += f"&y={robot.pose_current.y}"
            queries += f"&angle={robot.pose_current.O}"
            response = await client.get(f"http://robot{robot.robot_id}:{port}/camera_calibration?{queries}")
            if response.status_code != 200:
                logger.warning(f"Request camera_calibration: Failed: {response.status_code}: {response.text}")
                return None
            return Vertex.model_validate(response.json())
        except httpx.HTTPError as exc:
            logger.error(f"Request camera_calibration: HTTP Exception: {exc}")
            return None
        except Exception as exc:  # noqa
            logger.error(f"Request camera_calibration: Unknown exception: {exc}")
            return None


async def get_robot_position(robot: "Robot") -> Pose | None:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + robot.robot_id
            response = await client.get(f"http://robot{robot.robot_id}:{port}/robot_position")
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


async def get_solar_panels(robot: "Robot") -> dict[int, float]:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + robot.robot_id
            queries = f"x={robot.pose_current.x}"
            queries += f"&y={robot.pose_current.y}"
            queries += f"&angle={robot.pose_current.O}"
            response = await client.get(f"http://robot{robot.robot_id}:{port}/solar_panels?{queries}")
            if response.status_code != 200:
                logger.warning(f"Request solar_panels: Failed: {response.status_code}: {response.text}")
                return {}
            return {int(panel_id): angle for panel_id, angle in response.json().items()}
        except httpx.HTTPError as exc:
            logger.error(f"Request solar_panels: HTTP Exception: {exc}")
            return {}
        except Exception as exc:  # noqa
            logger.error(f"Request solar_panels: Unknown exception: {exc}")
            return {}
