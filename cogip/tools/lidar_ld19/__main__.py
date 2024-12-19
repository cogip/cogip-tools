#!/usr/bin/env python3
import json
import threading
import time
from pathlib import Path
from time import sleep
from typing import Annotated

import matplotlib.animation as animation
import numpy as np
import typer
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from matplotlib import pyplot
from numpy.typing import NDArray

from cogip.cpp.lidar_ld19 import BaudRate, LDLidarDriver

stop_event = threading.Event()
asgi_app = FastAPI()
asgi_server = uvicorn.Server(uvicorn.Config(asgi_app))


def start_console(lidar_points: NDArray):
    print("Starting console thread.")
    while not stop_event.is_set():
        print(f"angle 0: distance={lidar_points[0, 0]: 4d}mm - intensity={lidar_points[0, 1]: 3d}")
        sleep(0.1)
    print("Exiting console thread.")


def start_plot(lidar_points: NDArray):
    print("Starting plot GUI")

    # Generate angles from 0 to 359 degrees
    angles = np.radians(np.arange(360))

    # Create a polar plot
    fig, ax = pyplot.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    ax.set_ylim(0, 3100)

    # Initialize scatter plot with dummy data
    initial_distances = np.zeros(360)
    initial_colors = np.zeros(360)
    scatter = ax.scatter(angles, initial_distances, c=initial_colors, cmap="RdYlGn", s=5, vmin=0, vmax=255)
    pyplot.colorbar(scatter, label="Intensity (0 = red, 255 = green)")

    # Configure plot appearance
    ax.set_theta_direction(-1)  # Reverse direction
    ax.set_theta_offset(np.pi / 2.0)  # 0 degrees is upwards
    ax.set_title("Real-Time Lidar Data", va="bottom")

    # Function to handle zooming
    def on_scroll(event):
        current_ylim = ax.get_ylim()
        zoom_factor = 1.1 if event.button == "up" else 0.9  # Zoom in/out
        new_ylim = [limit * zoom_factor for limit in current_ylim]

        # Limit the zoom range
        new_ylim[0] = max(0, new_ylim[0])
        new_ylim[1] = min(5000, new_ylim[1])  # Prevent excessive zoom out
        ax.set_ylim(new_ylim)
        pyplot.draw()

    # Connect the scroll event to the handler
    fig.canvas.mpl_connect("scroll_event", on_scroll)

    # Animation update function
    def update(frame):
        # Extract distances and intensities safely
        distances = lidar_points[:, 0]
        intensities = lidar_points[:, 1]

        # Update scatter plot
        scatter.set_offsets(np.column_stack((angles, distances)))
        scatter.set_array(intensities)  # Update colors
        return (scatter,)

    try:
        # Animate the plot
        _ = animation.FuncAnimation(fig, update, interval=100, blit=True, cache_frame_data=False)
        pyplot.show()
    except KeyboardInterrupt:
        pass

    print("Exiting plot GUI.")


def start_server(lidar_points: NDArray):
    lidar_data_filename = Path("lidar_data.json")
    if not lidar_data_filename.exists():
        print("Error: JSON file does not exist.")
        return
    try:
        fake_data: list = json.loads(lidar_data_filename.read_text())
    except Exception as exc:
        print(f"Error: failed to parse JSON file ({exc})")
        return
    # lidar_data_file = lidar_data_filename.open("w")
    # lidar_data_file.write("[\n")

    asgi_app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static")), name="static")
    templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))

    @asgi_app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @asgi_app.get("/data", response_class=JSONResponse)
    def get_data():
        # data = lidar_points.tolist()
        # lidar_data_file.write("  " + json.dumps(data) + ",\n")

        data = fake_data.pop(0)
        fake_data.append(data)

        return JSONResponse(content=data)

    try:
        asgi_server.run()
    except KeyboardInterrupt:
        # lidar_data_file.write("]\n")
        # lidar_data_file.close()
        pass


def main_opt(
    port: Annotated[
        Path,
        typer.Option(
            "-p",
            "--port",
            help="Serial port.",
        ),
    ] = "/dev/ttyUSB0",
    filter: Annotated[
        bool,
        typer.Option(
            "-f",
            "--filter",
            help="Enable filter embedded in the driver.",
        ),
    ] = False,
    plot: Annotated[
        bool,
        typer.Option(
            "--plot",
            help="Show lidar data on polar chart.",
        ),
    ] = False,
    serve: Annotated[
        bool,
        typer.Option(
            "-s",
            "--serve",
            help=" Start a web server to display lidar data on polar chart.",
        ),
    ] = False,
    server_port: Annotated[
        int,
        typer.Option(
            "-sp",
            "--server-port",
            help=" Web server port.",
        ),
    ] = 8000,
):
    # lidar = LDLidarDriver()

    # if filter:
    #     lidar.enablePointCloudDataFilter(True)

    # res: bool = lidar.connect(str(port), BaudRate.BAUD_230400)
    # print(f"Connect result: {res}")

    # res: bool = lidar.waitLidarComm(3500)
    # print(f"Wait Lidar Comm result: {res}")

    # res: bool = lidar.start()
    # print(f"Start result: {res}")

    # lidar_points: NDArray = lidar.getLidarPoints()

    # console_thread = threading.Thread(target=start_console, args=(lidar_points,), name="Console thread")
    # console_thread.start()

    plot = False
    serve = True
    lidar_points = None
    if serve:
        asgi_server.config.port = server_port
        server_thread = threading.Thread(target=start_server, args=(lidar_points,), name="Server thread")
        server_thread.start()

    if plot:
        # This function is blocking so set the stop event after exiting the GUI
        start_plot(lidar_points)
        stop_event.set()
    else:
        try:
            # Keep the main thread alive
            # while console_thread.is_alive():
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Stopping the threads...")
            stop_event.set()

    asgi_server.should_exit = True
    server_thread.join()
    # console_thread.join()

    # lidar.disconnect()


def main():
    """
    Tool demonstrating usage of lidar_ld19 C++ driver.

    During installation of cogip-tools, a script called `cogip-lidar-ld19`
    will be created using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
