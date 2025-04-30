from PySide6 import QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender

from cogip.cpp.libraries.models import Pose
from cogip.entities.sensor import Sensor


class ColumnEntity(Qt3DCore.QEntity):
    height = 109.0
    diameter = 73.0

    def __init__(self, parent: Qt3DCore.QEntity, shift: float):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.parent = parent

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(0, shift, self.height / 2))
        self.transform.setRotationX(90)
        self.addComponent(self.transform)

        self.mesh = Qt3DExtras.QCylinderMesh()
        self.mesh.setLength(self.height)
        self.mesh.setRadius(self.diameter / 2)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self.material.setDiffuse(QtGui.QColor(192, 192, 192))
        self.material.setSpecular(QtGui.QColor(255, 255, 255))
        self.material.setShininess(100.0)
        self.addComponent(self.material)


class PlatformEntity(Qt3DCore.QEntity):
    length = 400.0
    width = 100.0
    thickness = 15.0
    height = 109.0

    def __init__(self, parent: Qt3DCore.QEntity):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.parent = parent

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(0, 0, self.height + self.thickness / 2))
        self.transform.setRotationZ(90)
        self.addComponent(self.transform)

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setXExtent(self.length)
        self.mesh.setYExtent(self.width)
        self.mesh.setZExtent(self.thickness)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self.material.setDiffuse(QtGui.QColor(139, 69, 19))
        self.material.setSpecular(QtGui.QColor(255, 255, 255))
        self.material.setShininess(10.0)
        self.addComponent(self.material)


class TribuneEntity(Qt3DCore.QEntity):
    """
    A dynamic obstacle detected by the robot.

    Base class for rectangle and circle obstacles.
    """

    def __init__(self, parent: Qt3DCore.QEntity, position: Pose):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.parent = parent

        # Global transform for the artifact
        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(position.x, position.y, 0))
        self.transform.setRotationZ(position.O)
        self.addComponent(self.transform)

        self.platform = PlatformEntity(self)
        self.column1 = ColumnEntity(self, -150)
        self.column2 = ColumnEntity(self, -50)
        self.column3 = ColumnEntity(self, 50)
        self.column4 = ColumnEntity(self, 150)

        # Create a layer used by sensors to activate detection on the artifacts
        self.layer = Qt3DRender.QLayer(self)
        self.layer.setRecursive(True)
        self.layer.setEnabled(True)
        self.addComponent(self.layer)

        Sensor.add_obstacle(self)
