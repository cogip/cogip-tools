from socketio import ASGIApp

from .server import Server


def create_app() -> ASGIApp:
    """
    Create server and return ASGIApp application for uvicorn/gunicorn.
    """
    server = Server()
    return server.app


app = create_app()
