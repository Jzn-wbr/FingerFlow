import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Window 6.5
import Qt5Compat.GraphicalEffects 1.0

Window {
    id: root
    visible: true
    width: defaultFrameW + 520
    height: defaultFrameH + 180
    color: "#00000000"
    title: "FingerFlow"
    flags: Qt.Window | Qt.FramelessWindowHint
    onClosing: Qt.quit()

    Rectangle {
        id: backdrop
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0f131a" }
            GradientStop { position: 0.6; color: "#0b0f17" }
            GradientStop { position: 1.0; color: "#070a12" }
        }
    }

    Rectangle {
        id: stageGlow
        width: parent.width * 0.8
        height: parent.height * 0.7
        radius: 36
        anchors.centerIn: parent
        color: "#1a2240"
        opacity: 0.22
        layer.enabled: true
        layer.effect: FastBlur { radius: 48 }
    }

    RowLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 28
        spacing: 22

        Rectangle {
            id: cameraCard
            radius: 20
            color: "#0f141f"
            border.color: "#1d2638"
            border.width: 1
            Layout.preferredWidth: defaultFrameW
            Layout.preferredHeight: defaultFrameH
            Layout.fillHeight: true

            layer.enabled: true
            layer.effect: DropShadow {
                horizontalOffset: 0
                verticalOffset: 14
                radius: 28
                samples: 30
                color: "#55000000"
            }

            Image {
                id: cameraImage
                anchors.fill: parent
                anchors.margins: 2
                fillMode: Image.PreserveAspectFit
                smooth: true
                cache: false
                asynchronous: false
                source: "image://camera/frame?" + uiState.imageCounter
            }

            Rectangle {
                anchors.fill: parent
                radius: 20
                border.color: "#27314a"
                border.width: 1
                color: "transparent"
            }
        }

        Rectangle {
            id: panelCard
            radius: 22
            clip: true
            Layout.preferredWidth: 360
            Layout.fillHeight: true
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#1c2232" }
                GradientStop { position: 1.0; color: "#151a26" }
            }
            border.color: "#27324a"
            border.width: 1

            layer.enabled: true
            layer.effect: DropShadow {
                horizontalOffset: 0
                verticalOffset: 18
                radius: 34
                samples: 34
                color: "#66000000"
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                anchors.topMargin: 14
                anchors.bottomMargin: 38
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text {
                            text: "FINGERFLOW"
                            color: "#7fb0ff"
                            font.pixelSize: 22
                            font.family: "Segoe UI Variable"
                            font.weight: Font.DemiBold
                            font.letterSpacing: 2
                        }
                        Text {
                            text: "TRACKING CONSOLE"
                            color: "#8793aa"
                            font.pixelSize: 12
                            font.family: "Segoe UI"
                            font.letterSpacing: 1
                        }
                    }

                    Button {
                        id: infoButton
                        text: "HELP"
                        Layout.preferredWidth: 66
                        Layout.preferredHeight: 28
                        background: Rectangle {
                            radius: 8
                            border.width: 1
                            border.color: infoButton.down ? "#3a4c72" : "#2b3550"
                            color: infoButton.down ? "#22304a" : (infoButton.hovered ? "#1f2a40" : "#1a2234")
                        }
                        contentItem: Text {
                            text: infoButton.text
                            color: "#cdd5e3"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: infoPopup.open()
                    }
                    Button {
                        text: "QUIT"
                        Layout.preferredWidth: 70
                        Layout.preferredHeight: 28
                        background: Rectangle {
                            radius: 8
                            border.width: 1
                            border.color: "#4b3340"
                            color: parent.down ? "#5a1f2a" : (parent.hovered ? "#3a1a22" : "#232331")
                        }
                        contentItem: Text {
                            text: "QUIT"
                            color: parent.hovered ? "#ffd7de" : "#d9ddea"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: Qt.quit()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#26304a"
                }

                ColumnLayout {
                    spacing: 10
                    Layout.fillWidth: true

                    Text {
                        text: "STATUS"
                        color: "#8793aa"
                        font.pixelSize: 12
                    }
                    Text {
                        text: uiState.mode.toUpperCase()
                        color: uiState.mode === "mode select" ? "#00e5ff" : "#5ce0a1"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        Behavior on color { ColorAnimation { duration: 180 } }
                    }

                    RowLayout {
                        spacing: 10
                        Text {
                            text: "VIEW"
                            color: "#8793aa"
                            font.pixelSize: 12
                        }
                        Text {
                            text: uiState.topmost ? "ON" : "OFF"
                            color: uiState.topmost ? "#5ce0a1" : "#8793aa"
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            width: 22
                            height: 18
                            radius: 5
                            color: "#20283a"
                            border.width: 1
                            border.color: "#2a344a"
                            Text {
                                anchors.centerIn: parent
                                text: modeKeyTop
                                color: "#cdd5e3"
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                            }
                        }
                        Text {
                            text: "TOGGLE"
                            color: "#8793aa"
                            font.pixelSize: 11
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#26304a"
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 56
                    radius: 12
                    color: "#141b29"
                    border.width: 1
                    border.color: "#24314a"
                    opacity: 0.95

                    Item {
                        anchors.fill: parent

                        Rectangle {
                            width: 54
                            height: 54
                            radius: 10
                            color: "#1c2538"
                            border.width: 1
                            border.color: "#2b3a56"
                            anchors.left: parent.left
                            anchors.leftMargin: 0
                            anchors.verticalCenter: parent.verticalCenter
                            Image {
                                anchors.centerIn: parent
                                source: gestureIconUrl
                                width: 40
                                height: 40
                                sourceSize.width: 40
                                sourceSize.height: 40
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                rotation: -90
                            }
                        }

                        Text {
                            text: "TO ACTIVATE MODE SELECT"
                            color: "#9bb4ff"
                            font.pixelSize: 10
                            font.letterSpacing: 1
                            anchors.left: parent.left
                            anchors.leftMargin: 70
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#26304a"
                }

                ColumnLayout {
                    spacing: 8
                    Layout.fillWidth: true
                    Layout.topMargin: 2

                    Text {
                        text: "MODES"
                        color: "#8793aa"
                        font.pixelSize: 12
                    }

                    ModeRow { label: "NORMAL"; keyLabel: modeKeyNormal; active: uiState.selectedMode === "normal" }
                    ModeRow { label: "DRAW"; keyLabel: modeKeyDraw; active: uiState.selectedMode === "draw" }
                    ModeRow { label: "ZOOM"; keyLabel: modeKeyZoom; active: uiState.selectedMode === "zoom" }
                    ModeRow { label: "SCROLL"; keyLabel: modeKeyScroll; active: uiState.selectedMode === "scroll" }
                    ModeRow { label: "PAUSE"; keyLabel: modeKeyPause; active: uiState.selectedMode === "pause" }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#26304a"
                }

                Item { Layout.fillHeight: true }
            }

            ColumnLayout {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 20
                anchors.bottomMargin: 10
                spacing: 6
                Text {
                    text: "PERFORMANCE"
                    color: "#8793aa"
                    font.pixelSize: 12
                }
                RowLayout {
                    spacing: 10
                    Text { text: "HAND"; color: "#8793aa"; font.pixelSize: 11 }
                    Text { text: uiState.handFps.toFixed(1); color: "#7fb0ff"; font.pixelSize: 14 }
                    Text { text: "FPS"; color: "#8793aa"; font.pixelSize: 11 }
                }
                RowLayout {
                    spacing: 10
                    Text { text: "DROPS"; color: "#8793aa"; font.pixelSize: 11 }
                    Text { text: uiState.dropFps.toFixed(1); color: "#7fb0ff"; font.pixelSize: 14 }
                    Text { text: "/S"; color: "#8793aa"; font.pixelSize: 11 }
                }
            }
        }
    }

    Popup {
        id: infoPopup
        modal: true
        focus: true
        anchors.centerIn: parent
        width: 540
        height: 380
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        enter: Transition { NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: 160 } }
        exit: Transition { NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: 140 } }

        background: Rectangle {
            radius: 18
            color: "#151c2a"
            border.color: "#2a3754"
            border.width: 1
            layer.enabled: true
            layer.effect: DropShadow {
                horizontalOffset: 0
                verticalOffset: 18
                radius: 32
                samples: 32
                color: "#88000000"
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            Text {
                text: "HELP"
                color: "#7fb0ff"
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            Text {
                text: "<p>The cursor follows the center of your palm. Keep your hand wide open and touch your index finger and thumb to perform a left click, or your middle finger and thumb for a right click.</p>\n<ul>\n<li>To <b>select a mode</b>, close your hand then press the key corresponding to the desired mode.</li>\n<li>You can also choose to <b>hide the window</b> FingerFlow by closing your hand and pressing the T key on your keyboard (just repeat this step to show the window again).</li>\n<li>To <b>quit the program</b>, press QUIT.</li>\n</ul>\n<p><b>Tips:</b></p>\n<ul>\n<li>Keep your palm facing the camera, this avoids false left or right clicks.</li>\n</ul>"
                color: "#cdd5e3"
                font.pixelSize: 14
                textFormat: Text.RichText
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignLeft
            }
            Item { Layout.fillHeight: true }
            Button {
                text: "OK"
                font.pixelSize: 14
                Layout.preferredWidth: 120
                Layout.preferredHeight: 30
                onClicked: infoPopup.close()
            }
        }
    }

    component ModeRow: Rectangle {
        property string label: ""
        property string keyLabel: ""
        property bool active: false
        radius: 10
        height: 34
        Layout.fillWidth: true
        Layout.leftMargin: 8
        Layout.rightMargin: 12
        color: active ? "#1f3b2f" : "#1a2234"
        border.color: active ? "#48d597" : "#27324a"
        border.width: 1
        Behavior on color { ColorAnimation { duration: 180 } }
        Behavior on border.color { ColorAnimation { duration: 180 } }

        Item {
            anchors.fill: parent
            anchors.margins: 10
            Rectangle {
                width: 10
                height: 10
                radius: 5
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                color: active ? "#5ce0a1" : "#51607a"
            }
            Item {
                id: labelArea
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 22
                height: parent.height
            }
            Text {
                text: label
                anchors.centerIn: labelArea
                color: active ? "#e9f7f0" : "#c1c9da"
                font.pixelSize: 13
                font.weight: active ? Font.DemiBold : Font.Normal
            }
            Rectangle {
                width: 26
                height: 20
                radius: 6
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                color: active ? "#294a3c" : "#20283a"
                border.width: 1
                border.color: active ? "#3f7a60" : "#2a344a"
                Text {
                    anchors.centerIn: parent
                    text: keyLabel
                    color: "#cdd5e3"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
            }
        }
    }
}
