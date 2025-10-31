#!/usr/bin/env python3
import cv2
import sys
import json

YUNET_MODEL = "face_detection_yunet_2023mar.onnx"

def detect_face(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Resim yuklenemedi"}
        
        # YuNet dedektörü
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
            return {"success": False, "error": "Yuz bulunamadi"}
        
        # En iyi yüzü al
        best_face = max(faces, key=lambda f: f[-1])
        x, y, face_w, face_h = best_face[:4].astype(int)
        
        # Kare çerçeve hesapla
        size = max(face_w, face_h)
        center_x = x + face_w // 2
        center_y = y + face_h // 2
        x_square = center_x - size // 2
        y_square = center_y - size // 2
        
        # Yeşil kare çiz
        cv2.rectangle(img, (x_square, y_square), (x_square + size, y_square + size), (0, 255, 0), 3)
        cv2.putText(img, "Yuz Tespit Edildi", (x_square, y_square - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
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
