import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick3D
import ".."

Window {
    id: pamiManualWindow

    property bool hasShown: false
    property Node pami: null
    property var parentWindow: null
    property var settings: null
    property bool updating: false

    function showPanel() {
        var target = pamiManualWindow.pami;
        if (!target) {
            return;
        }
        syncFromPami();
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

    function syncFromPami() {
        var target = pamiManualWindow.pami;
        if (!target) {
            return;
        }
        updating = true;
        xInput.realValue = target.x !== undefined ? target.x : 0;
        yInput.realValue = target.y !== undefined ? target.y : 0;
        var currentRot = target.eulerRotation;
        angleInput.realValue = currentRot ? currentRot.z : 0;
        updating = false;
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
    title: "Pami"
    visible: false

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

        DoubleSpinBox {
            id: xInput

            decimals: 0
            editable: true
            implicitWidth: 100
            realFrom: -2000
            realStepSize: 10
            realTo: 2000

            onRealValueChanged: {
                var target = pamiManualWindow.pami;
                if (!pamiManualWindow.updating && target) {
                    target.x = realValue;
                }
            }
        }

        Label {
            color: "white"
            height: yInput.implicitHeight
            text: "Y"
            verticalAlignment: Text.AlignVCenter
        }

        DoubleSpinBox {
            id: yInput

            decimals: 0
            editable: true
            implicitWidth: 100
            realFrom: -2500
            realStepSize: 10
            realTo: 2500

            onRealValueChanged: {
                var target = pamiManualWindow.pami;
                if (!pamiManualWindow.updating && target) {
                    target.y = realValue;
                }
            }
        }

        Label {
            color: "white"
            height: angleInput.implicitHeight
            text: "Angle"
            verticalAlignment: Text.AlignVCenter
        }

        DoubleSpinBox {
            id: angleInput

            decimals: 0
            editable: true
            implicitWidth: 100
            realFrom: -360
            realStepSize: 2
            realTo: 360

            onRealValueChanged: {
                var target = pamiManualWindow.pami;
                if (!pamiManualWindow.updating && target) {
                    var currentRot = target.eulerRotation || Qt.vector3d();
                    target.eulerRotation = Qt.vector3d(currentRot.x, currentRot.y, realValue);
                }
            }
        }
    }
}
