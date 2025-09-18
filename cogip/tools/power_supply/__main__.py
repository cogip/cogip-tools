import asyncio
from typing import Annotated

import typer

from cogip.models import PowerSupplyStatus
from cogip.protobuf import PB_PowerRailsStatus, PB_EmergencyStopStatus, PB_PowerSupplyRequest
from cogip.tools.copilot.copilot import (
    power_rails_status_uuid,
    emergency_stop_status_uuid,
    power_supply_request_uuid,
)
from cogip.tools.copilot.pbcom import PBCom, pb_exception_handler


# Global status storage
current_status = PowerSupplyStatus()
status_received = False


@pb_exception_handler
async def handle_power_rails_status(encoded_payload: bytes):
    """Handle power rails status message from power supply board"""
    global current_status, status_received
    pb_status = PB_PowerRailsStatus()
    pb_status.ParseFromString(encoded_payload)

    current_status.p3V3_pgood = pb_status.p3V3_pgood
    current_status.p5V0_pgood = pb_status.p5V0_pgood
    current_status.p7V5_pgood = pb_status.p7V5_pgood
    current_status.pxVx_pgood = pb_status.pxVx_pgood

    status_received = True


@pb_exception_handler
async def handle_emergency_stop_status(encoded_payload: bytes):
    """Handle emergency stop status message from power supply board"""
    global current_status, status_received
    pb_status = PB_EmergencyStopStatus()
    pb_status.ParseFromString(encoded_payload)

    current_status.emergency_stop = pb_status.emergency_stop
    status_received = True


async def request_status(pbcom: PBCom):
    """Request power supply status from the board"""
    request = PB_PowerSupplyRequest()
    await pbcom.send_can_message(power_supply_request_uuid, request)


async def main_async(pbcom: PBCom, once: bool, output_format: str, timeout: float):
    """Main async function"""
    global current_status, status_received

    pbcom_task = asyncio.create_task(pbcom.run())

    try:
        if once:
            # Single request mode
            await request_status(pbcom)
            await pbcom.messages_to_send.join()

            # Wait for response with timeout
            start_time = asyncio.get_event_loop().time()
            while not status_received and (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(0.1)

            if status_received:
                if output_format == "json":
                    print(current_status.model_dump_json())
                else:
                    print(f"3.3V Power Good: {current_status.p3V3_pgood}")
                    print(f"5.0V Power Good: {current_status.p5V0_pgood}")
                    print(f"7.5V Power Good: {current_status.p7V5_pgood}")
                    print(f"Variable Voltage Power Good: {current_status.pxVx_pgood}")
                    print(f"Emergency Stop: {'Released' if current_status.emergency_stop else 'Engaged'}")
            else:
                print("Timeout: No response from power supply board")
        else:
            # Continuous monitoring mode
            while True:
                await request_status(pbcom)
                await pbcom.messages_to_send.join()

                if output_format == "json" and status_received:
                    print(current_status.model_dump_json())
                    status_received = False  # Reset for next iteration

                await asyncio.sleep(1)  # Request every second

    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        pbcom_task.cancel()
        try:
            await pbcom_task
        except asyncio.CancelledError:
            pass


def main_opt(
    *,
    can_channel: Annotated[
        str,
        typer.Option(
            "-c",
            "--can-channel",
            help="CAN channel connected to power supply board",
            envvar="POWER_SUPPLY_CAN_CHANNEL",
        ),
    ] = "vcan0",
    can_bitrate: Annotated[
        int,
        typer.Option(
            "-b",
            "--can-bitrate",
            help="CAN bitrate",
            envvar="POWER_SUPPLY_CAN_BITRATE",
        ),
    ] = 500000,
    canfd_data_bitrate: Annotated[
        int,
        typer.Option(
            "-B",
            "--data-bitrate",
            help="CAN FD data bitrate",
            envvar="POWER_SUPPLY_CANFD_DATA_BITRATE",
        ),
    ] = 1000000,
    output_format: Annotated[
        str,
        typer.Option(
            "-f",
            "--format",
            help="Output format: json or text",
        ),
    ] = "json",
    once: Annotated[
        bool,
        typer.Option(
            "-o",
            "--once",
            help="Get status once and exit (instead of continuous monitoring)",
        ),
    ] = False,
    timeout: Annotated[
        float,
        typer.Option(
            "-t",
            "--timeout",
            help="Timeout in seconds for single status request",
        ),
    ] = 5.0,
):
    """Monitor power supply board status via CAN bus"""

    message_handlers = {
        power_rails_status_uuid: handle_power_rails_status,
        emergency_stop_status_uuid: handle_emergency_stop_status,
    }

    pbcom = PBCom(can_channel, can_bitrate, canfd_data_bitrate, message_handlers)
    asyncio.run(main_async(pbcom, once, output_format, timeout))


def main():
    """
    Run power supply status tool.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-power-supply` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()