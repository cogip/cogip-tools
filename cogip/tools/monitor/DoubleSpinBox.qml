import QtQuick
import QtQuick.Controls

SpinBox {
    id: control

    property int decimals: 2

    // Internal factor for integer conversion
    readonly property real factor: Math.pow(10, Math.max(0, decimals))
    property real realFrom: 0.0
    property real realStepSize: 1.0
    property real realTo: 100.0
    property real realValue: 0.0

    editable: true

    // Map real properties to integer SpinBox properties
    from: Math.round(realFrom * factor)
    stepSize: Math.max(1, Math.round(realStepSize * factor))
    textFromValue: function (value, locale) {
        let text = Number(value / factor).toLocaleString(locale, 'f', decimals);
        // Remove group separators to avoid height changes with some fonts/locales
        if (locale.groupSeparator) {
            text = text.split(locale.groupSeparator).join('');
        }
        return text;
    }
    to: Math.round(realTo * factor)
    value: Math.round(realValue * factor)
    valueFromText: function (text, locale) {
        return Math.round(Number.fromLocaleString(locale, text) * factor);
    }

    validator: DoubleValidator {
        bottom: Math.min(control.realFrom, control.realTo)
        decimals: control.decimals
        notation: DoubleValidator.StandardNotation
        top: Math.max(control.realFrom, control.realTo)
    }

    onRealValueChanged: {
        var newVal = Math.round(realValue * factor);
        if (value !== newVal) {
            value = newVal;
        }
    }

    // Two-way binding support
    onValueChanged: {
        var newVal = value / factor;
        if (Math.abs(newVal - realValue) > Number.EPSILON) {
            realValue = newVal;
        }
    }
}
