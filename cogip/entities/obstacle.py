from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip import models
from cogip.entities.sensor import Sensor


class ObstacleEntity(Qt3DCore.QEntity):
    """
    An obstacle on the table.

    It is represented as a cube ([QCuboidMesh](https://doc.qt.io/qtforpython-6/PySide6/Qt3DExtras/QCuboidMesh.html)).

    When selected with a mouse click, a property window is displayed
    to modify the obstacle properties.

    The obstacle can also be moved using the mouse.

    Attributes:
        enable_controller: Qt signal used to disable the camera controller
            when moving the obstacle using the mouse
    """

    enable_controller = qtSignal(bool)
    obstacle_moved: qtSignal = qtSignal()

    def __init__(
        self,
        parent_widget: QtWidgets.QWidget,
        x: int = 0,
        y: int = 0,
        rotation: int = 0,
        length: int = 225,
        width: int = 225,
        height: int = 350,
    ):
        """
        Class constructor.

        Arguments:
            parent_widget: Parent widget
            x: X position
            y: Y position
            rotation: Rotation
            length: Length
            width: Width
            height: Height
        """
        super().__init__()

        self.parent_widget = parent_widget

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)
        self.mesh.setZExtent(height)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent() / 2))
        self.transform.setRotationZ(rotation)
        self.addComponent(self.transform)

        self.picker = Qt3DRender.QObjectPicker()
        self.picker.setDragEnabled(True)
        self.picker.pressed.connect(self.pressed_obstacle)
        self.picker.released.connect(self.released_obstacle)
        self.picker.moved.connect(self.moved_obstacle)
        self.addComponent(self.picker)

        self.beacon_entity = Qt3DCore.QEntity(self)
        self.beacon_mesh = Qt3DExtras.QCylinderMesh(self.beacon_entity)
        self.beacon_mesh.setLength(80)
        self.beacon_mesh.setRadius(35)
        self.beacon_entity.addComponent(self.beacon_mesh)

        self.beacon_material = Qt3DExtras.QPhongMaterial(self.beacon_entity)
        self.beacon_entity.addComponent(self.beacon_material)

        self.beacon_transform = Qt3DCore.QTransform(self.beacon_entity)
        self.beacon_transform.setTranslation(
            QtGui.QVector3D(0, 0, self.mesh.zExtent() / 2 + self.beacon_mesh.length() / 2)
        )
        self.beacon_transform.setRotationX(90)
        self.beacon_entity.addComponent(self.beacon_transform)

        self.moving = False

        self.mesh.zExtentChanged.connect(self.updateZTranslation)

        # Create a layer used by sensors to activate detection on the obstacles
        self.layer = Qt3DRender.QLayer(self)
        self.layer.setRecursive(True)
        self.layer.setEnabled(True)
        self.addComponent(self.layer)

        # Create properties dialog
        self.properties = ObstacleProperties(self.parent_widget, self)

        Sensor.add_obstacle(self)

    @qtSlot(float)
    def updateZTranslation(self, zExtent: float):
        """
        Qt Slot

        Update the Z position based on the obstacle height.
        This function is called each time the height is modified
        to set the bottom on Z=0.
        """
        translation = self.transform.translation()
        translation.setZ(zExtent / 2)
        self.transform.setTranslation(translation)

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
    def pressed_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```pressed``` mouse event on the obstacle.

        Emit a signal to disable the camera controller before moving the obstacle.
        """
        self.enable_controller.emit(False)

    @qtSlot(Qt3DRender.QPickEvent)
    def released_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```released``` mouse event on the obstacle.

        If this event occurs just after a ```pressed``` event, it is only a mouse click,
        so display the property window.

        Emit a signal to re-enable the camera controller after moving the obstacle.
        """
        if not self.moving:
            if ObstacleProperties.active_properties:
                ObstacleProperties.active_properties.close()
            self.properties.show()
            self.properties.raise_()
            self.properties.activateWindow()
            ObstacleProperties.set_active_properties(self.properties)
        self.moving = False
        self.enable_controller.emit(True)

    @qtSlot(Qt3DRender.QPickEvent)
    def moved_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```moved``` mouse event on the obstacle.

        Just record that the obstacle is moving, the translation is computed
        in the [GameView][cogip.widgets.gameview.GameView] object.
        """
        self.moving = True
        self.obstacle_moved.emit()

    def get_model(self) -> models.DynRoundObstacle:
        """
        Returns the [Obstacle][cogip.models.models.DynRoundObstacle] model.
        Used to save the obstacles list.

        Returns:
            The obstacle model
        """
        return models.DynRoundObstacle(
            x=self.transform.translation().x(),
            y=self.transform.translation().y(),
            angle=self.transform.rotationZ(),
            radius=(self.mesh.xExtent() + self.mesh.yExtent()) / 2
        )

    @qtSlot(QtGui.QVector3D)
    def new_move_delta(self, delta: QtGui.QVector3D):
        """
        Qt Slot

        Update the obstacle position.

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


class ObstacleProperties(QtWidgets.QDialog):
    """
    The property window.

    Each obstacle has its own property window.

    Attributes:
        active_properties: The current property window displayed.
    """

    active_properties: "ObstacleProperties" = None

    def __init__(self, parent: QtWidgets.QWidget, obstacle_entity: ObstacleEntity):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            obstacle_entity: The related obstacle entity
        """
        super().__init__(parent)

        self.obstacle_entity = obstacle_entity
        self.setWindowTitle("Obstacle Properties")
        self.setModal(False)
        self.setMinimumWidth(self.fontMetrics().horizontalAdvance(self.windowTitle()))

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        row = 0

        label_x = QtWidgets.QLabel("X")
        self.spin_x = QtWidgets.QSpinBox()
        self.spin_x.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_x.setMinimum(-1000)
        self.spin_x.setMaximum(1000)
        self.spin_x.setValue(int(self.obstacle_entity.transform.translation().x()))
        self.spin_x.valueChanged.connect(self.obstacle_entity.setXTranslation)
        layout.addWidget(label_x, row, 0)
        layout.addWidget(self.spin_x, row, 1)
        row += 1

        label_y = QtWidgets.QLabel("Y")
        self.spin_y = QtWidgets.QSpinBox()
        self.spin_y.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_y.setMinimum(-1500)
        self.spin_y.setMaximum(1500)
        self.spin_y.setValue(int(self.obstacle_entity.transform.translation().y()))
        self.spin_y.valueChanged.connect(self.obstacle_entity.setYTranslation)
        layout.addWidget(label_y, row, 0)
        layout.addWidget(self.spin_y, row, 1)
        row += 1

        label_rotation = QtWidgets.QLabel("Rotation")
        self.spin_rotation = QtWidgets.QSpinBox()
        self.spin_rotation.setSuffix("°")
        self.spin_rotation.setMinimum(-180)
        self.spin_rotation.setMaximum(180)
        self.spin_rotation.setValue(int(self.obstacle_entity.transform.rotationZ()))
        self.spin_rotation.valueChanged.connect(self.obstacle_entity.transform.setRotationZ)
        layout.addWidget(label_rotation, row, 0)
        layout.addWidget(self.spin_rotation, row, 1)
        row += 1

        label_width = QtWidgets.QLabel("Width")
        self.spin_width = QtWidgets.QSpinBox()
        self.spin_width.setMaximum(2000)
        self.spin_width.setSingleStep(10)
        self.spin_width.setValue(int(self.obstacle_entity.mesh.xExtent()))
        self.spin_width.valueChanged.connect(self.obstacle_entity.mesh.setXExtent)
        layout.addWidget(label_width, row, 0)
        layout.addWidget(self.spin_width, row, 1)
        row += 1

        label_length = QtWidgets.QLabel("Length")
        self.spin_length = QtWidgets.QSpinBox()
        self.spin_length.setMaximum(2000)
        self.spin_length.setSingleStep(10)
        self.spin_length.setValue(int(self.obstacle_entity.mesh.yExtent()))
        self.spin_length.valueChanged.connect(self.obstacle_entity.mesh.setYExtent)
        layout.addWidget(label_length, row, 0)
        layout.addWidget(self.spin_length, row, 1)
        row += 1

        label_height = QtWidgets.QLabel("Height")
        self.spin_height = QtWidgets.QSpinBox()
        self.spin_height.setMaximum(1000)
        self.spin_height.setSingleStep(10)
        self.spin_height.setValue(int(self.obstacle_entity.mesh.zExtent()))
        self.spin_height.valueChanged.connect(self.obstacle_entity.mesh.setZExtent)
        layout.addWidget(label_height, row, 0)
        layout.addWidget(self.spin_height, row, 1)
        row += 1

        self.readSettings()

    @classmethod
    def set_active_properties(cls, properties: "ObstacleProperties"):
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
        ObstacleProperties.set_active_properties(None)

        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("obstacle_dialog/geometry", self.saveGeometry())

        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("obstacle_dialog/geometry"))
