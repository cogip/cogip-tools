pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Dialog {
    id: wizardDialog

    property var centerTarget: null
    readonly property bool isMessageType: wizardData.type === "message"
    property var socketClient: null
    property var wizardData: null

    signal wizardClosed

    function componentForType(typeName) {
        switch (typeName) {
        case "boolean":
            return booleanComponent;
        case "integer":
            return integerComponent;
        case "floating":
            return floatingComponent;
        case "str":
            return stringComponent;
        case "message":
            return messageComponent;
        case "choice_integer":
        case "choice_floating":
        case "choice_str":
            return choiceComponent;
        case "choice_str_group":
            return choiceStringGroupComponent;
        case "select_integer":
        case "select_floating":
        case "select_str":
            return selectComponent;
        case "camp":
            return campComponent;
        default:
            return fallbackComponent;
        }
    }

    closePolicy: Popup.NoAutoClose
    dim: true
    implicitHeight: 360
    implicitWidth: 420
    modal: false
    padding: 0
    x: (centerTarget.width - width) / 2
    y: (centerTarget.height - height) / 2

    contentItem: ColumnLayout {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        Loader {
            id: contentLoader

            Layout.fillHeight: true
            Layout.fillWidth: true
            sourceComponent: wizardDialog.componentForType(wizardDialog.wizardData.type)

            onLoaded: {
                headerLabel.text = wizardDialog.wizardData.name;
            }
        }
    }
    footer: Rectangle {
        id: footerRect

        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        border.color: "#404040"
        color: "#303030"
        implicitHeight: 40

        RowLayout {
            anchors.fill: parent
            anchors.margins: 4

            Item {
                Layout.fillWidth: true
            }

            Button {
                text: "Cancel"
                visible: !wizardDialog.isMessageType

                onClicked: wizardDialog.reject()
            }

            Button {
                text: wizardDialog.isMessageType ? "OK" : "Send"
                visible: true

                onClicked: {
                    wizardDialog.socketClient.wizard_response({
                        "type": wizardDialog.wizardData.type,
                        "name": wizardDialog.wizardData.name,
                        "value": wizardDialog.isMessageType ? "" : wizardDialog.wizardData.value,
                        "namespace": wizardDialog.wizardData.namespace
                    });
                    wizardDialog.accept();
                }
            }

            Item {
                Layout.fillWidth: true
                visible: wizardDialog.isMessageType
            }
        }
    }
    header: Rectangle {
        id: headerRect

        border.color: "#404040"
        color: "#303030"
        implicitHeight: 48

        Label {
            id: headerLabel

            Layout.alignment: Qt.AlignCenter | Qt.AlignVCenter
            anchors.fill: parent
            anchors.margins: 0
            color: "#f0f0f0"
            font.bold: true
            font.pixelSize: 20
            horizontalAlignment: Text.AlignHCenter
            text: wizardDialog.wizardData.title
            verticalAlignment: Text.AlignVCenter
        }
    }

    Component.onCompleted: wizardDialog.open()
    onClosed: wizardClosed()

    Component {
        id: booleanComponent

        ColumnLayout {
            id: booleanRoot

            CheckBox {
                id: booleanCheck

                Layout.alignment: Qt.AlignCenter
                checked: wizardDialog.wizardData.value

                indicator: Rectangle {
                    border.color: booleanCheck.checked ? "#4caf50" : "#ff3434"
                    border.width: 2
                    color: "transparent"
                    implicitHeight: 28
                    implicitWidth: 28
                    radius: 16

                    Rectangle {
                        anchors.centerIn: parent
                        color: booleanCheck.checked ? "#4caf50" : "transparent"
                        height: parent.height - 10
                        radius: 16
                        width: parent.width - 10
                    }
                }

                onCheckedChanged: {
                    wizardDialog.wizardData.value = checked;
                }
            }
        }
    }

    Component {
        id: integerComponent

        ColumnLayout {
            id: integerRoot

            DoubleSpinBox {
                id: integerSpin

                Layout.alignment: Qt.AlignCenter
                Layout.preferredWidth: 140
                decimals: 0
                editable: true
                realFrom: -1000000
                realStepSize: 1
                realTo: 1000000
                realValue: Number(wizardDialog.wizardData.value)

                onRealValueChanged: {
                    wizardDialog.wizardData.value = realValue;
                }
            }
        }
    }

    Component {
        id: floatingComponent

        ColumnLayout {
            id: floatingRoot

            DoubleSpinBox {
                id: floatSpin

                Layout.alignment: Qt.AlignCenter
                Layout.preferredWidth: 140
                decimals: 3
                editable: true
                realFrom: -1000000
                realStepSize: 0.1
                realTo: 1000000
                realValue: Number(wizardDialog.wizardData.value)

                onRealValueChanged: {
                    wizardDialog.wizardData.value = realValue;
                }
            }
        }
    }

    Component {
        id: stringComponent

        ColumnLayout {
            id: stringRoot

            Layout.fillWidth: true

            TextField {
                Layout.fillWidth: true
                Layout.leftMargin: 20
                Layout.rightMargin: 20
                text: wizardDialog.wizardData.value

                onTextChanged: {
                    wizardDialog.wizardData.value = text;
                }
            }
        }
    }

    Component {
        id: messageComponent

        ColumnLayout {
            id: messageRoot

            Layout.fillHeight: true
            Layout.fillWidth: true

            TextArea {
                Layout.fillWidth: true
                font.pixelSize: wizardDialog.wizardData.name == "Score" ? 60 : 20
                horizontalAlignment: Text.AlignHCenter
                text: wizardDialog.wizardData.value
                verticalAlignment: Text.AlignVCenter
                wrapMode: TextArea.WrapAtWordBoundaryOrAnywhere
            }
        }
    }

    Component {
        id: choiceComponent

        ColumnLayout {
            id: choiceRoot

            Item {
                Layout.fillHeight: true
            }

            ButtonGroup {
                id: choiceGroup

                exclusive: true
            }

            ScrollView {
                id: choiceScroll

                Layout.fillWidth: true
                Layout.preferredHeight: wizardDialog.height - headerRect.implicitHeight - footerRect.implicitHeight - 20
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                clip: true

                Column {
                    id: choiceColumn

                    x: (choiceScroll.availableWidth - width) / 2

                    Repeater {
                        id: choiceRepeater

                        model: wizardDialog.wizardData.choices

                        delegate: RadioButton {
                            required property var modelData

                            ButtonGroup.group: choiceGroup
                            checked: modelData === wizardDialog.wizardData.value
                            text: String(modelData)

                            onCheckedChanged: {
                                if (checked) {
                                    wizardDialog.wizardData.value = modelData;
                                }
                            }
                        }
                    }
                }
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }

    Component {
        id: choiceStringGroupComponent

        ColumnLayout {
            id: choiceStringGroupRoot

            property int currentTabIndex: 0
            property var groupMap: {
                var map = {};
                for (const entry of wizardDialog.wizardData.choices) {
                    var value = entry[0];
                    var group = entry[1];
                    var label = entry[2];
                    if (!map[group]) {
                        map[group] = Array();
                    }
                    if (value === wizardDialog.wizardData.value) {
                        currentTabIndex = Object.keys(map).indexOf(group);
                    }
                    map[group].push({
                        value: value,
                        label: label
                    });
                }
                return map;
            }

            ButtonGroup {
                id: choiceStringGroupButtons

                exclusive: true
            }

            TabBar {
                id: choiceStringGroupTabBar

                Layout.leftMargin: 5
                Layout.rightMargin: 5
                Layout.topMargin: headerRect.implicitHeight + 5
                currentIndex: choiceStringGroupRoot.currentTabIndex

                Repeater {
                    model: Object.keys(choiceStringGroupRoot.groupMap)

                    TabButton {
                        required property int index
                        required property var modelData

                        checked: index === choiceStringGroupTabBar.currentIndex
                        font.bold: true
                        font.pixelSize: 14
                        padding: 12
                        text: modelData
                        width: implicitWidth + 20

                        onClicked: choiceStringGroupTabBar.currentIndex = index
                    }
                }
            }

            StackLayout {
                id: choiceStringGroupStack

                Layout.bottomMargin: footerRect.implicitHeight + 5
                Layout.leftMargin: 5
                Layout.rightMargin: 5
                currentIndex: choiceStringGroupTabBar.currentIndex

                Repeater {
                    id: choiceStringGroupStackRepeater

                    model: Object.keys(choiceStringGroupRoot.groupMap)

                    Item {
                        id: choiceStringGroupTab

                        property var entries: choiceStringGroupRoot.groupMap[modelData]
                        required property var modelData

                        ScrollView {
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            anchors.fill: parent
                            clip: true

                            Column {
                                id: choiceStringGroupColumn

                                property var tabEntries: choiceStringGroupTab.entries

                                width: parent.width

                                Repeater {
                                    model: choiceStringGroupColumn.tabEntries

                                    delegate: RadioButton {
                                        required property var modelData

                                        ButtonGroup.group: choiceStringGroupButtons
                                        checked: String(modelData.value) === String(wizardDialog.wizardData.value)
                                        text: modelData.label

                                        onToggled: {
                                            if (checked) {
                                                wizardDialog.wizardData.value = modelData.value;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Component {
        id: selectComponent

        ColumnLayout {
            id: selectRoot

            Item {
                Layout.fillHeight: true
            }

            ScrollView {
                id: selectScroll

                Layout.fillWidth: true
                Layout.preferredHeight: wizardDialog.height - headerRect.implicitHeight - footerRect.implicitHeight - 20
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                clip: true

                Column {
                    id: selectColumn

                    x: (selectScroll.availableWidth - width) / 2

                    Repeater {
                        id: selectRepeater

                        model: wizardDialog.wizardData.choices

                        delegate: CheckBox {
                            required property var modelData

                            checked: wizardDialog.wizardData.value.includes(modelData)
                            text: String(modelData)

                            onToggled: {
                                if (checked) {
                                    wizardDialog.wizardData.value.push(modelData);
                                } else {
                                    var idx = wizardDialog.wizardData.value.indexOf(modelData);
                                    wizardDialog.wizardData.value.splice(idx, 1);
                                }
                            }
                        }
                    }
                }
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }

    Component {
        id: campComponent

        ColumnLayout {
            id: campRoot

            Layout.fillWidth: true

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                spacing: 24

                Button {
                    id: yellowButton

                    Layout.preferredHeight: 64
                    Layout.preferredWidth: 160
                    autoExclusive: true
                    checkable: true
                    checked: wizardDialog.wizardData.value === "yellow"

                    background: Rectangle {
                        border.color: yellowButton.checked ? "#ffffff" : "#5c4400"
                        border.width: yellowButton.checked ? 3 : 1
                        color: yellowButton.checked ? "#FFBF00" : "#8c6a00"
                        radius: 12
                    }

                    onToggled: {
                        if (checked) {
                            wizardDialog.wizardData.value = "yellow";
                        }
                    }
                }

                Button {
                    id: blueButton

                    Layout.preferredHeight: 64
                    Layout.preferredWidth: 160
                    autoExclusive: true
                    checkable: true
                    checked: wizardDialog.wizardData.value === "blue"

                    background: Rectangle {
                        border.color: blueButton.checked ? "#ffffff" : "#1b2f66"
                        border.width: blueButton.checked ? 3 : 1
                        color: blueButton.checked ? "#005CE6" : "#244a99"
                        radius: 12
                    }

                    onToggled: {
                        if (checked) {
                            wizardDialog.wizardData.value = "blue";
                        }
                    }
                }
            }
        }
    }

    Component {
        id: fallbackComponent

        ColumnLayout {
            id: fallbackRoot

            Layout.fillWidth: true

            Label {
                Layout.fillWidth: true
                color: "#f0f0f0"
                text: "Unsupported wizard type: " + wizardDialog.wizardData.type
                wrapMode: Text.WordWrap
            }

            TextArea {
                Layout.fillHeight: true
                Layout.fillWidth: true
                readOnly: true
                text: wizardDialog.wizardData ? JSON.stringify(wizardDialog.wizardData, null, 2) : "{}"
                wrapMode: TextArea.WrapAtWordBoundaryOrAnywhere
            }
        }
    }
}
