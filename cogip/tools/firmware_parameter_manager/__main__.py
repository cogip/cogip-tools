import asyncio
from pathlib import Path
from typing import Annotated

import socketio
import typer
import yaml

from cogip.models import FirmwareParameterSchema
from cogip.tools.firmware_parameter_manager import shell
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.utils.console_ui import ConsoleUI

DEFAULT_PARAMETERS_FILE = Path(__file__).with_name("firmware_parameters.yaml")


async def main_async(server_url: str, schema: FirmwareParameterSchema) -> None:
    sio = socketio.AsyncClient(logger=False)
    manager = FirmwareParameterManager(sio=sio, parameter_group=schema.group())
    ui = ConsoleUI()

    await sio.connect(server_url, namespaces=[manager.namespace])
    try:
        await shell.run(manager, ui, schema)
    finally:
        manager.cleanup()
        if sio.connected:
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
        typer.FileText | None,
        typer.Option(
            "-p",
            "--parameters",
            help=f"YAML file containing firmware parameter sections (default: {DEFAULT_PARAMETERS_FILE.name})",
            envvar="PARAMETER_LIST",
        ),
    ] = None,
):
    if not server_url:
        server_url = f"http://localhost:809{robot_id}"

    if parameters is None:
        parameters_data = yaml.safe_load(DEFAULT_PARAMETERS_FILE.read_text())
    else:
        parameters_data = yaml.safe_load(parameters)

    schema = FirmwareParameterSchema.model_validate(parameters_data)
    asyncio.run(main_async(server_url, schema))


def main():
    """
    Run firmware parameter manager utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-parameter-manager` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
