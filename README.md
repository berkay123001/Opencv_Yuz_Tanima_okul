# 🎯 Yüz Tanıma & Kişi Tanıma Uygulaması - C# & Avalonia UI

Bu proje, C# ve Avalonia UI kullanılarak geliştirilmiş **akıllı yüz tanıma ve kişi tanıma** uygulamasıdır. 

**Özellikler:**
- ✅ **YuNet Model** ile hızlı ve doğru yüz tespiti (OpenCV 2023 resmi modeli)
- 🎭 **Kişi Tanıma Sistemi** - Histogram tabanlı yüz tanıma
- 📸 **Statik Görüntü Tespiti** - Fotoğraf üzerinde yüz tespiti
- 🎥 **Canlı Kamera** - Gerçek zamanlı yüz tespiti
- 🎥 **Gelişmiş Kamera** - Canlı kamera ile kişi tanıma
- 💾 **Kişi Veritabanı** - Sınırsız kişi ekleyip tanıyın

Görüntü işleme için Python ve OpenCV entegrasyonu kullanılmaktadır.

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
- ✅ Hızlı ve doğru yüz tespiti (YuNet ONNX)
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
├── face_detector.py                         # YuNet ile statik yüz tespiti 🐍
├── camera_detector.py                       # YuNet ile canlı yüz tespiti
├── face_recognizer.py                       # Kişi ekleme/list/recognize (görsel)
├── camera_face_recognizer.py                # Canlı kamera kişi tanıma
├── augment_faces.py                         # Veri artırma (poz/ışık)
├── face_detection_yunet_2023mar.onnx        # YuNet modeli
├── ObjectDetection.csproj
└── Program.cs
```

## ⚠️ Beta Uyarısı ve Sınırlamalar

- Yüz tanıma modülü BETA. Yan dönük (yaw/pitch), kötü ışık, bulanıklık durumlarında doğruluk düşebilir.
- Daha iyi sonuç için her kişi için 6–10 farklı örnek ekleyin (frontal, hafif sola/sağa bakış, farklı ışık). Aynı isimle ekledikçe veritabanına yeni örnekler eklenir.
- Kamera tarafında isim gösterimi, birkaç kare üst üste aynı sonuç gelince yapılır (geçici kararlılık).

## 🎛️ Ayarlar ve İpuçları

- Eşik ayarı: kosinüs uzaklığı için ortam değişkeni ile ayarlayın.
  ```bash
  FACE_THRESHOLD=0.55 dotnet run
  ```
  0.45–0.60 aralığı iyi bir başlangıçtır. Terminaldeki `DEBUG: Mesafe` çıktılarına göre ayarlayın.

- Python bağımlılıkları:
  ```bash
  pip install opencv-python opencv-contrib-python numpy
  ```

## 🧪 Veri Artırma (Augmentation)

Tek fotoğraftan gerçekçi sayılabilecek varyantlar (küçük dönüş, perspektif yaw, ışık, flip, hafif noise) üretir. İsterseniz otomatik veritabanına ekler.

```bash
python3 augment_faces.py ./ornek.jpg Berkay --count 12 --output-dir augmented --register
```

- Çıktılar `augmented/<isim>/` klasörüne kaydedilir.
- `--register` kullanırsanız her oluşturulan görsel veritabanına aynı isimle eklenir.

## ☁️ GitHub’a Yükleme

Gereksiz/üretilen dosyaları `.gitignore` ile dışladık: `bin/`, `obj/`, `__pycache__/`, `face_database.pkl`, `*_recognized.*`, `*_detected.*`, `augmented/`. Büyük ve kullanılmayan Caffe modeli `res10_...caffemodel` ve `deploy.prototxt` de dışlandı.

1) Değişiklikleri ekleyin ve commit’leyin
```bash
git add -A
git commit -m "Prepare repo: ignore outputs, add augmentation, update README"
```

2) Uzak depo ayarı ve push
```bash
git branch -M main
git remote add origin https://github.com/berkay123001/Opencv_Yuz_Tanima_okul.git
git push -u origin main
```

Eğer uzaktan repo zaten bağlıysa:
```bash
git remote set-url origin https://github.com/berkay123001/Opencv_Yuz_Tanima_okul.git
git push -u origin main
```

## 🪟 Windows’ta Çalıştırma ve Yayınlama

### Geliştirme ortamında çalıştırma

Gereksinimler: .NET 8 SDK, Python 3.10+, `pip install opencv-python opencv-contrib-python numpy`.

Çalıştırma:
```powershell
set FACE_THRESHOLD=0.55
dotnet run
```

Not: Python çağrısı Windows’ta çoğunlukla `python` komutu iledir. Eğer `python3` bulunamazsa PATH ayarlarınızı yapın.

### .exe oluşturma (publish)

Runtime dahil tek dosya .exe:
```powershell
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o publish/
```

Hedef makinede .NET Runtime kurulu ise daha küçük paket için:
```powershell
dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o publish/
```

Dağıtım: `publish/` klasörünü zip’leyip GitHub **Releases** kısmına yüklemeniz önerilir. `publish/` klasörü repoya commit edilmez (.gitignore). Kullanıcıların Python 3 ve gerekli paketleri kurulu olmalıdır; uygulama çalışırken Python script’lerini çağırır.

## 🔧 Teknik Detaylar

### Statik Görsel İşlem Akışı
1. Kullanıcı görseli seçer (C# UI)
2. `face_detector.py` subprocess olarak çağrılır
3. OpenCV YuNet ile yüzler tespit edilir
4. İşlenmiş görsel kaydedilir
5. Sonuç JSON ile C#'a döndürülür
6. Görsel UI'da gösterilir

### Canlı Kamera İşlem Akışı
1. Kullanıcı "Canlı Kamera Başlat" butonuna basar
2. `camera_detector.py` subprocess olarak başlatılır
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
