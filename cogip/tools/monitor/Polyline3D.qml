pragma ComponentBehavior: Bound

import QtQuick
import QtQuick3D

Node {
    id: polylineRoot

    property real elevation: 3
    property color lineColor: "yellow"
    property var points: []
    property var segments: []
    property real thickness: 6

    function toNumber(value) {
        const num = Number(value);
        return isNaN(num) ? 0 : num;
    }

    function updateSegments() {
        const pts = polylineRoot.points;
        if (!pts || pts.length < 2) {
            polylineRoot.segments = [];
            return;
        }
        const result = [];
        for (let i = 0; i < pts.length - 1; ++i) {
            const start = pts[i] || {
                x: 0,
                y: 0,
                z: 0
            };
            const end = pts[i + 1] || {
                x: 0,
                y: 0,
                z: 0
            };
            const sx = toNumber(start.x);
            const sy = toNumber(start.y);
            const sz = toNumber(start.z);
            const ex = toNumber(end.x);
            const ey = toNumber(end.y);
            const ez = toNumber(end.z);
            const dx = ex - sx;
            const dy = ey - sy;
            const dz = ez - sz;
            const length = Math.sqrt(dx * dx + dy * dy + dz * dz);
            if (length === 0) {
                continue;
            }
            const midX = (sx + ex) / 2;
            const midY = (sy + ey) / 2;
            const midZ = (sz + ez) / 2 + polylineRoot.elevation;
            const yaw = Math.atan2(dy, dx) * 180 / Math.PI;
            result.push({
                position: Qt.vector3d(midX, midY, midZ),
                yaw: yaw,
                length: length
            });
        }
        polylineRoot.segments = result;
    }

    Component.onCompleted: updateSegments()
    onPointsChanged: updateSegments()

    Repeater3D {
        model: polylineRoot.segments.length

        delegate: Model {
            required property int index
            property var segment: polylineRoot.segments[index]

            eulerRotation: Qt.vector3d(0, 0, segment.yaw)
            position: segment.position
            scale: Qt.vector3d(segment.length / 100, polylineRoot.thickness / 100, polylineRoot.thickness / 100)
            source: "#Cube"

            materials: [
                DefaultMaterial {
                    diffuseColor: polylineRoot.lineColor
                    lighting: DefaultMaterial.NoLighting
                }
            ]
        }
    }
}
