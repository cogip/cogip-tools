from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QVector3D

from cogip.models import models


class RobotOrder:
    def __init__(self, root: QObject, robot_id: int):
        self.root = root
        self.robot_id = robot_id

        principled_materials = [
            m for m in self.root.children() if m.metaObject().className() == "QQuick3DPrincipledMaterial"
        ]
        for mat in principled_materials:
            mat.setProperty("baseColor", QColor(144, 238, 144, 150))  # RGBA: light green

        self.node = self.root.findChild(QObject, "Robot")
        self.models = [m for m in self.node.children() if m.metaObject().className() == "QQuick3DModel"]
        for model in self.models:
            model.setObjectName(f"robot_order_{model.objectName()}")

    def set_pose_order(self, order: models.Pose) -> None:
        """
        Update pose order.
        """
        self.root.setProperty("x", order.x)
        self.root.setProperty("y", order.y)
        self.root.setProperty("eulerRotation", QVector3D(0, 0, order.O))
