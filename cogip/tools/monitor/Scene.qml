import QtMultimedia
import QtQuick
import QtQuick.Window
import QtQuick3D
import "." as Components
import "artifacts" as Artifacts
import "cursor.mesh"
import "pami.mesh"
import "robot.mesh"
import "robots"
import "table.mesh"

Item {
    id: sceneRoot

    property alias circleObstacles: view.circleObstacles
    readonly property string gridGroundTexture: "../../../assets/grid_plain.webp"
    property alias groundTextureSource: view.groundTextureSource
    property alias liveRobotNode: view.liveRobotNode
    property alias obstacleSettings: view.obstacleSettings
    property alias orderRobotNode: view.orderRobotNode
    property alias rectangleObstacles: view.rectangleObstacles
    property int robotId: view.view3DBackend ? view.view3DBackend.robotId : 0
    property var robotPathPoints: []
    property bool showLivePip: false
    property bool showManualPip: false
    property var socketClient
    readonly property string tableGroundTexture: "../../../assets/table2026.webp"
    property string videoStreamUrl: {
        if (!socketClient || !view.liveRobotNode || !view.view3DBackend)
            return "";
        var url = socketClient.url;
        if (!url)
            return "";
        var parts = url.split("://");
        var hostname;
        if (parts.length > 1) {
            hostname = parts[1].split(":")[0];
        } else {
            hostname = url.split(":")[0];
        }
        var robotId = view.view3DBackend.robotId;
        return "http://" + hostname + ":810" + robotId;
    }
    property alias virtualDetector: view.virtualDetector
    property alias virtualPlanner: view.virtualPlanner

    function addObstacle() {
        var obstacle = view.createObstacle();
        return obstacle;
    }

    function clearObstacles() {
        if (view && view.clearObstacles) {
            view.clearObstacles();
        }
    }

    function exportObstacles() {
        if (view && view.exportObstacles) {
            return view.exportObstacles();
        }
        return [];
    }

    function grabPipView() {
        if (pipView && pipView.grabToImage) {
            pipView.grabToImage(function (result) {
                if (view && view.view3DBackend) {
                    view.view3DBackend.process_grab_result(result);
                }
            });
        }
    }

    function importObstacles(list) {
        if (view && view.importObstacles) {
            view.importObstacles(list);
        }
    }

    height: 600
    width: 800

    View3D {
        id: view

        property var circleObstacles: []
        property string cursorTextureSource: "../../../assets/cursor.webp"
        property string granaryTextureSource: "../../../assets/granary.webp"
        property string groundTextureSource: sceneRoot.tableGroundTexture
        property int lidarRayBatch: 360
        property int lidarRayCount: 360
        property int lidarRayIndex: 0
        property var lidarRayNodes: []
        property int lidarTimerInterval: 16
        property var liveRobotNode: null
        property int obstacleCounter: 0
        property var obstacleNodes: []
        property var obstacleSettings: null
        property var orderRobotNode: null
        property var rectangleObstacles: []
        property var robotPathPoints: []
        property string thermometerBlueTextureSource: "../../../assets/thermometer_blue.webp"
        property string thermometerYellowTextureSource: "../../../assets/thermometer_yellow.webp"
        property var view3DBackend: null
        property bool virtualDetector: false
        property bool virtualPlanner: false

        signal postLidarUpdate

        function addCrateBlue(x, y, z, rotZ) {
            var crate = crateBlueComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCrateEmpty(x, y, z, rotX, rotZ) {
            var crateEmpty = crateEmptyComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.x": rotX,
                "eulerRotation.z": rotZ
            });
        }

        function addCrateYellow(x, y, z, rotZ) {
            var crate = crateYellowComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCratesBBBB(x, y, z, rotZ) {
            var cratesBBBB = cratesBBBBComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCratesEEE(x, y, z, rotZ) {
            var cratesEEE = cratesEEEComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCratesYB(x, y, z, rotZ) {
            var cratesYB = cratesYBComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCratesYBYB(x, y, z, rotZ) {
            var cratesYBYB = cratesYBYBComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addCratesYYYY(x, y, z, rotZ) {
            var cratesYYYY = cratesYYYYComponent.createObject(sceneGroup, {
                "x": x,
                "y": y,
                "z": z,
                "eulerRotation.z": rotZ
            });
        }

        function addOrderRobotInstance(robotId) {
            const component = robotId === 1 ? orderRobotComponent : orderPamiComponent;
            if (!component) {
                console.warn("Missing component for robotId", robotId);
                return null;
            }
            const namePrefix = robotId === 1 ? "robot" : "pami";
            const expectedName = namePrefix + "_order_" + robotId;
            if (orderRobotNode) {
                if (orderRobotNode.objectName === expectedName) {
                    return orderRobotNode;
                }
                orderRobotNode.destroy();
                orderRobotNode = null;
            }
            const node = component.createObject(orderRobotGroup, {
                objectName: expectedName
            });
            if (!node) {
                console.error("Failed to create order robot instance for", robotId);
                return null;
            }
            orderRobotNode = node;
            return node;
        }

        function addRobotInstance(robotId) {
            const component = robotId === 1 ? liveRobotComponent : livePamiComponent;
            if (!component) {
                console.warn("Missing component for robotId", robotId);
                return null;
            }
            const namePrefix = robotId === 1 ? "robot" : "pami";
            const expectedName = namePrefix + "_live_" + robotId;
            if (liveRobotNode) {
                if (liveRobotNode.objectName === expectedName) {
                    return liveRobotNode;
                }
                liveRobotNode.destroy();
                liveRobotNode = null;
            }
            const node = component.createObject(sceneGroup, {
                objectName: expectedName,
                z: robotId === 5 ? 55 : 0
            });
            if (!node) {
                console.error("Failed to create robot instance for", robotId);
                return null;
            }
            if (view.virtualDetector) {
                view.createLidarRayNodes(node, robotId);
            }
            liveRobotNode = node;
            return node;
        }

        function clearObstacles() {
            if (obstacleWindow && obstacleWindow.visible) {
                obstacleWindow.visible = false;
                obstacleWindow.obstacle = null;
            }
            if (obstacleNodes && obstacleNodes.length) {
                for (const node of obstacleNodes) {
                    node.destroy();
                }
            }
            obstacleNodes = [];
            obstacleCounter = 0;
            updateMonitorObstacles();
        }

        function createLidarRayNodes(parentNode, robotId) {
            deleteLidarRayNodes();

            for (let i = 0; i < lidarRayCount; ++i) {
                const node = lidarRayComponent.createObject(view.scene, {
                    view3d: view,
                    relativeParent: parentNode,
                    sceneRoot: sceneGroup,
                    robotId: robotId,
                    angleDeg: i
                });
                if (node) {
                    lidarRayNodes.push(node);
                } else {
                    console.warn("Failed to create lidar ray node", i);
                }
            }
            lidarRayIndex = 0;
        }

        function createObstacle() {
            var params = {
                obstacleId: obstacleCounter
            };
            var obstacle = obstacleComponent.createObject(sceneGroup, params);
            if (!obstacle) {
                console.error("Failed to create obstacle");
                return null;
            }
            obstacleCounter += 1;
            obstacleNodes.push(obstacle);
            // qmllint disable missing-property
            obstacle.positionChanged.connect(view.updateMonitorObstacles);
            // qmllint enable missing-property
            view.updateMonitorObstacles();
            return obstacle;
        }

        function deleteLidarRayNodes() {
            if (lidarRayNodes && lidarRayNodes.length) {
                for (const node of lidarRayNodes) {
                    node.destroy();
                }
            }
            lidarRayNodes = [];
            lidarRayIndex = 0;
        }

        function exportObstacles() {
            const list = [];
            for (const node of obstacleNodes) {
                const rotation = node.eulerRotation || Qt.vector3d();
                list.push({
                    x: node.x !== undefined ? node.x : 0,
                    y: node.y !== undefined ? node.y : 0,
                    angle: rotation && rotation.z !== undefined ? rotation.z : 0,
                    baseWidth: node.baseWidth,
                    baseLength: node.baseLength,
                    baseHeight: node.baseHeight,
                    beaconLength: node.beaconLength,
                    beaconRadius: node.beaconRadius
                });
            }
            return list;
        }

        function importObstacles(list) {
            clearObstacles();
            if (!list || !list.length) {
                return;
            }
            var maxId = -1;
            for (const entry of list) {
                const obstacle = createObstacle();
                maxId = Math.max(maxId, obstacle.obstacleId);
                obstacle.x = entry.x;
                obstacle.y = entry.y;
                obstacle.eulerRotation.z = entry.angle;
                obstacle.baseWidth = entry.baseWidth;
                obstacle.baseLength = entry.baseLength;
                obstacle.baseHeight = entry.baseHeight;
                obstacle.beaconLength = entry.beaconLength;
                obstacle.beaconRadius = entry.beaconRadius;
            }
            obstacleCounter = Math.max(obstacleCounter, maxId + 1);
            view.updateMonitorObstacles();
        }

        function openNinjaManualDialog() {
            ninjaManualWindow.showPanel();
        }

        function openObstacleConfig(obstacle) {
            obstacleWindow.showPanel(obstacle);
        }

        function openPamiManualDialog() {
            pamiManualWindow.showPanel();
        }

        function openRobotManualDialog() {
            robotManualWindow.showPanel();
        }

        function removeOrderRobotInstance(robotId) {
            if (!orderRobotNode) {
                return;
            }
            orderRobotNode.destroy();
            orderRobotNode = null;
        }

        function removeRobotInstance(robotId) {
            if (!liveRobotNode) {
                return;
            }
            liveRobotNode.destroy();
            liveRobotNode = null;
            view.deleteLidarRayNodes();
        }

        function updateMonitorObstacles() {
            view.view3DBackend.update_shared_obstacles(view.exportObstacles());
        }

        activeFocusOnTab: true
        anchors.fill: parent
        focus: true
        objectName: "view"

        environment: SceneEnvironment {
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            backgroundMode: SceneEnvironment.Color
            clearColor: "#222222"
        }

        Keys.onPressed: function (event) {
            const step = 50;
            const rotStep = 5;
            if (event.key === Qt.Key_Left && event.modifiers & Qt.ShiftModifier) {
                sceneGroup.eulerRotation.x -= rotStep;
            } else if (event.key === Qt.Key_Right && event.modifiers & Qt.ShiftModifier) {
                sceneGroup.eulerRotation.x += rotStep;
            } else if (event.key === Qt.Key_Up && event.modifiers & Qt.ShiftModifier) {
                sceneGroup.eulerRotation.y += rotStep;
            } else if (event.key === Qt.Key_Down && event.modifiers & Qt.ShiftModifier) {
                sceneGroup.eulerRotation.y -= rotStep;
            } else if (event.key === Qt.Key_Left && event.modifiers & Qt.ControlModifier) {
                sceneGroup.eulerRotation.z += rotStep;
            } else if (event.key === Qt.Key_Right && event.modifiers & Qt.ControlModifier) {
                sceneGroup.eulerRotation.z -= rotStep;
            } else if (event.key === Qt.Key_Up && event.modifiers & Qt.ControlModifier) {
                sceneGroup.position.z -= step;
            } else if (event.key === Qt.Key_Down && event.modifiers & Qt.ControlModifier) {
                sceneGroup.position.z += step;
            } else if (event.key === Qt.Key_Left) {
                sceneGroup.position.y += step;
            } else if (event.key === Qt.Key_Right) {
                sceneGroup.position.y -= step;
            } else if (event.key === Qt.Key_Up) {
                sceneGroup.position.x += step;
            } else if (event.key === Qt.Key_Down) {
                sceneGroup.position.x -= step;
            } else if (event.key === Qt.Key_Space) {
                sceneGroup.position = Qt.vector3d(0, 0, 0);
                sceneGroup.eulerRotation = Qt.vector3d(0, 0, 0);
            } else if (event.key === Qt.Key_Return) {
                sceneGroup.position = Qt.vector3d(0, 0, 0);
                sceneGroup.eulerRotation = Qt.vector3d(5, 35, 15);
            }
        }

        Component {
            id: obstacleComponent

            Components.Obstacle {
            }
        }

        Component {
            id: lidarRayComponent

            Components.LidarRayNode {
            }
        }

        Component {
            id: liveRobotComponent

            Robot {
                property alias camera: liveRobotCamera

                PerspectiveCamera {
                    id: liveRobotCamera

                    eulerRotation.y: -45
                    eulerRotation.z: -90
                    objectName: "robotCamera"
                    position: Qt.vector3d(120, 0, 350)
                }
            }
        }

        Component {
            id: livePamiComponent

            Pami {
            }
        }

        Component {
            id: orderRobotComponent

            Robot {
            }
        }

        Component {
            id: orderPamiComponent

            Pami {
            }
        }

        Component {
            id: crateBlueComponent

            Artifacts.CrateBlue {
            }
        }

        Component {
            id: crateYellowComponent

            Artifacts.CrateYellow {
            }
        }

        Component {
            id: crateEmptyComponent

            Artifacts.CrateEmpty {
            }
        }

        Component {
            id: cratesYBComponent

            Artifacts.CratesYB {
            }
        }

        Component {
            id: cratesYBYBComponent

            Artifacts.CratesYBYB {
            }
        }

        Component {
            id: cratesBBBBComponent

            Artifacts.CratesBBBB {
            }
        }

        Component {
            id: cratesYYYYComponent

            Artifacts.CratesYYYY {
            }
        }

        Component {
            id: cratesEEEComponent

            Artifacts.CratesEEE {
            }
        }

        DirectionalLight {
            castsShadow: true
            eulerRotation.x: -45
            eulerRotation.y: 45
        }

        DirectionalLight {
            castsShadow: false
            color: "#808080"
            eulerRotation.x: -45
            eulerRotation.y: -45
        }

        PerspectiveCamera {
            id: cameraNode

            eulerRotation: Qt.vector3d(0, 0, -90)
            position: Qt.vector3d(0, 0, 3000)
        }

        Node {
            id: sceneGroup

            Model {
                id: ground

                objectName: "ground"
                position: Qt.vector3d(0, 0, 0)
                scale: Qt.vector3d(20, 30, 1)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.groundTextureSource
                        }
                    }
                ]
            }

            Table {
                id: table

                objectName: "table"
            }

            Model {
                id: granary

                objectName: "Granary"
                position: Qt.vector3d(775, 0, 27.5)
                scale: Qt.vector3d(4.5, 18, 0.55)
                source: "#Cube"

                materials: [
                    DefaultMaterial {
                        diffuseColor: "#96643f"
                    }
                ]
            }

            Model {
                id: granaryLeftBorder

                objectName: "GranaryLeftBorder"
                position: Qt.vector3d(775, 892.5, 62.5)
                scale: Qt.vector3d(4.5, 0.15, 0.15)
                source: "#Cube"

                materials: [
                    DefaultMaterial {
                        diffuseColor: "#96643f"
                    }
                ]
            }

            Model {
                id: granaryRightBorder

                objectName: "GranaryRightBorder"
                position: Qt.vector3d(775, -892.5, 62.5)
                scale: Qt.vector3d(4.5, 0.15, 0.15)
                source: "#Cube"

                materials: [
                    DefaultMaterial {
                        diffuseColor: "#96643f"
                    }
                ]
            }

            Model {
                id: granaryGround

                objectName: "granaryGround"
                position: Qt.vector3d(775, 0, 56)
                scale: Qt.vector3d(4.5, 18, 0.55)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.granaryTextureSource
                        }
                    }
                ]
            }

            Model {
                id: thermometerBlue

                eulerRotation: Qt.vector3d(0, -90, -90)
                objectName: "thermometerBlue"
                position: Qt.vector3d(-1022.1, -800, 24)
                scale: Qt.vector3d(14, 0.7, 1)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.thermometerBlueTextureSource
                        }
                    }
                ]
            }

            Model {
                id: thermometerYellow

                eulerRotation: Qt.vector3d(0, -90, -90)
                objectName: "thermometerYellow"
                position: Qt.vector3d(-1022.1, 800, 24)
                scale: Qt.vector3d(14, 0.7, 1)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.thermometerYellowTextureSource
                        }
                    }
                ]
            }

            Cursor {
                id: cursorBlue

                eulerRotation: Qt.vector3d(0, 0, 180)
                objectName: "cursorBlue"
                position: Qt.vector3d(-1023.5, -1250, 66)
            }

            Cursor {
                id: cursorYellow

                eulerRotation: Qt.vector3d(0, 0, 180)
                objectName: "cursorYellow"
                position: Qt.vector3d(-1023.5, 1250, 66)
            }

            Model {
                id: cursorTextureBlue

                eulerRotation: Qt.vector3d(0, -90, -90)
                objectName: "cursorTextureBlue"
                position: Qt.vector3d(-1040, 1250, 66)
                scale: Qt.vector3d(1, 1.05, 1)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.cursorTextureSource
                        }
                    }
                ]
            }

            Model {
                id: cursorTextureYellow

                eulerRotation: Qt.vector3d(0, -90, -90)
                objectName: "cursorTextureYellow"
                position: Qt.vector3d(-1040, -1250, 66)
                scale: Qt.vector3d(1, 1.05, 1)
                source: "#Rectangle"

                materials: [
                    DefaultMaterial {
                        diffuseMap: Texture {
                            source: view.cursorTextureSource
                        }
                    }
                ]
            }

            Components.Polyline3D {
                id: robotPlannedPath

                objectName: "robotPlannedPath"
                points: view.robotPathPoints
            }

            Node {
                id: dynamicObstacles

                objectName: "dynamicObstacles"

                Repeater3D {
                    id: rectangleObstacleRepeater

                    model: view.rectangleObstacles

                    delegate: Node {
                        id: rectangleObstacleNode

                        property var boundingPoints: []
                        required property int index
                        required property var modelData
                        readonly property real obstacleAngle: obstacleData && obstacleData.angle !== undefined ? obstacleData.angle : 0
                        property var obstacleData: modelData
                        readonly property real obstacleHeight: 4
                        readonly property real obstacleLengthX: obstacleData && obstacleData.length_x !== undefined ? obstacleData.length_x : 0
                        readonly property real obstacleLengthY: obstacleData && obstacleData.length_y !== undefined ? obstacleData.length_y : 0
                        readonly property real obstacleX: obstacleData && obstacleData.x !== undefined ? obstacleData.x : 0
                        readonly property real obstacleY: obstacleData && obstacleData.y !== undefined ? obstacleData.y : 0

                        function rebuildBoundingPoints() {
                            const source = obstacleData && obstacleData.bounding_box ? obstacleData.bounding_box : [];
                            if (!source || source.length < 2) {
                                boundingPoints = [];
                                return;
                            }
                            const list = [];
                            for (let i = 0; i < source.length; ++i) {
                                const point = source[i] || {};
                                list.push({
                                    x: point.x,
                                    y: point.y,
                                    z: 2
                                });
                            }
                            if (list.length > 0) {
                                const first = list[0];
                                list.push({
                                    x: first.x,
                                    y: first.y,
                                    z: first.z
                                });
                            }
                            boundingPoints = list;
                        }

                        objectName: "rectangle_obstacle_" + index

                        Component.onCompleted: rebuildBoundingPoints()
                        onObstacleDataChanged: rebuildBoundingPoints()

                        Model {
                            id: rectangleObstacleModel

                            eulerRotation: Qt.vector3d(0, 0, rectangleObstacleNode.obstacleAngle)
                            objectName: rectangleObstacleNode.objectName
                            opacity: 0.65
                            pickable: false
                            position: Qt.vector3d(rectangleObstacleNode.obstacleX, rectangleObstacleNode.obstacleY, rectangleObstacleNode.obstacleHeight / 2)
                            scale: Qt.vector3d(Math.max(rectangleObstacleNode.obstacleLengthX, 1) / 100, Math.max(rectangleObstacleNode.obstacleLengthY, 1) / 100, rectangleObstacleNode.obstacleHeight / 100)
                            source: "#Cube"

                            materials: [
                                DefaultMaterial {
                                    diffuseColor: Qt.rgba(1, 0.3, 0.3, 0.65)
                                }
                            ]
                        }

                        Components.Polyline3D {
                            id: rectangleBoundingPath

                            elevation: 2
                            lineColor: Qt.rgba(1, 0.2, 0.2, 0.85)
                            points: rectangleObstacleNode.boundingPoints
                            thickness: 4
                            visible: rectangleObstacleNode.boundingPoints && rectangleObstacleNode.boundingPoints.length > 1
                        }
                    }
                }

                Repeater3D {
                    id: circleObstacleRepeater

                    model: view.circleObstacles

                    delegate: Node {
                        id: circleObstacleNode

                        property var boundingPoints: []
                        required property int index
                        required property var modelData
                        readonly property real obstacleAngle: obstacleData && obstacleData.angle !== undefined ? obstacleData.angle : 0
                        property var obstacleData: modelData
                        readonly property real obstacleHeight: 4
                        readonly property real obstacleRadius: obstacleData && obstacleData.radius !== undefined ? obstacleData.radius : 0
                        readonly property real obstacleX: obstacleData && obstacleData.x !== undefined ? obstacleData.x : 0
                        readonly property real obstacleY: obstacleData && obstacleData.y !== undefined ? obstacleData.y : 0

                        function rebuildBoundingPoints() {
                            const source = obstacleData && obstacleData.bounding_box ? obstacleData.bounding_box : [];
                            if (!source || source.length < 2) {
                                boundingPoints = [];
                                return;
                            }
                            const list = [];
                            for (let i = 0; i < source.length; ++i) {
                                const point = source[i];
                                list.push({
                                    x: isNaN(point.x) ? 0 : point.x,
                                    y: isNaN(point.y) ? 0 : point.y,
                                    z: 2
                                });
                            }
                            if (list.length > 0) {
                                const first = list[0];
                                list.push({
                                    x: first.x,
                                    y: first.y,
                                    z: first.z
                                });
                            }
                            boundingPoints = list;
                        }

                        objectName: "circle_obstacle_" + index

                        Component.onCompleted: rebuildBoundingPoints()
                        onObstacleDataChanged: rebuildBoundingPoints()

                        Model {
                            id: circleObstacleModel

                            eulerRotation: Qt.vector3d(90, 0, circleObstacleNode.obstacleAngle)
                            objectName: circleObstacleNode.objectName
                            opacity: 0.765
                            pickable: false
                            position: Qt.vector3d(circleObstacleNode.obstacleX, circleObstacleNode.obstacleY, circleObstacleNode.obstacleHeight / 2)
                            scale: Qt.vector3d(Math.max(circleObstacleNode.obstacleRadius * 2, 1) / 100, circleObstacleNode.obstacleHeight / 100, Math.max(circleObstacleNode.obstacleRadius * 2, 1) / 100)
                            source: "#Cylinder"

                            materials: [
                                DefaultMaterial {
                                    diffuseColor: Qt.rgba(1, 0.3, 0.3, 0.65)
                                }
                            ]
                        }

                        Components.Polyline3D {
                            id: circleBoundingPath

                            elevation: 2
                            lineColor: Qt.rgba(1, 0.2, 0.2, 0.85)
                            points: circleObstacleNode.boundingPoints
                            thickness: 4
                            visible: circleObstacleNode.boundingPoints && circleObstacleNode.boundingPoints.length > 1
                        }
                    }
                }
            }

            Robot {
                id: robotManual

                property alias camera: robotManualCamera
                property bool dragging: false
                property var windowSettings: null

                eulerRotation.z: 180
                objectName: "robotManual"
                x: 1200
                y: 1200

                PerspectiveCamera {
                    id: robotManualCamera

                    eulerRotation.y: -45
                    eulerRotation.z: -90
                    objectName: "robotCamera"
                    position: Qt.vector3d(120, 0, 350)
                }
            }

            Pami {
                id: ninjaManual

                property bool dragging: false
                property var windowSettings: null

                eulerRotation.z: 180
                objectName: "ninjaManual"
                x: 955
                y: 0
                z: 55
            }

            Pami {
                id: pamiManual

                property bool dragging: false
                property var windowSettings: null

                eulerRotation.z: 180
                objectName: "pamiManual"
                x: 1200
                y: 800
            }
        }

        MouseArea {
            property var clickCandidate: null
            property real clickPressX: 0
            property real clickPressY: 0
            property var draggedObject: null
            property real lastX: 0
            property real lastY: 0

            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            anchors.fill: parent

            onPositionChanged: function (mouse) {
                if (clickCandidate) {
                    var movement = Math.max(Math.abs(mouse.x - clickPressX), Math.abs(mouse.y - clickPressY));
                    if (movement > 5) {
                        draggedObject = clickCandidate;
                        if (draggedObject && draggedObject.dragging !== undefined) {
                            draggedObject.dragging = true;
                        }
                        clickCandidate = null;
                        lastX = mouse.x;
                        lastY = mouse.y;
                    } else {
                        return;
                    }
                }
                if (draggedObject !== null) {
                    var dx = mouse.x - lastX;
                    var dy = mouse.y - lastY;
                    draggedObject.x -= 5 * dy;
                    draggedObject.y -= 5 * dx;
                    lastX = mouse.x;
                    lastY = mouse.y;
                    if (draggedObject === robotManual && robotManualWindow.visible) {
                        robotManualWindow.syncFromRobot();
                    } else if (draggedObject === ninjaManual && ninjaManualWindow.visible) {
                        ninjaManualWindow.syncFromNinja();
                    } else if (draggedObject === pamiManual && pamiManualWindow.visible) {
                        pamiManualWindow.syncFromPami();
                    } else if (obstacleWindow.visible && obstacleWindow.obstacle === draggedObject) {
                        obstacleWindow.syncFromObstacle();
                    }
                    return;
                }
                if (mouse.buttons & Qt.LeftButton) {
                    let dx = mouse.x - lastX;
                    let dy = mouse.y - lastY;
                    sceneGroup.position.x -= dy * 4;
                    sceneGroup.position.y -= dx * 4;
                    lastX = mouse.x;
                    lastY = mouse.y;
                } else if (mouse.buttons & Qt.MiddleButton) {
                    let dx = mouse.x - lastX;
                    sceneGroup.eulerRotation.z -= dx * 0.5;
                    lastX = mouse.x;
                    lastY = mouse.y;
                } else if (mouse.buttons & Qt.RightButton) {
                    let dx = mouse.x - lastX;
                    let dy = mouse.y - lastY;
                    sceneGroup.eulerRotation.y -= dy * 0.5;
                    sceneGroup.eulerRotation.x += dx * 0.5;
                    lastX = mouse.x;
                    lastY = mouse.y;
                }
            }
            onPressed: function (mouse) {
                lastX = mouse.x;
                lastY = mouse.y;
                clickCandidate = null;
                clickPressX = mouse.x;
                clickPressY = mouse.y;
                draggedObject = null;
                var result = view.pick(mouse.x, mouse.y);
                if (!result.objectHit || mouse.button !== Qt.LeftButton) {
                    return;
                }
                var hitNode = result.objectHit;
                while (hitNode && hitNode !== sceneGroup) {
                    if (hitNode.objectName === "robotManual") {
                        clickCandidate = robotManual;
                        clickPressX = mouse.x;
                        clickPressY = mouse.y;
                        break;
                    }
                    if (hitNode.objectName === "ninjaManual") {
                        clickCandidate = ninjaManual;
                        clickPressX = mouse.x;
                        clickPressY = mouse.y;
                        break;
                    }
                    if (hitNode.objectName === "pamiManual") {
                        clickCandidate = pamiManual;
                        clickPressX = mouse.x;
                        clickPressY = mouse.y;
                        break;
                    }
                    if (hitNode.objectName && hitNode.objectName.indexOf("obstacle_") === 0 && hitNode.objectName.indexOf("_base") === -1 && hitNode.objectName.indexOf("_beacon") === -1) {
                        clickCandidate = hitNode;
                        clickPressX = mouse.x;
                        clickPressY = mouse.y;
                        break;
                    }
                    hitNode = hitNode.parent;
                }
            }
            onReleased: function (mouse) {
                if (draggedObject !== null) {
                    if (draggedObject.dragging !== undefined) {
                        draggedObject.dragging = false;
                    }
                    draggedObject = null;
                } else if (clickCandidate === robotManual && mouse.button === Qt.LeftButton) {
                    view.openRobotManualDialog();
                } else if (clickCandidate === ninjaManual && mouse.button === Qt.LeftButton) {
                    view.openNinjaManualDialog();
                } else if (clickCandidate === pamiManual && mouse.button === Qt.LeftButton) {
                    view.openPamiManualDialog();
                } else if (clickCandidate && clickCandidate.objectName && clickCandidate.objectName.indexOf("obstacle_") === 0 && mouse.button === Qt.LeftButton) {
                    view.openObstacleConfig(clickCandidate);
                }
                clickCandidate = null;
            }
        }

        RobotManualWindow {
            id: robotManualWindow

            parentWindow: view.Window.window
            robot: robotManual
            settings: robotManual.windowSettings
        }

        NinjaManualWindow {
            id: ninjaManualWindow

            ninja: ninjaManual
            parentWindow: view.Window.window
            settings: ninjaManual.windowSettings
        }

        PamiManualWindow {
            id: pamiManualWindow

            pami: pamiManual
            parentWindow: view.Window.window
            settings: pamiManual.windowSettings
        }

        ObstacleWindow {
            id: obstacleWindow

            parentWindow: view.Window.window
            settings: view.obstacleSettings
        }

        Node {
            id: orderRobotGroup

            eulerRotation: sceneGroup.eulerRotation
            position: sceneGroup.position
            scale: sceneGroup.scale
            visible: !sceneRoot.showLivePip && !sceneRoot.showManualPip
        }

        Timer {
            id: lidarTimer

            interval: view.lidarTimerInterval
            repeat: true
            running: view.virtualDetector

            onTriggered: {
                if (!view.lidarRayNodes || view.lidarRayNodes.length === 0) {
                    return;
                }
                for (let i = 0; i < view.lidarRayBatch; ++i) {
                    const node = view.lidarRayNodes[view.lidarRayIndex];
                    if (node) {
                        node.pick();
                    }
                    view.lidarRayIndex = (view.lidarRayIndex + 1) % view.lidarRayNodes.length;
                }
                view.postLidarUpdate();
            }
        }

        WheelHandler {
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            target: view

            onWheel: function (event) {
                if (event.angleDelta && event.angleDelta.y !== undefined) {
                    sceneGroup.position.z += event.angleDelta.y > 0 ? -100 : 100;
                    event.accepted = true;
                }
            }
        }
    }

    View3D {
        id: pipView

        anchors.margins: 20
        anchors.right: parent.right
        anchors.top: parent.top
        camera: (view.liveRobotNode && view.liveRobotNode.camera) ? view.liveRobotNode.camera : null
        height: 240
        importScene: sceneGroup
        objectName: "pipView"
        visible: sceneRoot.showLivePip && view.liveRobotNode && view.virtualPlanner
        width: 320

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "black"
        }

        Rectangle {
            anchors.fill: parent
            border.color: "white"
            border.width: 2
            color: "transparent"
        }
    }

    MediaPlayer {
        id: player

        audioOutput: null
        autoPlay: true
        source: (sceneRoot.showLivePip && !view.virtualPlanner) ? sceneRoot.videoStreamUrl : ""
        videoOutput: videoOutput
    }

    VideoOutput {
        id: videoOutput

        anchors.fill: pipView
        visible: sceneRoot.showLivePip && !view.virtualPlanner && sceneRoot.videoStreamUrl !== ""

        Rectangle {
            anchors.fill: parent
            border.color: "white"
            border.width: 2
            color: "transparent"
        }
    }

    View3D {
        id: manualPipView

        anchors.bottom: parent.bottom
        anchors.margins: 20
        anchors.right: parent.right
        camera: robotManual.camera
        height: 240
        importScene: sceneGroup
        visible: sceneRoot.showManualPip
        width: 320

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "black"
        }

        Rectangle {
            anchors.fill: parent
            border.color: "white"
            border.width: 2
            color: "transparent"
        }
    }
}
