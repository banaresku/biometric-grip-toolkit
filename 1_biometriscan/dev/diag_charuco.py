#!/usr/bin/env python3
"""Diagnose ChArUco detection step by step on flipped photos."""
import cv2
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from plate_config import get_plate

PHOTOS = [
    "photos/viber_image_2026-05-22_16-57-51-816.jpg",
    "photos/IMG_20260522_165254.jpg",
]

plate = get_plate('7x9_30mm')
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

standard_board = plate.build_board(mirrored=False)
mirrored_board = plate.build_board(mirrored=True)

params = cv2.aruco.DetectorParameters()
params.adaptiveThreshWinSizeMin  = 3
params.adaptiveThreshWinSizeMax  = 73
params.adaptiveThreshWinSizeStep = 10
params.minMarkerPerimeterRate    = 0.01
params.errorCorrectionRate       = 0.8

charuco_params = cv2.aruco.CharucoParameters()
charuco_params.tryRefineMarkers = True

aruco_det = cv2.aruco.ArucoDetector(dictionary, params)
charuco_det_std = cv2.aruco.CharucoDetector(standard_board, charuco_params, params)
charuco_det_mir = cv2.aruco.CharucoDetector(mirrored_board, charuco_params, params)

for path in PHOTOS:
    img = cv2.imread(path)
    if img is None:
        print(f"{path}: not found"); continue

    img = cv2.flip(img, 1)
    h, w = img.shape[:2]
    if max(h, w) > 3000:
        scale = 3000 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 1: raw ArUco
    corners, ids, _ = aruco_det.detectMarkers(gray)
    n_aruco = len(ids) if ids is not None else 0
    board_ids = sorted(ids.flatten().tolist()) if ids is not None else []
    print(f"\n{path} (flipped {img.shape[1]}x{img.shape[0]}):")
    print(f"  ArUco: {n_aruco}  IDs: {board_ids}")

    # Step 2: standard board
    cc, ci, mc, mi = charuco_det_std.detectBoard(gray)
    n_c = len(ci) if ci is not None else 0
    n_m = len(mi) if mi is not None else 0
    print(f"  CharuCo standard:  {n_m} markers + {n_c} corners")

    # Step 3: mirrored board
    cc_m, ci_m, mc_m, mi_m = charuco_det_mir.detectBoard(gray)
    n_c_m = len(ci_m) if ci_m is not None else 0
    n_m_m = len(mi_m) if mi_m is not None else 0
    print(f"  CharuCo mirrored:  {n_m_m} markers + {n_c_m} corners")

    # Save debug with mirrored board result
    dbg = img.copy()
    if mi_m is not None:
        cv2.aruco.drawDetectedMarkers(dbg, mc_m, mi_m)
    if ci_m is not None and cc_m is not None:
        cv2.aruco.drawDetectedCornersCharuco(dbg, cc_m, ci_m)
    out = path.replace(".jpg", "_diag2.jpg")
    cv2.imwrite(out, dbg)
    print(f"  debug → {out}")
