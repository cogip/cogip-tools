from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class BeaconRouter(APIRouter):
    def __init__(self, templates: Jinja2Templates, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @self.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """
            Homepage of the dashboard web server.
            """
            return templates.TemplateResponse("dashboard.html", {"request": request, "robot_id": 0})
