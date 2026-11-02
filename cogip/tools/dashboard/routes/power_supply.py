import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class PowerSupplyRouter(APIRouter):
    def __init__(self, templates: Jinja2Templates, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @self.get("/power_supply", response_class=HTMLResponse)
        async def index(request: Request):
            """
            Power supply page of the dashboard web server.
            """
            robot_id = int(os.getenv("ROBOT_ID", 0))
            return templates.TemplateResponse("power_supply.html", {"request": request, "robot_id": robot_id})
