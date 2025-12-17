import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    PrincipledMaterial {
        id: part__Feature008_material
        objectName: "Part__Feature008"
        baseColor: "#ffbfbfbf"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature033_material
        objectName: "Part__Feature033"
        baseColor: "#ffc00000"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature032_material
        objectName: "Part__Feature032"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature031_material
        objectName: "Part__Feature031"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature009_material
        objectName: "Part__Feature009"
        baseColor: "#ffbfbfbf"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature030_material
        objectName: "Part__Feature030"
        baseColor: "#ffc00000"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature023_material
        objectName: "Part__Feature023"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature022_material
        objectName: "Part__Feature022"
        baseColor: "#ffc00000"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature019_material
        objectName: "Part__Feature019"
        baseColor: "#ff646464"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature025_material
        objectName: "Part__Feature025"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature029_material
        objectName: "Part__Feature029"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature028_material
        objectName: "Part__Feature028"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature027_material
        objectName: "Part__Feature027"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature026_material
        objectName: "Part__Feature026"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature018_material
        objectName: "Part__Feature018"
        baseColor: "#ff646464"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature024_material
        objectName: "Part__Feature024"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature011_material
        objectName: "Part__Feature011"
        baseColor: "#ffbfbfbf"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature010_material
        objectName: "Part__Feature010"
        baseColor: "#ffbfbfbf"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature012_material
        objectName: "Part__Feature012"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature016_material
        objectName: "Part__Feature016"
        baseColor: "#ff494949"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature015_material
        objectName: "Part__Feature015"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature014_material
        objectName: "Part__Feature014"
        baseColor: "#ff999999"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature013_material
        objectName: "Part__Feature013"
        baseColor: "#ff999999"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature004_material
        objectName: "Part__Feature004"
        baseColor: "#ffc00000"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature003_material
        objectName: "Part__Feature003"
        baseColor: "#ff404040"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature001_material
        objectName: "Part__Feature001"
        baseColor: "#ffaab2c4"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature_material
        objectName: "Part__Feature"
        baseColor: "#ffaab2c4"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature017_material
        objectName: "Part__Feature017"
        baseColor: "#ff646464"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature007_material
        objectName: "Part__Feature007"
        baseColor: "#ff141414"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature006_material
        objectName: "Part__Feature006"
        baseColor: "#ff141414"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature005_material
        objectName: "Part__Feature005"
        baseColor: "#ff303b96"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature002_material
        objectName: "Part__Feature002"
        baseColor: "#fff0ede6"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature034_material
        objectName: "Part__Feature034"
        baseColor: "#ffc00000"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature021_material
        objectName: "Part__Feature021"
        baseColor: "#ffcad1ee"
        indexOfRefraction: 1
    }
    PrincipledMaterial {
        id: part__Feature020_material
        objectName: "Part__Feature020"
        baseColor: "#ff494949"
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
            source: "meshes/part__Feature_mesh.mesh"
            materials: [
                part__Feature_material
            ]
        }
        Model {
            id: node1
            objectName: "node1"
            source: "meshes/part__Feature001_mesh.mesh"
            materials: [
                part__Feature001_material
            ]
        }
        Model {
            id: node2
            objectName: "node2"
            source: "meshes/part__Feature003_mesh.mesh"
            materials: [
                part__Feature003_material
            ]
        }
        Model {
            id: node3
            objectName: "node3"
            source: "meshes/part__Feature004_mesh.mesh"
            materials: [
                part__Feature004_material
            ]
        }
        Model {
            id: node4
            objectName: "node4"
            source: "meshes/part__Feature012_mesh.mesh"
            materials: [
                part__Feature012_material
            ]
        }
        Model {
            id: node5
            objectName: "node5"
            source: "meshes/part__Feature013_mesh.mesh"
            materials: [
                part__Feature013_material
            ]
        }
        Model {
            id: node6
            objectName: "node6"
            source: "meshes/part__Feature014_mesh.mesh"
            materials: [
                part__Feature014_material
            ]
        }
        Model {
            id: node7
            objectName: "node7"
            source: "meshes/part__Feature015_mesh.mesh"
            materials: [
                part__Feature015_material
            ]
        }
        Model {
            id: node8
            objectName: "node8"
            source: "meshes/part__Feature016_mesh.mesh"
            materials: [
                part__Feature016_material
            ]
        }
        Model {
            id: node9
            objectName: "node9"
            source: "meshes/part__Feature020_mesh.mesh"
            materials: [
                part__Feature020_material
            ]
        }
        Model {
            id: node10
            objectName: "node10"
            source: "meshes/part__Feature021_mesh.mesh"
            materials: [
                part__Feature021_material
            ]
        }
        Model {
            id: node11
            objectName: "node11"
            source: "meshes/part__Feature034_mesh.mesh"
            materials: [
                part__Feature034_material
            ]
        }
        Model {
            id: node12
            objectName: "node12"
            source: "meshes/part__Feature002_mesh.mesh"
            materials: [
                part__Feature002_material
            ]
        }
        Model {
            id: node13
            objectName: "node13"
            source: "meshes/part__Feature005_mesh.mesh"
            materials: [
                part__Feature005_material
            ]
        }
        Model {
            id: node14
            objectName: "node14"
            source: "meshes/part__Feature006_mesh.mesh"
            materials: [
                part__Feature006_material
            ]
        }
        Model {
            id: node15
            objectName: "node15"
            source: "meshes/part__Feature007_mesh.mesh"
            materials: [
                part__Feature007_material
            ]
        }
        Model {
            id: node16
            objectName: "node16"
            source: "meshes/part__Feature017_mesh.mesh"
            materials: [
                part__Feature017_material
            ]
        }
        Model {
            id: node17
            objectName: "node17"
            source: "meshes/part__Feature018_mesh.mesh"
            materials: [
                part__Feature018_material
            ]
        }
        Model {
            id: node18
            objectName: "node18"
            source: "meshes/part__Feature019_mesh.mesh"
            materials: [
                part__Feature019_material
            ]
        }
        Model {
            id: node19
            objectName: "node19"
            source: "meshes/part__Feature022_mesh.mesh"
            materials: [
                part__Feature022_material
            ]
        }
        Model {
            id: node20
            objectName: "node20"
            source: "meshes/part__Feature023_mesh.mesh"
            materials: [
                part__Feature023_material
            ]
        }
        Model {
            id: node21
            objectName: "node21"
            source: "meshes/part__Feature030_mesh.mesh"
            materials: [
                part__Feature030_material
            ]
        }
        Model {
            id: node22
            objectName: "node22"
            source: "meshes/part__Feature031_mesh.mesh"
            materials: [
                part__Feature031_material
            ]
        }
        Model {
            id: node23
            objectName: "node23"
            source: "meshes/part__Feature032_mesh.mesh"
            materials: [
                part__Feature032_material
            ]
        }
        Model {
            id: node24
            objectName: "node24"
            source: "meshes/part__Feature033_mesh.mesh"
            materials: [
                part__Feature033_material
            ]
        }
        Model {
            id: node25
            objectName: "node25"
            source: "meshes/part__Feature008_mesh.mesh"
            materials: [
                part__Feature008_material
            ]
        }
        Model {
            id: node26
            objectName: "node26"
            source: "meshes/part__Feature009_mesh.mesh"
            materials: [
                part__Feature009_material
            ]
        }
        Model {
            id: node27
            objectName: "node27"
            source: "meshes/part__Feature010_mesh.mesh"
            materials: [
                part__Feature010_material
            ]
        }
        Model {
            id: node28
            objectName: "node28"
            source: "meshes/part__Feature011_mesh.mesh"
            materials: [
                part__Feature011_material
            ]
        }
        Model {
            id: node29
            objectName: "node29"
            source: "meshes/part__Feature024_mesh.mesh"
            materials: [
                part__Feature024_material
            ]
        }
        Model {
            id: node30
            objectName: "node30"
            source: "meshes/part__Feature025_mesh.mesh"
            materials: [
                part__Feature025_material
            ]
        }
        Model {
            id: node31
            objectName: "node31"
            source: "meshes/part__Feature026_mesh.mesh"
            materials: [
                part__Feature026_material
            ]
        }
        Model {
            id: node32
            objectName: "node32"
            source: "meshes/part__Feature027_mesh.mesh"
            materials: [
                part__Feature027_material
            ]
        }
        Model {
            id: node33
            objectName: "node33"
            source: "meshes/part__Feature028_mesh.mesh"
            materials: [
                part__Feature028_material
            ]
        }
        Model {
            id: node34
            objectName: "node34"
            source: "meshes/part__Feature029_mesh.mesh"
            materials: [
                part__Feature029_material
            ]
        }
    }

    // Animations:
}
