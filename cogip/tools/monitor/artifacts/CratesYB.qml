import QtQuick
import QtQuick3D

Node {
    id: cratesYB

    objectName: "CratesYB"

    CrateYellow {
        position: Qt.vector3d(0, 25, 0)
    }

    CrateBlue {
        position: Qt.vector3d(0, -25, 0)
    }
}
