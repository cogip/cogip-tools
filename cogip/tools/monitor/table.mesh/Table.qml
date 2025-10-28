import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    PrincipledMaterial {
        id: defeat_material
        objectName: "defeat"
        baseColor: "#ffeacc61"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature089_material
        objectName: "Part__Feature089"
        baseColor: "#ff005ce6"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature088_material
        objectName: "Part__Feature088"
        baseColor: "#ffffbf00"
        indexOfRefraction: 1
    }

    // Nodes:
    Node {
        id: scene
        objectName: "Scene"
        rotation: Qt.quaternion(0.707107, -0.707107, 0, 0)
        Model {
            id: node0
            objectName: "node0"
            source: "meshes/defeat_mesh.mesh"
            materials: [
                defeat_material
            ]
        }
        Model {
            id: node1
            objectName: "node1"
            source: "meshes/part__Feature089_mesh.mesh"
            materials: [
                part__Feature089_material
            ]
        }
        Model {
            id: node2
            objectName: "node2"
            source: "meshes/part__Feature088_mesh.mesh"
            materials: [
                part__Feature088_material
            ]
        }
    }

    // Animations:
}
