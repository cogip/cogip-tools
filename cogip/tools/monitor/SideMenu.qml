pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: menuRoot

    property bool isConnected: false
    property var socketClient: null
    property var toolMenu: ({
            name: "",
            entries: []
        })

    spacing: 0

    // Collapsible Side Panel
    Rectangle {
        id: sidePanel

        property bool expanded: true
        property string filterText: ""

        Layout.fillHeight: true
        Layout.preferredWidth: expanded ? 260 : 0
        clip: true
        color: "#202020"

        Behavior on Layout.preferredWidth {
            NumberAnimation {
                duration: 250
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            visible: sidePanel.width > 50 // Hide content during collapse

            // Header
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                color: "#2a2a2a"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Label {
                        Layout.fillWidth: true
                        color: "#f0f0f0"
                        elide: Text.ElideRight
                        font.bold: true
                        font.pixelSize: 18
                        text: menuRoot.toolMenu && menuRoot.toolMenu.name ? menuRoot.toolMenu.name : "Menu"
                    }

                    ToolButton {
                        id: collapseButton

                        ToolTip.text: "Collapse Menu"
                        ToolTip.visible: hovered
                        font.pixelSize: 16
                        text: "◀"

                        background: Rectangle {
                            color: collapseButton.hovered ? "#3a3a3a" : "transparent"
                            radius: 4
                        }

                        onClicked: sidePanel.expanded = false
                    }
                }
            }

            // Search Bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                color: "transparent"
                visible: menuRoot.toolMenu && menuRoot.toolMenu.entries && menuRoot.toolMenu.entries.length > 5

                TextField {
                    id: searchField

                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 2
                    color: "#ffffff"
                    placeholderText: "Search commands..."
                    width: parent.width - 20

                    background: Rectangle {
                        border.color: searchField.activeFocus ? palette.highlight : "#404040"
                        color: "#303030"
                        radius: 6
                    }

                    onTextChanged: sidePanel.filterText = text.toLowerCase()

                    Label {
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#888888"
                        text: "🔍"
                    }
                }
            }

            // Menu List
            ListView {
                id: menuListView

                property var rawEntries: menuRoot.toolMenu && menuRoot.toolMenu.entries ? menuRoot.toolMenu.entries : []

                Layout.fillHeight: true
                Layout.fillWidth: true
                clip: true
                model: {
                    if (sidePanel.filterText === "")
                        return rawEntries;
                    return rawEntries.filter(entry => entry.desc.toLowerCase().includes(sidePanel.filterText));
                }

                ScrollBar.vertical: ScrollBar {
                    active: menuListView.moving || menuListView.contentHeight > menuListView.height
                    policy: ScrollBar.AsNeeded
                }
                delegate: ItemDelegate {
                    id: menuDelegate

                    required property var modelData

                    height: 44
                    text: modelData.desc
                    width: menuListView.width

                    background: Rectangle {
                        anchors.bottomMargin: 3
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        anchors.topMargin: 3
                        border.color: {
                            if (menuDelegate.pressed)
                                return palette.highlight;
                            if (menuDelegate.hovered)
                                return "#555555";
                            return "#353535";
                        }
                        border.width: 1
                        color: {
                            if (menuDelegate.pressed)
                                return palette.highlight;
                            if (menuDelegate.hovered)
                                return "#383838";
                            return "#2a2a2a";
                        }
                        radius: 6
                    }
                    contentItem: Text {
                        color: menuDelegate.pressed ? "#ffffff" : (menuDelegate.enabled ? "#eeeeee" : "#888888")
                        elide: Text.ElideRight
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        leftPadding: 16
                        text: menuDelegate.text
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        if (menuRoot.socketClient) {
                            menuRoot.socketClient.tool_command(modelData.cmd);
                        }
                    }
                }
            }

            // Status / Empty State
            Label {
                Layout.fillWidth: true
                Layout.margins: 20
                color: "#888888"
                font.italic: true
                horizontalAlignment: Text.AlignHCenter
                text: menuRoot.isConnected ? "No commands found." : "Waiting for connection…"
                visible: menuListView.count === 0
                wrapMode: Text.WordWrap
            }
        }
    }

    // Collapsed State Activator
    Rectangle {
        Layout.fillHeight: true
        Layout.preferredWidth: sidePanel.expanded ? 0 : 32
        clip: true
        color: "#252525"
        visible: !sidePanel.expanded

        Behavior on Layout.preferredWidth {
            NumberAnimation {
                duration: 250
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            ToolButton {
                id: expandButton

                Layout.fillWidth: true
                Layout.preferredHeight: 50
                font.pixelSize: 16
                text: "▶"

                background: Rectangle {
                    color: expandButton.hovered ? "#3a3a3a" : "transparent"
                }

                onClicked: sidePanel.expanded = true
            }

            Item {
                Layout.fillHeight: true
            }

            // Vertical Text for Menu Name when collapsed
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 100 // Reserve space for rotated text

                Text {
                    anchors.centerIn: parent
                    color: "#aaaaaa"
                    font.bold: true
                    font.pixelSize: 14
                    rotation: -90
                    text: menuRoot.toolMenu && menuRoot.toolMenu.name ? menuRoot.toolMenu.name : "Menu"
                }
            }
        }
    }
}
