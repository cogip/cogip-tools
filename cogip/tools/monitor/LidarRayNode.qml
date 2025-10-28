import QtQuick
import QtQuick3D

Node {
    id: root

    property real angleDeg: 0
    property vector3d directionVector: Qt.vector3d(1, 0, 0)
    property real distance: 0
    property real pamiHeight: 60.8
    property real pamiShiftX: 75.5
    property real rayLength: 4000
    property Node relativeParent: null
    property real robotHeight: 380
    property int robotId: 1
    property real robotShiftX: 0
    property Node sceneRoot: null
    readonly property real sensorHeight: robotId === 1 ? robotHeight : pamiHeight
    readonly property real sensorShiftX: robotId === 1 ? robotShiftX : pamiShiftX
    property View3D view3d: null

    function hasValidScene() {
        return !!(view3d && view3d.scene);
    }

    function pick() {
        if (!hasValidScene()) {
            return;
        }
        if (robotId > 1 && 90 < angleDeg && angleDeg < 270) {
            return;
        }
        const origin = originRayNode.position;
        const dirVector = Qt.vector3d(directionRayNode.position.x - origin.x, directionRayNode.position.y - origin.y, directionRayNode.position.z - origin.z);
        const dirLength = Math.sqrt(dirVector.x * dirVector.x + dirVector.y * dirVector.y + dirVector.z * dirVector.z);
        if (dirLength < 0.0001) {
            return;
        }
        const dirNorm = Qt.vector3d(dirVector.x / dirLength, dirVector.y / dirLength, dirVector.z / dirLength);
        const result = view3d.rayPickAll(origin, dirNorm);
        let hit = null;
        for (let i = 0; i < result.length; ++i) {
            const candidate = result[i];
            if (!candidate.objectHit || !candidate.objectHit.objectName) {
                continue;
            }
            if (candidate.objectHit.objectName.indexOf("robot_") === 0) {
                continue;
            }
            hit = candidate;
            break;
        }

        let newDistance = 65535;
        if (hit && hit.distance >= 0) {
            newDistance = hit.distance;
            hitGlobalModel.position = hit.scenePosition;
            hitGlobalModel.visible = true;
        } else {
            hitGlobalModel.visible = false;
        }
        if (distance !== newDistance) {
            distance = newDistance;
        }
    }

    function updatePositions() {
        const angleRad = angleDeg * Math.PI / 180;
        directionVector = Qt.vector3d(Math.cos(angleRad), Math.sin(angleRad), 0);

        if (!hasValidScene()) {
            return;
        }

        originRayNode.updatePosition();
        directionRayNode.updatePosition();
    }

    Component.onCompleted: updatePositions()
    onAngleDegChanged: updatePositions()
    onRelativeParentChanged: updatePositions()
    onSceneRootChanged: updatePositions()
    onView3dChanged: updatePositions()

    Connections {
        function onEulerRotationChanged() {
            root.updatePositions();
        }

        function onPositionChanged() {
            root.updatePositions();
        }

        function onScaleChanged() {
            root.updatePositions();
        }

        target: root.relativeParent
    }

    Connections {
        function onEulerRotationChanged() {
            root.updatePositions();
        }

        function onPositionChanged() {
            root.updatePositions();
        }

        function onScaleChanged() {
            root.updatePositions();
        }

        target: root.sceneRoot
    }

    Node {
        id: originRayNode

        function updatePosition() {
            position = root.relativeParent.mapPositionToScene(Qt.vector3d(root.sensorShiftX, root.directionVector.y, root.sensorHeight));
        }

        parent: root.view3d.scene
    }

    Node {
        id: directionRayNode

        function updatePosition() {
            position = root.relativeParent.mapPositionToScene(Qt.vector3d(root.sensorShiftX + root.directionVector.x * root.rayLength, root.directionVector.y * root.rayLength, root.sensorHeight));
        }

        parent: root.view3d.scene
    }

    Model {
        id: hitGlobalModel

        parent: root.view3d.scene
        pickable: false
        scale: Qt.vector3d(0.2, 0.2, 0.2)
        source: "#Sphere"
        visible: false

        materials: [
            PrincipledMaterial {
                baseColor: Qt.rgba(1.0, 0, 0, 1.0)
                metalness: 0.0
                roughness: 0.4
            }
        ]
    }
}
