import asyncio
from typing import TYPE_CHECKING

from cogip.models.models import CameraExtrinsicParameters
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.cameras import calibrate_camera
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class CameraCalibrationAction(Action):
    """
    This action moves around the front right table marker, and take pictures to compute
    camera extrinsic parameters (ie, the position of the camera relative to the robot center).
    """

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("CameraCalibration action", planner, strategy)
        self.camera_positions: list[CameraExtrinsicParameters] = []
        self.after_action_func = self.print_camera_positions

        self.poses.append(
            Pose(
                x=-500,
                y=-1200,
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-240,
                y=-1200,
                O=130,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-240,
                y=-570,
                O=-130,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-240,
                y=-440,
                O=-130,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-500,
                y=-420,
                O=-90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-610,
                y=-510,
                O=-70,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-710,
                y=-910,
                O=0,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-610,
                y=-1250,
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

    async def calibrate_camera(self):
        await asyncio.sleep(0.5)
        if pose := await calibrate_camera(self.planner):
            self.camera_positions.append(pose)
        await asyncio.sleep(0.2)

    async def print_camera_positions(self):
        x = 0
        y = 0
        z = 0
        roll = 0
        pitch = 0
        yaw = 0
        for i, p in enumerate(self.camera_positions):
            self.logger.info(
                f"Camera position {i: 2d}: X={p.x:.0f} Y={p.y:.0f} Z={p.z:.0f}"
                f" Roll={p.roll:.0f} Pitch={p.pitch:.0f} Yaw={p.yaw:.0f}"
            )
            x += p.x
            y += p.y
            z += p.z
            roll += p.roll
            pitch += p.pitch
            yaw += p.yaw

        if n := len(self.camera_positions):
            p = CameraExtrinsicParameters(x=x / n, y=y / n, z=z / n, roll=roll / n, pitch=pitch / n, yaw=yaw / n)
            self.logger.info(
                f"=> Camera position mean: X={p.x:.0f} Y={p.y:.0f} Z={p.z:.0f}"
                f" Roll={p.roll:.0f} Pitch={p.pitch:.0f} Yaw={p.yaw:.0f}"
            )
        else:
            self.logger.warning("No camera position found")

    def weight(self) -> float:
        return 1000000.0


class CameraCalibrationStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CameraCalibrationAction(planner, self))
