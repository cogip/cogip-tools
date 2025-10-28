pragma ComponentBehavior: Bound
import QtCore
import QtQml.Models

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: configWindow

    property string configEvent: "config_updated"
    property string configKey: ""
    property string configNamespace: ""
    property string configTitle: ""
    property real editorColumnWidth: 0
    property bool geometryRestored: false
    property real labelColumnWidth: 0
    property var rawConfig: ({})
    property var socketClient: null
    property bool suppressUpdates: false

    signal windowClosed

    function decimalsForStep(step) {
        const numeric = Number(step);
        if (!isFinite(numeric) || numeric <= 0) {
            return 0;
        }
        const text = numeric.toString();
        const dotIndex = text.indexOf(".");
        if (dotIndex === -1) {
            return 0;
        }
        return text.length - dotIndex - 1;
    }

    function ensureNumericFallback(reference, delta, forceInteger) {
        let value = Number(reference);
        if (!isFinite(value)) {
            value = 0;
        }
        if (forceInteger) {
            value = Math.trunc(value);
        }
        return value;
    }

    function geometryStorageKey() {
        if (configKey && configKey.length) {
            return configKey;
        }
        const ns = configNamespace || "";
        const title = configTitle || "";
        const combined = ns + "::" + title;
        return combined.length ? combined : "default";
    }

    function restoreGeometry() {
        if (geometryRestored) {
            return;
        }
        const key = geometryStorageKey();
        if (!key || !key.length) {
            geometryRestored = true;
            return;
        }
        const store = geometrySettings.storedGeometries || {};
        const stored = store[key];
        if (stored && typeof stored === "object") {
            const storedWidth = Number(stored.width);
            if (isFinite(storedWidth) && storedWidth >= configWindow.minimumWidth) {
                configWindow.width = storedWidth;
            }
            const storedHeight = Number(stored.height);
            if (isFinite(storedHeight) && storedHeight >= configWindow.minimumHeight) {
                configWindow.height = storedHeight;
            }
            const storedX = Number(stored.x);
            if (isFinite(storedX)) {
                configWindow.x = storedX;
            }
            const storedY = Number(stored.y);
            if (isFinite(storedY)) {
                configWindow.y = storedY;
            }
        }
        geometryRestored = true;
    }

    function saveGeometry() {
        const key = geometryStorageKey();
        if (!key || !key.length) {
            return;
        }
        let store = geometrySettings.storedGeometries;
        if (!store || typeof store !== "object") {
            store = {};
        }
        const nextStore = Object.assign({}, store);
        nextStore[key] = {
            x: Number(configWindow.x),
            y: Number(configWindow.y),
            width: Number(configWindow.width),
            height: Number(configWindow.height)
        };
        geometrySettings.storedGeometries = nextStore;
        geometrySettings.sync();
    }

    function setConfig(config) {
        rawConfig = config || {};
        configNamespace = rawConfig.namespace || "";
        configTitle = rawConfig.title || "";
        configEvent = rawConfig.sio_event || rawConfig.sio_events || "config_updated";
        configWindow.title = configTitle && configTitle.length ? configTitle : "Configuration";
        geometryRestored = false;

        suppressUpdates = true;
        propertiesModel.clear();

        const props = rawConfig.properties || {};
        for (const key in props) {
            if (!Object.prototype.hasOwnProperty.call(props, key)) {
                continue;
            }
            const prop = props[key] || {};
            let typeName = (prop.type || "").toString().toLowerCase();
            if (typeName === "boolean") {
                typeName = "bool";
            }

            let currentValue = prop.value;
            if (typeName === "integer") {
                currentValue = Number.isFinite(currentValue) ? Math.trunc(currentValue) : 0;
            } else if (typeName === "number") {
                currentValue = Number(currentValue);
                if (!isFinite(currentValue)) {
                    currentValue = 0.0;
                }
            } else if (typeName === "bool") {
                currentValue = Boolean(currentValue);
            }

            const rawStep = prop.multipleOf !== undefined ? Number(prop.multipleOf) : (typeName === "number" ? 0.1 : 1);
            const step = rawStep > 0 ? rawStep : (typeName === "number" ? 0.1 : 1);
            const decimals = typeName === "number" ? decimalsForStep(step) : 0;

            let minimum = prop.minimum;
            let maximum = prop.maximum;
            if (minimum !== undefined && minimum !== null) {
                minimum = Number(minimum);
            } else {
                minimum = null;
            }
            if (maximum !== undefined && maximum !== null) {
                maximum = Number(maximum);
            } else {
                maximum = null;
            }

            let sliderMin = minimum;
            let sliderMax = maximum;
            if (sliderMin === null) {
                const base = ensureNumericFallback(currentValue, step * 20, typeName === "integer");
                if (typeName === "integer") {
                    sliderMin = Math.floor(base - Math.max(step * 10, 10));
                } else if (typeName === "number") {
                    sliderMin = base - Math.max(step * 20, 1);
                } else {
                    sliderMin = 0;
                }
            }
            if (sliderMax === null) {
                const baseMax = ensureNumericFallback(currentValue, step * 20, typeName === "integer");
                if (typeName === "integer") {
                    sliderMax = Math.ceil(baseMax + Math.max(step * 10, 10));
                } else if (typeName === "number") {
                    sliderMax = baseMax + Math.max(step * 20, 1);
                } else {
                    sliderMax = 1;
                }
            }

            const isInteger = typeName === "integer";
            const isNumeric = isInteger || typeName === "number";
            let numericValue = isNumeric ? Number(currentValue) : 0;
            if (!isFinite(numericValue)) {
                numericValue = 0;
            }
            if (isInteger) {
                numericValue = Math.trunc(numericValue);
            }

            const boolValue = typeName === "bool" ? Boolean(currentValue) : false;
            const hasMinimum = minimum !== null;
            const hasMaximum = maximum !== null;

            propertiesModel.append({
                key: key,
                title: prop.title || key,
                description: prop.description || "",
                typeName: typeName,
                boolValue: boolValue,
                numberValue: numericValue,
                hasMinimum: hasMinimum,
                minimumValue: hasMinimum ? Number(minimum) : 0,
                hasMaximum: hasMaximum,
                maximumValue: hasMaximum ? Number(maximum) : 0,
                sliderMin: isNumeric ? Number(sliderMin) : 0,
                sliderMax: isNumeric ? Number(sliderMax) : 1,
                step: isNumeric ? Number(step) : 1,
                decimals: decimals
            });
        }

        restoreGeometry();
        suppressUpdates = false;
    }

    function submitValue(modelIndex, propertyName, rawValue) {
        const entry = propertiesModel.get(modelIndex);
        if (!entry) {
            return rawValue;
        }

        let normalized = rawValue;

        if (entry.typeName === "bool") {
            normalized = Boolean(rawValue);
        } else {
            normalized = Number(rawValue);
            if (!isFinite(normalized)) {
                normalized = 0.0;
            }
            if (entry.typeName === "integer") {
                normalized = Math.trunc(normalized);
            }

            if (entry.step) {
                const stepValue = Number(entry.step);
                if (stepValue > 0) {
                    normalized = Math.round(normalized / stepValue) * stepValue;
                }
            }

            if (entry.decimals !== undefined) {
                normalized = Number(normalized.toFixed(entry.decimals));
            }

            if (entry.hasMinimum) {
                normalized = Math.max(normalized, entry.minimumValue);
            }
            if (entry.hasMaximum) {
                normalized = Math.min(normalized, entry.maximumValue);
            }

            if (entry.typeName === "integer") {
                normalized = Math.trunc(normalized);
            }
        }

        const previousValue = entry.typeName === "bool" ? entry.boolValue : entry.numberValue;
        const changed = previousValue !== normalized;
        if (changed) {
            suppressUpdates = true;
            if (entry.typeName === "bool") {
                propertiesModel.setProperty(modelIndex, "boolValue", Boolean(normalized));
            } else {
                propertiesModel.setProperty(modelIndex, "numberValue", Number(normalized));
            }
            suppressUpdates = false;
        }

        if (changed && socketClient) {
            socketClient.send_config_update(configNamespace, configEvent, propertyName, entry.typeName === "bool" ? Boolean(normalized) : normalized, entry.typeName === "integer");
        }

        return normalized;
    }

    function updateEditorWidth(width) {
        if (width === undefined || width === null) {
            return;
        }
        const numericWidth = Number(width);
        if (isFinite(numericWidth) && numericWidth > editorColumnWidth) {
            editorColumnWidth = numericWidth;
        }
    }

    function updateLabelWidth(width) {
        if (width === undefined || width === null) {
            return;
        }
        const numericWidth = Number(width);
        if (isFinite(numericWidth) && numericWidth > labelColumnWidth) {
            labelColumnWidth = numericWidth;
        }
    }

    color: "#2b2b2b"
    height: 720
    minimumHeight: 260
    minimumWidth: 640
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
    width: 640

    onClosing: {
        saveGeometry();
        windowClosed();
    }
    onVisibleChanged: {
        if (visible) {
            restoreGeometry();
        } else {
            saveGeometry();
        }
    }

    ListModel {
        id: propertiesModel

    }

    Settings {
        id: geometrySettings

        property var storedGeometries: ({})

        category: "ConfigWindow"
    }

    Component {
        id: boolEditorComponent

        Rectangle {
            id: boolContainer

            required property bool boolValue
            required property string description
            required property int index
            required property string key
            required property string title
            required property string typeName
            property bool value: boolValue

            Layout.columnSpan: 3
            Layout.fillWidth: true
            border.color: "#3a3a3a"
            border.width: 1
            color: index % 2 === 0 ? "#343434" : "#2f2f2f"
            implicitHeight: boolRow.implicitHeight + 12
            radius: 6

            onBoolValueChanged: {
                if (value !== boolValue) {
                    value = boolValue;
                }
            }
            onValueChanged: if (boolCheckBox.checked !== boolContainer.value) {
                boolCheckBox.checked = boolContainer.value;
            }

            RowLayout {
                id: boolRow

                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12

                Label {
                    id: boolTitle

                    Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                    Layout.preferredWidth: configWindow.labelColumnWidth > 0 ? configWindow.labelColumnWidth : implicitWidth
                    ToolTip.text: boolContainer.description
                    ToolTip.visible: boolTitleHover.hovered && boolContainer.description.length > 0
                    color: "#f0f0f0"
                    text: boolContainer.title

                    Component.onCompleted: configWindow.updateLabelWidth(implicitWidth)
                    onImplicitWidthChanged: configWindow.updateLabelWidth(implicitWidth)

                    HoverHandler {
                        id: boolTitleHover

                    }
                }

                Item {
                    Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                    Layout.preferredWidth: configWindow.editorColumnWidth > 0 ? configWindow.editorColumnWidth : boolCheckBox.implicitWidth
                    implicitHeight: boolCheckBox.implicitHeight
                    implicitWidth: Layout.preferredWidth

                    Component.onCompleted: configWindow.updateEditorWidth(boolCheckBox.implicitWidth)
                    onImplicitWidthChanged: configWindow.updateEditorWidth(boolCheckBox.implicitWidth)

                    CheckBox {
                        id: boolCheckBox

                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        checked: boolContainer.value
                        enabled: !configWindow.suppressUpdates

                        onToggled: {
                            if (configWindow.suppressUpdates) {
                                return;
                            }
                            const finalValue = configWindow.submitValue(boolContainer.index, boolContainer.key, checked);
                            if (boolContainer.value !== finalValue) {
                                boolContainer.value = finalValue;
                            }
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                }
            }
        }
    }

    Component {
        id: numericEditorComponent

        Rectangle {
            id: numericContainer

            required property int decimals
            required property string description
            required property bool hasMaximum
            required property bool hasMinimum
            required property int index
            required property string key
            required property real maximumValue
            required property real minimumValue
            required property real numberValue
            readonly property int scalingDecimals: Math.max(0, decimals)
            required property real sliderMax
            required property real sliderMin
            required property real step
            required property string title
            required property string typeName
            property real value: numberValue

            function syncEditors() {
                if (Math.abs(numericSpin.realValue - numericContainer.value) > Number.EPSILON) {
                    numericSpin.internalUpdate = true;
                    numericSpin.realValue = numericContainer.value;
                    numericSpin.internalUpdate = false;
                }
                if (numericSlider.value !== numericContainer.value) {
                    numericSlider.internalUpdate = true;
                    numericSlider.value = numericContainer.value;
                    numericSlider.internalUpdate = false;
                }
            }

            Layout.columnSpan: 3
            Layout.fillWidth: true
            border.color: "#3a3a3a"
            border.width: 1
            color: index % 2 === 0 ? "#343434" : "#2f2f2f"
            implicitHeight: numericRow.implicitHeight + 12
            radius: 6

            Component.onCompleted: syncEditors()
            onNumberValueChanged: {
                if (value !== numberValue) {
                    value = numberValue;
                }
            }
            onScalingDecimalsChanged: syncEditors()
            onValueChanged: syncEditors()

            RowLayout {
                id: numericRow

                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12

                Label {
                    id: numericTitle

                    Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                    Layout.preferredWidth: configWindow.labelColumnWidth > 0 ? configWindow.labelColumnWidth : implicitWidth
                    ToolTip.text: numericContainer.description
                    ToolTip.visible: numericTitleHover.hovered && numericContainer.description.length > 0
                    color: "#f0f0f0"
                    text: numericContainer.title

                    Component.onCompleted: configWindow.updateLabelWidth(implicitWidth)
                    onImplicitWidthChanged: configWindow.updateLabelWidth(implicitWidth)

                    HoverHandler {
                        id: numericTitleHover

                    }
                }

                DoubleSpinBox {
                    id: numericSpin

                    property bool internalUpdate: false

                    Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                    Layout.preferredWidth: configWindow.editorColumnWidth > 0 ? configWindow.editorColumnWidth : implicitWidth
                    decimals: numericContainer.scalingDecimals
                    realFrom: numericContainer.hasMinimum ? numericContainer.minimumValue : numericContainer.sliderMin
                    realStepSize: Number(numericContainer.step)
                    realTo: numericContainer.hasMaximum ? numericContainer.maximumValue : numericContainer.sliderMax
                    realValue: numericContainer.value

                    Component.onCompleted: configWindow.updateEditorWidth(implicitWidth)
                    onImplicitWidthChanged: configWindow.updateEditorWidth(implicitWidth)
                    onValueModified: {
                        if (configWindow.suppressUpdates || internalUpdate) {
                            return;
                        }
                        const finalVal = configWindow.submitValue(numericContainer.index, numericContainer.key, realValue);

                        if (Math.abs(finalVal - realValue) > Number.EPSILON) {
                            internalUpdate = true;
                            realValue = finalVal;
                            internalUpdate = false;
                        }
                        if (numericContainer.value !== finalVal) {
                            numericContainer.value = finalVal;
                        }
                    }
                }

                Slider {
                    id: numericSlider

                    property bool internalUpdate: false

                    Layout.fillWidth: true
                    from: Number(numericContainer.sliderMin)
                    stepSize: Math.max(Number(numericContainer.step), 0.0001)
                    to: Number(numericContainer.sliderMax)
                    value: Number(numericContainer.value)

                    onMoved: {
                        if (configWindow.suppressUpdates || internalUpdate) {
                            return;
                        }
                        const finalVal = configWindow.submitValue(numericContainer.index, numericContainer.key, value);
                        if (finalVal !== value) {
                            internalUpdate = true;
                            value = finalVal;
                            internalUpdate = false;
                        }
                        if (numericContainer.value !== finalVal) {
                            numericContainer.value = finalVal;
                        }
                    }
                }
            }
        }
    }

    ScrollView {
        id: scrollArea

        anchors.fill: parent
        anchors.margins: 8
        clip: true
        contentWidth: availableWidth

        GridLayout {
            id: propertiesGrid

            columnSpacing: 10
            columns: 3
            rowSpacing: 8
            width: scrollArea.contentWidth

            Repeater {
                model: propertiesModel

                delegate: DelegateChooser {
                    role: "typeName"

                    DelegateChoice {
                        delegate: boolEditorComponent
                        roleValue: "bool"
                    }

                    DelegateChoice {
                        delegate: numericEditorComponent
                    }
                }
            }
        }
    }
}
