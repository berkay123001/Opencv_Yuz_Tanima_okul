#!/usr/bin/env python3
import cv2
import sys
import json
import numpy as np
import pickle
import os

FACE_DATABASE = "face_database.pkl"
YUNET_MODEL = "face_detection_yunet_2023mar.onnx"

def load_database():
    """Veritabanını yükle"""
    if os.path.exists(FACE_DATABASE):
        with open(FACE_DATABASE, 'rb') as f:
            return pickle.load(f)
    return {}

def recognize_face_features(features, db):
    """Özellikleri veritabanıyla karşılaştır"""
    if not db or features is None:
        return None, 0.0
    
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
            # Kosinüs tabanlı uzaklık (1 - dot)
            distance = 1.0 - float(np.dot(features, sf))
            
            if distance < best_distance:
                best_distance = distance
                best_match = name
    
    # Debug: mesafe yazdır
    print(f"DEBUG: En yakın: {best_match}, Mesafe: {best_distance:.4f}", flush=True)
    
    # Eşik değeri kontrolü (yeni özellik vektörü için optimize edilmiş)
    THRESHOLD = float(os.getenv("FACE_THRESHOLD", "0.35"))
    if best_distance < THRESHOLD:
        confidence = 1.0 - (best_distance / THRESHOLD)
        return best_match, confidence
    else:
        return None, 0.0

def extract_face_features(face_roi):
    """Yüz bölgesinden gelişmiş özellik çıkar"""
    try:
        # Yüzü normalize et (daha büyük boyut - daha fazla detay)
        face_roi = cv2.resize(face_roi, (128, 128))
        face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        face_gray = cv2.equalizeHist(face_gray)
        
        # 1. Gelişmiş Histogram özelliği (256 bin)
        hist = cv2.calcHist([face_gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # 2. HOG (Histogram of Oriented Gradients) özellikleri
        hog = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
        hog_features = hog.compute(face_gray).flatten()
        
        # 3. Laplacian kenar bilgisi
        laplacian = cv2.Laplacian(face_gray, cv2.CV_64F)
        laplacian_hist = cv2.calcHist([np.abs(laplacian).astype(np.uint8)], [0], None, [64], [0, 256])
        laplacian_hist = cv2.normalize(laplacian_hist, laplacian_hist).flatten()
        
        # Tüm özellikleri birleştir
        combined_features = np.concatenate([hist, hog_features[:512], laplacian_hist]).astype(np.float32)
        
        # L2 normalize
        features = combined_features / (np.linalg.norm(combined_features) + 1e-8)
        
        return features
    except:
        return None

def camera_face_recognition():
    try:
        # Veritabanını yükle
        db = load_database()
        if not db:
            print(json.dumps({"success": False, "error": "Veritabanı boş"}), flush=True)
            return {"success": False, "error": "Veritabanı boş"}
        
        print(json.dumps({"success": True, "message": f"{len(db)} kişi yüklendi"}), flush=True)
        
        # YuNet modelini yükle
        detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            score_threshold=0.7,
            nms_threshold=0.3
        )
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return {"success": False, "error": "Kamera açılamadı"}
        
        print(json.dumps({"success": True, "message": "Gelişmiş kamera başladı - ESC ile çıkış"}), flush=True)
        current_name = None
        streak = 0
        required_streak = 3
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            h, w = frame.shape[:2]
            detector.setInputSize((w, h))
            
            # Yüz tespiti
            _, faces = detector.detect(frame)
            
            if faces is not None and len(faces) > 0:
                # En iyi yüzü al
                best_face = max(faces, key=lambda f: f[-1])
                x, y, face_w, face_h = best_face[:4].astype(int)
                confidence = best_face[-1]
                
                # Yüz bölgesini kes
                face_roi = frame[y:y+face_h, x:x+face_w]
                le_x, le_y, re_x, re_y = best_face[4:8]
                le_rel = (float(le_x - x), float(le_y - y))
                re_rel = (float(re_x - x), float(re_y - y))
                angle = np.degrees(np.arctan2(re_rel[1] - le_rel[1], re_rel[0] - le_rel[0]))
                M = cv2.getRotationMatrix2D((face_roi.shape[1] / 2.0, face_roi.shape[0] / 2.0), -angle, 1.0)
                face_roi = cv2.warpAffine(face_roi, M, (face_roi.shape[1], face_roi.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                
                # Özellikleri çıkar ve tanı
                features = extract_face_features(face_roi)
                if features is not None:
                    name, recog_confidence = recognize_face_features(features, db)
                    if name:
                        if current_name == name:
                            streak += 1
                        else:
                            current_name = name
                            streak = 1
                    else:
                        if streak > 0:
                            streak -= 1
                            if streak == 0:
                                current_name = None
                    
                    # KARE çerçeve
                    size = max(face_w, face_h)
                    center_x = x + face_w // 2
                    center_y = y + face_h // 2
                    x_square = max(0, min(w - size, center_x - size // 2))
                    y_square = max(0, min(h - size, center_y - size // 2))
                    
                    if current_name and streak >= required_streak:
                        # Tanındı - Yeşil çerçeve
                        cv2.rectangle(frame, (x_square, y_square), (x_square+size, y_square+size), (0, 255, 0), 3)
                        text = f"{current_name}: %{recog_confidence*100:.0f}"
                        cv2.putText(frame, text, (x_square, y_square-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        # Bilinmeyen - Kırmızı çerçeve
                        cv2.rectangle(frame, (x_square, y_square), (x_square+size, y_square+size), (0, 0, 255), 3)
                        cv2.putText(frame, "Bilinmeyen", (x_square, y_square-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Bilgi
            cv2.putText(frame, f"Kayitli: {len(db)} kisi", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "ESC: Cikis", (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Yuz Tanima Sistemi', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return {"success": True, "message": "Kamera kapatıldı"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = camera_face_recognition()
    print(json.dumps(result, ensure_ascii=False))
