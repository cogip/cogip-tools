import asyncio
from typing import Annotated

import typer
import yaml

from cogip.models.models import PathPose
from cogip.protobuf import PB_PathPose
from cogip.tools.copilot.copilot import (
    game_reset_uuid,
    path_add_point_uuid,
    path_reset_uuid,
    path_start_uuid,
)
from cogip.tools.copilot.pbcom import PBCom


def parse_path(raw_path: list) -> list[PathPose]:
    """Parse YAML path entries into PathPose objects.

    Each entry can be either:
      - A list of 3 elements: [X_mm, Y_mm, O_deg]
      - A dict with PathPose fields (x, y, O, max_speed_linear, etc.)
    """
    path_poses = []
    for entry in raw_path:
        if isinstance(entry, list):
            if len(entry) != 3:
                raise ValueError(f"Expected [X, Y, O], got list of length {len(entry)}: {entry}")
            path_poses.append(PathPose(x=entry[0], y=entry[1], O=entry[2]))
        elif isinstance(entry, dict):
            path_poses.append(PathPose(**entry))
        else:
            raise ValueError(f"Unexpected path entry type: {type(entry)}: {entry}")
    return path_poses


async def send_waypoint(pbcom: PBCom, path_pose: PathPose):
    pb_path_pose = PB_PathPose()
    path_pose.copy_pb(pb_path_pose)
    await pbcom.send_can_message(path_add_point_uuid, pb_path_pose)


async def main_async(pbcom: PBCom, path_poses: list[PathPose]):
    pbcom_task = asyncio.create_task(pbcom.run())

    # Game reset
    await pbcom.send_can_message(game_reset_uuid, None)
    await pbcom.messages_to_send.join()

    # Path reset
    await pbcom.send_can_message(path_reset_uuid, None)
    await pbcom.messages_to_send.join()

    # Add each waypoint
    for path_pose in path_poses:
        await send_waypoint(pbcom, path_pose)
        await pbcom.messages_to_send.join()

    # Start path execution
    await pbcom.send_can_message(path_start_uuid, None)
    await pbcom.messages_to_send.join()

    try:
        pbcom_task.cancel()
        await pbcom_task
    except asyncio.CancelledError:
        pass


def main_opt(
    *,
    can_channel: Annotated[
        str,
        typer.Option(
            "-cc",
            "--can-channel",
            help="CAN channel connected to STM32 modules",
            envvar="PATH_SENDER_CAN_CHANNEL",
        ),
    ] = "vcan0",
    can_bitrate: Annotated[
        int,
        typer.Option(
            "-b",
            "--can-bitrate",
            help="CAN bitrate",
            envvar="PATH_SENDER_CAN_BITRATE",
        ),
    ] = 500000,
    can_data_bitrate: Annotated[
        int,
        typer.Option(
            "-B",
            "--data-bitrate",
            help="CAN FD data bitrate",
            envvar="PATH_SENDER_CANFD_DATA_BITRATE",
        ),
    ] = 1000000,
    path_file: Annotated[
        typer.FileText,
        typer.Option(
            "-p",
            "--path",
            help="YAML file containing the path as a sequence of [X, Y, O] waypoints in [mm, mm, deg]",
            envvar="PATH_SENDER_PATH",
        ),
    ],
):
    data = yaml.safe_load(path_file)
    path_poses = parse_path(data["path"])
    pbcom = PBCom(can_channel, can_bitrate, can_data_bitrate, {})
    asyncio.run(main_async(pbcom, path_poses))


def main():
    """
    Run path-sender utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-path-sender` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
