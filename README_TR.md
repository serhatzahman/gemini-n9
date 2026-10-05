<img width="1376" height="768" alt="banner gemini" src="https://github.com/user-attachments/assets/da7b630a-8944-45f3-8bb9-5d9522bb40f9" />
# Nokia N9 için Google Gemini Yapay Zekâ İstemcisi (MeeGo 1.2 Harmattan)

[![Platform](https://img.shields.io/badge/Platform-MeeGo%201.2%20Harmattan-blue.svg)](https://en.wikipedia.org/wiki/MeeGo)
[![Cihaz](https://img.shields.io/badge/Cihaz-Nokia%20N9-lightgrey.svg)](https://en.wikipedia.org/wiki/Nokia_N9)
[![Arayüz](https://img.shields.io/badge/Aray%C3%BCz-QtQuick%201.1%20%7C%20Blanco-green.svg)](https://qt.io)
[![Çalışma Ortamı](https://img.shields.io/badge/%C3%87al%C4%B1%C5%9Fma%20Ortam%C4%B1-Python%202.7%20%2B%20PySide-yellow.svg)](https://pyside.org)
[![API](https://img.shields.io/badge/Yapay%20Zek%C3%A2-Google%20Gemini%20API-orange.svg)](https://ai.google.dev)
[![Lisans](https://img.shields.io/badge/Lisans-MIT-purple.svg)](LICENSE)

Efsanevi **Nokia N9** akıllı telefonu ve **MeeGo 1.2 Harmattan** işletim sistemi için sıfırdan geliştirilmiş, yerel (native) ve tam donanımlı **Google Gemini Yapay Zekâ İstemcisi**.

MeeGo'nun ünlü *Blanco* tasarım diline, AMOLED ekranın saf siyah güç tasarrufuna ve N9'un benzersiz donanım yeteneklerine tam uyumlu olarak hazırlanmıştır.

---

## 🔑 Google Gemini API Anahtarınızı Tanımlama

Bu açık kaynaklı depoda kod içine gömülü sabit bir anahtar bulunmaz. Uygulamayı kullanmak için kendi ücretsiz anahtarınızı girmeniz yeterlidir:

1. [Google AI Studio](https://aistudio.google.com/app/apikey) sayfasına giderek ücretsiz bir Gemini API anahtarı oluşturun.
2. Nokia N9'da uygulamayı açın.
3. Sağ alt köşedeki **Ayarlar (Çark)** simgesine dokunun.
4. **"Google Gemini API Anahtarı"** alanına anahtarınızı yapıştırın.
5. **"Ayarları Kaydet"** butonuna basın. Anahtarınız telefonunuzda `/opt/gemini-n9/data/config.json` dosyasına yerel olarak kaydedilecektir.

---

## 🌟 Öne Çıkan Özellikler

* **Özgün MeeGo & Gemini Tasarımı:**
  * MeeGo Blanco standartlarında 80x80 squircle (yuvarlatılmış kare) uygulama menü ikonu (`gemini-n9.png`).
  * Resmi Google Gemini mavi-mor-pembe gradyanlı başlık logosu.
  * Pil tasarrufu sağlayan saf AMOLED siyah (`#000000`) arka plan.
  * 44x44 piksel boyutunda kusursuz simetrik giriş butonları: **Ataç (Galeri/Kamera)**, **Mikrofon (Sesli Giriş)** ve **Kağıt Uçak (Gönder)**.

* **Gelişmiş Çok Modlu (Multimodal) Yapay Zekâ:**
  * **Metin Sohbeti & Soru-Cevap:** `gemini-3.8-flash` ve `gemini-3.1-pro-preview` modelleri.
  * **Kamera & Görsel Analiz (Vision):** N9'un Carl Zeiss kamerasıyla anlık çekilen fotoğrafları veya galerideki görselleri Gemini'ye sorabilme ("Bu nedir?", "Metni çevir" vb.).
  * **Sesli Soru Sorma (Speech-to-Text):** Dahili mikrofon ve GStreamer altyapısıyla sesinizi kaydedip doğrudan Gemini multimodal ses anlama motoruna iletme.
  * **Otomatik Model & Kota Koruması:** Bir modelin günlük ücretsiz istek kotası (20 istek) dolduğunda sistem durmaz; alternatif modeller arasında otomatik geçiş yapar.

* **Yapay Zekâ ile Görsel Üretimi (Image Generation):**
  * Görsel üretim sekmesi, dönen animasyonlu çark ve canlı geçen süre sayacı ("...s").
  * Google API kotası tükendiğinde devreye giren yüksek hızlı FLUX motoru sayesinde kesintisiz üretim garantisi.
  * Tek dokunuşla **"Duvar Kâğıdı Yap"** butonu: Üretilen görseli anında N9 ana ekran duvar kâğıdı yapma.
  * İlham veren hazır istem öneri çipleri.

* **MeeGo Sistem Entegrasyonu:**
  * **Events Screen (Bildirim Akışı):** Yanıtları N9'un kilit ekranı solundaki Akış/Events ekranına bildirim kartı olarak düşürme.
  * **Sesli Okuma (TTS):** Gelen yanıtları sesli olarak dinleme.
  * **Zen Okuma Modu:** Uzun makale ve yanıtları saf siyah ekranda büyük yazı tipiyle rahatça okuma.
  * **Sohbeti Kaydetme:** Konuşmaları tarihli `.txt` dosyası olarak `/home/user/MyDocs/Documents` klasörüne arşivleme.
  * **Rol / Persona Değiştirici:** Tek tıkla "Standart Gemini", "MeeGo & Linux Uzmanı", "Türkçe Yazı Editörü" veya "Kısa & Net Özetleyici" moduna geçiş.

---

## 📱 Donanım ve Sistem Gereksinimleri

* **Cihaz:** Nokia N9 (16GB veya 64GB)
* **İşletim Sistemi:** MeeGo 1.2 Harmattan (PR 1.2 veya PR 1.3)
* **Gerekli Paketler:**
  * `python` (2.7)
  * `python-pyside.qtgui`
  * `python-pyside.qtdeclarative`
  * `gstreamer0.10-plugins-good` (mikrofon kaydı için)

---

## 🚀 Kurulum Rehberi

### Yöntem 1: Hazır Paket (.deb) ile Kurulum (Önerilen)

1. **Paketi Nokia N9'a Gönderin:**
   Bilgisayarınızdaki PowerShell veya Linux terminalinden:
   ```bash
   scp -O -oHostKeyAlgorithms=+ssh-rsa releases/gemini-n9-v22.deb user@192.168.8.144:/home/user/
   ```

2. **Nokia N9 Üzerinde Kurun ve Başlatın (root olarak):**
   N9 terminalinde veya SSH oturumunda:
   ```bash
   devel-su
   # Şifre: rootme (veya belirlediğiniz root şifresi)

   # Eski sürümü temizleyin ve paketi açın:
   rm -rf /opt/gemini-n9
   dpkg-deb -x /home/user/gemini-n9-v22.deb /
   chmod +x /opt/gemini-n9/main.py

   # Varsa eski Python süreçlerini kapatın:
   killall -9 python

   # Uygulamayı başlatın:
   DISPLAY=:0 python /opt/gemini-n9/main.py
   ```

### Yöntem 2: Kaynak Koddan .deb Paketi Derleme

Kendi `.deb` paketinizi Linux üzerinde üretmek için:
```bash
git clone https://github.com/serhatzahman/gemini-n9.git
cd gemini-n9
chmod +x build_deb.sh
./build_deb.sh
```
Oluşturulan paket `releases/` klasörü altına kaydedilir.

---

## 🛠️ Nokia N9 ve MeeGo Harmattan Teknik Notları

1. **Debian Paket Sıkıştırması:** Paketler mutlaka `dpkg-deb -Zgzip --build` ile oluşturulmalıdır (`xz` N9'da desteklenmez).
2. **PySide 1.0 Sinyal Kararlılığı:** Tüm sinyaller parametresiz tanımlanmıştır (`QtCore.Signal()`).
3. **Yazı Tipi & Emoji Sınırı:** Emojiler yerine yerel MeeGo tema vektörleri (`image://theme/icon-m-*`) kullanılmıştır.
4. **Kısıtlı `/tmp` Alanı (tmpfs 4MB):** Ses dosyaları `/home/user/MyDocs/.gemini_cache` alanına yönlendirilmiş ve 20 saniye otomatik durdurma eklenmiştir.
5. **Qt 4.7 QML Katılığı:** `border.width` strictly tam sayı (`int`) gerektirir.

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında lisanslanmıştır.
