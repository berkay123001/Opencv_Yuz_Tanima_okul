# 🎯 Yüz Tanıma Uygulaması - C# & Avalonia UI

Bu proje, C# ve Avalonia UI kullanılarak geliştirilmiş modern bir yüz tanıma uygulamasıdır. Görüntü işleme için Python ve OpenCV entegrasyonu kullanılmaktadır.

## 📋 Gereksinimler

### C# Tarafı
- .NET 8.0 SDK
- Linux x64 (Ubuntu 20.04 veya üzeri)

### Python Tarafı  
- Python 3.x
- opencv-python paketi

## 🚀 Kurulum

### 1. Python OpenCV Kurulumu
```bash
pip install opencv-python
# veya conda kullanıyorsanız:
conda run --no-capture-output pip install opencv-python
```

### 2. Projeyi Derleyin
```bash
dotnet restore
dotnet build
```

### 3. Haar Cascade Dosyası (Zaten Mevcut)

`haarcascade_frontalface_default.xml` dosyası projede mevcuttur. Eksikse:
```bash
wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
```

### 4. Uygulamayı Çalıştırın
```bash
dotnet run
```

## 🎯 Kullanım

### Mod 1: Görsel Dosyası ile Yüz Tespiti
1. **📁 Görsel Yükle** butonuna tıklayarak bir fotoğraf seçin (.jpg, .png, .bmp)
2. **🔍 Yüzleri Tespit Et** butonuna basın
3. Tespit edilen yüzler yeşil dikdörtgenle işaretlenecektir
4. **🗑️ Temizle** butonu ile görseli temizleyebilirsiniz

### Mod 2: Canlı Kamera ile Gerçek Zamanlı Tespit 🎥
1. İsterseniz önce kendi fotoğrafınızı yükleyin (referans için)
2. **📹 Canlı Kamera Başlat** butonuna basın
3. Kamera penceresi açılacak ve gerçek zamanlı yüzleri tespit edecek
4. Kontroller:
   - **ESC tuşu**: Kamerayı kapatır
   - **SPACE tuşu**: Ekran görüntüsü alır
5. Yüzler yeşil dikdörtgenle canlı olarak işaretlenir

## 🏗️ Mimari

```
┌─────────────┐         ┌──────────────┐
│   C# UI     │ ------> │  Python      │
│  (Avalonia) │  JSON   │  OpenCV      │
│             │ <------ │              │
└─────────────┘         └──────────────┘
```

- **Frontend**: C# ile Avalonia UI (Cross-platform)
- **Backend**: Python + OpenCV (Görüntü işleme)
- **İletişim**: Process communication + JSON

## ✨ Özellikler

- ✅ Modern ve kullanıcı dostu arayüz
- ✅ Hızlı ve doğru yüz tanıma (Haar Cascade)
- ✅ **Canlı kamera desteği** 📹 (Gerçek zamanlı yüz tespiti)
- ✅ Dosyadan görsel yükleme ve analiz
- ✅ Çoklu yüz tespiti
- ✅ Ekran görüntüsü kaydetme (SPACE tuşu)
- ✅ Cross-platform desteği (Avalonia)
- ✅ Python-C# hybrid mimarisi
- ✅ İki mod: Statik görsel ve Canlı kamera

## 📂 Proje Yapısı

```
OMCV/
├── MainWindow.axaml                         # UI tasarımı
├── MainWindow.axaml.cs                      # C# UI mantığı
├── face_detector.py                         # Python yüz tanıma (statik) 🐍
├── camera_face_detector.py                  # Python kamera modülü �
├── haarcascade_frontalface_default.xml      # OpenCV Cascade modeli
├── ObjectDetection.csproj
└── Program.cs
```

## 🔧 Teknik Detaylar

### Statik Görsel İşlem Akışı
1. Kullanıcı görseli seçer (C# UI)
2. `face_detector.py` subprocess olarak çağrılır
3. OpenCV ile yüzler tespit edilir (Haar Cascade)
4. İşlenmiş görsel kaydedilir
5. Sonuç JSON ile C#'a döndürülür
6. Görsel UI'da gösterilir

### Canlı Kamera İşlem Akışı
1. Kullanıcı "Canlı Kamera Başlat" butonuna basar
2. `camera_face_detector.py` subprocess olarak başlatılır
3. Kamera açılır ve sürekli frame alır
4. Her frame'de yüzler tespit edilir (real-time)
5. Tespit edilen yüzler yeşil dikdörtgenle işaretlenir
6. OpenCV penceresi ile canlı görüntü gösterilir
7. ESC tuşu ile kamera kapatılır
8. İstatistikler JSON ile C#'a döndürülür

## 🐛 Sorun Giderme

### OpenCV Bulunamıyor
```bash
python3 -c "import cv2; print(cv2.__version__)"
# Kurulum:
pip install opencv-python
```

### Python Script Çalışmıyor
```bash
chmod +x face_detector.py
chmod +x camera_face_detector.py
```

### Kamera Açılmıyor
```bash
# Kamera erişim iznini kontrol edin
ls -la /dev/video*
# Kameranız /dev/video0 olmalı
```

### "Kamera açılamadı" Hatası
- Başka bir uygulama kamerayı kullanıyor olabilir (Zoom, Skype vb.)
- Kamera iznini kontrol edin
- Laptop'ta kamera fiziksel olarak kapalı olabilir

## 💡 İpuçları

- **Daha iyi tespit için**: Yüzünüzü kameraya doğru tutun ve iyi aydınlatma sağlayın
- **Çoklu yüz**: Kamera aynı anda birden fazla yüzü tespit edebilir
- **Ekran görüntüsü**: Kamera modunda SPACE tuşu ile an görüntüsü alabilirsiniz
- **Referans görsel**: Önce fotoğrafınızı yüklerseniz, gelecekte yüz karşılaştırması için kullanılabilir

## 🎓 Eğitim Projesi
Bu proje okul ödevi için geliştirilmiştir. C# UI ile Python backend entegrasyonunu gösterir. Hem statik görsel analizi hem de gerçek zamanlı kamera desteği sunar.

## Notlar

- Uygulama jpg, jpeg, png ve bmp formatlarını destekler
- Haar Cascade dosyası olmadan yüz tanıma çalışmaz
- En iyi sonuçlar için yüzlerin net ve ön cepheden olduğu fotoğrafları kullanın

## Lisans

Bu proje eğitim amaçlıdır.
