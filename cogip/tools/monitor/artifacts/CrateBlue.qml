import QtQuick
import QtQuick3D

Node {
    id: crateBlue

    objectName: "CrateBlue"

    Model {
        id: crateBlueCube

        objectName: "CrateBlueCube"
        position: Qt.vector3d(0, 0, 15)
        scale: Qt.vector3d(1.50, 0.5, 0.3)
        source: "#Cube"

        materials: [
            DefaultMaterial {
                diffuseColor: "#d9b484"
            }
        ]
    }

    Model {
        id: crateBlueTag

        objectName: "CrateBlueTag"
        position: Qt.vector3d(0, 0, 30.2)
        scale: Qt.vector3d(0.50, 0.50, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseMap: Texture {
                    source: "../../../../assets/crate_blue_tag.webp"
                }
            }
        ]
    }

    Model {
        id: crateBlueFace

        objectName: "CrateBlueFace"
        position: Qt.vector3d(0, 0, 30.10)
        scale: Qt.vector3d(1.50, 0.50, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseColor: "#005b8c"
            }
        ]
    }

    Model {
        id: crateYellowTag

        eulerRotation: Qt.vector3d(180, 0, 0)
        objectName: "CrateYellowTag"
        position: Qt.vector3d(0, 0, -0.2)
        scale: Qt.vector3d(0.50, 0.50, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseMap: Texture {
                    source: "../../../../assets/crate_yellow_tag.webp"
                }
            }
        ]
    }

    Model {
        id: crateYellowFace

        eulerRotation: Qt.vector3d(180, 0, 0)
        objectName: "CrateYellowFace"
        position: Qt.vector3d(0, 0, -0.1)
        scale: Qt.vector3d(1.50, 0.50, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseColor: "#f7b500"
            }
        ]
    }

    Model {
        id: crateWhiteFaceLeft

        eulerRotation: Qt.vector3d(-90, 0, 0)
        objectName: "CrateWhiteFaceLeft"
        position: Qt.vector3d(0, 25.15, 15)
        scale: Qt.vector3d(0.50, 0.30, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseColor: "#ffffff"
            }
        ]
    }

    Model {
        id: crateWhiteFaceRight

        eulerRotation: Qt.vector3d(90, 0, 0)
        objectName: "CrateWhiteFaceRight"
        position: Qt.vector3d(0, -25.15, 15)
        scale: Qt.vector3d(0.50, 0.30, 1)
        source: "#Rectangle"

        materials: [
            DefaultMaterial {
                diffuseColor: "#ffffff"
            }
        ]
    }
}
