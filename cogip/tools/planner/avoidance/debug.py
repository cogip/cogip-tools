import sys
import threading
import time

from PySide6 import QtCore, QtGui, QtWidgets

from cogip import models
from . import visibility_road_map


class MainWindow(QtWidgets.QWidget):
    def __init__(self, win: "DebugWindow"):
        super().__init__()
        self.win = win
        self.scale = 0.30
        self.margin = 500
        self.offset_x = 1500
        self.offset_y = 1000
        self.setStyleSheet("background-color:white;")
        self.setWindowTitle("Avoidance")
        self.setGeometry(QtCore.QRect(0, 500, 1250, 900))

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.scale(self.scale, self.scale)
        qp.setFont(QtGui.QFont("Ubuntu", 40))

        if self.win.point_start:
            qp.setPen(QtGui.QPen(QtCore.Qt.blue, 40, QtCore.Qt.SolidLine))
            qp.drawPoint(
                self.margin + self.offset_x - self.win.point_start.y,
                self.margin + self.offset_y - self.win.point_start.x,
            )
        if self.win.point_goal:
            qp.setPen(QtGui.QPen(QtCore.Qt.darkBlue, 40, QtCore.Qt.SolidLine))
            qp.drawPoint(
                self.margin + self.offset_x - self.win.point_goal.y,
                self.margin + self.offset_y - self.win.point_goal.x,
            )

        # Draw 0,0 coordinates
        qp.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.green, 40))
        qp.drawPoint(self.margin + 1500, self.margin + 1000)

        self.draw_border(qp)
        self.draw_obstacles(qp)
        self.draw_graph(qp)
        self.draw_visibility_nodes(qp)
        self.draw_road_map(qp)
        self.draw_path(qp)

        qp.end()

    def draw_border(self, qp: QtGui.QPainter):
        pen = QtGui.QPen(QtCore.Qt.black, 5, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        qp.drawRect(QtCore.QRect(self.margin, self.margin, 3000, 2000))

    def draw_obstacles(self, qp: QtGui.QPainter):
        qp.setPen(QtGui.QPen(QtCore.Qt.black, 5, QtCore.Qt.SolidLine))
        for obstacle in self.win.dyn_obstacles:
            points = QtGui.QPolygon(
                [
                    QtCore.QPoint(self.margin + self.offset_x - y, self.margin + self.offset_y - x)
                    for x, y in zip(obstacle.x_list, obstacle.y_list)
                ]
            )
            qp.drawPolyline(points)

        qp.setPen(QtGui.QPen(QtCore.Qt.magenta, 20))

        for obstacle in self.win.dyn_obstacles:
            cv_points = [
                QtCore.QPoint(self.margin + self.offset_x - y, self.margin + self.offset_y - x)
                for x, y in zip(obstacle.cvx_list, obstacle.cvy_list)
            ]
            qp.drawPoints(cv_points)

    def draw_graph(self, qp: QtGui.QPainter):
        qp.setPen(QtGui.QPen(QtCore.Qt.darkGreen, 20, QtCore.Qt.SolidLine))
        for x, y in self.win.graph:
            qp.drawPoint(self.margin + self.offset_x - y, self.margin + self.offset_y - x)

    def draw_visibility_nodes(self, qp: QtGui.QPainter):
        qp.setPen(QtGui.QPen(QtCore.Qt.red, 20, QtCore.Qt.SolidLine))
        for x, y in self.win.visibility_nodes:
            qp.drawPoint(self.margin + self.offset_x - y, self.margin + self.offset_y - x)

    def draw_road_map(self, qp: QtGui.QPainter):
        qp.setPen(QtGui.QPen(QtCore.Qt.blue, 5, QtCore.Qt.SolidLine))
        for x1, y1, x2, y2 in self.win.road_map:
            qp.drawLine(
                QtCore.QLine(
                    self.margin + self.offset_x - y1,
                    self.margin + self.offset_y - x1,
                    self.margin + self.offset_x - y2,
                    self.margin + self.offset_y - x2,
                )
            )

    def draw_path(self, qp: QtGui.QPainter):
        qp.setPen(QtGui.QPen(QtCore.Qt.red, 10, QtCore.Qt.SolidLine))
        points = QtGui.QPolygon(
            [QtCore.QPoint(self.margin + self.offset_x - y, self.margin + self.offset_y - x) for x, y in self.win.path]
        )
        qp.drawPolyline(points)


class DebugWindow:
    ui_thread: threading.Thread | None = None

    def __init__(self):
        self.app = None
        if DebugWindow.ui_thread is None:
            DebugWindow.ui_thread = threading.Thread(target=self.start_qapp)
            DebugWindow.ui_thread.start()
            time.sleep(0.05)  # Wait for a short time to ensure QApplication instance created.

        self.point_start: models.Pose | None = None
        self.point_goal: models.Pose | None = None

        self.dyn_obstacles: list[visibility_road_map.ObstaclePolygon] = []

        self.visibility_nodes: list[tuple[float, float]] = []
        self.graph: list[tuple[float, float]] = []
        self.road_map: list[tuple[float, float, float, float]] = []
        self.path: list[tuple[float, float]] = []

        self.win = MainWindow(self)
        self.win.show()

    def start_qapp(self):
        """a thread for QApplication event loop"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.exec_()

    def update(self):
        self.win.repaint()

    def reset(self):
        self.point_start = None
        self.point_goal = None
        self.dyn_obstacles.clear()
        self.visibility_nodes.clear()
        self.graph.clear()
        self.road_map.clear()
        self.path.clear()
