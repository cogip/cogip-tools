pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: window

    property var configWindows: ({})
    property bool isConnected: false
    property url lastObstacleFile: ""
    property var obstacleStorage: null
    property var socketClient: null
    property bool starterChecked: false
    property var toolMenu: ({
            name: "",
            entries: []
        })
    property var wizardWindow: null

    function closeAllConfigWindows() {
        for (const key in configWindows) {
            if (!Object.prototype.hasOwnProperty.call(configWindows, key)) {
                continue;
            }
            const windowInstance = configWindows[key];
            // qmllint disable missing-property
            if (windowInstance && windowInstance.close) {
                windowInstance.close();
            }
            // qmllint enable missing-property
        }
        configWindows = ({});
    }

    function closeWizardWindow() {
        if (!wizardWindow) {
            return;
        }

        const instance = wizardWindow;
        wizardWindow = null;

        if (instance.destroy) {
            instance.destroy();
        } else if (instance.close) {
            instance.close();
        }
    }

    function configWindowKey(config) {
        if (!config) {
            return "";
        }
        const ns = config.namespace !== undefined && config.namespace !== null ? config.namespace : "";
        const title = config.title !== undefined && config.title !== null ? config.title : "";
        return ns + "::" + title;
    }

    function fileNameFromUrl(url) {
        if (!url) {
            return "";
        }
        const normalized = normalizeFileUrl(url);
        const index = normalized.lastIndexOf("/");
        if (index < 0) {
            return normalized;
        }
        return normalized.substring(index + 1);
    }

    function folderFromUrl(url) {
        if (!url) {
            return "";
        }
        const normalized = normalizeFileUrl(url);
        const index = normalized.lastIndexOf("/");
        if (index <= 7) {
            return normalized;
        }
        return normalized.substring(0, index);
    }

    function handleStarterCheckboxClicked(value) {
        if (window.starterChecked === value) {
            // Value already propagated from UI; nothing to do.
            return;
        }
        window.starterChecked = value;
        if (window.socketClient) {
            if (window.socketClient.starter_changed) {
                window.socketClient.starter_changed(value);
            }
        }
    }

    function loadObstaclesFromFile(fileUrl) {
        const data = window.obstacleStorage.read_obstacles(fileUrl);
        if (!data) {
            console.warn("Failed to load obstacles from", fileUrl);
            return;
        }
        scene.importObstacles(data);
        window.lastObstacleFile = fileUrl;
    }

    function normalizeFileUrl(fileUrl) {
        if (!fileUrl) {
            return "";
        }
        if (typeof fileUrl === "string") {
            return fileUrl;
        }
        if (fileUrl.toString) {
            return fileUrl.toString();
        }
        return "";
    }

    function openConfigWindow(config) {
        if (!config) {
            return;
        }
        const key = configWindowKey(config);
        var existing = configWindows[key];
        if (existing) {
            existing.setConfig(config);
            if (!existing.visible) {
                existing.visible = true;
            }
            existing.raise();
            existing.requestActivate();
            return;
        }

        const created = configWindowComponent.createObject(window, {
            socketClient: window.socketClient,
            configKey: key
        });
        if (!created) {
            console.error("Failed to create ConfigWindow:", configWindowComponent.errorString());
            return;
        }

        // qmllint disable missing-property
        if (created && created.setConfig) {
            created.setConfig(config);
        }
        if (created && created.show) {
            created.show();
        }
        if (created && created.raise) {
            created.raise();
        }
        if (created && created.requestActivate) {
            created.requestActivate();
        }
        configWindows[key] = created;
        if (created && created.windowClosed) {
            created.windowClosed.connect(function () {
                delete configWindows[key];
            });
        }
    // qmllint enable missing-property
    }

    function openLoadObstaclesDialog() {
        setupDialogDefaults(loadObstaclesDialog, true);
        loadObstaclesDialog.open();
    }

    function openSaveObstaclesDialog() {
        setupDialogDefaults(saveObstaclesDialog, false);
        saveObstaclesDialog.open();
    }

    function openWizardWindow(payload) {
        if (!payload) {
            return;
        }
        closeWizardWindow();

        const created = wizardWindowComponent.createObject(window, {
            socketClient: window.socketClient,
            centerTarget: window,
            wizardData: payload
        });

        if (!created) {
            console.error("Failed to create Wizard window:", wizardWindowComponent.errorString());
            return;
        }

        created.wizardClosed.connect(function () {
            if (wizardWindow === created) {
                wizardWindow = null;
            }
        });

        wizardWindow = created;
    }

    function saveObstaclesToFile(fileUrl) {
        const payload = scene.exportObstacles();
        const success = window.obstacleStorage.write_obstacles(fileUrl, payload);
        if (!success) {
            console.error("Failed to save obstacles to", fileUrl);
            return;
        }
        window.lastObstacleFile = fileUrl;
    }

    function setupDialogDefaults(dialog, requireExisting) {
        if (!window.lastObstacleFile) {
            return;
        }
        const folderUrl = folderFromUrl(window.lastObstacleFile);
        if (folderUrl) {
            dialog.currentFolder = folderUrl;
        }
        const exists = Boolean(window.obstacleStorage.file_exists(window.lastObstacleFile));
        if (requireExisting && !exists) {
            return;
        }
        if (exists) {
            dialog.selectedFile = window.lastObstacleFile;
        } else if (!requireExisting) {
            const name = fileNameFromUrl(window.lastObstacleFile);
            let candidate = "";
            if (folderUrl && name) {
                candidate = folderUrl + "/" + name;
            } else if (name) {
                candidate = name;
            }
            if (candidate) {
                dialog.selectedFile = candidate;
            }
        }
    }

    height: 720
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
    title: "COGIP Monitor"
    visible: true
    width: 1280

    footer: Footer {
        id: statusBar

        isConnected: window.isConnected
        liveRobotNode: scene.liveRobotNode
        objectName: "statusBar"
        orderRobotNode: scene.orderRobotNode
        starterChecked: window.starterChecked
        virtualPlanner: scene.virtualPlanner
    }
    header: ToolBar {
        objectName: "header"

        RowLayout {
            ToolButton {
                id: addObstacleButton

                ToolTip.delay: 250
                ToolTip.text: "Add obstacle"
                ToolTip.visible: hovered
                display: AbstractButton.IconOnly
                icon.source: "../../../assets/add.png"
                text: "+"

                onClicked: {
                    if (scene) {
                        scene.addObstacle();
                    }
                }
            }

            Switch {
                id: groundTextureSwitch

                checked: scene.groundTextureSource === scene.gridGroundTexture
                text: "Grid"

                indicator: Rectangle {
                    border.color: groundTextureSwitch.checked ? "#353535" : "#888888"
                    color: groundTextureSwitch.checked ? "#888888" : "#353535"
                    implicitHeight: 18
                    implicitWidth: 32
                    radius: 13
                    x: groundTextureSwitch.leftPadding
                    y: parent.height / 2 - height / 2

                    Rectangle {
                        border.color: groundTextureSwitch.checked ? "#888888" : "#353535"
                        color: groundTextureSwitch.checked ? "#353535" : "#888888"
                        height: 14
                        radius: 13
                        width: 14
                        x: groundTextureSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                    }
                }

                onToggled: scene.groundTextureSource = checked ? scene.gridGroundTexture : scene.tableGroundTexture
            }

            Switch {
                id: livePipSwitch

                checked: scene.showLivePip
                text: "Live Cam"

                indicator: Rectangle {
                    border.color: livePipSwitch.checked ? "#353535" : "#888888"
                    color: livePipSwitch.checked ? "#888888" : "#353535"
                    implicitHeight: 18
                    implicitWidth: 32
                    radius: 13
                    x: livePipSwitch.leftPadding
                    y: parent.height / 2 - height / 2

                    Rectangle {
                        border.color: livePipSwitch.checked ? "#888888" : "#353535"
                        color: livePipSwitch.checked ? "#353535" : "#888888"
                        height: 14
                        radius: 13
                        width: 14
                        x: livePipSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                    }
                }

                onToggled: scene.showLivePip = checked
            }

            Switch {
                id: manualPipSwitch

                checked: scene.showManualPip
                text: "Manual Cam"

                indicator: Rectangle {
                    border.color: manualPipSwitch.checked ? "#353535" : "#888888"
                    color: manualPipSwitch.checked ? "#888888" : "#353535"
                    implicitHeight: 18
                    implicitWidth: 32
                    radius: 13
                    x: manualPipSwitch.leftPadding
                    y: parent.height / 2 - height / 2

                    Rectangle {
                        border.color: manualPipSwitch.checked ? "#888888" : "#353535"
                        color: manualPipSwitch.checked ? "#353535" : "#888888"
                        height: 14
                        radius: 13
                        width: 14
                        x: manualPipSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                    }
                }

                onToggled: scene.showManualPip = checked
            }
        }
    }
    menuBar: MenuBar {
        objectName: "menuBar"

        Menu {
            objectName: "fileMenu"
            title: "&File"

            Action {
                shortcut: "Ctrl+Q"
                text: "&Exit"

                onTriggered: Qt.quit()
            }
        }

        Menu {
            objectName: "obstacleMenu"
            title: "Obstacles"

            Action {
                text: "Load Obstacles…"

                onTriggered: window.openLoadObstaclesDialog()
            }

            Action {
                text: "Save Obstacles…"

                onTriggered: window.openSaveObstaclesDialog()
            }
        }
    }

    onSocketClientChanged: {
        if (wizardWindow) {
            wizardWindow.socketClient = window.socketClient;
            wizardWindow.centerTarget = window;
        }
    }

    Component {
        id: configWindowComponent

        ConfigWindow {
        }
    }

    Component {
        id: wizardWindowComponent

        Wizard {
            socketClient: window.socketClient
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        SideMenu {
            isConnected: window.isConnected
            socketClient: window.socketClient
            toolMenu: window.toolMenu
        }

        Scene {
            id: scene

            Layout.fillHeight: true
            Layout.fillWidth: true
            objectName: "Scene"
        }
    }

    Connections {
        function onSignal_config_request(config) {
            window.openConfigWindow(config);
        }

        target: window.socketClient
    }

    Connections {
        function onVirtualPlannerChanged() {
            if (!scene.virtualPlanner) {
                window.starterChecked = false;
            }
        }

        target: scene
    }

    FileDialog {
        id: loadObstaclesDialog

        fileMode: FileDialog.OpenFile
        nameFilters: ["Obstacle JSON (*.json)", "All Files (*)"]
        title: "Load Obstacles"

        onAccepted: {
            if (selectedFile) {
                window.loadObstaclesFromFile(selectedFile);
            }
        }
    }

    FileDialog {
        id: saveObstaclesDialog

        defaultSuffix: "json"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Obstacle JSON (*.json)", "All Files (*)"]
        title: "Save Obstacles"

        onAccepted: {
            if (selectedFile) {
                window.saveObstaclesToFile(selectedFile);
            }
        }
    }

    Item {
        id: wizardInteractionShield

        anchors.fill: parent
        visible: window.wizardWindow !== null
        z: 999

        MouseArea {
            function allowPoint(x, y) {
                if (!statusBar || !statusBar.starterCheckboxItem) {
                    return false;
                }
                var checkbox = statusBar.starterCheckboxItem;
                if (!checkbox.visible) {
                    return false;
                }
                var pos = checkbox.mapToItem(window.contentItem, 0, 0);
                return x >= pos.x && x <= pos.x + checkbox.width && y >= pos.y && y <= pos.y + checkbox.height;
            }

            function updateAcceptance(mouse) {
                mouse.accepted = !allowPoint(mouse.x, mouse.y);
            }

            acceptedButtons: Qt.AllButtons
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true

            onClicked: function (mouse) {
                updateAcceptance(mouse);
            }
            onDoubleClicked: function (mouse) {
                updateAcceptance(mouse);
            }
            onPositionChanged: function (mouse) {
                if (!allowPoint(mouse.x, mouse.y)) {
                    mouse.accepted = true;
                }
            }
            onPressed: function (mouse) {
                updateAcceptance(mouse);
            }
            onReleased: function (mouse) {
                updateAcceptance(mouse);
            }
            onWheel: function (wheel) {
                if (!allowPoint(wheel.x, wheel.y)) {
                    wheel.accepted = true;
                }
            }
        }
    }
}
