from array import array

from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender

from cogip.models import models


class LineEntity(Qt3DCore.QEntity):
    """
    A simple entity drawing a line between two vertices.
    """

    def __init__(self, color: QtGui.QColor = QtCore.Qt.blue, parent: Qt3DCore.QEntity | None = None):
        """
        Class constructor.

        Arguments:
            color: color
            parent: parent entity
        """
        super().__init__(parent)
        self.color = color

        self.geometry = Qt3DCore.QGeometry(self)

        self.position_buffer = Qt3DCore.QBuffer(self.geometry)

        self.position_attribute = Qt3DCore.QAttribute(self.geometry)
        self.position_attribute.setName(Qt3DCore.QAttribute.defaultPositionAttributeName())
        self.position_attribute.setAttributeType(Qt3DCore.QAttribute.VertexAttribute)
        self.position_attribute.setVertexBaseType(Qt3DCore.QAttribute.Float)
        self.position_attribute.setVertexSize(3)
        self.position_attribute.setCount(2)
        self.position_attribute.setBuffer(self.position_buffer)
        self.geometry.addAttribute(self.position_attribute)

        # Connectivity between vertices
        self.indices = array("I", [0, 1])
        self.indices_bytes = QtCore.QByteArray(self.indices.tobytes())
        self.indices_buffer = Qt3DCore.QBuffer(self.geometry)
        self.indices_buffer.setData(self.indices_bytes)

        self.indices_attribute = Qt3DCore.QAttribute(self.geometry)
        self.indices_attribute.setVertexBaseType(Qt3DCore.QAttribute.UnsignedInt)
        self.indices_attribute.setAttributeType(Qt3DCore.QAttribute.IndexAttribute)
        self.indices_attribute.setBuffer(self.indices_buffer)
        self.indices_attribute.setCount(2)
        self.geometry.addAttribute(self.indices_attribute)

        # Mesh
        self.line = Qt3DRender.QGeometryRenderer(self)
        self.line.setGeometry(self.geometry)
        self.line.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
        self.material = Qt3DExtras.QPhongMaterial(self)
        self.material.setAmbient(self.color)

        # Entity
        self.addComponent(self.line)
        self.addComponent(self.material)

    def set_points(self, start: models.Vertex, end: models.Vertex):
        """
        Set start and end vertices.

        Arguments:
            start: start position
            end: end position
        """

        # Position vertices (start and end)
        positions = array("f")
        positions.fromlist([start.x, start.y, start.z])
        positions.fromlist([end.x, end.y, end.z])
        buffer_bytes = QtCore.QByteArray(positions.tobytes())
        self.position_buffer.setData(buffer_bytes)
