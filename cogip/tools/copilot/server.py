import asyncio
import base64
import binascii
import json
import logging
from pathlib import Path
from typing import Any, Dict

from aioserial import AioSerial
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.protobuf.json_format import MessageToDict as ProtobufMessageToDict
from google.protobuf.message import DecodeError as ProtobufDecodeError
import socketio
from uvicorn.main import Server as UvicornServer

from cogip import models, logger
from .messages import PB_Command, PB_Wizard, PB_GameInputMessage, PB_GameOutputMessage
from .recorder import GameRecordFileHandler
from .settings import Settings


def create_app() -> FastAPI:
    server = CopilotServer()
    return server.app


class CopilotServer:
    _serial_port: AioSerial = None                   # Async serial port
    _loop: asyncio.AbstractEventLoop = None          # Event loop to use for all async objects
    _nb_connections: int = 0                         # Number of monitors connected
    _menu: models.ShellMenu = None                   # Last received shell menu
    _samples: Dict[str, Any] = None                  # Last detected samples
    _exiting: bool = False                           # True if Uvicorn server was ask to shutdown
    _record_handler: GameRecordFileHandler = None    # Log file handler to record games
    _serial_messages_received: asyncio.Queue = None  # Queue for messages received from serial port
    _serial_messages_to_send: asyncio.Queue = None   # Queue for messages waiting to be sent on serial port
    _sio_messages_to_send: asyncio.Queue = None      # Queue for messages waiting to be sent on SocketIO server
    _original_uvicorn_exit_handler = UvicornServer.handle_exit  # Backup of original exit handler to overload it

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application and SocketIO server.
        """
        self.settings = Settings()

        # Create FastAPI application
        self.app = FastAPI(title="COGIP Web Monitor", debug=False)
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )

        # Overload default Uvicorn exit handler
        UvicornServer.handle_exit = self.handle_exit

        # Create SocketIO server and mount it in /sio
        self.sio_app = socketio.ASGIApp(self.sio)
        self.app.mount("/sio", self.sio_app)

        # Mount static files
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir/"static"), name="static")

        # Create HTML templates
        self.templates = Jinja2Templates(directory=current_dir/"templates")

        # Create game recorder
        self._game_recorder = logging.getLogger('GameRecorder')
        self._game_recorder.setLevel(logging.INFO)
        self._game_recorder.propagate = False
        try:
            self._record_handler = GameRecordFileHandler(self.settings.record_dir)
            self._game_recorder.addHandler(self._record_handler)
        except OSError:
            logger.warning(f"Failed to record games in directory '{self.settings.record_dir}'")
            self._record_handler = None

        # Open serial port
        self._serial_port = AioSerial()
        self._serial_port.port = str(self.settings.serial_port)
        self._serial_port.baudrate = self.settings.serial_baud
        self._serial_port.open()

        self.register_endpoints()
        self.register_sio_events()

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        CopilotServer._exiting = True
        CopilotServer._original_uvicorn_exit_handler(*args, **kwargs)

    async def serial_receiver(self):
        """
        Async worker reading messages from the robot on serial ports.

        Messages is base64-encoded and separated by '\n'.
        After decoding, first byte is the message type, following bytes are
        the Protobuf encoded message (if any).
        """
        while(True):
            # Read next base64 message
            base64_message = await self._serial_port.readline_async()

            # Base64 decoding
            try:
                pb_message = base64.decodebytes(base64_message)
            except binascii.Error:
                print("Failed to decode base64 message.")
                continue

            # Send Protobuf message for decoding
            await self._serial_messages_received.put(pb_message)

    async def serial_sender(self):
        """
        Async worker encoding and sending Protobuf messages to the robot on serial ports.

        See `serial_receiver` for message encoding.
        """
        while True:
            pb_message: PB_GameInputMessage = await self._serial_messages_to_send.get()
            response_serialized = await self._loop.run_in_executor(None, pb_message.SerializeToString)
            response_base64 = await self._loop.run_in_executor(None, base64.encodebytes, response_serialized)
            await self._serial_port.write_async(response_base64)
            await self._serial_port.write_async(b"\0")
            self._serial_messages_to_send.task_done()

    async def serial_decoder(self):
        """
        Async worker decoding messages received from the robot.
        """
        encoded_message: bytes
        request_handlers = {
            "reset": self.handle_reset,
            "menu": self.handle_message_menu,
            "state": self.handle_message_state,
            "wizard": self.handle_message_wizard
        }

        while True:
            encoded_message = await self._serial_messages_received.get()

            try:
                message = PB_GameOutputMessage()
                await self._loop.run_in_executor(None, message.ParseFromString, encoded_message)
            except ProtobufDecodeError as exc:
                logger.error(f"Protobuf decode error: {exc}")
            except Exception as exc:
                logger.error(f"Unknown Protobuf decode error {type(exc)}: {exc}")

            message_type = message.WhichOneof("type")

            request_handler = request_handlers.get(message_type, None)
            if not request_handler:
                logger.error(f"No handler found for message type '{message_type}'")
            else:
                await request_handler(message)

            self._serial_messages_received.task_done()

    async def sio_sender(self):
        """
        Async worker waiting for messages to send to monitors through SocketIO server.
        """
        message_type: str
        message_dict: Dict

        while True:
            message_type, message_dict = await self._sio_messages_to_send.get()
            await self.sio.emit(message_type, message_dict)
            self._sio_messages_to_send.task_done()

    async def handle_reset(self, message: PB_GameOutputMessage) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a reset message to all connected monitors.
        """
        self._menu = None
        message = PB_GameInputMessage()
        message.copilot_connected = True
        await self._serial_messages_to_send.put(message)
        await self._sio_messages_to_send.put(("reset", None))
        if self._record_handler:
            await self._loop.run_in_executor(None, self._record_handler.doRollover)

    async def handle_message_menu(self, message: PB_GameOutputMessage) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        menu = ProtobufMessageToDict(message)["menu"]
        self._menu = models.ShellMenu.parse_obj(menu)
        await self.emit_menu()

    async def handle_message_state(self, message: PB_GameOutputMessage) -> None:
        """
        Send robot state received from the robot to connected monitors.
        """
        state = ProtobufMessageToDict(
            message,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )["state"]

        # Convert obstacles format to comply with Pydantic models used by the monitor
        obstacles = state.get("obstacles", [])
        new_obstacles = []
        for obstacle in obstacles:
            bb = obstacle.pop("bounding_box")
            try:
                new_obstacle = list(obstacle.values())[0]
            except IndexError:
                continue
            new_obstacle["bb"] = bb
            new_obstacles.append(new_obstacle)
        state["obstacles"] = new_obstacles
        await self._sio_messages_to_send.put(("state", state))
        await self._loop.run_in_executor(None, self.record_state, state)

    async def handle_message_wizard(self, message: PB_GameOutputMessage) -> None:
        wizard = ProtobufMessageToDict(
            message,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )["wizard"]
        wizard_type = message.wizard.WhichOneof("type")
        wizard["type"] = wizard_type
        wizard.update(**wizard[wizard_type])
        del wizard[wizard_type]
        await self._sio_messages_to_send.put(("wizard", wizard))

    async def emit_menu(self) -> None:
        """
        Sent current shell menu to connected monitors.
        """
        if not self._menu or self._nb_connections == 0:
            return

        await self._sio_messages_to_send.put(
            ("menu", self._menu.dict(exclude_defaults=True, exclude_unset=True))
        )

    def record_state(self, state: Dict[str, Any]) -> None:
        """
        Add a robot robot state in the current record file.
        Do it only the the robot the game has started, ie mode != 0.
        """
        if self._record_handler and state.get("mode", 0):
            self._game_recorder.info(json.dumps(state))

    def register_endpoints(self) -> None:

        @self.app.on_event("startup")
        async def startup_event():
            """
            Function called at FastAPI server startup.

            Initialize serial port, message queues and start async workers.
            Also send a
            [COPILOT_CONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_CONNECTED]
            message on serial port.
            """
            self._loop = asyncio.get_event_loop()

            # Create asyncio queues
            self._serial_messages_received = asyncio.Queue()
            self._pb_messages_to_send = asyncio.Queue()
            self._serial_messages_received = asyncio.Queue()
            self._serial_messages_to_send = asyncio.Queue()
            self._sio_messages_to_send = asyncio.Queue()

            # Create async workers
            asyncio.create_task(self.serial_decoder(), name="Serial Decoder")
            asyncio.create_task(self.serial_receiver(), name="Serial Receiver")
            asyncio.create_task(self.serial_sender(), name="Serial Sender")
            asyncio.create_task(self.sio_sender(), name="SocketIO Sender")

            # Send CONNECTED message to firmware
            message = PB_GameInputMessage()
            message.copilot_connected = True
            await self._serial_messages_to_send.put(message)

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """
            Function called at FastAPI server shutdown.

            Send a
            [COPILOT_DISCONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_DISCONNECTED]
            message on serial port.
            Wait for all serial messages to be sent.
            """
            message = PB_GameInputMessage()
            message.copilot_disconnected = True
            await self._serial_messages_to_send.put(message)
            await self._serial_messages_to_send.join()

        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """
            Homepage of the dashboard web server.
            """
            return self.templates.TemplateResponse("index.html", {"request": request})

    def register_sio_events(self) -> None:

        @self.sio.event
        async def connect(sid, environ):
            """
            Callback on new monitor connection.

            Send the current menu to monitors.
            """
            self._nb_connections += 1
            await self.emit_menu()

        @self.sio.event
        async def disconnect(sid):
            """
            Callback on monitor disconnection.
            """
            self._nb_connections -= 1

        @self.sio.on("cmd")
        async def on_cmd(sid, data):
            """
            Callback on command message.

            Receive a command from a monitor.

            Build the Protobuf command message:

            * split received string at first space if any.
            * first is the command and goes to `cmd` attribute.
            * second part is arguments, if any, and goes to `desc` attribute.
            """
            response = PB_Command()
            response.cmd, _, response.desc = data.partition(" ")
            message = PB_GameInputMessage()
            message.command.CopyFrom(response)
            await self._serial_messages_to_send.put(message)

        @self.sio.on("wizard")
        async def on_wizard(sid, data):
            """
            Callback on Wizard message.

            Receive a command from a monitor.

            Build the Protobuf wizard message and send to firmware.
            """
            await self._sio_messages_to_send.put(("close_wizard", None))

            response = PB_Wizard()
            response.name = data["name"]
            data_type = data["type"]
            if not isinstance(data["value"], list):
                value = getattr(response, data_type).value
                value_type = type(value)
                getattr(response, data_type).value = value_type(data["value"])
            elif data_type == "select_integer":
                response.select_integer.value[:] = [int(v) for v in data["value"]]
            elif data_type == "select_floating":
                response.select_floating.value[:] = [float(v) for v in data["value"]]
            elif data_type == "select_str":
                response.select_str.value[:] = data["value"]

            message = PB_GameInputMessage()
            message.wizard.CopyFrom(response)
            await self._serial_messages_to_send.put(message)

        @self.sio.on("samples")
        async def on_sample(sid, data):
            self._samples = data
