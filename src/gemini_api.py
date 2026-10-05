# -*- coding: utf-8 -*-
"""
Gemini API Client for Nokia N9 (MeeGo Harmattan) - Version 6
Features:
- Dual Authentication (API Key & Google OAuth Bearer Token)
- Automatic Pro vs. Free Tier Detection
- Automatic 503 High Demand Retry & Model Fallback
- Updated 2026 Models: gemini-3.8-flash & gemini-3.1-pro-preview
"""

import sys
import os
import json
import base64
import time

try:
    import urllib2
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urllib import quote, urlencode
except ImportError:
    import urllib.request as urllib2
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import quote, urlencode

DEFAULT_CONFIG_DIR = "/opt/gemini-n9/data"
CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(DEFAULT_CONFIG_DIR, "history.json")
DEFAULT_PICTURES_DIR = "/home/user/MyDocs/Pictures/Gemini"

# Doğrulanmış API Anahtarınız
# API key is left empty for public repository. Enter your key in Settings.
DEFAULT_API_KEY = ""

DEFAULT_MODEL = "gemini-3.8-flash"
PRO_MODEL = "gemini-3.1-pro-preview"
FALLBACK_FLASH_MODEL = "gemini-flash-latest"

SUPPORTED_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.1-pro-preview",
    "gemini-flash-latest"
]

PERSONA_PRESETS = [
    {
        "id": "default",
        "title": "Standart Gemini",
        "prompt": "Sen Nokia N9 akıllı telefonunda çalışan hızlı, yardımsever ve zeki bir Google Gemini yapay zekâ asistanısın. Kullanıcıya Türkçe, net ve akıcı yanıtlar ver."
    },
    {
        "id": "meego_expert",
        "title": "MeeGo & Linux Uzmanı",
        "prompt": "Sen Nokia N9, MeeGo 1.2 Harmattan, Maemo, Linux terminali, bash betikleri ve Python/Qt geliştirme konularında derin uzmanlığa sahip bir sistem mühendisisin. Yanıtlarında doğrudan terminal komutları, dosya yolları ve pratik çözümler sun."
    },
    {
        "id": "writer",
        "title": "Türkçe Yazı Editörü",
        "prompt": "Sen usta bir Türk edebiyatçısı ve dil editörüsün. Kullanıcının metinlerindeki yazım, imla ve anlatım bozukluklarını düzeltir, zengin ve etkileyici Türkçe metinler yazarsın."
    },
    {
        "id": "concise",
        "title": "Kısa & Net Özetleyici",
        "prompt": "Yanıtlarını sadece en kritik bilgileri içerecek şekilde, maddeler halinde ve son derece kısa, net ve öz tut. Gereksiz giriş ve kapanış cümleleri kullanma."
    }
]

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, concise AI assistant running on a classic Nokia N9 smartphone. "
    "Keep responses readable on a mobile screen. Be direct and helpful."
)

def ensure_dirs():
    for d in [DEFAULT_CONFIG_DIR, DEFAULT_PICTURES_DIR]:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                os.chmod(d, 0o777)
            except Exception:
                pass

def load_settings():
    ensure_dirs()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                d = json.load(f)
                if not d.get("api_key"):
                    d["api_key"] = DEFAULT_API_KEY
                if d.get("model") in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-flash", "gemini-2.5-pro"]:
                    d["model"] = DEFAULT_MODEL
                return d
        except Exception:
            pass
    return {
        "api_key": DEFAULT_API_KEY,
        "oauth_token": "",
        "proxy_url": "",
        "account_tier": "FREE",  # PRO or FREE
        "model": DEFAULT_MODEL,
        "system_instruction": DEFAULT_SYSTEM_PROMPT
    }

def save_settings(settings):
    try:
        ensure_dirs()
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

def load_history():
    ensure_dirs()
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history_list):
    try:
        ensure_dirs()
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_list, f, indent=2)
    except Exception:
        pass


class GeminiClient(object):
    def __init__(self, api_key="", oauth_token="", proxy_url="", model=DEFAULT_MODEL, system_prompt=DEFAULT_SYSTEM_PROMPT):
        self.api_key = api_key or DEFAULT_API_KEY
        self.oauth_token = oauth_token or ""
        self.proxy_url = proxy_url.rstrip("/") if proxy_url else ""
        self.model = model or DEFAULT_MODEL
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.account_tier = "FREE"

    def update_config(self, api_key=None, oauth_token=None, proxy_url=None, model=None, system_prompt=None):
        if api_key is not None:
            self.api_key = api_key or DEFAULT_API_KEY
        if oauth_token is not None:
            self.oauth_token = oauth_token
        if proxy_url is not None:
            self.proxy_url = proxy_url.rstrip("/")
        if model is not None:
            self.model = model
        if system_prompt is not None:
            self.system_prompt = system_prompt

    def detect_account_tier(self):
        """
        Tests whether the current credentials have access to Gemini 3.1 Pro (Pro/Paid tier)
        or are restricted to Free Tier (Flash models).
        Returns: (tier: "PRO"|"FREE"|"ERROR", message: str)
        """
        key = self.api_key or DEFAULT_API_KEY
        if not key and not self.oauth_token:
            return "ERROR", u"API Anahtarı veya Google Hesabı girilmedi."

        # Test request to 3.1 Pro
        url = "https://generativelanguage.googleapis.com/v1beta/models/{0}:generateContent".format(PRO_MODEL)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 2}
        }
        json_body = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NokiaN9-Gemini/3.0"
        }
        if self.oauth_token:
            headers["Authorization"] = "Bearer " + self.oauth_token
        else:
            headers["X-goog-api-key"] = key

        try:
            req = Request(url, data=json_body.encode("utf-8"), headers=headers)
            resp = urlopen(req, timeout=15)
            # If 200 OK -> PRO tier is active!
            self.account_tier = "PRO"
            return "PRO", u"Tebrikler! Pro Hesabınız aktif. Gemini 3.1 Pro ve tüm modeller limitsiz kullanılabilir."
        except HTTPError as e:
            if e.code == 429:
                # Quota exceeded / limit 0 for pro -> Free Tier
                self.account_tier = "FREE"
                return "FREE", u"Standart Ücretsiz Hesap aktif. Gemini 3.8 Flash modeli kullanıma hazır."
            elif e.code == 401:
                return "ERROR", u"Yetkilendirme hatası (401). Lütfen anahtarı kontrol edin."
            elif e.code == 404:
                self.account_tier = "FREE"
                return "FREE", u"Model bulunamadı (404). Flash modeline yönlendiriliyor."
            else:
                self.account_tier = "FREE"
                return "FREE", u"Hesap bağlandı (Standart Plan)."
        except Exception as e:
            self.account_tier = "FREE"
            return "FREE", u"Hesap bağlandı (Çevrimdışı/Standart mod)."

    def send_chat_message(self, prompt, conversation_history=None, image_path=None, audio_path=None):
        """
        Sends chat message with automatic retry on HTTP 503 (high demand) and fallback.
        """
        key = self.api_key or DEFAULT_API_KEY
        if not key and not self.oauth_token:
            return False, u"Lütfen Ayarlar sayfasından Google Gemini API anahtarınızı girin."
        contents = []
        if conversation_history:
            for item in conversation_history:
                role = item.get("role", "user")
                text = item.get("text", "")
                parts = [{"text": text}]
                contents.append({"role": role, "parts": parts})

        user_parts = []
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as img_file:
                    raw_bytes = img_file.read()
                    b64_data = base64.b64encode(raw_bytes).decode("ascii")
                mime_type = "image/jpeg"
                if image_path.lower().endswith(".png"):
                    mime_type = "image/png"
                user_parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
            except Exception as e:
                return False, u"Görsel okunamadı: " + str(e)

        if audio_path and os.path.exists(audio_path):
            try:
                with open(audio_path, "rb") as aud_file:
                    raw_bytes = aud_file.read()
                    b64_data = base64.b64encode(raw_bytes).decode("ascii")
                mime_type = "audio/wav"
                if audio_path.lower().endswith(".mp3"):
                    mime_type = "audio/mp3"
                user_parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
                if not prompt:
                    prompt = u"Bu ses kaydını dinle ve Türkçe olarak yanıt ver."
            except Exception as e:
                return False, u"Ses dosyası okunamadı: " + str(e)

        if prompt:
            user_parts.append({"text": prompt})
        elif image_path:
            user_parts.append({"text": "Describe this image."})

        contents.append({"role": "user", "parts": user_parts})
        payload = {"contents": contents}

        if self.system_prompt:
            payload["system_instruction"] = {"parts": [{"text": self.system_prompt}]}

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NokiaN9-Gemini/3.0"
        }

        if self.oauth_token:
            headers["Authorization"] = "Bearer " + self.oauth_token
        else:
            headers["X-goog-api-key"] = key

        # Otomatik Çoklu-Model Kota ve Talep Koruması (Multi-Model Quota Fallback):
        # Aktif model (örn: gemini-3.8-flash) günlük 20 istek ücretsiz kotasını doldurursa
        # otomatik olarak ayrı kota havuzuna sahip Pro ve Lite modellerine geçer!
        candidate_models = [
            self.model,
            PRO_MODEL,               # gemini-3.1-pro-preview (ayrı kota havuzu)
            "gemini-3.5-flash",       # gemini-3.5-flash
            "gemini-3.8-flash-lite",  # gemini-3.8-flash-lite
            DEFAULT_MODEL,           # gemini-3.8-flash
            FALLBACK_FLASH_MODEL     # gemini-flash-latest
        ]
        models_to_try = []
        for m in candidate_models:
            if m not in models_to_try:
                models_to_try.append(m)

        last_error = ""

        for current_model_name in models_to_try:
            clean_model = current_model_name
            if clean_model.startswith("models/"):
                clean_model = clean_model[7:]

            if self.proxy_url:
                target_url = "{0}/api/chat".format(self.proxy_url)
                req_data = {
                    "api_key": key,
                    "oauth_token": self.oauth_token,
                    "model": clean_model,
                    "payload": payload
                }
                json_body = json.dumps(req_data)
            else:
                target_url = "https://generativelanguage.googleapis.com/v1beta/models/{0}:generateContent".format(clean_model)
                json_body = json.dumps(payload)

            # Max 2 attempts per model (for 503 spikes)
            for attempt in range(2):
                try:
                    req = Request(target_url, data=json_body.encode("utf-8"), headers=headers)
                    resp = urlopen(req, timeout=40)
                    resp_data = resp.read().decode("utf-8")
                    resp_json = json.loads(resp_data)

                    if self.proxy_url and "text" in resp_json:
                        return True, resp_json["text"]

                    candidates = resp_json.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if "text" in p]
                        return True, "".join(text_parts)
                    else:
                        return False, u"Model yanıt üretemedi veya içerik filtrelendi."

                except HTTPError as e:
                    if e.code == 503 and attempt == 0:
                        # 503 High demand spike - wait 1.2s and retry
                        time.sleep(1.2)
                        continue
                    try:
                        err_text = e.read().decode("utf-8")
                        err_json = json.loads(err_text)
                        last_error = err_json.get("error", {}).get("message", str(e))
                    except Exception:
                        last_error = str(e)
                    break
                except Exception as e:
                    last_error = str(e)
                    break

        return False, u"Hata: " + last_error

    def generate_image(self, prompt):
        key = self.api_key or DEFAULT_API_KEY
        ensure_dirs()
        filename = "gemini_{0}.jpg".format(int(time.time()))
        output_path = os.path.join(DEFAULT_PICTURES_DIR, filename)

        auth_header = self.oauth_token or key
        last_err = ""

        # 1. Custom Proxy (if configured)
        if self.proxy_url:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "NokiaN9-Gemini/3.0"
            }
            if self.oauth_token:
                headers["Authorization"] = "Bearer " + self.oauth_token
            else:
                headers["X-goog-api-key"] = key

            target_url = "{0}/api/image".format(self.proxy_url)
            req_data = {"api_key": key, "oauth_token": self.oauth_token, "prompt": prompt}
            try:
                req = Request(target_url, data=json.dumps(req_data).encode("utf-8"), headers=headers)
                resp = urlopen(req, timeout=65)
                resp_json = json.loads(resp.read().decode("utf-8"))
                if "image_b64" in resp_json:
                    img_data = base64.b64decode(resp_json["image_b64"])
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    return True, output_path
            except Exception as e:
                pass

        # 2. Try Google OpenAI Endpoint & Native Endpoint
        openai_models = [
            "gemini-3.1-flash-image-preview",
            "gemini-2.5-flash-image",
            "imagen-3.0-generate-002"
        ]
        openai_url = "https://generativelanguage.googleapis.com/v1beta/openai/images/generations"
        headers_openai = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + auth_header,
            "User-Agent": "NokiaN9-Gemini/3.0"
        }

        for m in openai_models:
            payload = {
                "prompt": prompt,
                "model": m,
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json"
            }
            try:
                req = Request(openai_url, data=json.dumps(payload).encode("utf-8"), headers=headers_openai)
                resp = urlopen(req, timeout=40)
                resp_json = json.loads(resp.read().decode("utf-8"))
                data_list = resp_json.get("data", [])
                if data_list and "b64_json" in data_list[0]:
                    img_data = base64.b64decode(data_list[0]["b64_json"])
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    return True, output_path
            except Exception as e:
                last_err = str(e)
                # Continue to next or fallback

        # 3. Automatic Seamless Fallback: Pollinations AI (High-Speed Free Generative AI)
        # Guarantees images are created even if Google Free Tier quota is 0!
        try:
            prompt_clean = prompt.encode("utf-8") if isinstance(prompt, unicode) else str(prompt)
            quoted_prompt = quote(prompt_clean)
            pollinations_url = "https://image.pollinations.ai/prompt/{0}?width=854&height=480&nologo=true&model=flux".format(quoted_prompt)
            req = Request(pollinations_url, headers={"User-Agent": "NokiaN9-Gemini/3.0"})
            resp = urlopen(req, timeout=50)
            img_data = resp.read()
            if img_data and len(img_data) > 1000:
                with open(output_path, "wb") as f:
                    f.write(img_data)
                return True, output_path
        except Exception as e:
            last_err = str(e)

        return False, u"Görsel Hatası: " + last_err
