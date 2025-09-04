from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore

from cogip.models import models
from .line import LineEntity


class PathEntity(Qt3DCore.QEntity):
    """
    A simple entity drawing a path along a list of vertices.
    """

    def __init__(self, color: QtGui.QColor = QtCore.Qt.blue, parent: Qt3DCore.QEntity | None = None):
        """
        Class constructor.

        Arguments:
            color: color
            parent: parent entity
        """
        super().__init__(parent)
        self.points = []
        self.color = color
        self.lines: list[LineEntity] = []
        self.lines_pool: list[LineEntity] = []

    def set_points(self, points: list[models.Vertex]):
        """
        Set points of the path.

        Arguments:
            points: list of vertices composing the line
        """
        self.points = points

        if len(self.points) < 2:
            return

        self.points += [self.points[0]]

        for line in self.lines:
            line.setEnabled(False)
            self.lines_pool.append(line)

        self.lines = []

        start = self.points.pop(0)
        for next in self.points:
            if len(self.lines_pool) == 0:
                self.lines_pool.append(LineEntity(self.color, self))
            line = self.lines_pool.pop()
            line.setEnabled(True)
            line.set_points(start, next)
            self.lines.append(line)
            start = next
