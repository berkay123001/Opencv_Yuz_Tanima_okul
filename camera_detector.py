#!/usr/bin/env python3
import cv2
import sys
import json

def camera_face_tracking():
    try:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return {"success": False, "error": "Kamera acilamadi"}
        
        print(json.dumps({"success": True, "message": "Kamera basladi - ESC ile cikis"}), flush=True)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            # Daha hassas tespit - yan dönüş için
            faces = cascade.detectMultiScale(
                gray, 
                scaleFactor=1.05,      # Daha hassas
                minNeighbors=3,        # Daha az sıkı
                minSize=(40, 40),      # Daha küçük minimum
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(frame, "Yuz Tespit Edildi", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Tespit: {len(faces)} yuz", (10, 30),
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
