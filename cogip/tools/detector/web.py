import typing
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

if typing.TYPE_CHECKING:
    from cogip.tools.detector_pami.detector import Detector

asgi_app = FastAPI()
asgi_server = uvicorn.Server(uvicorn.Config(asgi_app, host="0.0.0.0", access_log=False))


def start_web(detector: "Detector", port: int):
    asgi_server.config.port = port
    asgi_app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static")), name="static")
    templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))

    @asgi_app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @asgi_app.get("/data", response_class=JSONResponse)
    def get_data():
        if detector.shared_lidar_data is None:
            return JSONResponse(content=[])

        lidar_data = detector.shared_lidar_data[: np.argmax(detector.shared_lidar_data[:, 0] == -1)].copy()

        return JSONResponse(content=lidar_data.tolist())

    try:
        asgi_server.run()
    except KeyboardInterrupt:
        pass


def stop_web():
    asgi_server.should_exit = True
