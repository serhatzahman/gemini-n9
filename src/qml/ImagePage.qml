import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id: imagePage
    tools: imageTools

    property string currentImagePath: ""
    property string lastErrorText: ""
    property int elapsedSeconds: 0
    property bool isGenerating: false

    // AMOLED True Black Background
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        z: 0
    }

    Timer {
        id: genTimer
        interval: 1000
        repeat: true
        running: isGenerating
        onTriggered: elapsedSeconds += 1
    }

    // Modal Popup Dialog for Errors (Never hidden by navigation bar!)
    QueryDialog {
        id: errorDialog
        titleText: "Görsel Üretim Bildirimi"
        message: lastErrorText
        acceptButtonText: "Tamam"
    }

    Connections {
        target: geminiBridge
        onImageGenerated: {
            isGenerating = false;
            var err = geminiBridge.getLastImageError();
            if (err && err.length > 0) {
                lastErrorText = err;
                errorDialog.message = err;
                errorDialog.open();
            } else {
                lastErrorText = "";
                var url = geminiBridge.getLastGeneratedImage();
                currentImagePath = url;
                generatedImage.source = url;
            }
        }
        onBusyChanged: {
            if (!geminiBridge.isBusy()) {
                isGenerating = false;
                var err = geminiBridge.getLastImageError();
                if (err && err.length > 0) {
                    lastErrorText = err;
                    errorDialog.message = err;
                    errorDialog.open();
                }
            }
        }
    }

    // Top Header Bar
    Rectangle {
        id: headerBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 60
        color: "#121214"
        z: 2

        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#28282C"
        }

        Row {
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8

            Image {
                anchors.verticalCenter: parent.verticalCenter
                width: 120
                height: 32
                source: "../icons/gemini-original-logo.png"
                smooth: true
            }

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 72
                height: 22
                radius: 11
                color: "#1E182A"
                border.color: "#8A2BE2"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "Imagen 3"
                    color: "#D946EF"
                    font.pixelSize: 12
                    font.bold: true
                }
            }
        }
    }

    // Content Area (with ample bottom padding so nothing is cut off)
    Flickable {
        id: contentFlickable
        anchors.top: headerBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        contentHeight: 750
        clip: true

        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 12

            Text {
                text: "Oluşturmak istediğiniz görseli tarif edin:"
                color: "#9999A0"
                font.pixelSize: 17
            }

            TextField {
                id: imagePromptInput
                width: parent.width
                placeholderText: "Örn: Siberpunk neon Nokia N9 telefonu..."
                font.pixelSize: 18
                enabled: !isGenerating
            }

            // Prompt Ideas Bar
            Rectangle {
                width: parent.width
                height: 34
                color: "transparent"

                ListView {
                    anchors.fill: parent
                    orientation: ListView.Horizontal
                    spacing: 8
                    clip: true

                    model: ListModel {
                        ListElement { title: "Nokia N9 Neon"; promptText: "Nokia N9 smartphone in neon cyberpunk city, 8k resolution, cinematic lighting" }
                        ListElement { title: "AMOLED Uzay"; promptText: "Deep space galaxy with purple nebula, true black AMOLED background" }
                        ListElement { title: "Fütüristik Araba"; promptText: "Futuristic concept supercar driving at night with glowing blue lights" }
                        ListElement { title: "Doğa Manzarası"; promptText: "Breathtaking sunset over misty alpine mountains with pine forest" }
                        ListElement { title: "Soyut 3D"; promptText: "Vibrant colorful 3D fluid waves floating in dark minimalist space" }
                    }

                    delegate: Rectangle {
                        height: 28
                        anchors.verticalCenter: parent.verticalCenter
                        width: ideaText.paintedWidth + 16
                        radius: 14
                        color: "#1C1B26"
                        border.color: "#8A2BE2"
                        border.width: 1

                        Text {
                            id: ideaText
                            anchors.centerIn: parent
                            text: title
                            color: "#D946EF"
                            font.pixelSize: 12
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                imagePromptInput.text = promptText;
                            }
                        }
                    }
                }
            }

            // Generate Button
            Button {
                id: generateBtn
                width: parent.width
                height: 48
                text: isGenerating ? ("Oluşturuluyor (" + elapsedSeconds + "s)...") : "Görsel Oluştur"
                enabled: !isGenerating

                onClicked: {
                    if (imagePromptInput.text.trim().length > 0) {
                        currentImagePath = "";
                        generatedImage.source = "";
                        lastErrorText = "";
                        elapsedSeconds = 0;
                        isGenerating = true;
                        geminiBridge.requestImage(imagePromptInput.text);
                    }
                }
            }

            // Visible Error Banner right below button
            Rectangle {
                width: parent.width
                height: errLabel.paintedHeight + 18
                radius: 8
                color: "#301515"
                border.color: "#EA4335"
                border.width: 1
                visible: (lastErrorText.length > 0 && !isGenerating)

                Text {
                    id: errLabel
                    anchors.centerIn: parent
                    width: parent.width - 20
                    text: lastErrorText
                    color: "#F28B82"
                    font.pixelSize: 13
                    wrapMode: Text.Wrap
                }
            }

            // Image Preview Frame with Rotating Spinner + Timer
            Rectangle {
                width: parent.width
                height: 320
                color: "#121216"
                radius: 12
                border.color: "#282832"
                border.width: 1

                // Rotating Spinner & Timer Counter
                Column {
                    anchors.centerIn: parent
                    spacing: 12
                    visible: isGenerating

                    Item {
                        width: 32
                        height: 32
                        anchors.horizontalCenter: parent.horizontalCenter

                        Rectangle {
                            id: imgSpinRing
                            anchors.fill: parent
                            radius: 16
                            color: "transparent"
                            border.color: "#8A2BE2"
                            border.width: 3

                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: "#D946EF"
                                anchors.top: parent.top
                                anchors.horizontalCenter: parent.horizontalCenter
                            }

                            NumberAnimation on rotation {
                                running: isGenerating
                                loops: Animation.Infinite
                                from: 0
                                to: 360
                                duration: 750
                            }
                        }
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Görsel üretiliyor... " + elapsedSeconds + "s"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Yapay zekâ çiziyor, lütfen bekleyin"
                        color: "#888899"
                        font.pixelSize: 13
                    }
                }

                Image {
                    id: generatedImage
                    anchors.fill: parent
                    anchors.margins: 8
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    visible: !isGenerating && (currentImagePath.length > 0)
                }

                Text {
                    anchors.centerIn: parent
                    text: "Üretilen görsel burada belirecek"
                    color: "#555560"
                    font.pixelSize: 16
                    visible: !isGenerating && (currentImagePath.length === 0) && (lastErrorText.length === 0)
                }
            }

            // Wallpaper Action Button
            Button {
                id: wallpaperBtn
                width: parent.width
                height: 48
                text: "Duvar Kâğıdı Yap"
                visible: (currentImagePath.length > 0 && !isGenerating)
                onClicked: {
                    if (currentImagePath.length > 0) {
                        geminiBridge.setAsWallpaper(currentImagePath);
                    }
                }
            }

            Item { height: 70; width: 1 } // Extra clearance for bottom toolbar
        }
    }

    ToolBarLayout {
        id: imageTools

        ToolIcon {
            iconId: "toolbar-back"
            onClicked: pageStack.pop()
        }
    }
}
