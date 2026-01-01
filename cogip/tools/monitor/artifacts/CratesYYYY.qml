import QtQuick
import QtQuick3D

Node {
    id: cratesYYYY

    objectName: "CratesYYYY"

    CrateYellow {
        position: Qt.vector3d(0, 75, 0)
    }

    CrateYellow {
        position: Qt.vector3d(0, 25, 0)
    }

    CrateYellow {
        eulerRotation: Qt.vector3d(0, 0, 180)
        position: Qt.vector3d(0, -25, 0)
    }

    CrateYellow {
        eulerRotation: Qt.vector3d(0, 0, 180)
        position: Qt.vector3d(0, -75, 0)
    }
}
