import QtQuick
import QtQuick3D

Node {
    id: cratesBBBB

    objectName: "CratesBBBB"

    CrateBlue {
        position: Qt.vector3d(0, 75, 0)
    }

    CrateBlue {
        position: Qt.vector3d(0, 25, 0)
    }

    CrateBlue {
        position: Qt.vector3d(0, -25, 0)
    }

    CrateBlue {
        position: Qt.vector3d(0, -75, 0)
    }
}
