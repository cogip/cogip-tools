import asyncio
import time
from typing import Annotated

import socketio
import typer

from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager


async def main_async(server_url: str, duration: float):
    """
    CLI utility to test firmware telemetry reception.
    Creates its own Socket.IO client to host the FirmwareTelemetryManager.
    """
    sio = socketio.AsyncClient(logger=False)
    telemetry = FirmwareTelemetryManager(sio=sio)

    print(f"Connecting to {server_url}...")
    await sio.connect(server_url, namespaces=[telemetry.namespace])

    print("Enabling telemetry...")
    await telemetry.enable()

    print(f"Receiving telemetry data for {duration} seconds...")
    print("-" * 60)

    start_time = time.monotonic()
    last_print_time = 0.0

    try:
        while (time.monotonic() - start_time) < duration:
            await asyncio.sleep(0.1)

            # Print telemetry values every second
            current_time = time.monotonic() - start_time
            if current_time - last_print_time >= 1.0:
                last_print_time = current_time
                print(f"\n[{current_time:.1f}s] Telemetry store ({len(telemetry.store)} entries):")
                for key_hash, data in telemetry.store.items():
                    print(f"  hash=0x{key_hash:08x} ts={data.timestamp_ms}ms value={data.value}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    print("-" * 60)
    print("Disabling telemetry...")
    await telemetry.disable()

    await sio.disconnect()
    print("Disconnected.")


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
    duration: Annotated[
        float,
        typer.Option(
            "-d",
            "--duration",
            help="Duration in seconds to receive telemetry data.",
        ),
    ] = 10.0,
):
    if not server_url:
        server_url = f"http://localhost:809{robot_id}"

    asyncio.run(main_async(server_url, duration))


def main():
    """
    Run firmware telemetry utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-telemetry` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
