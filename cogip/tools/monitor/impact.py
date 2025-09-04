from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras


class ImpactEntity(Qt3DCore.QEntity):
    """
    `QEntity` used to visualize to points detected by sensors.

    It is represented with [`QSphereMesh`](https://doc.qt.io/qtforpython-6/PySide6/Qt3DExtras/QSphereMesh.html),
    its radius and color are configurable in the constructor.
    """

    def __init__(self, radius: float = 50, color: QtCore.Qt.GlobalColor = QtCore.Qt.red):
        """
        Class constructor.

        Arguments:
            radius: Radius of the sphere
            color: Color of the sphere
        """
        super().__init__()

        self.mesh = Qt3DExtras.QSphereMesh()
        self.mesh.setRadius(radius)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial()
        self.material.setDiffuse(QtGui.QColor(color))
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform()
        self.addComponent(self.transform)
        self.setEnabled(False)
