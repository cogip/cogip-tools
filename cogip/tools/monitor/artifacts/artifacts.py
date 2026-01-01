from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from cogip.models.artifacts import PantryID, collection_areas, pantries
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


def add_crates_blue(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCrateBlue", x, y, z, rot_z)


def add_crates_yellow(root: QObject, x: float, y: float, z: float, rot_z: float) -> None:
    add_crates_by_name(root, "addCrateYellow", x, y, z, rot_z)


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

    # Add pseudo-random crates in pantries

    ## LocalTop
    ## - compatible alignment
    ## - horizontal but too close to granary border
    ## - do nothing
    x, y, angle, _ = pantries[PantryID.LocalTop]
    add_crates_blue(root, x + 60, y + 5, 0.0, 90.0)
    add_crates_yellow(root, x + 5, y, 0.0, 90.0)
    add_crates_yellow(root, x - 50, y - 3, 0.0, 90.0)
    add_crates_blue(root, x - 105, y + 2, 0.0, 90.0)

    ## MiddleCenter
    ## - compatible alignment
    ## - 2 rows of 4 crates
    ## - 2 possible positions for approach
    x, y, angle, _ = pantries[PantryID.MiddleCenter]
    add_crates_blue(root, x + 82, y - 85, 0.0, 0.0)
    add_crates_yellow(root, x + 80, y - 30, 0.0, 0.0)
    add_crates_blue(root, x + 83, y + 25, 0.0, 0.0)
    add_crates_yellow(root, x + 78, y + 80, 0.0, 0.0)
    add_crates_yellow(root, x - 74, y - 85, 0.0, 0.0)
    add_crates_yellow(root, x - 73, y - 30, 0.0, 0.0)
    add_crates_yellow(root, x - 73, y + 25, 0.0, 0.0)
    add_crates_yellow(root, x - 79, y + 80, 0.0, 0.0)

    ## MiddleBottom
    ## - compatible alignment
    ## - only one possible position for approach
    ## - close to border, be careful on blocking during approach/alignment
    x, y, angle, _ = pantries[PantryID.MiddleBottom]
    add_crates_blue(root, x + 1, y - 85, 0.0, 0.0)
    add_crates_yellow(root, x - 3, y - 30, 0.0, 0.0)
    add_crates_blue(root, x + 2, y + 25, 0.0, 0.0)
    add_crates_yellow(root, x - 5, y + 80, 0.0, 0.0)

    ## OppositeCenter
    ## - compatible alignment
    ## - 2 possible positions for approach
    ## - need to disable CollectionAreaID.OppositeCenter in test strategy before stealing
    x, y, angle, _ = pantries[PantryID.OppositeCenter]
    add_crates_yellow(root, x + 55, y - 75, 0.0, 35.0)
    add_crates_yellow(root, x + 25, y - 25, 0.0, 30.0)
    add_crates_blue(root, x, y + 25, 0.0, 33.0)
    add_crates_blue(root, x - 25, y + 75, 0.0, 31.0)

    ## OppositeBottom
    ## - good alignment
    ## - already blue
    ## - do nothing
    x, y, angle, _ = pantries[PantryID.OppositeBottom]
    add_crates_blue(root, x, y - 75, 0.0, 0.0)
    add_crates_blue(root, x, y - 25, 0.0, 0.0)
    add_crates_blue(root, x, y + 25, 0.0, 0.0)
    add_crates_blue(root, x, y + 75, 0.0, 0.0)

    ## OppositeTop
    ## - compatible alignment
    ## - blocking crate in front of good ones
    ## - do nothing
    x, y, angle, _ = pantries[PantryID.OppositeTop]
    add_crates_blue(root, x + 15, y + 87, 0.0, 0.0)
    add_crates_yellow(root, x + 15, y + 28, 0.0, 0.0)
    add_crates_yellow(root, x + 15, y - 25, 0.0, 0.0)
    add_crates_blue(root, x + 15, y - 80, 0.0, 0.0)
    add_crates_blue(root, x - 90, y, 0.0, 90.0)

    ## OppositeSide
    ## - compatible alignment
    ## - 6 crates
    ## - need to select the most opposite color but consecutive crates
    x, y, angle, _ = pantries[PantryID.OppositeSide]
    add_crates_yellow(root, x - 125, y, 0.0, 90.0)
    add_crates_yellow(root, x - 75, y, 0.0, 90.0)
    add_crates_yellow(root, x - 25, y, 0.0, -90.0)
    add_crates_yellow(root, x + 25, y, 0.0, 90.0)
    add_crates_blue(root, x + 75, y, 0.0, 90.0)
    add_crates_blue(root, x + 125, y, 0.0, 90.0)
