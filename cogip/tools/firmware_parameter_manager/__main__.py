import asyncio
from typing import Annotated

import typer
import yaml

from cogip.models.firmware_parameter import FirmwareParametersGroup
from cogip.tools.copilot.pbcom import PBCom
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager


async def main_async(pbcom: PBCom, manager: FirmwareParameterManager):
    pbcom_task = asyncio.create_task(pbcom.run())

    print("Firmware parameter values before reading from firmware:")
    for param in manager.parameter_group:
        print(f"  {param.name:.<40} {param.value}")
    print()

    for param in manager.parameter_group:
        await manager.get_parameter_value(param.name)

    print("Firmware parameter values after reading from firmware:")
    for param in manager.parameter_group:
        print(f"  {param.name:.<40} {param.value}")
    print()

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
            envvar="PARAMETER_CAN_CHANNEL",
        ),
    ] = "can0",
    can_bitrate: Annotated[
        int,
        typer.Option(
            "-b",
            "--can-bitrate",
            help="CAN bitrate",
            envvar="PARAMETER_CAN_BITRATE",
        ),
    ] = 500000,
    can_data_bitrate: Annotated[
        int,
        typer.Option(
            "-B",
            "--data-bitrate",
            help="CAN FD data bitrate",
            envvar="PARAMETER_CANFD_DATA_BITRATE",
        ),
    ] = 1000000,
    parameters: Annotated[
        typer.FileText,
        typer.Option(
            "-p",
            "--parameters",
            help="YAML file containing firmware parameter list",
            envvar="PARAMETER_LIST",
        ),
    ],
):
    parameters_data = yaml.safe_load(parameters)
    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    pbcom = PBCom(can_channel, can_bitrate, can_data_bitrate, message_handlers={})
    manager = FirmwareParameterManager(pbcom, parameters_group)

    asyncio.run(main_async(pbcom, manager))


def main():
    """
    Run firmware parameter manager utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-parameter-manager` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
