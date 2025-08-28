"""
This module defines the base class [AssetEntity][cogip.tools.monitor.asset.AssetEntity]
used directly or inherited for specific assets.

Asset entities are graphic element displayed on the 3D view and loaded from asset files.
It is typically used for table and robot assets.

Supported asset files are in [Collada](https://en.wikipedia.org/wiki/COLLADA) format (`.dae`).
Other formats could be also supported, but not tested
(see [Open Asset Import Library](https://github.com/assimp/assimp)).
"""

from pathlib import Path
from typing import TextIO

from PySide6 import QtCore
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot


class AssetEntity(Qt3DCore.QEntity):
    """Base class for asset entities

    This class inherits from [`Qt3DCore.QEntity`](https://doc.qt.io/qtforpython-6/PySide6/Qt3DCore/QEntity.html)

    Attributes:
        ready: Qt signal emitted when the asset entity is ready to be used
        asset_ready: `True` if the asset is ready
        asset_entity: first useful `QEntity` in the asset tree
        transform_component: `QTransform` holding the asset's translation and orientation
    """

    ready: qtSignal = qtSignal()

    def __init__(self, asset_path: Path, scale: float = 1.0, parent: Qt3DCore.QEntity = None):
        """
        The constructor checks the asset's file and starts loading the entity.

        The entity load is asynchronous, a signal is emitted when it is done
        (see [`on_loader_status_changed`][cogip.tools.monitor.asset.AssetEntity.on_loader_status_changed])

        Arguments:
            asset_path: path of the asset file
            scale: scale to apply to the entity after load
        """

        super().__init__(parent)

        self.asset_ready: bool = False
        self.asset_path: Path = asset_path
        self.scale: float = scale
        self.asset_entity: Qt3DCore.QEntity = None

        self.transform_component = Qt3DCore.QTransform()
        self.addComponent(self.transform_component)

        if not self.asset_path.exists():
            raise FileNotFoundError(f"File not found '{self.asset_path}'")
        if not self.asset_path.is_file():
            raise IsADirectoryError(f"'{self.asset_path}' is not a file")

        self.loader = Qt3DRender.QSceneLoader(self)
        self.loader.statusChanged.connect(self.on_loader_status_changed)
        self.loader.setObjectName(self.asset_path.name)
        self.addComponent(self.loader)
        self.loader.setSource(QtCore.QUrl(f"file:{self.asset_path}"))

    @qtSlot(Qt3DRender.QSceneLoader.Status)
    def on_loader_status_changed(self, status: Qt3DRender.QSceneLoader.Status):
        """
        When the loader has finished, clean the entity tree,
        record the main `QEntity` and its `QTransform` component.

        Then it generated the dot tree
        (see [`generate_tree`][cogip.tools.monitor.asset.AssetEntity.generate_tree]),
        run the [`post_init`][cogip.tools.monitor.asset.AssetEntity.post_init] pass,
        and emit the `ready` signal.

        Arguments:
            status: current loader status
        """
        if (
            status.value != Qt3DRender.QSceneLoader.Ready.value
        ):  # .value is workaround to a Python binding bug in PySide6 6.4.
            return

        self.post_init()

        self.generate_tree()

        self.asset_ready = True

        self.ready.emit()

    def generate_tree(self):
        """
        Generate a tree of all entities and components starting from the main entity.

        The generated file is stored next to the asset file and it has the same name
        but with `.tree.dot` extension.

        It is a text file written in [Graphviz](https://graphviz.org/) format.

        To read this file:
        ```bash
            sudo apt install graphviz okular
            dot -Tpdf assets/robot2019.tree.dot | okular -
        ```
        """

        tree_filename = self.asset_path.with_suffix(".tree.dot")
        with tree_filename.open(mode="w") as fd:
            fd.write('graph ""\n')
            fd.write("{\n")
            fd.write('label="Entity tree"\n')
            root_node_number = 0
            traverse_tree(self, root_node_number, fd)
            fd.write("}\n")

    def post_init(self):
        """
        Post initialization method that can be overloaded.
        It it executed after entity and transform components are ready.
        """
        pass


def traverse_tree(node: Qt3DCore.QEntity, next_node_nb: int, fd: TextIO) -> tuple[int, int]:
    """
    Recursive function traversing all child entities and write its node
    and all its components to the .dot file.

    Arguments:
        node: entity to traverse
        next_node_nb: next node number
        fd: opened file descriptor used to write the tree

    Return:
        tuple of current and next node numbers
    """

    current_node_nb = next_node_nb
    next_node_nb += 1

    # Insert current node in the tree
    fd.write(f'n{current_node_nb:03d} [label="{node.metaObject().className()}\n{node.objectName()}"] ;\n')

    # Enumerate components
    for comp in node.components():
        fd.write(f'n{next_node_nb:03d} [shape=box,label="{comp.metaObject().className()}\n{comp.objectName()}"] ;\n')
        fd.write(f"n{current_node_nb:03d} -- n{next_node_nb:03d} [style=dotted];\n")
        next_node_nb += 1

    # Build tree for children
    for child_node in node.children():
        if isinstance(child_node, Qt3DCore.QEntity):
            child_node_nb, next_node_nb = traverse_tree(child_node, next_node_nb, fd)
            fd.write(f"n{current_node_nb:03d} -- n{child_node_nb:03d} ;\n")

    return current_node_nb, next_node_nb
