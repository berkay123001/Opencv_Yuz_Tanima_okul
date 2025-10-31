#!/usr/bin/env python3
import cv2
import os
import sys
import json
import math
import argparse
import numpy as np
import subprocess

YUNET_MODEL = "face_detection_yunet_2023mar.onnx"


def ensure_yunet(model_path: str) -> str:
    if os.path.exists(model_path):
        return model_path
    try:
        import urllib.request
        url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
        urllib.request.urlretrieve(url, model_path)
        return model_path
    except Exception:
        return model_path


def detect_and_align(img: np.ndarray) -> np.ndarray | None:
    try:
        h, w = img.shape[:2]
        model = ensure_yunet(YUNET_MODEL)
        detector = cv2.FaceDetectorYN.create(
            model,
            "",
            (320, 320),
            score_threshold=0.7,
            nms_threshold=0.3,
        )
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)
        if faces is None or len(faces) == 0:
            return None
        best = max(faces, key=lambda f: f[-1])
        x, y, fw, fh = best[:4].astype(int)
        face_roi = img[y : y + fh, x : x + fw]
        # eye alignment (roll)
        try:
            le_x, le_y, re_x, re_y = best[4:8]
            le_rel = (float(le_x - x), float(le_y - y))
            re_rel = (float(re_x - x), float(re_y - y))
            angle = math.degrees(math.atan2(re_rel[1] - le_rel[1], re_rel[0] - le_rel[0]))
            M = cv2.getRotationMatrix2D((face_roi.shape[1] / 2.0, face_roi.shape[0] / 2.0), -angle, 1.0)
            face_roi = cv2.warpAffine(
                face_roi,
                M,
                (face_roi.shape[1], face_roi.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
        except Exception:
            pass
        return face_roi
    except Exception:
        return None


def perspective_yaw(img: np.ndarray, strength: float) -> np.ndarray:
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    dx = int(w * 0.15 * strength)
    if strength >= 0:
        dst = np.float32([[dx, 0], [w - 1, 0], [w - 1 - dx, h - 1], [0, h - 1]])
    else:
        dx = -dx
        dst = np.float32([[0, 0], [w - 1 - dx, 0], [w - 1, h - 1], [dx, h - 1]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def rotate(img: np.ndarray, deg: float) -> np.ndarray:
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), deg, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def jitter_brightness(img: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    out = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    return out


def gaussian_noise(img: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return img
    noise = np.random.normal(0, sigma, img.shape).astype(np.float32)
    noisy = img.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Generate augmented face images and optionally register them.")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("name", help="Person name to register")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--output-dir", default="augmented")
    parser.add_argument("--register", action="store_true")
    args = parser.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        print(json.dumps({"success": False, "error": "Gorsel yuklenemedi"}))
        sys.exit(1)

    face = detect_and_align(img)
    if face is None:
        print(json.dumps({"success": False, "error": "Yuz bulunamadi"}))
        sys.exit(1)

    face = cv2.resize(face, (256, 256))

    out_dir = os.path.join(args.output_dir, args.name)
    ensure_dir(out_dir)

    saved = []
    for i in range(args.count):
        aug = face.copy()
        # small in-plane rotation
        deg = np.random.uniform(-12, 12)
        aug = rotate(aug, deg)
        # slight yaw via perspective
        yaw = np.random.uniform(-1.0, 1.0)
        aug = perspective_yaw(aug, yaw * 0.6)
        # random flip
        if np.random.rand() < 0.5:
            aug = cv2.flip(aug, 1)
        # light jitter
        alpha = np.random.uniform(0.85, 1.25)
        beta = np.random.uniform(-20, 20)
        aug = jitter_brightness(aug, alpha, beta)
        # mild noise
        aug = gaussian_noise(aug, sigma=np.random.uniform(0, 5))
        # crop center and resize to 256 to remove black borders
        h, w = aug.shape[:2]
        m = min(h, w)
        y0 = (h - m) // 2
        x0 = (w - m) // 2
        aug = aug[y0 : y0 + m, x0 : x0 + m]
        aug = cv2.resize(aug, (256, 256))

        out_path = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(args.image))[0]}_aug_{i:02d}.jpg")
        cv2.imwrite(out_path, aug)
        saved.append(out_path)

        if args.register:
            try:
                proc = subprocess.run([
                    sys.executable if sys.executable else "python3",
                    "face_recognizer.py",
                    "add",
                    out_path,
                    args.name,
                ], capture_output=True, text=True)
                # optional: print debug
                if proc.stderr:
                    print(proc.stderr, file=sys.stderr)
            except Exception:
                pass

    print(json.dumps({"success": True, "generated": len(saved), "paths": saved}))


if __name__ == "__main__":
    main()
