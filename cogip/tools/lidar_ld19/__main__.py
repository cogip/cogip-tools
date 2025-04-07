#!/usr/bin/env python3
import threading
import time
from pathlib import Path
from time import sleep
from typing import Annotated

import typer
from numpy.typing import NDArray

from cogip.cpp.drivers.lidar_ld19 import BaudRate, LDLidarDriver
from cogip.cpp.libraries.shared_memory import SharedMemory
from .gui import start_gui
from .web import start_web, stop_web

stop_event = threading.Event()


def start_console(lidar_data: NDArray):
    print("Starting console thread.")
    while not stop_event.is_set():
        print(
            f"angle {lidar_data[0, 0]}: distance={int(lidar_data[0, 1]): 4d}mm - intensity={int(lidar_data[0, 2]): 3d}"
        )
        sleep(0.1)
    print("Exiting console thread.")


def main_opt(
    port: Annotated[
        Path,
        typer.Option(
            "-p",
            "--port",
            help="Serial port.",
        ),
    ] = "/dev/ttyUSB0",
    gui: Annotated[
        bool,
        typer.Option(
            "-g",
            "--gui",
            help="Show lidar data on polar chart.",
        ),
    ] = False,
    web: Annotated[
        bool,
        typer.Option(
            "-w",
            "--web",
            help=" Start a web server to display lidar data on polar chart.",
        ),
    ] = False,
    web_port: Annotated[
        int,
        typer.Option(
            "-wp",
            "--web-port",
            help=" Web server port.",
        ),
    ] = 8000,
):
    shared_memory = SharedMemory("lidar_ld19", owner=True)
    lidar_data: NDArray = shared_memory.get_lidar_data()

    lidar = LDLidarDriver(lidar_data)

    res = lidar.connect(str(port), BaudRate.BAUD_230400)
    if not res:
        print("Error: Lidar connection failed.")
        return
    print("Lidar connected.")

    res = lidar.wait_lidar_comm(1000)
    if not res:
        print("Error: Lidar not ready.")
        return
    print("Lidar is ready.")

    res = lidar.start()
    if not res:
        print("Error: Lidar not started.")
        return
    print("Lidar started.")

    console_thread = threading.Thread(target=start_console, args=(lidar_data,), name="Console thread")
    console_thread.start()

    if web:
        server_thread = threading.Thread(target=start_web, args=(lidar_data, web_port), name="Server thread")
        server_thread.start()

    if gui:
        # This function is blocking so set the stop event after exiting the GUI
        start_gui(lidar_data)
        stop_event.set()
    else:
        try:
            # Keep the main thread alive
            while console_thread.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Stopping the threads...")
            stop_event.set()

    if web:
        stop_web()
        server_thread.join()

    console_thread.join()

    lidar.disconnect()


def main():
    """
    Tool demonstrating usage of lidar_ld19 C++ driver.

    During installation of cogip-tools, a script called `cogip-lidar-ld19`
    will be created using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
