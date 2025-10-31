#!/usr/bin/env python3
import cv2
import sys
import json
import numpy as np

def camera_face_tracking():
    try:
        # YuNet - OpenCV'nin modern face detection modeli
        # Model indir
        model_path = "face_detection_yunet_2023mar.onnx"
        if not cv2.os.path.exists(model_path):
            print("YuNet model indiriliyor...", flush=True)
            import urllib.request
            urllib.request.urlretrieve(
                "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
                model_path
            )
        
        # YuNet modelini yükle
        detector = cv2.FaceDetectorYN.create(
            model_path,
            "",
            (320, 320),
            score_threshold=0.7,
            nms_threshold=0.3
        )
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return {"success": False, "error": "Kamera acilamadi"}
        
        print(json.dumps({"success": True, "message": "YuNet model yuklendi - ESC ile cikis"}), flush=True)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            h, w = frame.shape[:2]
            
            # YuNet için input boyutunu ayarla
            detector.setInputSize((w, h))
            
            # Yüz tespiti
            _, faces = detector.detect(frame)
            
            face_count = 0
            
            if faces is not None and len(faces) > 0:
                # En yüksek skorlu yüzü al
                best_face = max(faces, key=lambda f: f[-1])
                
                # Koordinatları al (x, y, w, h, ... , confidence)
                x, y, face_w, face_h = best_face[:4].astype(int)
                confidence = best_face[-1]
                
                # KARE çerçeve için boyutu eşitle
                size = max(face_w, face_h)
                
                # Merkezi hesapla
                center_x = x + face_w // 2
                center_y = y + face_h // 2
                
                # Kare koordinatları
                x_square = center_x - size // 2
                y_square = center_y - size // 2
                
                # Ekran sınırları içinde tut
                x_square = max(0, min(w - size, x_square))
                y_square = max(0, min(h - size, y_square))
                
                # KARE çerçeve çiz
                cv2.rectangle(frame, (x_square, y_square), (x_square+size, y_square+size), (0, 255, 0), 3)
                
                # Güven oranı
                text = f"Yuz: {confidence:.1%}"
                cv2.putText(frame, text, (x_square, y_square-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                face_count = 1
            
            cv2.putText(frame, f"Tespit: {face_count} yuz", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "ESC: Cikis", (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Canli Yuz Tespiti', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return {"success": True, "message": "Kamera kapatildi"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = camera_face_tracking()
    print(json.dumps(result, ensure_ascii=False))
