pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Rectangle {
    id: statusFooter

    property bool isConnected: false
    property var liveRobotNode: null
    property var orderRobotNode: null
    property alias starterCheckboxItem: starterCheckbox
    property bool starterChecked: false
    property bool syncingStarter: false
    property bool virtualPlanner: false

    color: "#333333"
    height: 43

    Component.onCompleted: starterCheckbox.checked = starterChecked
    onStarterCheckedChanged: {
        if (statusFooter.syncingStarter) {
            return;
        }
        statusFooter.syncingStarter = true;
        starterCheckbox.checked = starterChecked;
        statusFooter.syncingStarter = false;
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 6
        anchors.rightMargin: 1
        spacing: 8

        Rectangle {
            color: statusFooter.isConnected ? "#27ae60" : "#c0392b"
            implicitHeight: 12
            implicitWidth: 12
            radius: 6
        }

        Text {
            color: "white"
            font.pixelSize: 14
            horizontalAlignment: Text.AlignLeft
            objectName: "connectionStatusText"
            text: statusFooter.isConnected ? "Connected" : "Not connected"
        }

        Item {
            Layout.fillWidth: true
        }

        Rectangle {
            id: poseTable

            Layout.alignment: Qt.AlignVCenter | Qt.AlignCenter
            border.color: "#555555"
            border.width: 1
            color: "transparent"
            implicitHeight: poseColumn.implicitHeight
            implicitWidth: poseColumn.implicitWidth
            objectName: "robotPoseTable"
            radius: 2

            Column {
                id: poseColumn

                property var rows: (function () {
                        const labels = ["X", "Y", "θ"];

                        function fallbackRow() {
                            return labels.map(function (label, i) {
                                return {
                                    label: label,
                                    value: label === "θ" ? "--°" : "--",
                                    showSeparator: i < labels.length - 1,
                                    isRowLabel: false
                                };
                            });
                        }

                        function formatNumber(value) {
                            const numeric = Number(value);
                            return isNaN(numeric) ? "--" : numeric.toFixed(0);
                        }

                        function buildRow(node) {
                            if (!node) {
                                return fallbackRow();
                            }
                            const xEntry = {
                                label: "X",
                                value: formatNumber(node.x),
                                isRowLabel: false
                            };
                            const yEntry = {
                                label: "Y",
                                value: formatNumber(node.y),
                                isRowLabel: false
                            };
                            let angleValue = "--°";
                            if (node.eulerRotation && node.eulerRotation.z !== undefined) {
                                const angleNumeric = Number(node.eulerRotation.z);
                                angleValue = isNaN(angleNumeric) ? "--°" : angleNumeric.toFixed(0) + "°";
                            }
                            const thetaEntry = {
                                label: "θ",
                                value: angleValue,
                                isRowLabel: false
                            };
                            const entries = [xEntry, yEntry, thetaEntry];
                            entries.forEach(function (entry, i) {
                                entry.showSeparator = i < entries.length - 1;
                            });
                            return entries;
                        }

                        const liveEntries = buildRow(statusFooter.liveRobotNode);
                        const orderEntries = buildRow(statusFooter.orderRobotNode);

                        function addRowLabel(labelText, entries) {
                            const labelledEntries = entries.slice();
                            labelledEntries.unshift({
                                label: labelText,
                                value: "",
                                isRowLabel: true,
                                showSeparator: true
                            });
                            if (labelledEntries.length > 1) {
                                labelledEntries[labelledEntries.length - 1].showSeparator = false;
                            }
                            return labelledEntries;
                        }

                        return [
                            {
                                entries: addRowLabel("Current", liveEntries),
                                showDivider: true
                            },
                            {
                                entries: addRowLabel("Order", orderEntries),
                                showDivider: false
                            }
                        ];
                    })()

                anchors.fill: parent
                anchors.margins: 0
                spacing: 0

                Repeater {
                    model: poseColumn.rows

                    delegate: Item {
                        id: poseRowItem

                        required property int index
                        required property var modelData

                        implicitHeight: rowContent.implicitHeight + (poseRowItem.modelData.showDivider ? divider.height : 0)
                        implicitWidth: rowContent.implicitWidth

                        Row {
                            id: rowContent

                            property var entries: poseRowItem.modelData.entries

                            spacing: 0

                            Repeater {
                                model: rowContent.entries

                                delegate: Item {
                                    id: poseCell

                                    property real cellHeight: Math.max(labelText.implicitHeight, valueLabel.visible ? valueLabel.implicitHeight : 0)
                                    required property int index
                                    required property var modelData

                                    implicitHeight: cellRow.implicitHeight
                                    implicitWidth: cellRow.implicitWidth

                                    Row {
                                        id: cellRow

                                        height: poseCell.cellHeight
                                        spacing: 0
                                        y: (poseCell.cellHeight - cellRow.implicitHeight) / 2

                                        Label {
                                            id: labelText

                                            bottomPadding: 2
                                            color: "white"
                                            font.bold: poseCell.modelData.isRowLabel
                                            font.pixelSize: 14
                                            horizontalAlignment: Text.AlignLeft
                                            leftPadding: poseCell.modelData.isRowLabel ? 8 : 6
                                            rightPadding: 6
                                            text: poseCell.modelData.label
                                            topPadding: 2
                                            verticalAlignment: Text.AlignVCenter
                                            width: poseCell.modelData.isRowLabel ? 70 : implicitWidth
                                        }

                                        Label {
                                            id: valueLabel

                                            bottomPadding: 2
                                            color: "white"
                                            font.bold: false
                                            font.pixelSize: 14
                                            horizontalAlignment: Text.AlignRight
                                            leftPadding: 6
                                            rightPadding: 6
                                            text: poseCell.modelData.value
                                            topPadding: 2
                                            verticalAlignment: Text.AlignVCenter
                                            visible: !poseCell.modelData.isRowLabel
                                            width: valueLabel.visible ? 45 : 0

                                            background: Rectangle {
                                                color: "#4a4a4a"
                                                radius: 3
                                            }
                                        }
                                    }

                                    Rectangle {
                                        color: "#555555"
                                        height: poseCell.cellHeight
                                        visible: poseCell.modelData.showSeparator
                                        width: 1
                                        x: cellRow.implicitWidth
                                        y: (poseCell.cellHeight - height) / 2
                                    }
                                }
                            }
                        }

                        Rectangle {
                            id: divider

                            color: "#555555"
                            height: 1
                            visible: poseRowItem.modelData.showDivider
                            width: rowContent.implicitWidth
                            y: rowContent.implicitHeight
                        }
                    }
                }
            }
        }

        Rectangle {
            id: starterRect

            Layout.preferredHeight: parent.implicitHeight
            Layout.preferredWidth: starterLabelRow.implicitWidth
            border.color: "#555555"
            border.width: 1
            color: "transparent"
            radius: 2

            Column {
                id: starterColumn

                anchors.fill: parent
                anchors.margins: 0
                spacing: 0

                Row {
                    id: starterLabelRow

                    spacing: 0

                    Label {
                        id: starterLabelText

                        bottomPadding: 2
                        color: "white"
                        font.bold: true
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        leftPadding: 6
                        rightPadding: 6
                        text: "Starter"
                        topPadding: 2
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Row {
                    id: starterCheckboxRow

                    anchors.horizontalCenter: parent.horizontalCenter
                    height: starterCheckbox.implicitHeight
                    spacing: 0

                    CheckBox {
                        id: starterCheckbox

                        anchors.verticalCenter: parent.verticalCenter
                        enabled: statusFooter.virtualPlanner
                        objectName: "starterCheckbox"
                        padding: 0
                        text: ""

                        onClicked: {
                            if (statusFooter.syncingStarter) {
                                return;
                            }
                            const win = Window.window;
                            if (!win) {
                                return;
                            }
                            // qmllint disable missing-property
                            const handler = win.handleStarterCheckboxClicked;
                            // qmllint enable missing-property
                            if (!handler) {
                                return;
                            }
                            handler.call(win, checked);
                        }
                    }
                }
            }
        }
    }
}
