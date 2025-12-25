from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

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
    ## LocalBottom
    add_crates_ybyb(root, -825, -400, 0.0, 180.0)
    ## LocalBottomSide
    add_crates_ybyb(root, -600, -1325, 0.0, -90.0)
    ## LocalTopSide
    add_crates_ybyb(root, 200, -1325, 0.0, -90.0)
    ## LocalCenter
    add_crates_ybyb(root, -200, -350, 0.0, 180.0)
    ## OppositeBottom
    add_crates_ybyb(root, -825, 400, 0.0, 180.0)
    ## OppositeBottomSide
    add_crates_ybyb(root, -600, 1325, 0.0, 90.0)
    ## OppositeTopSide
    add_crates_ybyb(root, 200, 1325, 0.0, 90.0)
    ## OppositeCenter
    add_crates_ybyb(root, -200, 350, 0.0, 180.0)
