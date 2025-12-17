from contextlib import asynccontextmanager
from pathlib import Path

import systemd.daemon
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import logger, routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    logger.info("Dashboard starting up...")
    try:
        systemd.daemon.notify("READY=1")
        logger.info("Systemd notified: READY=1")
    except Exception as e:
        logger.error(f"Failed to notify systemd: {e}")

    yield

    logger.info("Dashboard shutting down...")


class Dashboard:
    def __init__(self):
        """
        Class constructor.

        Create FastAPI application.
        """
        self.app = FastAPI(title="COGIP Web Monitor", lifespan=lifespan, debug=False)

        # Mount static files
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

        # Create HTML templates
        self.templates = Jinja2Templates(directory=current_dir / "templates")

        # Register routes
        self.app.include_router(routes.BeaconRouter(self.templates), prefix="")
