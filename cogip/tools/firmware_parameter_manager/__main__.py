import asyncio
from pathlib import Path
from typing import Annotated

import socketio
import typer
import yaml

from cogip.models import FirmwareParametersGroup
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager


async def main_async(server_url: str, parameters_group: FirmwareParametersGroup, yaml_data: dict | None = None, output_path: Path | None = None):
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

    if yaml_data is not None and output_path is not None:
        for yaml_param in yaml_data["parameters"]:
            name = yaml_param["name"]
            if name in manager.parameter_group:
                yaml_param["value"]["content"] = manager.parameter_group[name]

        with open(output_path, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"Extracted parameters saved to {output_path}")

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
    extract: Annotated[
        Path | None,
        typer.Option(
            "-e",
            "--extract",
            help="Extract firmware values and save to this YAML file",
        ),
    ] = None,
):
    if not server_url:
        server_url = f"http://localhost:809{robot_id}"

    parameters_data = yaml.safe_load(parameters)
    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    asyncio.run(main_async(server_url, parameters_group, yaml_data=parameters_data if extract else None, output_path=extract))


def main():
    """
    Run firmware parameter manager utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-parameter-manager` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
