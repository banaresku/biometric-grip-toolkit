#!/usr/bin/env python3
"""
test_detect.py — quick ChArUco detection check on a plate photo (no hand required).
Outputs a debug image with detected corners marked.

Usage:
    python test_detect.py <image> [--plate <name>]
"""

import sys
import argparse
import cv2
import numpy as np
from pathlib import Path
from plate_config import select_plate
from analyze_photo import _preprocess, _make_detector_params


def run(image_path: str, plate_name: str = None):
    plate = select_plate(plate_name)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Cannot open: {image_path}")
        sys.exit(1)

    h, w = img.shape[:2]
    if max(h, w) > 3000:
        scale = 3000 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]
    print(f"Image: {w}x{h}")

    board = plate.build_board()
    detector = cv2.aruco.CharucoDetector(
        board,
        cv2.aruco.CharucoParameters(),
        _make_detector_params(),
    )
    processed = _preprocess(img)
    ch_corners, ch_ids, aruco_corners, aruco_ids = detector.detectBoard(processed)

    n_charuco = len(ch_ids) if ch_ids is not None else 0
    n_aruco   = len(aruco_ids) if aruco_ids is not None else 0
    print(f"ArUco markers detected:  {n_aruco}")
    print(f"ChArUco corners detected: {n_charuco}")

    max_corners = (plate.squares_x - 1) * (plate.squares_y - 1)
    print(f"Max possible corners:     {max_corners}")
    print(f"Coverage:                 {n_charuco}/{max_corners} = {100*n_charuco/max_corners:.0f}%")

    if n_charuco < 4:
        print("FAIL: need at least 4 corners for homography")
    else:
        print("OK: enough corners for homography")

    # Draw results
    debug = img.copy()
    if aruco_ids is not None:
        cv2.aruco.drawDetectedMarkers(debug, aruco_corners, aruco_ids)
    if ch_ids is not None and ch_corners is not None:
        cv2.aruco.drawDetectedCornersCharuco(debug, ch_corners, ch_ids, (0, 255, 0))

    # Draw wrist baseline if set
    if plate.wrist_baseline_y_mm is not None:
        # Approximate pixel position: find homography first
        if n_charuco >= 4:
            from analyze_photo import _world_corners
            world = _world_corners(plate.squares_x, plate.squares_y, plate.square_mm)
            obj_pts = world[ch_ids.flatten()]
            img_pts = ch_corners.reshape(-1, 2)
            H_inv, mask = cv2.findHomography(obj_pts, img_pts, cv2.RANSAC, 3.0)
            if H_inv is not None:
                world_y = plate.wrist_baseline_y_mm - plate.square_mm
                left  = H_inv @ np.array([0.0, world_y, 1.0])
                right = H_inv @ np.array([float((plate.squares_x - 1) * plate.square_mm), world_y, 1.0])
                lx, ly = int(left[0]/left[2]),  int(left[1]/left[2])
                rx, ry = int(right[0]/right[2]), int(right[1]/right[2])
                cv2.line(debug, (lx, ly), (rx, ry), (0, 0, 255), 3)
                cv2.putText(debug, f"wrist baseline ({plate.wrist_baseline_y_mm}mm)",
                            (lx + 5, ly - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    out_path = Path(image_path).with_name(Path(image_path).stem + "_charuco_debug.jpg")
    cv2.imwrite(str(out_path), debug)
    print(f"\nDebug image: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="Path to plate photo")
    ap.add_argument("--plate", default=None, help="Plate name (default: interactive)")
    args = ap.parse_args()
    run(args.image, args.plate)
