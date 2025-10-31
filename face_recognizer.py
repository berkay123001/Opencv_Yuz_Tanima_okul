#!/usr/bin/env python3
import cv2
import sys
import json
import numpy as np
import pickle
import os

# Basit face encoding için global değişkenler
FACE_DATABASE = "face_database.pkl"
YUNET_MODEL = "face_detection_yunet_2023mar.onnx"

def extract_face_features(image_path, augment=False):
    """Yüzden gelişmiş özellik çıkar (histogram + HOG)"""
    try:
        # Görüntüyü yükle
        img = cv2.imread(image_path)
        if img is None:
            return None, "Görsel yüklenemedi"
        
        # YuNet ile yüz tespiti
        detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            score_threshold=0.7,
            nms_threshold=0.3
        )
        
        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        
        _, faces = detector.detect(img)
        
        if faces is None or len(faces) == 0:
            return None, "Yüz bulunamadı"
        
        # En iyi yüzü al
        best_face = max(faces, key=lambda f: f[-1])
        x, y, face_w, face_h = best_face[:4].astype(int)
        
        # Yüz bölgesini kes
        face_roi = img[y:y+face_h, x:x+face_w]
        le_x, le_y, re_x, re_y = best_face[4:8]
        le_rel = (float(le_x - x), float(le_y - y))
        re_rel = (float(re_x - x), float(re_y - y))
        angle = np.degrees(np.arctan2(re_rel[1] - le_rel[1], re_rel[0] - le_rel[0]))
        M = cv2.getRotationMatrix2D((face_roi.shape[1] / 2.0, face_roi.shape[0] / 2.0), -angle, 1.0)
        face_roi = cv2.warpAffine(face_roi, M, (face_roi.shape[1], face_roi.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        # Yüzü normalize et (daha büyük boyut - daha fazla detay)
        face_roi = cv2.resize(face_roi, (128, 128))
        face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        face_gray = cv2.equalizeHist(face_gray)
        
        # 1. Gelişmiş Histogram özelliği (256 bin - çok daha fazla detay)
        hist = cv2.calcHist([face_gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # 2. HOG (Histogram of Oriented Gradients) özellikleri
        hog = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
        hog_features = hog.compute(face_gray).flatten()
        
        # 3. LBP (Local Binary Pattern) benzeri basit doku özelliği
        # Laplacian ile kenar bilgisi
        laplacian = cv2.Laplacian(face_gray, cv2.CV_64F)
        laplacian_hist = cv2.calcHist([np.abs(laplacian).astype(np.uint8)], [0], None, [64], [0, 256])
        laplacian_hist = cv2.normalize(laplacian_hist, laplacian_hist).flatten()
        
        combined_features = np.concatenate([hist, hog_features[:512], laplacian_hist]).astype(np.float32)
        norm = np.linalg.norm(combined_features) + 1e-8
        features = combined_features / norm

        if augment:
            face_roi_flip = cv2.flip(face_roi, 1)
            face_roi_flip = cv2.resize(face_roi_flip, (128, 128))
            face_gray_flip = cv2.cvtColor(face_roi_flip, cv2.COLOR_BGR2GRAY)
            face_gray_flip = cv2.equalizeHist(face_gray_flip)
            hist_f = cv2.calcHist([face_gray_flip], [0], None, [256], [0, 256])
            hist_f = cv2.normalize(hist_f, hist_f).flatten()
            hog_f = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
            hog_features_f = hog_f.compute(face_gray_flip).flatten()
            laplacian_f = cv2.Laplacian(face_gray_flip, cv2.CV_64F)
            laplacian_hist_f = cv2.calcHist([np.abs(laplacian_f).astype(np.uint8)], [0], None, [64], [0, 256])
            laplacian_hist_f = cv2.normalize(laplacian_hist_f, laplacian_hist_f).flatten()
            combined_f = np.concatenate([hist_f, hog_features_f[:512], laplacian_hist_f]).astype(np.float32)
            features_f = combined_f / (np.linalg.norm(combined_f) + 1e-8)
            return [features, features_f], None

        return features, None
        
    except Exception as e:
        return None, str(e)

def load_database():
    """Veritabanını yükle"""
    if os.path.exists(FACE_DATABASE):
        with open(FACE_DATABASE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_database(db):
    """Veritabanını kaydet"""
    with open(FACE_DATABASE, 'wb') as f:
        pickle.dump(db, f)

def add_person(image_path, name):
    """Yeni kişi ekle"""
    try:
        features, error = extract_face_features(image_path, augment=True)
        if error:
            return {"success": False, "error": error}
        
        db = load_database()
        new_samples = features if isinstance(features, list) else [features]
        existing = db.get(name)
        if isinstance(existing, list):
            existing.extend(new_samples)
            db[name] = existing
        elif existing is None:
            db[name] = new_samples
        else:
            db[name] = [existing] + new_samples
        save_database(db)
        
        return {
            "success": True, 
            "message": f"{name} veritabanına eklendi",
            "total_people": len(db)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def recognize_person(image_path):
    """Fotoğraftaki kişiyi tanı ve yüzü işaretle"""
    try:
        # Görüntüyü yükle
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Görsel yüklenemedi"}
        
        # YuNet ile yüz tespiti
        detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            score_threshold=0.7,
            nms_threshold=0.3
        )
        
        h, w = img.shape[:2]
        detector.setInputSize((w, h))
        
        _, faces = detector.detect(img)
        
        if faces is None or len(faces) == 0:
            return {"success": False, "error": "Yüz bulunamadı"}
        
        # En iyi yüzü al
        best_face = max(faces, key=lambda f: f[-1])
        x, y, face_w, face_h = best_face[:4].astype(int)
        
        # Yüz bölgesini kes ve features çıkar
        face_roi = img[y:y+face_h, x:x+face_w]
        face_roi_resized = cv2.resize(face_roi, (128, 128))
        face_gray = cv2.cvtColor(face_roi_resized, cv2.COLOR_BGR2GRAY)
        face_gray = cv2.equalizeHist(face_gray)
        
        # 1. Gelişmiş Histogram özelliği (256 bin)
        hist = cv2.calcHist([face_gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # 2. HOG özellikleri
        hog = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
        hog_features = hog.compute(face_gray).flatten()
        
        # 3. Laplacian kenar bilgisi
        laplacian = cv2.Laplacian(face_gray, cv2.CV_64F)
        laplacian_hist = cv2.calcHist([np.abs(laplacian).astype(np.uint8)], [0], None, [64], [0, 256])
        laplacian_hist = cv2.normalize(laplacian_hist, laplacian_hist).flatten()
        
        # Tüm özellikleri birleştir
        features = np.concatenate([hist, hog_features[:512], laplacian_hist]).astype(np.float32)
        # L2 normalize
        features = features / (np.linalg.norm(features) + 1e-8)
        
        db = load_database()
        if not db:
            return {"success": False, "error": "Veritabanı boş"}
        
        # Histogram karşılaştırma (chi-square)
        best_match = None
        best_distance = float('inf')
        
        for name, stored_features in db.items():
            if isinstance(stored_features, list):
                for sf in stored_features:
                    sf = np.asarray(sf, dtype=np.float32).reshape(-1)
                    sf = sf / (np.linalg.norm(sf) + 1e-8)
                    distance = 1.0 - float(np.dot(features, sf))
                    if distance < best_distance:
                        best_distance = distance
                        best_match = name
            else:
                sf = np.asarray(stored_features, dtype=np.float32).reshape(-1)
                sf = sf / (np.linalg.norm(sf) + 1e-8)
                distance = 1.0 - float(np.dot(features, sf))
                if distance < best_distance:
                    best_distance = distance
                    best_match = name
        
        # Kare çerçeve hesapla (camera_detector ile aynı)
        size = max(face_w, face_h)
        center_x = x + face_w // 2
        center_y = y + face_h // 2
        x_square = center_x - size // 2
        y_square = center_y - size // 2
        
        # Eşik değeri (yeni özellik vektörü için optimize edilmiş)
        # Daha düşük = daha seçici tanıma
        THRESHOLD = float(os.getenv("FACE_THRESHOLD", "0.35"))
        if best_distance < THRESHOLD:
            confidence = (1.0 - (best_distance / THRESHOLD)) * 100
            # Yeşil kare çiz
            cv2.rectangle(img, (x_square, y_square), (x_square + size, y_square + size), (0, 255, 0), 3)
            cv2.putText(img, f"{best_match}: %{confidence:.1f}", (x_square, y_square - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Çıktı kaydet
            output_path = image_path.replace('.', '_recognized.')
            cv2.imwrite(output_path, img)
            
            return {
                "success": True,
                "name": best_match,
                "confidence": confidence / 100,
                "message": f"Tanındı: {best_match}",
                "output_path": output_path
            }
        else:
            # Kırmızı kare çiz
            cv2.rectangle(img, (x_square, y_square), (x_square + size, y_square + size), (0, 0, 255), 3)
            cv2.putText(img, "Bilinmeyen", (x_square, y_square - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Çıktı kaydet
            output_path = image_path.replace('.', '_recognized.')
            cv2.imwrite(output_path, img)
            
            return {
                "success": False,
                "message": "Bilinmeyen kişi",
                "closest": best_match,
                "distance": float(best_distance),
                "output_path": output_path
            }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_people():
    """Kayıtlı kişileri listele"""
    try:
        db = load_database()
        return {
            "success": True,
            "people": list(db.keys()),
            "count": len(db)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def clear_database():
    """Veritabanını temizle"""
    try:
        if os.path.exists(FACE_DATABASE):
            os.remove(FACE_DATABASE)
        return {"success": True, "message": "Veritabanı temizlendi"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Komut belirtilmedi"}))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 4:
            print(json.dumps({"success": False, "error": "Kullanım: add <image_path> <name>"}))
        else:
            result = add_person(sys.argv[2], sys.argv[3])
            print(json.dumps(result, ensure_ascii=False))
    
    elif command == "recognize":
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Kullanım: recognize <image_path>"}))
        else:
            result = recognize_person(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False))
    
    elif command == "list":
        result = list_people()
        print(json.dumps(result, ensure_ascii=False))
    
    elif command == "clear":
        result = clear_database()
        print(json.dumps(result, ensure_ascii=False))
    
    else:
        print(json.dumps({"success": False, "error": f"Bilinmeyen komut: {command}"}))
