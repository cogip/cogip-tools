import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    PrincipledMaterial {
        id: mat_34_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff727980"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_34.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_61_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff494949"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_61.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_62_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff2b1100"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_62.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_73_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff046e11"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_73.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_74_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#fff3e5a7"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_74.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_16_002_material

        alphaMode: PrincipledMaterial.Opaque
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_16.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_30_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffaab2c4"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_30.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_70_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff616969"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_70.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_4_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffcad1ee"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_4.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_63_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff800000"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_63.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_64_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#fff3cb7c"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_64.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_3_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffa0a0a0"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_3.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_22_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff1a1a1a"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_22.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_69_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffa6abb5"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_69.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_2_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff404040"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_2.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_71_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffff8040"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_71.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_68_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ff212121"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_68.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_67_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#fff5f5f6"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_67.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_65_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffc6c1bc"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_65.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_1_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffb11919"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_1.002"
        roughness: 0.6000000238418579
    }

    PrincipledMaterial {
        id: mat_0_002_material

        alphaMode: PrincipledMaterial.Opaque
        baseColor: "#ffe5ebed"
        cullMode: PrincipledMaterial.NoCulling
        objectName: "mat_0.002"
        roughness: 0.6000000238418579
    }

    // Nodes:
    Node {
        id: robot

        objectName: "Robot"
        position: Qt.vector3d(7.62342, -3.94689, 0)

        Model {
            id: back_Belt

            materials: [mat_2_002_material, mat_4_002_material]
            objectName: "Back_Belt"
            source: "meshes/back_Belt_mesh.mesh"
        }

        Node {
            id: back_Grips

            objectName: "Back_Grips"

            Model {
                id: back_Grip_Left_Center

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Back_Grip_Left_Center"
                position: Qt.vector3d(-125.044, 24.9789, 219.085)
                source: "meshes/back_Grip_Left_Center_mesh.mesh"
            }

            Model {
                id: back_Grip_Left_Side

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Back_Grip_Left_Side"
                position: Qt.vector3d(-124.972, 74.9964, 219.085)
                source: "meshes/back_Grip_Left_Side_mesh.mesh"
            }

            Model {
                id: back_Grip_Right_Center

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Back_Grip_Right_Center"
                position: Qt.vector3d(-125.044, -25.0211, 219.085)
                source: "meshes/back_Grip_Right_Center_mesh.mesh"
            }

            Model {
                id: back_Grip_Right_Side

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Back_Grip_Right_Side"
                position: Qt.vector3d(-125.114, -75.0531, 219.085)
                source: "meshes/back_Grip_Right_Side_mesh.mesh"
            }
        }

        Model {
            id: back_Lift

            materials: [mat_22_002_material, mat_63_002_material, mat_69_002_material, mat_70_002_material, mat_71_002_material, mat_68_002_material, mat_67_002_material]
            objectName: "Back_Lift"
            source: "meshes/back_Lift_mesh.mesh"

            Model {
                id: back_Arm_Left

                materials: [mat_2_002_material, mat_63_002_material, mat_65_002_material]
                objectName: "Back_Arm_Left"
                position: Qt.vector3d(-72.5088, 130, 71.8907)
                source: "meshes/back_Arm_Left_mesh.mesh"
            }

            Model {
                id: back_Arm_Right

                materials: [mat_4_002_material, mat_2_002_material, mat_63_002_material, mat_65_002_material]
                objectName: "Back_Arm_Right"
                position: Qt.vector3d(-72.5083, -130, 69.3908)
                source: "meshes/back_Arm_Right_mesh.mesh"
            }
        }

        Model {
            id: back_Scissor

            materials: [mat_63_002_material, mat_65_002_material, mat_2_002_material]
            objectName: "Back_Scissor"
            source: "meshes/back_Scissor_mesh.mesh"
        }

        Model {
            id: base

            materials: [mat_1_002_material, mat_0_002_material, mat_16_002_material, mat_4_002_material, mat_61_002_material, mat_2_002_material, mat_63_002_material, mat_62_002_material]
            objectName: "Base"
            source: "meshes/base_mesh.mesh"
        }

        Node {
            id: beacon

            objectName: "Beacon"

            Model {
                id: beacon_Covers

                materials: [mat_1_002_material]
                objectName: "Beacon_Covers"
                source: "meshes/beacon_Covers_mesh.mesh"
            }

            Model {
                id: beacon_Spacers

                materials: [mat_2_002_material]
                objectName: "Beacon_Spacers"
                source: "meshes/beacon_Spacers_mesh.mesh"
            }

            Model {
                id: lidar_Plate

                materials: [mat_3_002_material]
                objectName: "Lidar_Plate"
                source: "meshes/lidar_Plate_mesh.mesh"
            }

            Model {
                id: lidar_Unit

                materials: [mat_2_002_material]
                objectName: "Lidar_Unit"
                source: "meshes/lidar_Unit_mesh.mesh"
            }
        }

        Node {
            id: camera_Set

            objectName: "Camera_Set"

            Node {
                id: camera

                objectName: "Camera"

                Model {
                    id: camera_PCB

                    materials: [mat_73_002_material, mat_74_002_material]
                    objectName: "Camera_PCB"
                    source: "meshes/camera_PCB_mesh.mesh"
                }

                Model {
                    id: camera_Sensor

                    materials: [mat_34_002_material]
                    objectName: "Camera_Sensor"
                    source: "meshes/camera_Sensor_mesh.mesh"
                }
            }

            Model {
                id: camera_Bracket

                materials: [mat_63_002_material]
                objectName: "Camera_Bracket"
                source: "meshes/camera_Braket_mesh.mesh"
            }
        }

        Model {
            id: emergency_Button

            materials: [mat_30_002_material]
            objectName: "Emergency_Button"
            source: "meshes/emergency_Button_mesh.mesh"
        }

        Node {
            id: front_Grips

            objectName: "Front_Grips"

            Model {
                id: front_Grip_Left_Center

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Front_Grip_Left_Center"
                position: Qt.vector3d(124.989, 25.0161, 219.115)
                source: "meshes/front_Grip_Left_Center_mesh.mesh"
            }

            Model {
                id: front_Grip_Left_Side

                materials: [mat_2_002_material, mat_64_002_material, mat_3_002_material, mat_63_002_material]
                objectName: "Front_Grip_Left_Side"
                position: Qt.vector3d(125.056, 75.0253, 219.115)
                source: "meshes/front_Grip_Left_Side_mesh.mesh"
            }

            Model {
                id: front_Grip_Right_Center

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Front_Grip_Right_Center"
                position: Qt.vector3d(124.973, -24.9999, 219.115)
                source: "meshes/front_Grip_Right_Center_mesh.mesh"
            }

            Model {
                id: front_Grip_Right_Side

                materials: [mat_63_002_material, mat_2_002_material, mat_64_002_material, mat_3_002_material]
                objectName: "Front_Grip_Right_Side"
                position: Qt.vector3d(124.96, -74.9922, 219.115)
                source: "meshes/front_Grip_Right_Side_mesh.mesh"
            }
        }

        Model {
            id: front_Lift

            materials: [mat_22_002_material, mat_63_002_material, mat_67_002_material, mat_68_002_material, mat_69_002_material, mat_70_002_material, mat_71_002_material]
            objectName: "Front_Lift"
            source: "meshes/front_Lift_mesh.mesh"

            Model {
                id: front_Arm_Left

                materials: [mat_63_002_material, mat_4_002_material, mat_2_002_material, mat_65_002_material]
                objectName: "Front_Arm_Left"
                position: Qt.vector3d(72.4912, 130, 71.9083)
                source: "meshes/front_Arm_Left_mesh.mesh"
            }

            Model {
                id: front_Arm_Right

                materials: [mat_63_002_material, mat_2_002_material, mat_65_002_material]
                objectName: "Front_Arm_Right"
                position: Qt.vector3d(72.2111, -130.051, 70.9198)
                source: "meshes/front_Arm_Right_mesh.mesh"
            }
        }

        Model {
            id: front_Scissor

            materials: [mat_63_002_material, mat_65_002_material, mat_2_002_material]
            objectName: "Front_Scissor"
            source: "meshes/front_Scissor_mesh.mesh"
        }
    }

    // Animations:
}
