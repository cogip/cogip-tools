import QtQuick
import QtQuick3D

Node {
    id: obstacleRoot

    property real baseHeight: 350
    property real baseLength: 225
    property real baseWidth: 225
    property real beaconLength: 80
    property real beaconRadius: 35
    property bool dragging: false
    property int obstacleId: -1

    objectName: obstacleId >= 0 ? "obstacle_" + obstacleId : "obstacle"

    Model {
        id: obstacleBase

        objectName: obstacleRoot.objectName + "_base"
        pickable: true
        position: Qt.vector3d(0, 0, obstacleRoot.baseHeight / 2)
        scale: Qt.vector3d(obstacleRoot.baseWidth / 100, obstacleRoot.baseLength / 100, obstacleRoot.baseHeight / 100)
        source: "#Cube"

        materials: [
            DefaultMaterial {
                diffuseColor: "#ff8c42"
            }
        ]
    }

    Model {
        id: obstacleBeacon

        eulerRotation.x: 90
        objectName: obstacleRoot.objectName + "_beacon"
        pickable: true
        position: Qt.vector3d(0, 0, obstacleRoot.baseHeight + obstacleRoot.beaconLength / 2)
        scale: Qt.vector3d(obstacleRoot.beaconRadius * 2 / 100, obstacleRoot.beaconLength / 100, obstacleRoot.beaconRadius * 2 / 100)
        source: "#Cylinder"

        materials: [
            DefaultMaterial {
                diffuseColor: "#ffcc33"
            }
        ]
    }
}
