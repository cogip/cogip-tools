from pathlib import Path

from PySide6.Qt3DCore import Qt3DCore

from cogip.entities.asset import AssetEntity


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
