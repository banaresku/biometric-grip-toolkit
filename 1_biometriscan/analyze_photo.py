#!/usr/bin/env python3
"""
analyze_photo.py — photo analysis for BiometriScan
Input:  top-view photo (required) + side-view photo (optional)
        Both must include ChArUco calibration plate in frame.
Output: <stem>_params.json with grip_params matching grip_calculator.py schema

Accuracy: ±1-2mm. Scan recommended for final fitting.

Photo protocol:
  Top view:  palm UP on ChArUco plate, wrist crease against baseline ridge,
             fingers slightly spread, camera strictly vertical, even lighting
  Side view: hand gripping selected calibration cylinder,
             ChArUco plate vertical next to hand, camera strictly lateral
"""

import json
import sys
from pathlib import Path

# TODO: import cv2
# TODO: import numpy as np
# TODO: import mediapipe as mp

# ChArUco board parameters — must match printed plates exactly
# DICT_4X4_250: do NOT use DICT_4X4_50 (too few markers for A4 coverage)
CHARUCO_A4 = {
    'squares_x':     14,
    'squares_y':     19,
    'square_length': 0.015,   # meters
    'marker_length': 0.011,
    'dict':          '4X4_250',
}
CHARUCO_300 = {
    'squares_x':     15,
    'squares_y':     15,
    'square_length': 0.020,
    'marker_length': 0.015,
    'dict':          '4X4_250',
}

CYLINDER_DIAMETERS_MM = [28, 32, 36, 40, 44, 48]


def detect_charuco(image):
    """
    Detect ChArUco board and compute homography from image to real-world mm coords.

    Returns: (homography_matrix, px_per_mm) or raises RuntimeError if detection fails.
    Tolerates up to ~40° camera tilt via homography correction.
    """
    # TODO: cv2.aruco.detectMarkers → charuco.interpolateCornersCharuco
    # TODO: cv2.findHomography(image_corners, world_corners_mm)
    raise NotImplementedError


def extract_landmarks_top(image, homography):
    """
    Extract palm measurements from top-view image using MediaPipe hand landmarks.

    IMPORTANT: wrist Y position comes from the known physical baseline ridge on the
    ChArUco plate — NOT from MediaPipe landmark 0. MediaPipe wrist is unreliable
    because the plate edge occludes the wrist crease.
    """
    # TODO: mp.solutions.hands — 21 landmarks, static_image_mode=True
    # TODO: apply homography to each landmark (x_mm, y_mm) = H @ (px, py, 1)
    # TODO: palm_width_max = max distance across landmarks 5,9,13,17 along X
    # TODO: palm_length    = wrist_baseline_y → landmark 9 (middle MCP)
    # TODO: width_profile  = width at each 5% increment of palm_length
    raise NotImplementedError


def detect_cylinder_side(image, homography):
    """
    Detect calibration cylinder in side-view photo using HoughCircles.

    Do NOT use MediaPipe here — hand in grip posture causes landmark regression errors.
    Matches detected radius to nearest value in CYLINDER_DIAMETERS_MM.

    Returns: (grip_diameter_mm, palm_depth_max_mm)
    """
    # TODO: cv2.HoughCircles with param1/param2 tuned for PETG cylinder surface
    # TODO: snap detected diameter to nearest CYLINDER_DIAMETERS_MM value
    # TODO: palm_depth_max from hand silhouette width in side view
    raise NotImplementedError


def analyze_photo(top_path: str, side_path: str = None) -> dict:
    top_path    = Path(top_path)
    source_type = 'photo_2view' if side_path else 'photo_1view'
    accuracy    = '±1-2mm (photo). Scan recommended for final.'

    print(f"\nBiometriScan — photo ({source_type})")
    print(f"  Top:  {top_path}")
    if side_path:
        print(f"  Side: {side_path}")

    # TODO: top_img = cv2.imread(str(top_path))
    # TODO: homography, px_per_mm = detect_charuco(top_img)
    # TODO: top_m = extract_landmarks_top(top_img, homography)

    # TODO: if side_path:
    #     side_img = cv2.imread(side_path)
    #     side_h, _ = detect_charuco(side_img)
    #     grip_diameter, palm_depth = detect_cylinder_side(side_img, side_h)
    # else:
    #     grip_diameter = None   # user selects cylinder manually; update JSON after
    #     palm_depth = None

    params = {
        'palm_width_max':     None,
        'palm_length':        None,
        'palm_depth_max':     None,
        'width_at_fingers':   None,
        'width_at_palm':      None,
        'width_at_wrist':     None,
        'grip_diameter':      None,
        'grip_thickness_rec': None,
        'grip_height':        None,
        'palm_swell_y_pct':   None,
        'trigger_reach_est':  None,
        'thumb_angle_deg':    None,
    }

    output = {
        'source_file':   str(top_path),
        'source_type':   source_type,
        'accuracy_note': accuracy,
        'grip_params':   params,
        'width_profile': [],
    }

    out_path = top_path.with_name(top_path.stem + '_params.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {out_path}")
    output['output_file'] = str(out_path)
    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze_photo.py top_view.jpg")
        print("  python analyze_photo.py top_view.jpg side_view.jpg")
        sys.exit(1)

    top  = sys.argv[1]
    side = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_photo(top, side)
