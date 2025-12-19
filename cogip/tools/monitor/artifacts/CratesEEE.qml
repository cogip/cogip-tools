import QtQuick
import QtQuick3D

Node {
    id: cratesEEE

    objectName: "CratesEEE"

    CrateEmpty {
        position: Qt.vector3d(0, 50, 0)
    }

    CrateEmpty {
        position: Qt.vector3d(0, 0, 0)
    }

    CrateEmpty {
        position: Qt.vector3d(0, -50, 0)
    }
}
