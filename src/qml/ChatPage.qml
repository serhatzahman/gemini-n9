import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id: chatPage
    tools: chatTools

    property string attachedImagePath: ""
    property string currentModel: "gemini-3.8-flash"
    property string activeMessageText: ""
    property bool isWaitingResponse: false
    property bool isRecordingAudio: false
    property string currentPersonaTitle: "Standart Gemini"

    // AMOLED Deep Black
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        z: 0
    }

    // Modal Popup Dialog for Errors
    QueryDialog {
        id: chatErrorDialog
        titleText: "Sohbet Bildirimi"
        message: ""
        acceptButtonText: "Tamam"
    }

    // Confirm Clear Dialog
    QueryDialog {
        id: clearConfirmDialog
        titleText: "Sohbeti Temizle"
        message: "Tüm sohbet geçmişi silinsin mi?"
        acceptButtonText: "Evet, Sil"
        rejectButtonText: "Vazgeç"
        onAccepted: {
            messageModel.clear();
            geminiBridge.clearHistory();
        }
    }

    // Model Selection Dialog
    SelectionDialog {
        id: modelSelectionDialog
        titleText: "Gemini Model Seçimi"
        model: ListModel {
            ListElement { name: "Gemini 3.8 Flash (Hızlı & Günlük)"; modelId: "gemini-3.8-flash" }
            ListElement { name: "Gemini 3.1 Pro (Derin Akıl Yürütme)"; modelId: "gemini-3.1-pro-preview" }
        }
        onAccepted: {
            if (selectedIndex >= 0 && selectedIndex < model.count) {
                var mId = model.get(selectedIndex).modelId;
                geminiBridge.setModel(mId);
            }
        }
    }

    // Persona Selection Dialog
    SelectionDialog {
        id: personaSelectionDialog
        titleText: "Gemini Rol / Karakter Seçimi"
        model: ListModel {
            ListElement { name: "Standart Gemini (Günlük Asistan)"; personaId: "default" }
            ListElement { name: "MeeGo & Linux Uzmanı (Kod & Terminal)"; personaId: "meego_expert" }
            ListElement { name: "Türkçe Yazı Editörü (İmla & Edebiyat)"; personaId: "writer" }
            ListElement { name: "Kısa & Net Özetleyici (Maddeler)"; personaId: "concise" }
        }
        onAccepted: {
            if (selectedIndex >= 0 && selectedIndex < model.count) {
                var pId = model.get(selectedIndex).personaId;
                geminiBridge.setPersona(pId);
            }
        }
    }

    // Photo Attachment Choice Dialog
    SelectionDialog {
        id: attachChoiceDialog
        titleText: "Fotoğraf Ekle (Gemini Vision)"
        model: ListModel {
            ListElement { name: "Kamerayı Aç (Fotoğraf Çek)" }
            ListElement { name: "En Son Çekilen Fotoğrafı Ekle" }
            ListElement { name: "Galeriden Fotoğraf Seç..." }
        }
        onAccepted: {
            if (selectedIndex === 0) {
                geminiBridge.launchCamera();
            } else if (selectedIndex === 1) {
                var latest = geminiBridge.getLatestDcimPhoto();
                if (latest && latest.length > 0) {
                    attachedImagePath = latest;
                } else {
                    geminiBridge.postToEventsScreen("Fotoğraf", "DCIM klasöründe fotoğraf bulunamadı.");
                }
            } else if (selectedIndex === 2) {
                openGalleryPicker();
            }
        }
    }

    // Gallery Photo Picker Dialog
    SelectionDialog {
        id: photoPickerDialog
        titleText: "Galeriden Seç"
        model: ListModel { id: photoModel }

        onAccepted: {
            if (selectedIndex >= 0 && selectedIndex < photoModel.count) {
                attachedImagePath = photoModel.get(selectedIndex).filePath;
            }
        }
    }

    function openGalleryPicker() {
        photoModel.clear();
        var photosJson = geminiBridge.getRecentPhotosJson();
        try {
            var photos = JSON.parse(photosJson);
            for (var i = 0; i < photos.length; i++) {
                var p = photos[i];
                var name = p.substring(p.lastIndexOf("/") + 1);
                photoModel.append({ name: name, filePath: p });
            }
            if (photos.length > 0) {
                photoPickerDialog.open();
            } else {
                geminiBridge.postToEventsScreen("Fotoğraf", "Galeride fotoğraf bulunamadı.");
            }
        } catch (e) {
        }
    }

    ListModel {
        id: messageModel
    }

    Component.onCompleted: {
        currentModel = geminiBridge.getModel();
        currentPersonaTitle = geminiBridge.getCurrentPersonaTitle();
        var savedJson = geminiBridge.getSavedHistoryJson();
        try {
            var arr = JSON.parse(savedJson);
            if (arr && arr.length > 0) {
                for (var i = 0; i < arr.length; i++) {
                    messageModel.append({
                        role: arr[i].role,
                        content: arr[i].text,
                        image: arr[i].image ? arr[i].image : "",
                        time: "Geçmiş"
                    });
                }
            } else {
                messageModel.append({
                    role: "model",
                    content: "Merhaba! Ben Nokia N9 için Gemini asistanınız. Size nasıl yardımcı olabilirim?",
                    image: "",
                    time: "Şimdi"
                });
            }
        } catch (e) {
            messageModel.append({
                role: "model",
                content: "Merhaba! Size nasıl yardımcı olabilirim?",
                image: "",
                time: "Şimdi"
            });
        }
        chatListView.positionViewAtEnd();
    }

    Connections {
        target: geminiBridge
        onMessageReceived: {
            isWaitingResponse = false;
            try {
                var msg = JSON.parse(geminiBridge.getLastMessageJson());
                var now = new Date();
                var timeStr = ("0" + now.getHours()).slice(-2) + ":" + ("0" + now.getMinutes()).slice(-2);
                messageModel.append({
                    role: msg.role,
                    content: msg.text,
                    image: msg.image ? msg.image : "",
                    time: timeStr
                });
                chatListView.positionViewAtEnd();
                if (msg.role === "error") {
                    chatErrorDialog.message = msg.text;
                    chatErrorDialog.open();
                }
            } catch (e) {
            }
        }
        onBusyChanged: {
            var b = geminiBridge.isBusy();
            isWaitingResponse = b;
        }
        onModelChanged: {
            currentModel = geminiBridge.getModel();
        }
        onRecordingChanged: {
            isRecordingAudio = geminiBridge.isRecording();
        }
        onPersonaChanged: {
            currentPersonaTitle = geminiBridge.getCurrentPersonaTitle();
        }
    }

    // Top Header Bar with Original Google Gemini Brand Logo
    Rectangle {
        id: headerBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 60
        color: "#121214"
        z: 3

        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#28282C"
        }

        Row {
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8

            // Orijinal Google Gemini Logosu
            Image {
                anchors.verticalCenter: parent.verticalCenter
                width: 124
                height: 33
                source: "../icons/gemini-original-logo.png"
                smooth: true
            }

            // Tıklanabilir Model Rozeti
            Rectangle {
                id: modelBadge
                anchors.verticalCenter: parent.verticalCenter
                width: modelBadgeRow.width + 12
                height: 26
                radius: 13
                color: (currentModel.indexOf("pro") !== -1) ? "#261536" : "#162338"
                border.color: (currentModel.indexOf("pro") !== -1) ? "#8A2BE2" : "#0078D7"
                border.width: 1

                Row {
                    id: modelBadgeRow
                    anchors.centerIn: parent
                    spacing: 3

                    Text {
                        text: (currentModel.indexOf("pro") !== -1) ? "3.1 Pro" : "3.8 Flash"
                        color: (currentModel.indexOf("pro") !== -1) ? "#D946EF" : "#54A5FF"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Text {
                        text: "v"
                        color: (currentModel.indexOf("pro") !== -1) ? "#D946EF" : "#54A5FF"
                        font.pixelSize: 10
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: modelSelectionDialog.open()
                }
            }

            // Rol / Persona Rozeti
            Rectangle {
                id: personaBadge
                anchors.verticalCenter: parent.verticalCenter
                width: personaBadgeText.paintedWidth + 12
                height: 24
                radius: 12
                color: "#1B1B22"
                border.color: "#353542"
                border.width: 1

                Text {
                    id: personaBadgeText
                    anchors.centerIn: parent
                    text: currentPersonaTitle
                    color: "#A0A0B0"
                    font.pixelSize: 11
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: personaSelectionDialog.open()
                }
            }
        }

        // Header Animated Spinner
        Item {
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            width: 22
            height: 22
            visible: isWaitingResponse

            Rectangle {
                id: headerSpinRing
                anchors.fill: parent
                radius: 11
                color: "transparent"
                border.color: (currentModel.indexOf("pro") !== -1) ? "#8A2BE2" : "#0078D7"
                border.width: 2

                Rectangle {
                    width: 6
                    height: 6
                    radius: 3
                    color: (currentModel.indexOf("pro") !== -1) ? "#D946EF" : "#54A5FF"
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                NumberAnimation on rotation {
                    running: isWaitingResponse
                    loops: Animation.Infinite
                    from: 0
                    to: 360
                    duration: 750
                }
            }
        }
    }

    // Message Actions Menu (Clean text without emojis)
    ContextMenu {
        id: messageActionMenu
        MenuLayout {
            MenuItem {
                text: "Panoya Kopyala"
                onClicked: geminiBridge.copyToClipboard(activeMessageText)
            }
            MenuItem {
                text: "Seslendir (TTS)"
                onClicked: geminiBridge.speakText(activeMessageText)
            }
            MenuItem {
                text: "Tam Ekran Oku (Zen)"
                onClicked: zenReader.visible = true
            }
            MenuItem {
                text: "Events Ekranına Gönder"
                onClicked: geminiBridge.postToEventsScreen("Gemini Notu", activeMessageText)
            }
        }
    }

    // More Options Toolbar Menu (Clean text without emojis)
    ContextMenu {
        id: chatMoreMenu
        MenuLayout {
            MenuItem {
                text: "Rol / Karakter Seç..."
                onClicked: personaSelectionDialog.open()
            }
            MenuItem {
                text: "Model Değiştir..."
                onClicked: modelSelectionDialog.open()
            }
            MenuItem {
                text: "Sohbeti Dışa Aktar (.txt)"
                onClicked: geminiBridge.exportHistory()
            }
            MenuItem {
                text: "Sohbeti Temizle..."
                onClicked: clearConfirmDialog.open()
            }
        }
    }

    // Messages List
    ListView {
        id: chatListView
        anchors.top: headerBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: (isWaitingResponse) ? thinkingBubble.top : chipsContainer.top
        anchors.margins: 8
        clip: true
        model: messageModel
        spacing: 12

        footer: Item {
            width: chatListView.width
            height: 28
        }

        delegate: Item {
            id: delegateItem
            width: chatListView.width
            height: bubbleRect.height + 6

            Text {
                id: contentDummy
                visible: false
                text: content
                font.pixelSize: 20
            }

            property int maxBubbleWidth: chatListView.width * 0.84

            Rectangle {
                id: bubbleRect
                anchors.right: (role === "user") ? parent.right : undefined
                anchors.left: (role !== "user") ? parent.left : undefined
                anchors.rightMargin: (role === "user") ? 6 : 0
                anchors.leftMargin: (role !== "user") ? 6 : 0

                width: Math.max(
                    70,
                    Math.min(
                        maxBubbleWidth,
                        Math.max(contentDummy.paintedWidth, timeLabel.paintedWidth) + 26
                    )
                )

                height: bubbleCol.height + 16
                radius: 14

                color: (role === "user") ? "#0066CC" : ((role === "error") ? "#4A1515" : "#18181C")
                border.color: (role === "user") ? "#2980D6" : ((role === "error") ? "#EA4335" : "#2A2A34")
                border.width: 1

                Column {
                    id: bubbleCol
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 10
                    spacing: 6

                    Image {
                        width: Math.min(220, bubbleRect.width - 20)
                        height: 140
                        fillMode: Image.PreserveAspectCrop
                        clip: true
                        source: (image && image.length > 0) ? ("file://" + image) : ""
                        visible: (image && image.length > 0)
                    }

                    Text {
                        id: messageText
                        width: bubbleRect.width - 20
                        text: content
                        color: "#FFFFFF"
                        font.pixelSize: 20
                        wrapMode: Text.Wrap
                    }

                    Row {
                        anchors.right: parent.right
                        spacing: 8

                        Text {
                            id: timeLabel
                            text: time
                            color: (role === "user") ? "#B2D7FF" : "#777780"
                            font.pixelSize: 12
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onPressAndHold: {
                        activeMessageText = content;
                        messageActionMenu.open();
                    }
                }
            }
        }
    }

    // In-chat Animated Thinking Bubble
    Rectangle {
        id: thinkingBubble
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.bottom: chipsContainer.top
        anchors.bottomMargin: 6
        width: thinkingRow.width + 26
        height: 46
        radius: 23
        color: "#16161C"
        border.color: (currentModel.indexOf("pro") !== -1) ? "#8A2BE2" : "#0078D7"
        border.width: 2
        visible: isWaitingResponse
        z: 3

        Row {
            id: thinkingRow
            anchors.centerIn: parent
            spacing: 12

            Item {
                width: 24
                height: 24
                anchors.verticalCenter: parent.verticalCenter

                Rectangle {
                    id: bubbleSpinRing
                    anchors.fill: parent
                    radius: 12
                    color: "transparent"
                    border.color: (currentModel.indexOf("pro") !== -1) ? "#8A2BE2" : "#0078D7"
                    border.width: 3

                    Rectangle {
                        width: 7
                        height: 7
                        radius: 3.5
                        color: (currentModel.indexOf("pro") !== -1) ? "#D946EF" : "#54A5FF"
                        anchors.top: parent.top
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    NumberAnimation on rotation {
                        running: isWaitingResponse
                        loops: Animation.Infinite
                        from: 0
                        to: 360
                        duration: 750
                    }
                }
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: (currentModel.indexOf("pro") !== -1) ? "Gemini 3.1 Pro düşünüyor..." : "Gemini yanıt hazırlıyor..."
                color: (currentModel.indexOf("pro") !== -1) ? "#D946EF" : "#54A5FF"
                font.pixelSize: 15
                font.bold: true
            }
        }
    }

    // Quick Prompt Chips Bar
    Rectangle {
        id: chipsContainer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: (attachedPreview.visible) ? attachedPreview.top : inputBar.top
        height: 38
        color: "#0A0A0C"
        z: 2

        ListView {
            id: chipsList
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            orientation: ListView.Horizontal
            spacing: 8
            clip: true

            model: ListModel {
                ListElement { chipTitle: "Özetle"; chipPrompt: "Lütfen yukarıdaki konuyu maddeler halinde kısaca özetle." }
                ListElement { chipTitle: "Çevir"; chipPrompt: "Bu metni akıcı bir Türkçe ile çevir: " }
                ListElement { chipTitle: "MeeGo İpucu"; chipPrompt: "Nokia N9 ve MeeGo Harmattan için faydalı bir terminal ipucu ver." }
                ListElement { chipTitle: "Düzelt"; chipPrompt: "Şu metindeki yazım ve noktalama hatalarını düzelt: " }
                ListElement { chipTitle: "Duvar Kâğıdı"; chipPrompt: "Nokia N9 için harika bir AMOLED duvar kâğıdı promptu öner." }
                ListElement { chipTitle: "Rol Seç"; chipPrompt: "CMD_PERSONA" }
                ListElement { chipTitle: "Dışa Aktar"; chipPrompt: "CMD_EXPORT" }
            }

            delegate: Rectangle {
                height: 28
                anchors.verticalCenter: parent.verticalCenter
                width: chipText.paintedWidth + 18
                radius: 14
                color: "#1E1E24"
                border.color: "#34343E"
                border.width: 1

                Text {
                    id: chipText
                    anchors.centerIn: parent
                    text: chipTitle
                    color: "#D0D0D8"
                    font.pixelSize: 13
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (chipPrompt === "CMD_PERSONA") {
                            personaSelectionDialog.open();
                        } else if (chipPrompt === "CMD_EXPORT") {
                            geminiBridge.exportHistory();
                        } else if (chipPrompt.slice(-2) === ": ") {
                            messageInput.text = chipPrompt;
                            messageInput.forceActiveFocus();
                        } else {
                            isWaitingResponse = true;
                            geminiBridge.sendMessage(chipPrompt, attachedImagePath);
                            attachedImagePath = "";
                        }
                    }
                }
            }
        }
    }

    // Attached Image Preview Strip
    Rectangle {
        id: attachedPreview
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: inputBar.top
        height: 48
        color: "#18181C"
        visible: (attachedImagePath.length > 0)
        z: 2

        Row {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 10

            Image {
                width: 36
                height: 36
                fillMode: Image.PreserveAspectCrop
                source: (attachedImagePath.length > 0) ? ("file://" + attachedImagePath) : ""
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "Fotoğraf eklendi (Vision analizi)"
                color: "#54A5FF"
                font.pixelSize: 14
            }

            Button {
                anchors.verticalCenter: parent.verticalCenter
                text: "Kaldır"
                height: 32
                onClicked: attachedImagePath = ""
            }
        }
    }

    // Bottom Input Bar
    Rectangle {
        id: inputBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 64
        color: "#121214"
        z: 2

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 1
            color: "#28282C"
        }

        // Attach Button (Camera & Gallery options)
        Button {
            id: attachButton
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            height: 44
            iconSource: "image://theme/icon-m-toolbar-attachment"
            onClicked: attachChoiceDialog.open()
        }

        // Voice Recording Button (Microphone Icon)
        Button {
            id: micButton
            anchors.left: attachButton.right
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            height: 44
            iconSource: isRecordingAudio ? "../icons/mic-recording.png" : "../icons/mic-normal.png"
            onClicked: geminiBridge.toggleVoiceRecording()
        }

        TextField {
            id: messageInput
            anchors.left: micButton.right
            anchors.leftMargin: 6
            anchors.right: sendButton.left
            anchors.rightMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            placeholderText: isRecordingAudio ? "Sesiniz kaydediliyor..." : (isWaitingResponse ? "Gemini yanıt hazırlıyor..." : ((attachedImagePath.length > 0) ? "Fotoğraf hakkında sorun..." : "Mesajınızı yazın..."))
            font.pixelSize: 19
            enabled: !isWaitingResponse && !isRecordingAudio

            Keys.onReturnPressed: {
                if ((messageInput.text.trim().length > 0 || attachedImagePath.length > 0) && !isWaitingResponse) {
                    isWaitingResponse = true;
                    geminiBridge.sendMessage(messageInput.text, attachedImagePath);
                    messageInput.text = "";
                    attachedImagePath = "";
                }
            }
        }

        Button {
            id: sendButton
            anchors.right: parent.right
            anchors.rightMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            width: 44
            height: 44
            iconSource: (messageInput.text.trim().length > 0 || attachedImagePath.length > 0) ? "../icons/send-active.png" : "../icons/send-normal.png"
            enabled: !isWaitingResponse && !isRecordingAudio && (messageInput.text.trim().length > 0 || attachedImagePath.length > 0)

            onClicked: {
                if ((messageInput.text.trim().length > 0 || attachedImagePath.length > 0) && !isWaitingResponse) {
                    isWaitingResponse = true;
                    geminiBridge.sendMessage(messageInput.text, attachedImagePath);
                    messageInput.text = "";
                    attachedImagePath = "";
                }
            }
        }
    }

    // Fullscreen AMOLED Zen Reader Overlay
    Rectangle {
        id: zenReader
        anchors.fill: parent
        color: "#000000"
        visible: false
        z: 99

        Rectangle {
            id: zenHeader
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 60
            color: "#121214"

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
                text: "AMOLED Okuma Modu"
                color: "#FFFFFF"
                font.pixelSize: 18
                font.bold: true
            }

            Row {
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                Button {
                    height: 38
                    text: "Seslendir"
                    onClicked: geminiBridge.speakText(activeMessageText)
                }

                Button {
                    height: 38
                    text: "Kapat"
                    onClicked: zenReader.visible = false
                }
            }
        }

        Flickable {
            anchors.top: zenHeader.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 16
            contentHeight: zenContentText.paintedHeight + 50
            clip: true

            Text {
                id: zenContentText
                width: parent.width
                text: activeMessageText
                color: "#F0F0F5"
                font.pixelSize: 22
                wrapMode: Text.Wrap
            }
        }
    }

    // Harmattan ToolBar
    ToolBarLayout {
        id: chatTools

        ToolIcon {
            iconId: "toolbar-gallery"
            onClicked: pageStack.push(imagePage)
        }

        ToolIcon {
            iconId: "toolbar-settings"
            onClicked: pageStack.push(settingsPage)
        }

        ToolIcon {
            iconId: "toolbar-view-menu"
            onClicked: chatMoreMenu.open()
        }
    }
}
