import asyncio
import os
from typing import Annotated

import socketio
import typer
import yaml

from cogip.models import FirmwareParametersGroup
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager


async def main_async(server_url: str, parameters_group: FirmwareParametersGroup):
    """
    CLI utility to test firmware parameter communication.
    Creates its own Socket.IO client to host the FirmwareParameterManager.
    """
    sio = socketio.AsyncClient(logger=False)
    manager = FirmwareParameterManager(sio=sio, parameter_group=parameters_group)

    await sio.connect(server_url, namespaces=[manager.namespace])

    print("Firmware parameter values before reading from firmware:")
    for param in manager.parameter_group:
        print(f"  {param.name:.<40} {param.value}")
    print()

    for param in manager.parameter_group:
        try:
            await manager.get_parameter_value(param.name)
        except TimeoutError:
            print(f"  {param.name:.<40} TIMEOUT")

    print("Firmware parameter values after reading from firmware:")
    for param in manager.parameter_group:
        print(f"  {param.name:.<40} {param.value}")
    print()

    manager.cleanup()
    await sio.disconnect()


def main_opt(
    *,
    server_url: Annotated[
        str | None,
        typer.Option(
            help="Socket.IO Server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    robot_id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID.",
            envvar=["ROBOT_ID"],
        ),
    ] = 1,
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
    if not server_url:
        host = os.environ.get("COGIP_SERVER_HOST", "localhost")
        server_url = f"http://{host}:809{robot_id}"

    parameters_data = yaml.safe_load(parameters)
    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    asyncio.run(main_async(server_url, parameters_group))


def main():
    """
    Run firmware parameter manager utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-parameter-manager` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
