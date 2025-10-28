import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QSettings, QUrl
from PySide6.QtCore import Slot as QtSlot
from PySide6.QtQml import QJSValue

from . import logger


class ObstacleStorage(QObject):
    def __init__(self) -> None:
        super().__init__()

    @QtSlot(str, result="QVariant")
    def read_obstacles(self, url: str):
        path = self.resolve_path(url)
        if path is None:
            logger.error("Invalid obstacle file path: %s", url)
            return
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.error("Obstacle file not found: %s", path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to read obstacles from %s: %s", path, exc)
        return

    @QtSlot(str, "QVariant", result=bool)
    def write_obstacles(self, url: str, data: Any) -> bool:
        path = self.resolve_path(url)
        if path is None:
            logger.error("Invalid obstacle file path: %s", url)
            return False
        try:
            resolved = self.coerce_data(data)
            if resolved is None:
                resolved = []
            if path.suffix.lower() != ".json":
                path = path.with_suffix(".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(resolved, indent=2, ensure_ascii=False), encoding="utf-8")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to write obstacles to %s: %s", path, exc)
        return False

    @QtSlot(str, result=bool)
    def file_exists(self, url: str) -> bool:
        path = self.resolve_path(url)
        return bool(path and path.exists())

    @classmethod
    def resolve_path(cls, url: str) -> Path | None:
        if not url:
            return None
        qurl = QUrl(url)
        if qurl.isValid() and qurl.scheme():
            if qurl.isLocalFile():
                return Path(qurl.toLocalFile())
            logger.error("Unsupported URL scheme for obstacles: %s", url)
            return None
        return Path(url)

    @classmethod
    def coerce_data(cls, value: QJSValue) -> list[dict[str, float]] | None:
        if isinstance(value, QJSValue):
            if value.isNull() or value.isUndefined():
                return None
            return cls.coerce_data(value.toVariant())
        if isinstance(value, Mapping):
            return {str(key): cls.coerce_data(inner) for key, inner in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
            return [cls.coerce_data(item) for item in value]
        return value


class ObstacleWindowSettings(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings()

    def _get_int(self, key: str) -> int:
        value = self._settings.value(key, -1)
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1

    def _set_int(self, key: str, value: int) -> None:
        self._settings.setValue(key, int(value))
        self._settings.sync()

    @Property(int)
    def windowX(self) -> int:
        return self._get_int("ObstacleWindow/windowX")

    @windowX.setter
    def windowX(self, value: int) -> None:
        self._set_int("ObstacleWindow/windowX", value)

    @Property(int)
    def windowY(self) -> int:
        return self._get_int("ObstacleWindow/windowY")

    @windowY.setter
    def windowY(self, value: int) -> None:
        self._set_int("ObstacleWindow/windowY", value)
