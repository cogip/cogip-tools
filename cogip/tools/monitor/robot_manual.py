from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot


class RobotManualEntity(Qt3DCore.QEntity):
    """
    An robot entity that can be moved and rotated manually on the table.

    When selected with a mouse click, a property window is displayed
    to modify the robot properties.

    The robot can also be moved using the mouse.

    Attributes:
        color: Robot color
        enable_controller: Qt signal used to disable the camera controller
            when moving the robot using the mouse
    """

    color: QtGui.QColor = QtGui.QColor.fromRgb(17, 70, 92, 100)
    enable_controller = qtSignal(bool)

    def __init__(
        self,
        parent: Qt3DCore.QEntity,
        parent_widget: QtWidgets.QWidget,
        robot_id: int = 1,
        x: int = 1200,
        y: int = 1200,
        rotation: int = 180,
    ):
        """
        Class constructor.

        Arguments:
            parent: The parent entity
            parent_widget: Parent widget
            x: X position
            y: Y position
            rotation: Rotation
        """
        super().__init__(parent)

        self.parent_widget = parent_widget

        self.mesh = Qt3DRender.QMesh(self)
        self.mesh.setSource(QtCore.QUrl(f"file:assets/{'robot' if robot_id == 1 else 'pami'}2025.stl"))
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.material.setShininess(1.0)
        self.material.setDiffuse(self.color)
        self.material.setSpecular(self.color)
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(x, y, 0))
        self.transform.setRotationZ(rotation)
        self.addComponent(self.transform)

        self.picker = Qt3DRender.QObjectPicker()
        self.picker.setDragEnabled(True)
        self.picker.pressed.connect(self.pressed)
        self.picker.released.connect(self.released)
        self.picker.moved.connect(self.moved)
        self.addComponent(self.picker)

        self.moving = False

        # Create a layer used by sensors to activate detection on the robot
        self.layer = Qt3DRender.QLayer(self)
        self.layer.setRecursive(True)
        self.layer.setEnabled(True)
        self.addComponent(self.layer)

        # Create properties dialog
        self.properties = RobotManualProperties(self.parent_widget, self)

    @qtSlot(int)
    def setXTranslation(self, x: int):
        """
        Qt Slot

        Set the X position.
        """
        translation = self.transform.translation()
        translation.setX(float(x))
        self.transform.setTranslation(translation)

    @qtSlot(int)
    def setYTranslation(self, y: int):
        """
        Qt Slot

        Set the Y position.
        """
        translation = self.transform.translation()
        translation.setY(float(y))
        self.transform.setTranslation(translation)

    @qtSlot(Qt3DRender.QPickEvent)
    def pressed(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```pressed``` mouse event on the robot.

        Emit a signal to disable the camera controller before moving the robot.
        """
        self.enable_controller.emit(False)

    @qtSlot(Qt3DRender.QPickEvent)
    def released(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```released``` mouse event on the robot.

        If this event occurs just after a ```pressed``` event, it is only a mouse click,
        so display the property window.

        Emit a signal to re-enable the camera controller after moving the robot.
        """
        if not self.moving:
            if RobotManualProperties.active_properties:
                RobotManualProperties.active_properties.close()
            self.properties.show()
            self.properties.raise_()
            self.properties.activateWindow()
            RobotManualProperties.set_active_properties(self.properties)
        self.moving = False
        self.enable_controller.emit(True)

    @qtSlot(Qt3DRender.QPickEvent)
    def moved(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```moved``` mouse event on the robot.

        Just record that the robot is moving, the translation is computed
        in the [GameView][cogip.tools.monitor.gameview.GameView] object.
        """
        self.moving = True

    @qtSlot(QtGui.QVector3D)
    def new_move_delta(self, delta: QtGui.QVector3D):
        """
        Qt Slot

        Update the robot position.

        Arguments:
            delta: The difference between current and new position
        """
        if not delta:
            self.moving = False
        elif self.moving:
            new_translation = self.transform.translation() + delta
            self.transform.setTranslation(new_translation)
            self.properties.spin_x.setValue(new_translation.x())
            self.properties.spin_y.setValue(new_translation.y())


class RobotManualProperties(QtWidgets.QDialog):
    """
    The property window.

    Attributes:
        active_properties: The current property window displayed.
    """

    active_properties: "RobotManualProperties" = None

    def __init__(self, parent: QtWidgets.QWidget, robot_entity: RobotManualEntity):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            robot_entity: The related robot entity
        """
        super().__init__(parent)

        self.robot_entity = robot_entity
        self.setWindowTitle("Robot Properties")
        self.setModal(False)
        self.setMinimumWidth(self.fontMetrics().horizontalAdvance(self.windowTitle()))

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        row = 0

        label_x = QtWidgets.QLabel("X")
        self.spin_x = QtWidgets.QSpinBox()
        self.spin_x.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_x.setMinimum(-1200)
        self.spin_x.setMaximum(1200)
        self.spin_x.setValue(int(self.robot_entity.transform.translation().x()))
        self.spin_x.valueChanged.connect(self.robot_entity.setXTranslation)
        layout.addWidget(label_x, row, 0)
        layout.addWidget(self.spin_x, row, 1)
        row += 1

        label_y = QtWidgets.QLabel("Y")
        self.spin_y = QtWidgets.QSpinBox()
        self.spin_y.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_y.setMinimum(-1700)
        self.spin_y.setMaximum(1700)
        self.spin_y.setValue(int(self.robot_entity.transform.translation().y()))
        self.spin_y.valueChanged.connect(self.robot_entity.setYTranslation)
        layout.addWidget(label_y, row, 0)
        layout.addWidget(self.spin_y, row, 1)
        row += 1

        label_rotation = QtWidgets.QLabel("Rotation")
        self.spin_rotation = QtWidgets.QSpinBox()
        self.spin_rotation.setSuffix("°")
        self.spin_rotation.setMinimum(-180)
        self.spin_rotation.setMaximum(180)
        self.spin_rotation.setValue(int(self.robot_entity.transform.rotationZ()))
        self.spin_rotation.valueChanged.connect(self.robot_entity.transform.setRotationZ)
        layout.addWidget(label_rotation, row, 0)
        layout.addWidget(self.spin_rotation, row, 1)
        row += 1

        self.readSettings()

    @classmethod
    def set_active_properties(cls, properties: "RobotManualProperties"):
        """
        Class method.

        Set the current property window displayed.

        Arguments:
            properties: The current property
        """
        cls.active_properties = properties

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Close the property windows.

        Arguments:
            event: The close event (unused)
        """
        RobotManualProperties.set_active_properties(None)

        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("manual_robot_dialog/geometry", self.saveGeometry())

        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("manual_robot_dialog/geometry"))
