from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from numpy.typing import NDArray

asgi_app = FastAPI()
asgi_server = uvicorn.Server(uvicorn.Config(asgi_app, host="0.0.0.0", access_log=False))


def start_web(lidar_points: NDArray, port: int):
    asgi_server.config.port = port
    asgi_app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static")), name="static")
    templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))

    @asgi_app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html")

    @asgi_app.get("/data", response_class=JSONResponse)
    def get_data():
        data = lidar_points.tolist()
        return JSONResponse(content=data)

    try:
        asgi_server.run()
    except KeyboardInterrupt:
        pass


def stop_web():
    asgi_server.should_exit = True
