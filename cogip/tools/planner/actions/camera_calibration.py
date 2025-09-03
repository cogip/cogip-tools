import asyncio
from typing import TYPE_CHECKING

from cogip.models.models import Vertex
from cogip.tools.planner import logger
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.cameras import calibrate_camera
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class CameraCalibrationAction(Action):
    """
    This action moves around the front right table marker, and take pictures to compute
    camera extrinsic parameters (ie, the position of the camera relative to the robot center).
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("CameraCalibration action", planner, actions)
        self.camera_positions: list[Vertex] = []
        self.after_action_func = self.print_camera_positions

        self.poses.append(
            Pose(
                x=-220,
                y=-(1500 - 450 + self.planner.shared_properties.robot_width / 2),
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-220,
                y=-800,
                O=160,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-220,
                y=-540,
                O=-160,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-260,
                y=-320,
                O=-130,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-500,
                y=-320,
                O=-90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-710,
                y=-460,
                O=-70,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-810,
                y=-760,
                O=0,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

        self.poses.append(
            Pose(
                x=-(1000 - 450 + self.planner.shared_properties.robot_width / 2),
                y=-(1500 - 450 + self.planner.shared_properties.robot_width / 2),
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.calibrate_camera,
            )
        )

    async def calibrate_camera(self):
        await asyncio.sleep(1)
        if pose := await calibrate_camera(self.planner):
            self.camera_positions.append(pose)
        await asyncio.sleep(0.5)

    async def print_camera_positions(self):
        x = 0
        y = 0
        z = 0
        for i, p in enumerate(self.camera_positions):
            logger.info(f"Camera position {i: 2d}: X={p.x:.0f} Y={p.y:.0f} Z={p.z:.0f}")
            x += p.x
            y += p.y
            z += p.z

        if n := len(self.camera_positions):
            p = Vertex(x=x / n, y=y / n, z=z / n)
            logger.info(f"=> Camera position mean: X={p.x:.0f} Y={p.y:.0f} Z={p.z:.0f}")
        else:
            logger.warning("No camera position found")

    def weight(self) -> float:
        return 1000000.0


class CameraCalibrationActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(CameraCalibrationAction(planner, self))
