from pathlib import Path

from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender

from cogip.entities.asset import AssetEntity
from cogip.entities.sensor import Sensor


class TableEntity(AssetEntity):
    """
    The table entity.

    Attributes:
        asset_path: Path of the asset file
    """

    asset_path: Path = Path("assets/table2025.dae")

    def __init__(self, parent: Qt3DCore.QEntity | None = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, parent=parent)
        self._parent = parent

        # Create a layer used by sensors to activate detection on the table borders
        self.layer = Qt3DRender.QLayer(self)
        self.layer.setRecursive(True)
        self.layer.setEnabled(True)
        self.addComponent(self.layer)

        Sensor.add_obstacle(self)
