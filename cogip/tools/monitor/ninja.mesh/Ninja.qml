import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    PrincipledMaterial {
        id: mat_0_material
        objectName: "mat_0"
        baseColor: "#ff71777c"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_10_material
        objectName: "mat_10"
        baseColor: "#ff000000"
        metalness: 1
        roughness: 1
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_9_material
        objectName: "mat_9"
        baseColor: "#ff343434"
        metalness: 1
        roughness: 1
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_8_material
        objectName: "mat_8"
        baseColor: "#ffff0000"
        metalness: 1
        roughness: 1
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_7_material
        objectName: "mat_7"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_3_material
        objectName: "mat_3"
        baseColor: "#ff7f7f7f"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_4_material
        objectName: "mat_4"
        baseColor: "#ff8d8d8d"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_2_material
        objectName: "mat_2"
        baseColor: "#ffaa0000"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_5_material
        objectName: "mat_5"
        baseColor: "#fff5f5f6"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_6_material
        objectName: "mat_6"
        baseColor: "#ff212121"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: mat_1_material
        objectName: "mat_1"
        baseColor: "#ff727980"
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }

    // Nodes:
    Node {
        id: robot
        objectName: "Robot"
        rotation: Qt.quaternion(-4.37114e-08, 0, 0, 1)
        scale: Qt.vector3d(1000, 1000, 1000)
        Node {
            id: arm_Left_Assembly
            objectName: "Arm Left Assembly"
            position: Qt.vector3d(0.100594, -0.104074, 0.0770201)
            rotation: Qt.quaternion(0.707107, 0, 0, -0.707107)
            scale: Qt.vector3d(1, 1, 1)
            Model {
                id: ninja_Arm_Left
                objectName: "Ninja_Arm_Left"
                position: Qt.vector3d(-0.0340743, -0.0335944, -0.0420201)
                source: "meshes/body_003_mesh.mesh"
                materials: [
                    mat_1_material
                ]
            }
            Node {
                id: part_001
                objectName: "Part.001"
                position: Qt.vector3d(-0.0440743, -0.0335944, 0.0104799)
                Node {
                    id: scs15_asm15kg20160222_asm_v4_001
                    objectName: "scs15_asm15kg20160222_asm v4.001"
                    rotation: Qt.quaternion(0.707107, -0.707107, 0, 0)
                    scale: Qt.vector3d(1, 1, 1)
                    Node {
                        id: scs15_ASM_ASM_001
                        objectName: "SCS15_ASM_ASM.001"
                        Model {
                            id: msbr_1_001
                            objectName: "MSBR-1.001"
                            source: "meshes/msbr_1_001_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_2_001
                            objectName: "MSBR-2.001"
                            source: "meshes/msbr_2_001_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_3_001
                            objectName: "MSBR-3.001"
                            source: "meshes/msbr_3_001_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_6_001
                            objectName: "MSBR-6.001"
                            source: "meshes/msbr_6_001_mesh.mesh"
                            materials: [
                                mat_5_material
                            ]
                        }
                    }
                }
            }
        }
        Node {
            id: arm_Right_Assembly
            objectName: "Arm Right Assembly"
            position: Qt.vector3d(0.0334056, 0.104074, 0.0770201)
            rotation: Qt.quaternion(0.707107, 0, 0, 0.707107)
            scale: Qt.vector3d(1, 1, 1)
            Model {
                id: ninja_Arm_Right
                objectName: "Ninja_Arm_Right"
                position: Qt.vector3d(-0.0340743, -0.0335943, -0.0420201)
                source: "meshes/body_002_mesh.mesh"
                materials: [
                    mat_1_material
                ]
            }
            Node {
                id: part
                objectName: "Part"
                position: Qt.vector3d(-0.0440743, -0.0335944, 0.0104799)
                Node {
                    id: scs15_asm15kg20160222_asm_v4
                    objectName: "scs15_asm15kg20160222_asm v4"
                    rotation: Qt.quaternion(0.707107, -0.707107, 0, 0)
                    scale: Qt.vector3d(1, 1, 1)
                    Node {
                        id: scs15_ASM_ASM
                        objectName: "SCS15_ASM_ASM"
                        Model {
                            id: msbr_1
                            objectName: "MSBR-1"
                            source: "meshes/msbr_1_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_2
                            objectName: "MSBR-2"
                            source: "meshes/msbr_2_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_3
                            objectName: "MSBR-3"
                            source: "meshes/msbr_3_mesh.mesh"
                            materials: [
                                mat_6_material
                            ]
                        }
                        Model {
                            id: msbr_6
                            objectName: "MSBR-6"
                            source: "meshes/msbr_6_mesh.mesh"
                            materials: [
                                mat_5_material
                            ]
                        }
                    }
                }
            }
        }
        Model {
            id: corps002
            objectName: "Corps002"
            source: "meshes/corps002_mesh.mesh"
            materials: [
                mat_2_material
            ]
        }
        Node {
            id: lidar
            objectName: "LIDAR"
            position: Qt.vector3d(-0.05, 0, 0.0358)
            Model {
                id: ld19_middle
                objectName: "LD19_middle"
                position: Qt.vector3d(0, 0, 0.0102)
                source: "meshes/ld19_middle_mesh.mesh"
                materials: [
                    mat_4_material
                ]
            }
            Model {
                id: ld19_up
                objectName: "LD19_up"
                position: Qt.vector3d(0, 0, 0.0222)
                rotation: Qt.quaternion(0.707107, 0, 0, 0.707107)
                scale: Qt.vector3d(1, 1, 1)
                source: "meshes/ld19_up_mesh.mesh"
                materials: [
                    mat_3_material
                ]
            }
        }
        Node {
            id: otos
            objectName: "OTOS"
            position: Qt.vector3d(0, 0, 0.026)
            Model {
                id: paa5160E1
                objectName: "PAA5160E1"
                source: "meshes/paa5160E1_mesh.mesh"
                materials: [
                    mat_7_material,
                    mat_8_material,
                    mat_9_material,
                    mat_10_material
                ]
            }
        }
        Node {
            id: top_EMS_SCREEN
            objectName: "TOP EMS SCREEN"
            position: Qt.vector3d(-6.74057e-05, -0.000396496, 0.145496)
            Model {
                id: corps_001
                objectName: "Corps.001"
                position: Qt.vector3d(6.74057e-05, 0.000396496, -0.00149579)
                source: "meshes/corps_002_mesh.mesh"
                materials: [
                    mat_1_material
                ]
            }
        }
        Node {
            id: wheel_left
            objectName: "Wheel left"
            position: Qt.vector3d(0, 0.056, 0.028)
            rotation: Qt.quaternion(0.707107, -0.707107, 0, 0)
            scale: Qt.vector3d(1, 1, 1)
            Model {
                id: body001
                objectName: "Body001"
                source: "meshes/body_mesh.mesh"
                materials: [
                    mat_0_material
                ]
            }
            Model {
                id: corps001
                objectName: "Corps001"
                position: Qt.vector3d(0, 0, 0.016)
                rotation: Qt.quaternion(-1.60812e-16, 0, 0, 1)
                source: "meshes/corps_mesh.mesh"
                materials: [
                    mat_1_material
                ]
            }
        }
        Node {
            id: wheel_right
            objectName: "Wheel right"
            position: Qt.vector3d(0, -0.056, 0.028)
            rotation: Qt.quaternion(0, 0, -0.707107, 0.707107)
            scale: Qt.vector3d(1, 1, 1)
            Model {
                id: body
                objectName: "Body"
                source: "meshes/body_001_mesh.mesh"
                materials: [
                    mat_0_material
                ]
            }
            Model {
                id: corps
                objectName: "Corps"
                position: Qt.vector3d(0, 0, 0.016)
                rotation: Qt.quaternion(-1.60812e-16, 0, 0, 1)
                source: "meshes/corps_001_mesh.mesh"
                materials: [
                    mat_1_material
                ]
            }
        }
    }

    // Animations:
}
