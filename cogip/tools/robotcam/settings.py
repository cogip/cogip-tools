from typing import Annotated

from pydantic import AnyHttpUrl, Field, FilePath, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from cogip.tools.camera.arguments import (
    CameraName,
    CameraNameLiteral,
    VideoCodec,
    VideoCodecLiteral,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="robotcam_", use_enum_values=False)

    id: Annotated[
        int,
        Field(
            ge=1,
            help="Robot ID",
            alias="robot_id",
        ),
    ] = 1
    socketio_server_url: Annotated[
        AnyHttpUrl | None,
        Field(
            description="Socket.IO Server URL",
            alias="cogip_socketio_server_url",
            validate_default=True,
        ),
    ] = None
    camera_name: Annotated[
        CameraNameLiteral,
        Field(
            description="Name of the camera",
            validate_default=True,
        ),
    ] = CameraName.hbv.name
    camera_width: Annotated[
        int,
        Field(
            description="Camera frame width",
        ),
    ] = 640
    camera_height: Annotated[
        int,
        Field(
            description="Camera frame height",
        ),
    ] = 480
    camera_codec: Annotated[
        VideoCodecLiteral,
        Field(
            description="Camera video codec",
            validate_default=True,
        ),
    ] = VideoCodec.yuyv.name
    camera_intrinsic_params: Annotated[
        FilePath | None,
        Field(
            description="Camera intrinsic parameters",
        ),
    ] = None
    camera_extrinsic_params: Annotated[
        FilePath | None,
        Field(
            description="Camera extrinsic parameters",
        ),
    ] = None
    nb_workers: Annotated[
        int,
        Field(
            description="Number of uvicorn workers (ignored if launched by gunicorn)",
        ),
    ] = 1

    @field_validator("socketio_server_url")
    @classmethod
    def validate_url(cls, v: str, info: ValidationInfo) -> str:
        robot_id = info.data.get("id")
        if v is None:
            return f"http://localhost:809{robot_id}"
        return v
