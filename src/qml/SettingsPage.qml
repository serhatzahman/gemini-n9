import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id: settingsPage
    tools: settingsTools

    property string selectedModel: "gemini-3.8-flash"

    Rectangle {
        anchors.fill: parent
        color: "#000000"
        z: 0
    }

    Component.onCompleted: {
        apiKeyField.text = geminiBridge.getApiKey();
        oauthTokenField.text = geminiBridge.getOAuthToken();
        proxyField.text = geminiBridge.getProxyUrl();
        selectedModel = geminiBridge.getModel();
        systemPromptField.text = geminiBridge.getSystemPrompt();
    }

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

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            text: "Ayarlar & Hesap"
            color: "#FFFFFF"
            font.pixelSize: 24
            font.bold: true
        }
    }

    SelectionDialog {
        id: modelDialog
        titleText: "Gemini Modeli Seçin"
        selectedIndex: (selectedModel === "gemini-3.1-pro-preview") ? 1 : ((selectedModel === "gemini-flash-latest") ? 2 : 0)
        model: ListModel {
            ListElement { name: "Gemini 3.8 Flash (Önerilen & Hızlı)" }
            ListElement { name: "Gemini 3.1 Pro Preview (Gelişmiş)" }
            ListElement { name: "Gemini Flash Latest" }
        }
        onAccepted: {
            if (selectedIndex === 1) {
                selectedModel = "gemini-3.1-pro-preview";
            } else if (selectedIndex === 2) {
                selectedModel = "gemini-flash-latest";
            } else {
                selectedModel = "gemini-3.8-flash";
            }
        }
    }

    Flickable {
        anchors.top: headerBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        contentHeight: 820
        clip: true

        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 12

            Text {
                text: "Google Gemini API Anahtarı:"
                color: "#9999A0"
                font.pixelSize: 17
            }

            TextField {
                id: apiKeyField
                width: parent.width
                placeholderText: "AIzaSy... veya AQ.Ab8..."
                echoMode: TextInput.Normal
                font.pixelSize: 16
            }

            Text {
                width: parent.width
                text: "Ücretsiz anahtarınızı https://aistudio.google.com adresinden alabilirsiniz."
                color: "#777785"
                font.pixelSize: 13
                wrapMode: Text.Wrap
            }

            Text {
                text: "Google OAuth / Pro Token (Limitsiz Giriş):"
                color: "#54A5FF"
                font.pixelSize: 17
                font.bold: true
            }

            TextField {
                id: oauthTokenField
                width: parent.width
                placeholderText: "ya29.a0A... (İsteğe bağlı Google Token)"
                echoMode: TextInput.PasswordEchoOnEdit
                font.pixelSize: 17
            }

            Text {
                text: "Aracı Proxy URL (TLS aşımı için):"
                color: "#9999A0"
                font.pixelSize: 17
            }

            TextField {
                id: proxyField
                width: parent.width
                placeholderText: "http://192.168.1.100:5000"
                font.pixelSize: 17
            }

            Text {
                text: "Seçili Model:"
                color: "#9999A0"
                font.pixelSize: 17
            }

            Button {
                id: modelSelectButton
                width: parent.width
                height: 48
                text: (selectedModel === "gemini-3.1-pro-preview") ? "Gemini 3.1 Pro (v)" : ((selectedModel === "gemini-flash-latest") ? "Gemini Flash Latest (v)" : "Gemini 3.8 Flash (v)")
                onClicked: modelDialog.open()
            }

            Text {
                text: "Sistem Talimatı (Prompt):"
                color: "#9999A0"
                font.pixelSize: 17
            }

            TextArea {
                id: systemPromptField
                width: parent.width
                height: 110
                font.pixelSize: 15
            }

            Button {
                width: parent.width
                height: 48
                text: "Ayarları Kaydet"
                onClicked: {
                    geminiBridge.saveConfigWithOAuth(
                        apiKeyField.text,
                        oauthTokenField.text,
                        proxyField.text,
                        selectedModel,
                        systemPromptField.text
                    );
                    pageStack.pop();
                }
            }
        }
    }

    ToolBarLayout {
        id: settingsTools

        ToolIcon {
            iconId: "toolbar-back"
            onClicked: pageStack.pop()
        }
    }
}
