from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from cogip.models.artifacts import collection_areas
from .. import logger


def add_artifacts(root: QObject) -> None:
    add_crates(root)


def add_crates_by_name(root: QObject, name: str, x: float, y: float, z: float, rot_z: float) -> None:
    if not root:
        logger.warning("View3D root not available for add_crate")
        return
    QMetaObject.invokeMethod(
        root,
        name,
        Qt.ConnectionType.QueuedConnection,
        Q_ARG("QVariant", x),
        Q_ARG("QVariant", y),
        Q_ARG("QVariant", z),
        Q_ARG("QVariant", rot_z),
    )


def add_crates_yb(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCratesYB", x, y, z, rot_z)


def add_crates_ybyb(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCratesYBYB", x, y, z, rot_z)


def add_crates_bbbb(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCratesBBBB", x, y, z, rot_z)


def add_crates_yyyy(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCratesYYYY", x, y, z, rot_z)


def add_crates_eee(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCratesEEE", x, y, z, rot_z)


def add_crates(root: QObject) -> None:
    # Granary area
    ## Fridges
    add_crates_yb(root, 725, 400, 55, 0.0)
    add_crates_yb(root, 725, -400, 55, 0.0)
    add_crates_yb(root, 775, 150, 55, 0.0)
    add_crates_yb(root, 775, -150, 55, 0.0)
    ## Loading areas
    add_crates_bbbb(root, 675, -700, 55, 0.0)
    add_crates_eee(root, 675, -700, 85, 0.0)
    add_crates_yyyy(root, 675, 700, 55, 0.0)
    add_crates_eee(root, 675, 700, 85, 0.0)

    # Collection areas
    for x, y, angle, _ in collection_areas.values():
        if angle is None:
            angle = 0.0
        add_crates_ybyb(root, x, y, 0.0, angle)
