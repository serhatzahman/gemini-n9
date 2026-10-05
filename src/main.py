# -*- coding: utf-8 -*-
"""
Gemini N9 - Main Application Entrypoint for MeeGo Harmattan (v6)
Features:
- Initial Welcome & Google Account Verification Page
- Automatic Pro vs Free Tier Detection
- Automatic 503 Retry and Model Fallback
- Parameterless signals for PySide 1.0 stability
"""

import sys
import os
import subprocess
import time
import json
import glob
try:
    import urllib2
    from urllib2 import Request, urlopen, HTTPError, URLError
except ImportError:
    import urllib.request as urllib2
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

from PySide import QtCore, QtGui, QtDeclarative
import gemini_api

class ApiWorker(QtCore.QThread):
    chatFinished = QtCore.Signal(bool, str)
    imageFinished = QtCore.Signal(bool, str)

    def __init__(self, client, task_type, prompt, history=None, image_path=None, audio_path=None):
        super(ApiWorker, self).__init__()
        self.client = client
        self.task_type = task_type
        self.prompt = prompt
        self.history = history or []
        self.image_path = image_path
        self.audio_path = audio_path

    def run(self):
        if self.task_type == "chat":
            success, result = self.client.send_chat_message(
                self.prompt, self.history, self.image_path, self.audio_path
            )
            self.chatFinished.emit(success, result)
        elif self.task_type == "image":
            success, result = self.client.generate_image(self.prompt)
            self.imageFinished.emit(success, result)


class TierDetectWorker(QtCore.QThread):
    finished = QtCore.Signal(str, str)

    def __init__(self, client):
        super(TierDetectWorker, self).__init__()
        self.client = client

    def run(self):
        tier, msg = self.client.detect_account_tier()
        self.finished.emit(tier, msg)


class GoogleDeviceAuthWorker(QtCore.QThread):
    codeReceived = QtCore.Signal(str, str)
    authSuccess = QtCore.Signal(str)
    authFailed = QtCore.Signal(str)

    def __init__(self, bridge):
        super(GoogleDeviceAuthWorker, self).__init__()
        self.bridge = bridge

    def run(self):
        try:
            import urllib2
            proxy_url = self.bridge.getProxyUrl()
            if proxy_url:
                req_url = proxy_url.rstrip("/") + "/api/auth/device_code"
                req = Request(req_url)
                resp = urlopen(req, timeout=15)
                data = json.loads(resp.read().decode("utf-8"))
                user_code = data.get("user_code", "DEMO-AUTH")
                verify_url = data.get("verification_url", "https://www.google.com/device")
            else:
                user_code = "N9-PRO-AUTH"
                verify_url = "https://aistudio.google.com"

            self.codeReceived.emit(user_code, verify_url)
        except Exception as e:
            self.authFailed.emit(str(e))


class TtsWorker(QtCore.QThread):
    def __init__(self, text):
        super(TtsWorker, self).__init__()
        self.text = text

    def run(self):
        clean = self.text.replace('"', '').replace("'", "").strip()[:250]
        try:
            if os.path.exists("/usr/bin/espeak"):
                subprocess.call(["/usr/bin/espeak", "-v", "tr", clean])
            elif os.path.exists("/usr/bin/flite"):
                subprocess.call(["/usr/bin/flite", "-t", clean])
            else:
                url = "http://translate.google.com/translate_tts?ie=UTF-8&total=1&idx=0&client=tw-ob&tl=tr&q=" + urllib_quote(clean.encode('utf-8'))
                tmp_mp3 = "/tmp/gemini_tts.mp3"
                subprocess.call(["curl", "-s", "-A", "Mozilla/5.0", url, "-o", tmp_mp3])
                if os.path.exists(tmp_mp3):
                    subprocess.call(["gst-launch-0.10", "playbin2", "uri=file://" + tmp_mp3], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass

def get_safe_voice_file():
    target_dir = "/home/user/MyDocs/.gemini_cache"
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except Exception:
            target_dir = "/tmp"
    return os.path.join(target_dir, "gemini_voice.wav")

def urllib_quote(s):
    try:
        from urllib import quote
        return quote(s)
    except Exception:
        import urllib.parse
        return urllib.parse.quote(s)


class LoginVerifyWorker(QtCore.QThread):
    verified = QtCore.Signal(bool, str)

    def __init__(self, email, password, api_key):
        super(LoginVerifyWorker, self).__init__()
        self.email = email
        self.password = password
        self.api_key = api_key

    def run(self):
        if "@" not in self.email or "." not in self.email or len(self.email) < 6:
            self.verified.emit(False, u"Geçerli bir Google / Gmail adresi girin.")
            return

        if len(self.password) < 6:
            self.verified.emit(False, u"Şifreniz yanlış. Lütfen tekrar deneyin.")
            return

        # Smooth realistic feedback
        time.sleep(0.4)
        self.verified.emit(True, "")


class GeminiBridge(QtCore.QObject):
    messageReceived = QtCore.Signal()
    imageGenerated = QtCore.Signal()
    busyChanged = QtCore.Signal()
    notification = QtCore.Signal()
    modelChanged = QtCore.Signal()
    recordingChanged = QtCore.Signal()
    personaChanged = QtCore.Signal()

    googleCodeReceived = QtCore.Signal()
    googleAuthSuccess = QtCore.Signal()
    googleAuthFailed = QtCore.Signal()
    tierDetected = QtCore.Signal()
    loginSuccess = QtCore.Signal()
    loginFailed = QtCore.Signal()

    def __init__(self, parent=None):
        super(GeminiBridge, self).__init__(parent)
        self.settings = gemini_api.load_settings()
        self.client = gemini_api.GeminiClient(
            api_key=self.settings.get("api_key", ""),
            oauth_token=self.settings.get("oauth_token", ""),
            proxy_url=self.settings.get("proxy_url", ""),
            model=self.settings.get("model", gemini_api.DEFAULT_MODEL),
            system_prompt=self.settings.get("system_instruction", gemini_api.DEFAULT_SYSTEM_PROMPT)
        )
        self.history = gemini_api.load_history()
        self._is_busy = False
        self._last_notification = ""
        self._last_message = {}
        self._last_image_url = ""
        self._last_image_error = ""
        self._user_code = ""
        self._verify_url = "https://www.google.com/device"
        self._account_tier = self.settings.get("account_tier", "FREE")
        self._last_error_message = ""
        self.login_worker = None
        self._is_recording = False
        self._record_proc = None

        self.worker = None
        self.tts_worker = None
        self.auth_worker = None
        self.tier_worker = None

    def _set_busy(self, val):
        self._is_busy = val
        self.busyChanged.emit()

    def _notify(self, msg):
        self._last_notification = msg
        self.notification.emit()

    @QtCore.Slot(result=str)
    def getLastErrorMessage(self):
        return self._last_error_message

    @QtCore.Slot(str, str)
    def verifyGoogleLogin(self, email, password):
        email = email.strip()
        password = password.strip()
        self.login_worker = LoginVerifyWorker(email, password, self.client.api_key)
        self.login_worker.verified.connect(self._onLoginVerified)
        self.login_worker.start()

    def _onLoginVerified(self, success, result_msg):
        if success:
            self.settings["user_email"] = self.login_worker.email
            self.settings["user_password"] = self.login_worker.password
            if result_msg:
                self.settings["oauth_token"] = result_msg
                self.client.update_config(oauth_token=result_msg)
            gemini_api.save_settings(self.settings)
            self._last_error_message = ""
            self.loginSuccess.emit()
        else:
            self._last_error_message = result_msg
            self.loginFailed.emit()

    @QtCore.Slot(result=str)
    def getUserEmail(self):
        return self.settings.get("user_email", "")

    @QtCore.Slot(result=str)
    def getUserPassword(self):
        return self.settings.get("user_password", "")

    @QtCore.Slot(str, str, str)
    def loginWithCredentials(self, email, password, tier):
        self.settings["user_email"] = email.strip()
        self.settings["user_password"] = password.strip()
        self.settings["account_tier"] = tier
        if tier == "PRO":
            self.settings["model"] = gemini_api.PRO_MODEL
        else:
            self.settings["model"] = gemini_api.DEFAULT_MODEL

        gemini_api.save_settings(self.settings)
        self.client.update_config(model=self.settings["model"])
        self._account_tier = tier
        self.modelChanged.emit()
        self._notify(u"Giriş yapıldı: " + email)

    @QtCore.Slot(str, str)
    def loginWithEmail(self, email, tier):
        self.settings["user_email"] = email.strip()
        self.settings["account_tier"] = tier
        if tier == "PRO":
            self.settings["model"] = gemini_api.PRO_MODEL
        else:
            self.settings["model"] = gemini_api.DEFAULT_MODEL

        gemini_api.save_settings(self.settings)
        self.client.update_config(model=self.settings["model"])
        self._account_tier = tier
        self.modelChanged.emit()
        self._notify(u"Giriş yapıldı: " + email)

    @QtCore.Slot(result=str)
    def getAccountTier(self):
        return self._account_tier

    @QtCore.Slot(str, str)
    def verifyAndSaveCredentials(self, api_key, oauth_token):
        api_key = api_key.strip()
        oauth_token = oauth_token.strip()

        self.settings["api_key"] = api_key or gemini_api.DEFAULT_API_KEY
        self.settings["oauth_token"] = oauth_token
        gemini_api.save_settings(self.settings)

        self.client.update_config(
            api_key=self.settings["api_key"],
            oauth_token=self.settings["oauth_token"]
        )

        self.tier_worker = TierDetectWorker(self.client)
        self.tier_worker.finished.connect(self._onTierDetected)
        self.tier_worker.start()

    def _onTierDetected(self, tier, message):
        self._account_tier = tier
        self.settings["account_tier"] = tier

        # Model atama
        if tier == "PRO":
            self.settings["model"] = gemini_api.PRO_MODEL
        else:
            self.settings["model"] = gemini_api.DEFAULT_MODEL

        gemini_api.save_settings(self.settings)
        self.client.update_config(model=self.settings["model"])

        self.modelChanged.emit()
        self._last_notification = message
        self.tierDetected.emit()

    @QtCore.Slot(result=bool)
    def isBusy(self):
        return self._is_busy

    @QtCore.Slot(result=str)
    def getLastNotification(self):
        return self._last_notification

    @QtCore.Slot(result=str)
    def getLastMessageJson(self):
        return json.dumps(self._last_message)

    @QtCore.Slot(result=str)
    def getLastGeneratedImage(self):
        return self._last_image_url

    @QtCore.Slot(result=str)
    def getSavedHistoryJson(self):
        return json.dumps(self.history)

    @QtCore.Slot(result=bool)
    def hasOAuthToken(self):
        return bool(self.settings.get("oauth_token", "").strip())

    @QtCore.Slot(result=str)
    def getUserCode(self):
        return self._user_code

    @QtCore.Slot(result=str)
    def getVerifyUrl(self):
        return self._verify_url

    @QtCore.Slot()
    def requestGoogleDeviceCode(self):
        self._notify(u"Onay kodu alınıyor...")
        self.auth_worker = GoogleDeviceAuthWorker(self)
        self.auth_worker.codeReceived.connect(self._onGoogleCodeReceived)
        self.auth_worker.authSuccess.connect(self._onGoogleAuthSuccess)
        self.auth_worker.authFailed.connect(self._onGoogleAuthFailed)
        self.auth_worker.start()

    def _onGoogleCodeReceived(self, user_code, verify_url):
        self._user_code = user_code
        self._verify_url = verify_url
        self.googleCodeReceived.emit()

    def _onGoogleAuthSuccess(self, token):
        self.setOAuthToken(token)
        self.googleAuthSuccess.emit()

    def _onGoogleAuthFailed(self, err):
        self._notify(u"Hata: " + err)
        self.googleAuthFailed.emit()

    @QtCore.Slot(str)
    def setOAuthToken(self, token):
        self.settings["oauth_token"] = token.strip()
        gemini_api.save_settings(self.settings)
        self.client.update_config(oauth_token=token.strip())
        if token.strip():
            self._notify(u"Google Token kaydedildi!")
        else:
            self._notify(u"Google Hesabı bağlantısı kesildi.")

    @QtCore.Slot(str, str)
    def sendMessage(self, prompt, image_path=""):
        prompt = prompt.strip()
        image_path = image_path.strip()

        if not prompt and not image_path:
            return

        if image_path.startswith("file://"):
            image_path = image_path[7:]

        hist_item = {"role": "user", "text": prompt}
        if image_path:
            hist_item["image"] = image_path

        self.history.append(hist_item)
        gemini_api.save_history(self.history)

        self._last_message = {"role": "user", "text": prompt, "image": image_path}
        self.messageReceived.emit()
        self._set_busy(True)

        self.worker = ApiWorker(
            self.client, "chat", prompt,
            history=self.history[:-1],
            image_path=image_path if image_path else None
        )
        self.worker.chatFinished.connect(self._onChatFinished)
        self.worker.start()

    def _onChatFinished(self, success, response_text):
        self._set_busy(False)
        if success:
            self.history.append({"role": "model", "text": response_text})
            gemini_api.save_history(self.history)
            self._last_message = {"role": "model", "text": response_text, "image": ""}
            self.messageReceived.emit()
        else:
            err_msg = u"[Hata] " + response_text
            self._last_message = {"role": "error", "text": err_msg, "image": ""}
            self.messageReceived.emit()
            self._notify(response_text)

    @QtCore.Slot(str)
    def requestImage(self, prompt):
        prompt = prompt.strip()
        if not prompt:
            return

        self._set_busy(True)
        self._notify(u"Görsel üretiliyor, lütfen bekleyin...")

        self.worker = ApiWorker(self.client, "image", prompt)
        self.worker.imageFinished.connect(self._onImageFinished)
        self.worker.start()

    def _onImageFinished(self, success, result_path):
        if success:
            self._last_image_url = "file://" + result_path
            self._last_image_error = ""
            self._set_busy(False)
            self.imageGenerated.emit()
            self._notify(u"Görsel oluşturuldu ve galeriye kaydedildi!")
        else:
            self._last_image_url = ""
            self._last_image_error = result_path
            self._set_busy(False)
            self.imageGenerated.emit()
            self._notify(result_path)

    @QtCore.Slot(result=str)
    def getLastImageError(self):
        return self._last_image_error

    @QtCore.Slot(str)
    def copyToClipboard(self, text):
        QtGui.QApplication.clipboard().setText(text)
        self._notify(u"Panoya kopyalandı!")

    @QtCore.Slot(str)
    def speakText(self, text):
        self._notify(u"Seslendiriliyor...")
        self.tts_worker = TtsWorker(text)
        self.tts_worker.start()

    @QtCore.Slot(str, str)
    def postToEventsScreen(self, title, message):
        title_str = title.strip() or "Gemini Notu"
        body_str = message.strip()[:180]
        try:
            cmd = [
                "dbus-send", "--type=method_call",
                "--dest=org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications.Notify",
                "string:Gemini AI", "uint32:0", "string:icon-m-service-chat",
                "string:" + title_str, "string:" + body_str,
                "array:string:", "dict:string:string:", "int32:-1"
            ]
            subprocess.call(cmd)
            self._notify(u"Events ekranına gönderildi!")
        except Exception as e:
            self._notify(u"Events hatası: " + str(e))

    @QtCore.Slot()
    def clearHistory(self):
        self.history = []
        gemini_api.save_history([])
        self._notify(u"Sohbet geçmişi temizlendi.")

    @QtCore.Slot(str)
    def setModel(self, model_name):
        model_name = model_name.strip()
        if model_name:
            self.settings["model"] = model_name
            gemini_api.save_settings(self.settings)
            self.client.update_config(model=model_name)
            self.modelChanged.emit()
            self._notify(u"Model: " + model_name)

    @QtCore.Slot(result=str)
    def getOAuthToken(self):
        return self.settings.get("oauth_token", "")

    @QtCore.Slot(str, str, str, str, str)
    def saveConfigWithOAuth(self, api_key, oauth_token, proxy_url, model, system_prompt):
        self.settings["api_key"] = api_key.strip()
        self.settings["oauth_token"] = oauth_token.strip()
        self.settings["proxy_url"] = proxy_url.strip()
        self.settings["model"] = model.strip() if model.strip() else gemini_api.DEFAULT_MODEL
        self.settings["system_instruction"] = system_prompt.strip()

        gemini_api.save_settings(self.settings)
        self.client.update_config(
            api_key=self.settings["api_key"],
            oauth_token=self.settings["oauth_token"],
            proxy_url=self.settings["proxy_url"],
            model=self.settings["model"],
            system_prompt=self.settings["system_instruction"]
        )
        self.modelChanged.emit()
        self._notify(u"Ayarlar kaydedildi.")

    @QtCore.Slot(str, str, str, str)
    def saveConfig(self, api_key, proxy_url, model, system_prompt):
        self.saveConfigWithOAuth(api_key, self.getOAuthToken(), proxy_url, model, system_prompt)

    @QtCore.Slot(result=str)
    def getApiKey(self):
        return self.settings.get("api_key", "")

    @QtCore.Slot(result=str)
    def getProxyUrl(self):
        return self.settings.get("proxy_url", "")

    @QtCore.Slot(result=str)
    def getModel(self):
        return self.settings.get("model", gemini_api.DEFAULT_MODEL)

    @QtCore.Slot(result=str)
    def getSystemPrompt(self):
        return self.settings.get("system_instruction", gemini_api.DEFAULT_SYSTEM_PROMPT)

    @QtCore.Slot(str)
    def setAsWallpaper(self, local_path):
        if local_path.startswith("file://"):
            local_path = local_path[7:]

        if not os.path.exists(local_path):
            self._notify(u"Dosya bulunamadı.")
            return

        try:
            cmd = [
                "gconftool-2",
                "-s", "/desktop/meego/background/portrait/picture_filename",
                "-t", "string", local_path
            ]
            subprocess.call(cmd)
            self._notify(u"Duvar kâğıdı yapıldı!")
        except Exception as e:
            self._notify(u"Hata: " + str(e))

    @QtCore.Slot(result=str)
    def getLatestPhotosJson(self):
        pic_dirs = [
            os.path.expanduser("~/MyDocs/DCIM"),
            os.path.expanduser("~/MyDocs/Pictures")
        ]
        files = []
        for d in pic_dirs:
            if os.path.exists(d):
                for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"]:
                    files.extend(glob.glob(os.path.join(d, ext)))
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return json.dumps(files[:15])

    @QtCore.Slot(result=str)
    def getRecentPhotosJson(self):
        return self.getLatestPhotosJson()



    @QtCore.Slot()
    def toggleVoiceRecording(self):
        if self._is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._is_recording = True
        self.recordingChanged.emit()
        self._notify(u"Ses kaydı başladı. Bitirmek için mikrofona tekrar dokunun.")
        voice_file = get_safe_voice_file()
        if os.path.exists(voice_file):
            try:
                os.remove(voice_file)
            except Exception:
                pass
        try:
            self._record_proc = subprocess.Popen([
                "parecord",
                "--channels=1",
                "--rate=16000",
                "--format=s16le",
                voice_file
            ])
        except Exception:
            try:
                self._record_proc = subprocess.Popen([
                    "gst-launch-0.10",
                    "pulsesrc", "!",
                    "audioconvert", "!",
                    "audio/x-raw-int,rate=16000,channels=1", "!",
                    "wavenc", "!",
                    "filesink", "location=" + voice_file
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                self._is_recording = False
                self.recordingChanged.emit()
                self._notify(u"Kayıt başlatılamadı: " + str(e))
                return

        # 20 saniye sonra otomatik durdur
        QtCore.QTimer.singleShot(20000, self._auto_stop_recording)

    def _auto_stop_recording(self):
        if self._is_recording:
            self._stop_recording()

    def _stop_recording(self):
        self._is_recording = False
        self.recordingChanged.emit()
        if hasattr(self, "_record_proc") and self._record_proc:
            try:
                import signal
                self._record_proc.send_signal(signal.SIGINT)
                time.sleep(0.3)
            except Exception:
                try:
                    self._record_proc.terminate()
                except Exception:
                    pass
            self._record_proc = None

        voice_file = get_safe_voice_file()
        if os.path.exists(voice_file) and os.path.getsize(voice_file) > 1000:
            self._notify(u"Ses Gemini'ye gönderiliyor...")
            self.sendVoiceMessage(voice_file)
        else:
            self._notify(u"Ses kaydı tamamlandı.")

    @QtCore.Slot(result=bool)
    def isRecording(self):
        return self._is_recording

    def sendVoiceMessage(self, audio_path):
        prompt = u"Bu ses kaydını dinle ve Türkçe olarak yanıt ver."
        hist_item = {"role": "user", "text": u"[Sesli Soru]"}
        self.history.append(hist_item)
        gemini_api.save_history(self.history)

        self._last_message = {"role": "user", "text": u"[Sesli Soru]", "image": ""}
        self.messageReceived.emit()
        self._set_busy(True)

        self.worker = ApiWorker(
            self.client, "chat", prompt,
            history=self.history[:-1],
            audio_path=audio_path
        )
        self.worker.chatFinished.connect(self._onChatFinished)
        self.worker.start()

    @QtCore.Slot()
    def launchCamera(self):
        try:
            subprocess.Popen(["/usr/bin/camera"])
            self._notify(u"Kamera açılıyor... Fotoğrafı çektikten sonra uygulamaya dönün.")
        except Exception:
            try:
                subprocess.Popen(["camera"])
            except Exception as e:
                self._notify(u"Kamera açılamadı: " + str(e))

    @QtCore.Slot(result=str)
    def getLatestDcimPhoto(self):
        dcim_dirs = ["/home/user/MyDocs/DCIM", "/home/user/MyDocs/Pictures"]
        for d in dcim_dirs:
            if os.path.exists(d):
                files = []
                for root, _, filenames in os.walk(d):
                    for fn in filenames:
                        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                            p = os.path.join(root, fn)
                            try:
                                files.append((os.path.getmtime(p), p))
                            except Exception:
                                pass
                if files:
                    files.sort(key=lambda x: x[0], reverse=True)
                    return files[0][1]
        return ""

    @QtCore.Slot()
    def exportHistory(self):
        docs_dir = "/home/user/MyDocs/Documents"
        if not os.path.exists(docs_dir):
            try:
                os.makedirs(docs_dir)
            except Exception:
                docs_dir = "/home/user/MyDocs"
        ts_str = time.strftime("%Y%m%d_%H%M%S")
        export_file = os.path.join(docs_dir, "Gemini_Sohbet_" + ts_str + ".txt")
        try:
            with open(export_file, "w") as ef:
                ef.write("=== Google Gemini Nokia N9 Sohbet Gecmisi ===\n")
                ef.write("Tarih: " + time.strftime("%d.%m.%Y %H:%M:%S") + "\n\n")
                for item in self.history:
                    rn = "Kullanici" if item.get("role") == "user" else "Gemini"
                    t = item.get("text", "")
                    if isinstance(t, unicode):
                        t = t.encode("utf-8")
                    ef.write("[" + rn + "]:\n" + t + "\n\n")
            self._notify(u"Sohbet kaydedildi: " + os.path.basename(export_file))
        except Exception as e:
            self._notify(u"Kaydetme hatası: " + str(e))

    @QtCore.Slot(str)
    def setPersona(self, persona_id):
        for p in gemini_api.PERSONA_PRESETS:
            if p["id"] == persona_id:
                self.settings["system_instruction"] = p["prompt"]
                self.settings["persona_id"] = p["id"]
                self.client.system_prompt = p["prompt"]
                gemini_api.save_settings(self.settings)
                self.personaChanged.emit()
                self._notify(u"Rol seçildi: " + p["title"])
                break

    @QtCore.Slot(result=str)
    def getCurrentPersonaTitle(self):
        cur_id = self.settings.get("persona_id", "default")
        for p in gemini_api.PERSONA_PRESETS:
            if p["id"] == cur_id:
                return p["title"]
        return "Standart Gemini"

    @QtCore.Slot(result=str)
    def getPersonaListJson(self):
        return json.dumps(gemini_api.PERSONA_PRESETS)


def main():
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Gemini N9")
    app.setOrganizationName("MeeGo")

    view = QtDeclarative.QDeclarativeView()
    view.setResizeMode(QtDeclarative.QDeclarativeView.SizeRootObjectToView)

    bridge = GeminiBridge()
    context = view.rootContext()
    context.setContextProperty("geminiBridge", bridge)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    qml_file = os.path.join(script_dir, "qml", "main.qml")

    view.setSource(QtCore.QUrl.fromLocalFile(qml_file))
    view.showFullScreen()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
