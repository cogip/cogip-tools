import QtQuick
import QtQuick3D

Node {
    id: crateYellow

    objectName: "CrateYellow"

    CrateBlue {
        eulerRotation: Qt.vector3d(180, 0, 0)
        position: Qt.vector3d(0, 0, 30)
    }
}
