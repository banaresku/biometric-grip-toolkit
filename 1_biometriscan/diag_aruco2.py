#!/usr/bin/env python3
"""Try different preprocessing and detector params."""
import sys, cv2, numpy as np

img_orig = cv2.imread(sys.argv[1])
h, w = img_orig.shape[:2]
if max(h, w) > 3000:
    scale = 3000 / max(h, w)
    img_orig = cv2.resize(img_orig, (int(w*scale), int(h*scale)))

print(f"Image: {img_orig.shape[1]}x{img_orig.shape[0]}\n")

DICTS_TO_TRY = [
    ('DICT_4X4_50',   cv2.aruco.DICT_4X4_50),
    ('DICT_4X4_100',  cv2.aruco.DICT_4X4_100),
    ('DICT_4X4_250',  cv2.aruco.DICT_4X4_250),
    ('DICT_4X4_1000', cv2.aruco.DICT_4X4_1000),
]

variants = [
    ('original', img_orig),
]

# CLAHE
gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
eq = clahe.apply(gray)
variants.append(('clahe_gray', cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR)))

# Sharpen
kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
sharp = cv2.filter2D(img_orig, -1, kernel)
variants.append(('sharpen', sharp))

for img_name, img in variants:
    print(f"--- {img_name} ---")
    for dict_name, dict_id in DICTS_TO_TRY:
        d = cv2.aruco.getPredefinedDictionary(dict_id)
        
        # Default params
        p = cv2.aruco.DetectorParameters()
        det = cv2.aruco.ArucoDetector(d, p)
        corners, ids, _ = det.detectMarkers(img)
        n = len(ids) if ids is not None else 0
        
        # Lenient params
        p2 = cv2.aruco.DetectorParameters()
        p2.adaptiveThreshWinSizeMin = 3
        p2.adaptiveThreshWinSizeMax = 53
        p2.adaptiveThreshWinSizeStep = 10
        p2.minMarkerPerimeterRate = 0.01
        p2.maxMarkerPerimeterRate = 10.0
        p2.polygonalApproxAccuracyRate = 0.1
        p2.errorCorrectionRate = 1.0
        det2 = cv2.aruco.ArucoDetector(d, p2)
        corners2, ids2, _ = det2.detectMarkers(img)
        n2 = len(ids2) if ids2 is not None else 0
        
        mark = " <---" if (n > 0 or n2 > 0) else ""
        print(f"  {dict_name:<18} default={n:2d}  lenient={n2:2d}{mark}")
    print()
