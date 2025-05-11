import asyncio
from typing import Annotated

import typer
import yaml
from pydantic import TypeAdapter

from cogip.models.actuators import (
    ActuatorCommand,
    PositionalActuatorCommand,
)
from cogip.protobuf import PB_ActuatorCommand
from cogip.tools.copilot.copilot import (
    actuator_command_uuid,
)
from cogip.tools.copilot.pbcom import PBCom


async def actuator_command(pbcom: PBCom, uuid: int, command: ActuatorCommand):
    pb_command = PB_ActuatorCommand()
    if isinstance(command, PositionalActuatorCommand):
        command.pb_copy(pb_command.positional_actuator)
    await pbcom.send_can_message(uuid, pb_command)


async def main_async(pbcom: PBCom, commands: list[ActuatorCommand]):
    pbcom_task = asyncio.create_task(pbcom.run())

    for command in commands:
        await actuator_command(pbcom, actuator_command_uuid, command)
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
            envvar="CANSEND_CAN_CHANNEL",
        ),
    ] = "vcan0",
    can_bitrate: Annotated[
        int,
        typer.Option(
            "-b",
            "--can-bitrate",
            help="CAN bitrate",
            envvar="CANSEND_CAN_BITRATE",
        ),
    ] = 500000,
    can_data_bitrate: Annotated[
        int,
        typer.Option(
            "-B",
            "--data-bitrate",
            help="CAN FD data bitrate",
            envvar="CANSEND_CANFD_DATA_BITRATE",
        ),
    ] = 1000000,
    commands: Annotated[
        typer.FileText,
        typer.Option(
            "-c",
            "--commands",
            help="YAML file containing ",
            envvar="CANSEND_COMMANDS",
        ),
    ],
):
    commands_list = yaml.safe_load(commands)
    actuators_commands = TypeAdapter(list[ActuatorCommand]).validate_python(commands_list)
    pbcom = PBCom(can_channel, can_bitrate, can_data_bitrate, {})
    asyncio.run(main_async(pbcom, actuators_commands))


def main():
    """
    Run cansend utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-cansend` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
