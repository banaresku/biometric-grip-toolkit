#!/usr/bin/env python3
import sys, cv2

DICTS = {
    'DICT_4X4_50':    cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100':   cv2.aruco.DICT_4X4_100,
    'DICT_4X4_250':   cv2.aruco.DICT_4X4_250,
    'DICT_4X4_1000':  cv2.aruco.DICT_4X4_1000,
    'DICT_5X5_50':    cv2.aruco.DICT_5X5_50,
    'DICT_5X5_100':   cv2.aruco.DICT_5X5_100,
    'DICT_5X5_250':   cv2.aruco.DICT_5X5_250,
    'DICT_5X5_1000':  cv2.aruco.DICT_5X5_1000,
    'DICT_6X6_250':   cv2.aruco.DICT_6X6_250,
    'DICT_7X7_250':   cv2.aruco.DICT_7X7_250,
    'DICT_ARUCO_ORIGINAL': cv2.aruco.DICT_ARUCO_ORIGINAL,
}

img = cv2.imread(sys.argv[1])
h, w = img.shape[:2]
if max(h, w) > 3000:
    scale = 3000 / max(h, w)
    img = cv2.resize(img, (int(w * scale), int(h * scale)))

params = cv2.aruco.DetectorParameters()
print(f"Image: {img.shape[1]}x{img.shape[0]}\n")
best = None
for name, dict_id in DICTS.items():
    d = cv2.aruco.getPredefinedDictionary(dict_id)
    det = cv2.aruco.ArucoDetector(d, params)
    corners, ids, _ = det.detectMarkers(img)
    n = len(ids) if ids is not None else 0
    mark = " <---" if n > 0 else ""
    print(f"  {name:<25} {n:2d} markers{mark}")
    if n > 0 and best is None:
        best = (name, sorted(ids.flatten().tolist()))

if best:
    print(f"\nBest: {best[0]}\nIDs: {best[1][:20]}")
else:
    print("\nNothing detected with any dictionary.")
