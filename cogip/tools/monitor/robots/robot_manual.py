from PySide6.QtCore import Property, QObject, QSettings
from PySide6.QtGui import QColor


class RobotManual:
    def __init__(self, root: QObject):
        self.root = root

        principled_materials = [
            m for m in self.root.children() if m.metaObject().className() == "QQuick3DPrincipledMaterial"
        ]
        for mat in principled_materials:
            mat.setProperty("baseColor", QColor(102, 179, 255, 150))  # RGBA: light blue

        self.node = self.root.findChild(QObject, "Robot")
        self.models = [m for m in self.node.children() if m.metaObject().className() == "QQuick3DModel"]
        for model in self.models:
            model.setObjectName(f"robot_manual_{model.objectName()}")
            model.setProperty("pickable", True)

        self.window_settings = RobotManualWindowSettings()
        self.root.setProperty("windowSettings", self.window_settings)


class RobotManualWindowSettings(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()

    def _get_int(self, key: str) -> int:
        value = self.settings.value(key, -1)
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1

    def _set_int(self, key: str, value: int) -> None:
        self.settings.setValue(key, int(value))
        self.settings.sync()

    @Property(int)
    def windowX(self) -> int:
        return self._get_int("RobotManualWindow/windowX")

    @windowX.setter
    def windowX(self, value: int) -> None:
        self._set_int("RobotManualWindow/windowX", value)

    @Property(int)
    def windowY(self) -> int:
        return self._get_int("RobotManualWindow/windowY")

    @windowY.setter
    def windowY(self, value: int) -> None:
        self._set_int("RobotManualWindow/windowY", value)
