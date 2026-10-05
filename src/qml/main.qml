import QtQuick 1.1
import com.nokia.meego 1.0

PageStackWindow {
    id: appWindow
    initialPage: chatPage

    Rectangle {
        id: notificationBanner
        z: 99
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 56
        color: "#1E1E1E"
        opacity: 0
        visible: opacity > 0

        property alias text: bannerText.text

        function show(msg) {
            if (msg) text = msg;
            showAnim.restart();
        }

        Text {
            id: bannerText
            anchors.centerIn: parent
            anchors.margins: 10
            color: "#FFFFFF"
            font.pixelSize: 20
        }

        SequentialAnimation {
            id: showAnim
            NumberAnimation { target: notificationBanner; property: "opacity"; to: 0.95; duration: 200 }
            PauseAnimation { duration: 2500 }
            NumberAnimation { target: notificationBanner; property: "opacity"; to: 0.0; duration: 300 }
        }
    }

    ChatPage {
        id: chatPage
    }

    ImagePage {
        id: imagePage
    }

    SettingsPage {
        id: settingsPage
    }

    Connections {
        target: geminiBridge
        onNotification: {
            notificationBanner.show(geminiBridge.getLastNotification());
        }
    }
}
