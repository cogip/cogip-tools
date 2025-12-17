#!/usr/bin/env python3
from multiprocessing import Process, Queue

import uvicorn

from .app import app, server
from .camera import CameraHandler
from .settings import Settings


def start_camera_handler(frame_queue: Queue, stream_queue: Queue):
    camera = CameraHandler(frame_queue, stream_queue)
    camera.camera_handler()


def main() -> None:
    """
    Launch COGIP Robot Camera.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-robotcam` script using this function as entrypoint.
    """
    settings = Settings()

    frame_queue = Queue(maxsize=1)
    stream_queue = Queue(maxsize=1)

    server.set_queues(frame_queue, stream_queue)

    # Start Camera handler process
    p = Process(target=start_camera_handler, args=(frame_queue, stream_queue))
    p.start()

    # Start web server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8100 + settings.id,
        workers=settings.nb_workers,
        log_level="warning",
    )

    p.terminate()
    p.join()
