import QtQuick
import QtQuick3D

Node {
    id: cratesYBYB

    objectName: "CratesYBYB"

    CratesYB {
        position: Qt.vector3d(0, 50, 0)
    }

    CratesYB {
        position: Qt.vector3d(0, -50, 0)
    }
}
