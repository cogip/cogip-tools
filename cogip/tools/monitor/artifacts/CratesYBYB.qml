import QtQuick
import QtQuick3D

Node {
    id: cratesYBYB

    objectName: "CratesYBYB"

    CrateYellow {
        position: Qt.vector3d(0, 75, 0)
    }

    CrateBlue {
        position: Qt.vector3d(0, 25, 0)
    }

    CrateYellow {
        eulerRotation: Qt.vector3d(0, 0, 180)
        position: Qt.vector3d(0, -25, 0)
    }

    CrateBlue {
        eulerRotation: Qt.vector3d(0, 0, 180)
        position: Qt.vector3d(0, -75, 0)
    }
}
