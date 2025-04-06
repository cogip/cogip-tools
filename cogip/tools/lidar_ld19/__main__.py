#!/usr/bin/env python3
import threading
import time
from pathlib import Path
from time import sleep
from typing import Annotated

import typer
from numpy.typing import NDArray

from cogip.cpp.drivers.lidar_ld19 import BaudRate, LDLidarDriver
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory
from cogip.cpp.libraries.utils import LidarDataConverter
from .gui import start_gui
from .web import start_web, stop_web

stop_event = threading.Event()

LIDAR_OFFSET_X: float = 75.5
LIDAR_OFFSET_Y: float = 0.0
TABLE_LIMITS_MARGIN: int = 50
MIN_DISTANCE: int = 50
MAX_DISTANCE: int = 2000
MIN_INTENSITY: int = 100
MIN_ANGLE: int = 90
MAX_ANGLE: int = 270


def start_console(lidar_data: NDArray, lidar_coords: NDArray):
    print("Starting console thread.")
    while not stop_event.is_set():
        print(
            f"angle: {lidar_data[0, 0]:>5.1f}"
            f" - distance: {int(lidar_data[0, 1]):>4d}mm"
            f" - intensity: {int(lidar_data[0, 2]):>3d}"
            f" - x: {lidar_coords[0, 0]:>5.1f}mm"
            f" - y: {lidar_coords[0, 1]:>5.1f}mm"
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
    lidar_coords: NDArray = shared_memory.get_lidar_coords()
    pose_current_buffer = shared_memory.get_pose_current_buffer()
    table_limits = shared_memory.get_table_limits()
    lidar_data = shared_memory.get_lidar_data()
    lidar_data_lock = shared_memory.get_lock(LockName.LidarData)
    lidar_coords = shared_memory.get_lidar_coords()
    lidar_coords_lock = shared_memory.get_lock(LockName.LidarCoords)
    pose_current_buffer.push(0.0, 0.0, 0.0)
    table_limits[0] = -1000
    table_limits[1] = 1000
    table_limits[2] = -1500
    table_limits[3] = 1500

    lidar_data_lock.reset()
    lidar_coords_lock.reset()
    lidar_coords_lock.register_consumer()

    # Lidar data is initialized to -1 to indicate that no data is available
    lidar_data[0][0] = -1
    lidar_data[0][1] = -1
    lidar_data[0][2] = -1
    lidar_coords[0][0] = -1
    lidar_coords[0][1] = -1

    lidar = LDLidarDriver(lidar_data)
    lidar.set_data_write_lock(lidar_data_lock)
    lidar.set_min_distance(MIN_DISTANCE)
    lidar.set_max_distance(MAX_DISTANCE)
    lidar.set_min_intensity(MIN_INTENSITY)
    lidar.set_invalid_angle_range(MIN_ANGLE, MAX_ANGLE)  # Skip rear-facing Lidar data because Lidar is mounted in PAMI

    lidar_data_converter = LidarDataConverter("lidar_ld19")
    lidar_data_converter.set_pose_current_index(0)
    lidar_data_converter.set_lidar_offset_x(LIDAR_OFFSET_X)
    lidar_data_converter.set_lidar_offset_y(LIDAR_OFFSET_Y)
    lidar_data_converter.set_table_limits_margin(TABLE_LIMITS_MARGIN)
    lidar_data_converter.start()

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

    console_thread = threading.Thread(target=start_console, args=(lidar_data, lidar_coords), name="Console thread")
    console_thread.start()

    if web:
        server_thread = threading.Thread(target=start_web, args=(lidar_data, web_port), name="Server thread")
        server_thread.start()

    if gui:
        # This function is blocking so set the stop event after exiting the GUI
        start_gui(lidar_coords, lidar_offset=(LIDAR_OFFSET_X, LIDAR_OFFSET_Y))
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

    lidar_data_converter.stop()
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
