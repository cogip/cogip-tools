import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "."

Window {
    id: obstacleWindows

    property bool hasShown: false
    property Obstacle obstacle: null
    property var parentWindow: null
    property var settings: null
    property bool updating: false

    function showPanel(obstacle) {
        obstacleWindows.obstacle = obstacle;
        if (!obstacle) {
            return;
        }
        syncFromObstacle();
        if (!visible) {
            if (settings && settings.windowX !== -1 && settings.windowY !== -1) {
                x = settings.windowX;
                y = settings.windowY;
            } else if (parentWindow) {
                x = parentWindow.x + (parentWindow.width - width) / 2;
                y = parentWindow.y + (parentWindow.height - height) / 2;
            }
        }
        visible = true;
        raise();
        if (requestActivate) {
            requestActivate();
        }
    }

    function syncFromObstacle() {
        var target = obstacleWindows.obstacle;
        if (!target) {
            return;
        }
        updating = true;
        xInput.value = target.x !== undefined ? target.x : 0;
        yInput.value = target.y !== undefined ? target.y : 0;
        var currentRot = target.eulerRotation;
        angleInput.value = currentRot ? currentRot.z : 0;
        widthInput.value = target.baseWidth !== undefined ? target.baseWidth : 0;
        lengthInput.value = target.baseLength !== undefined ? target.baseLength : 0;
        updating = false;
    }

    function updateObstacleAngle(value) {
        if (updating) {
            return;
        }
        var target = obstacleWindows.obstacle;
        if (target) {
            var currentRot = target.eulerRotation || Qt.vector3d();
            target.eulerRotation = Qt.vector3d(currentRot.x, currentRot.y, value);
        }
    }

    function updateObstacleLength(value) {
        if (updating) {
            return;
        }
        var target = obstacleWindows.obstacle;
        if (target) {
            target.baseLength = value;
        }
    }

    function updateObstacleWidth(value) {
        if (updating) {
            return;
        }
        var target = obstacleWindows.obstacle;
        if (target) {
            target.baseWidth = value;
        }
    }

    function updateObstacleX(value) {
        if (updating) {
            return;
        }
        var target = obstacleWindows.obstacle;
        if (target) {
            target.x = value;
        }
    }

    function updateObstacleY(value) {
        if (updating) {
            return;
        }
        var target = obstacleWindows.obstacle;
        if (target) {
            target.y = value;
        }
    }

    color: Qt.rgba(0.2, 0.2, 0.2, 0.92)
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
    maximumHeight: grid.implicitHeight + 30
    maximumWidth: grid.implicitWidth + 30
    minimumHeight: grid.implicitHeight + 30
    minimumWidth: grid.implicitWidth + 30
    modality: Qt.NonModal
    palette.accent: "#000000"
    palette.alternateBase: "#272727"
    palette.base: "#2a2a2a"
    palette.button: "#2a2a2a"
    palette.buttonText: "#ffffff"
    palette.dark: "#252525"
    palette.highlight: "#e95420"
    palette.highlightedText: "#ffffff"
    palette.light: "#343434"
    palette.mid: "#2f2f2f"
    palette.midlight: "#2f2f2f"
    palette.placeholderText: "#9b9b9b"
    palette.shadow: "#020202"
    palette.text: "#ffffff"
    palette.window: "#2a2a2a"
    palette.windowText: "#ffffff"
    title: "Obstacle"
    visible: false

    onObstacleChanged: {
        if (visible) {
            syncFromObstacle();
        }
    }
    onVisibleChanged: {
        if (visible) {
            hasShown = true;
        } else if (hasShown && settings) {
            settings.windowX = x;
            settings.windowY = y;
        }
    }
    onXChanged: {
        if (visible && hasShown && settings) {
            settings.windowX = x;
        }
    }
    onYChanged: {
        if (visible && hasShown && settings) {
            settings.windowY = y;
        }
    }

    Grid {
        id: grid

        anchors.fill: parent
        anchors.margins: 16
        columns: 2
        spacing: 12

        Label {
            color: "white"
            height: xInput.implicitHeight
            text: "X"
            verticalAlignment: Text.AlignVCenter
        }

        SpinBox {
            id: xInput

            editable: true
            from: -2000
            implicitWidth: 100
            stepSize: 10
            to: 2000

            onValueChanged: obstacleWindows.updateObstacleX(value)
        }

        Label {
            color: "white"
            height: yInput.implicitHeight
            text: "Y"
            verticalAlignment: Text.AlignVCenter
        }

        SpinBox {
            id: yInput

            editable: true
            from: -2500
            implicitWidth: 100
            stepSize: 10
            to: 2500

            onValueChanged: obstacleWindows.updateObstacleY(value)
        }

        Label {
            color: "white"
            height: angleInput.implicitHeight
            text: "Angle"
            verticalAlignment: Text.AlignVCenter
        }

        SpinBox {
            id: angleInput

            editable: true
            from: -360
            implicitWidth: 100
            stepSize: 1
            to: 360

            onValueChanged: obstacleWindows.updateObstacleAngle(value)
        }

        Label {
            color: "white"
            height: widthInput.implicitHeight
            text: "Width"
            verticalAlignment: Text.AlignVCenter
        }

        SpinBox {
            id: widthInput

            editable: true
            from: 50
            implicitWidth: 100
            stepSize: 10
            to: 2000

            onValueChanged: obstacleWindows.updateObstacleWidth(value)
        }

        Label {
            color: "white"
            height: lengthInput.implicitHeight
            text: "Length"
            verticalAlignment: Text.AlignVCenter
        }

        SpinBox {
            id: lengthInput

            editable: true
            from: 50
            implicitWidth: 100
            stepSize: 10
            to: 2000

            onValueChanged: obstacleWindows.updateObstacleLength(value)
        }
    }
}
