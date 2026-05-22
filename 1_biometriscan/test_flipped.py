#!/usr/bin/env python3
"""
Test ArUco detection on original + flipped photos.
Reports raw marker IDs without board constraints to diagnose mirroring.
"""
import cv2

PHOTOS = [
    "photos/IMG_20260522_165254.jpg",
    "photos/viber_image_2026-05-22_16-57-51-816.jpg",
]

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
params = cv2.aruco.DetectorParameters()
params.adaptiveThreshWinSizeMin = 3
params.adaptiveThreshWinSizeMax = 53
params.adaptiveThreshWinSizeStep = 10
params.minMarkerPerimeterRate = 0.01  # smaller markers OK
aruco_detector = cv2.aruco.ArucoDetector(dictionary, params)

for path in PHOTOS:
    img = cv2.imread(path)
    if img is None:
        print(f"{path}: not found")
        continue

    for label, image in [("original", img), ("flipped", cv2.flip(img, 1))]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = aruco_detector.detectMarkers(gray)
        n = len(ids) if ids is not None else 0
        id_list = sorted(ids.flatten().tolist()) if ids is not None else []
        board_ids = [i for i in id_list if i <= 30]
        print(f"{path} [{label}]: {n} markers found")
        if id_list:
            print(f"  all IDs:   {id_list}")
            print(f"  board IDs (≤30): {board_ids}")

        out = path.replace(".jpg", f"_{label}_aruco.jpg")
        dbg = image.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(dbg, corners, ids)
        cv2.imwrite(out, dbg)
        print(f"  debug → {out}")
