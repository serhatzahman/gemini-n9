<img width="1376" height="768" alt="banner gemini" src="https://github.com/user-attachments/assets/16bfc0cd-74c8-478a-8e1f-d60794221467" />
# Google Gemini Client for Nokia N9 (MeeGo 1.2 Harmattan)

[![Platform](https://img.shields.io/badge/Platform-MeeGo%201.2%20Harmattan-blue.svg)](https://en.wikipedia.org/wiki/MeeGo)
[![Device](https://img.shields.io/badge/Device-Nokia%20N9-lightgrey.svg)](https://en.wikipedia.org/wiki/Nokia_N9)
[![UI](https://img.shields.io/badge/UI-QtQuick%201.1%20%7C%20Blanco-green.svg)](https://qt.io)
[![Runtime](https://img.shields.io/badge/Runtime-Python%202.7%20%2B%20PySide-yellow.svg)](https://pyside.org)
[![API](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

A fully native, feature-complete **Google Gemini AI Client** built specifically for the iconic **Nokia N9** running MeeGo 1.2 Harmattan.

Designed from the ground up to respect MeeGo's *Blanco* design language, AMOLED display power characteristics, and the unique hardware capabilities of the Nokia N9.

---

## 🔑 Setting Up Your Google Gemini API Key

This repository does **not** include hardcoded API keys. To use the application, provide your own free Gemini API key:

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and generate a free API key.
2. Launch the **Gemini N9** app on your phone.
3. Tap the **Settings (Gear)** icon in the bottom toolbar.
4. Paste your key into the **"Google Gemini API Anahtarı"** field.
5. Tap **"Ayarları Kaydet"** (Save Settings). Your key will be securely saved locally to `/opt/gemini-n9/data/config.json`.

---

## 🌟 Key Features

* **Authentic MeeGo & Gemini Aesthetics:**
  * Native 80x80 Harmattan squircle launcher icon (`gemini-n9.png`).
  * Official Google Gemini multi-color gradient sparkle header branding.
  * Pure AMOLED True Black (`#000000`) background for battery savings.
  * Symmetric 44x44 action buttons with custom pixel-perfect icons (Attachment, Mic, and Paper Plane Send).

* **Advanced Multimodal Intelligence:**
  * **Text Question & Answering:** Powered by `gemini-3.8-flash` and `gemini-3.1-pro-preview`.
  * **Vision (Camera & Gallery):** Analyze images using N9's Carl Zeiss camera or the photo gallery.
  * **Voice Input (Speech-to-Text):** Record audio via N9's built-in microphone using GStreamer and send it directly to Gemini's native audio understanding engine.
  * **Automatic Multi-Model Quota Fallback:** If one model reaches daily free tier limits, the engine automatically falls over to alternative models without failing.

* **AI Image Generation:**
  * Dedicated Image Generation tab with live rotating spinner and elapsed second counter.
  * Dual-engine architecture: Tries Google Generative Media API first, with automatic high-speed fallback to ensure images always generate without quota exhaustion.
  * One-tap **"Duvar Kâğıdı Yap" (Set as Wallpaper)** to immediately apply generated images to the Nokia N9 home screen.
  * Prompt inspiration chips for quick visual ideas.

* **Nokia N9 System Integration:**
  * **MeeGo Events Screen:** Post Gemini summaries or notes directly to the N9 Feeds/Events screen (`com.nokia.home.eventfeed`).
  * **Text-to-Speech (TTS):** Read responses aloud using local speech synthesis or streaming audio.
  * **Zen Reader Mode:** Full-screen AMOLED reader with large typography and distraction-free reading.
  * **Chat Export:** Export conversation history as formatted `.txt` files directly into `/home/user/MyDocs/Documents`.
  * **Persona & Model Switcher:** Switch between General Assistant, MeeGo/Linux Expert, Turkish Writer, and Concise Summarizer on the fly.

---

## 📱 Hardware & OS Requirements

* **Device:** Nokia N9 (16GB or 64GB)
* **Operating System:** MeeGo 1.2 Harmattan (PR 1.2 or PR 1.3 recommended)
* **Pre-installed Packages:**
  * `python` (2.7)
  * `python-pyside.qtgui`
  * `python-pyside.qtdeclarative`
  * `gstreamer0.10-plugins-good` (for microphone input)

---

## 🚀 Installation Guide

### Option 1: Quick Install via Pre-built Package

1. **Copy the package to your Nokia N9:**
   From your PC (PowerShell / Linux Terminal):
   ```bash
   scp -O -oHostKeyAlgorithms=+ssh-rsa releases/gemini-n9-v22.deb user@192.168.8.144:/home/user/
   ```

2. **Install and run on Nokia N9 (as root):**
   Open SSH or terminal on N9:
   ```bash
   devel-su
   # Password: rootme (or your custom root password)

   # Clean previous version and extract package:
   rm -rf /opt/gemini-n9
   dpkg-deb -x /home/user/gemini-n9-v22.deb /
   chmod +x /opt/gemini-n9/main.py

   # Kill any old background instances:
   killall -9 python

   # Run application:
   DISPLAY=:0 python /opt/gemini-n9/main.py
   ```

### Option 2: Build From Source

To build your own `.deb` package on Linux:
```bash
git clone https://github.com/serhatzahman/gemini-n9.git
cd gemini-n9
chmod +x build_deb.sh
./build_deb.sh
```
The resulting `.deb` package will be generated inside the `releases/` directory.

---

## 🛠️ Critical MeeGo Harmattan Quirks & Solutions

1. **Debian Packaging Compression:** Packages must use `dpkg-deb -Zgzip --build` because N9 rejects modern `xz` compression.
2. **PySide 1.0 Signal Stability:** All signals are parameterless (`QtCore.Signal()`) to avoid C++ `QMetaObject` segmentation faults.
3. **Font Glyph Limitations:** Replaced modern emojis with native MeeGo Blanco vector icons (`image://theme/icon-m-*`) to avoid tofu boxes (`[]`).
4. **Limited `/tmp` Storage (tmpfs 4MB):** Audio cache and temp files are safely stored in `/home/user/MyDocs/.gemini_cache` with a 20-second automatic recording cutoff to prevent EGL crashes (`Bad alloc 0x3003`).
5. **Qt 4.7 QML Strictness:** `border.width` strictly requires integer values (`int`).

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
