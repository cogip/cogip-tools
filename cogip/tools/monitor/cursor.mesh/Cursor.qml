import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    PrincipledMaterial {
        id: defaultMaterial_material

        objectName: "DefaultMaterial"
    }

    // Nodes:
    Node {
        id: node1

        Model {
            id: stl

            materials: [defaultMaterial_material]
            objectName: "STL"
            source: "meshes/stl_mesh.mesh"
        }
    }

    // Animations:
}
