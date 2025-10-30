#!/usr/bin/env python3
import cv2
import sys
import json

def detect_face(image_path):
    try:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Resim yuklenemedi"}
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        if len(faces) == 0:
            return {"success": False, "error": "Yuz bulunamadi"}
        x, y, w, h = faces[0]
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
        cv2.putText(img, "Yuz Tespit Edildi", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        output_path = image_path.replace('.', '_detected.')
        cv2.imwrite(output_path, img)
        return {"success": True, "face_count": len(faces), "output_path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Resim yolu yok"}))
        sys.exit(1)
    result = detect_face(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
