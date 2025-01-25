from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender


class RobotOrderEntity(Qt3DCore.QEntity):
    """
    A robot entity to display to order position.

    Attributes:
        color: Robot color
    """

    color: QtGui.QColor = QtGui.QColor.fromRgb(10, 77, 18, 100)

    def __init__(self, parent: Qt3DCore.QEntity, robot_id: int = 1):
        """
        Class constructor.
        """
        super().__init__(parent)

        mesh = Qt3DRender.QMesh(self)
        mesh.setSource(QtCore.QUrl(f"file:assets/{'robot' if robot_id == 1 else 'pami'}2025.stl"))

        self.transform = Qt3DCore.QTransform(self)

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self.material.setShininess(1.0)
        self.material.setDiffuse(self.color)
        self.material.setSpecular(self.color)

        self.addComponent(mesh)
        self.addComponent(self.transform)
        self.addComponent(self.material)
