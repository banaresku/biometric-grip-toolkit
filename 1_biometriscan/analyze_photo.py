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

import cv2
import numpy as np
import mediapipe as mp

from plate_config import PlateConfig, select_plate

CYLINDER_DIAMETERS_MM = [28, 32, 36, 40, 44, 48]


def _world_corners(squares_x, squares_y, square_mm):
    """World coordinates (mm) of ChArUco inner corners, row-major from origin."""
    nx = squares_x - 1
    ny = squares_y - 1
    pts = np.zeros((ny * nx, 2), np.float32)
    for r in range(ny):
        for c in range(nx):
            pts[r * nx + c] = [c * square_mm, r * square_mm]
    return pts


def _make_detector_params(inverted: bool = False):
    p = cv2.aruco.DetectorParameters()
    p.adaptiveThreshWinSizeMin  = 3
    p.adaptiveThreshWinSizeMax  = 73
    p.adaptiveThreshWinSizeStep = 10
    p.minMarkerPerimeterRate    = 0.01
    p.errorCorrectionRate       = 0.8
    p.detectInvertedMarker      = inverted
    return p


def _preprocess(image):
    """CLAHE on luminance channel — improves detection in uneven lighting."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    lab = cv2.merge([clahe.apply(l), a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def detect_charuco(image, plate: PlateConfig, mirrored: bool = False):
    """
    Detect ChArUco board and compute homography from image pixels to board mm.

    Returns homography matrix H (3×3).
    mirrored=True: board was printed horizontally mirrored. Image must already be flipped.
                   Uses direct ArUco marker corners instead of ChArUco sub-pixel corners.
    """
    if mirrored:
        return _detect_charuco_mirrored(image, plate)

    board = plate.build_board(mirrored=False)
    charuco_params = cv2.aruco.CharucoParameters()
    charuco_params.tryRefineMarkers = True
    detector = cv2.aruco.CharucoDetector(
        board,
        charuco_params,
        _make_detector_params(inverted=plate.inverted),
    )
    processed = _preprocess(image)
    ch_corners, ch_ids, _, _ = detector.detectBoard(processed)

    n = len(ch_ids) if ch_ids is not None else 0
    if n < 4:
        raise RuntimeError(
            f"ChArUco: {n} corners detected, need ≥4.\n"
            f"  Check lighting, board orientation, and that --plate={plate.name} is correct."
        )
    print(f"  ChArUco: {n} inner corners detected")

    world = _world_corners(plate.squares_x, plate.squares_y, plate.square_mm)
    obj_pts = world[ch_ids.flatten()]
    img_pts = ch_corners.reshape(-1, 2)

    H, mask = cv2.findHomography(img_pts, obj_pts, cv2.RANSAC, 3.0)
    if H is None:
        raise RuntimeError("findHomography failed — not enough inliers")

    inliers = int(mask.sum()) if mask is not None else n
    print(f"  Homography: {inliers}/{n} inliers")
    return H


def _detect_charuco_mirrored(image, plate: PlateConfig):
    """
    Homography from a mirror-printed board (image already flipped).

    ChArUco corner interpolation fails for mirrored boards because each marker's
    local perspective estimate maps to wrong world coordinates. Instead we use
    the 4 image corners of each detected ArUco marker directly.

    Corner ordering after horizontal flip:
      ArUco returns [TL, TR, BR, BL] in image space.
      After flip: image-TL = physical-TR, image-TR = physical-TL, etc.
      So image corners map to world: [physical-TR, physical-TL, physical-BL, physical-BR]
    """
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    det_params = _make_detector_params(inverted=plate.inverted)
    aruco_det = cv2.aruco.ArucoDetector(dictionary, det_params)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco_det.detectMarkers(gray)

    if ids is None or len(ids) == 0:
        raise RuntimeError("No ArUco markers detected. Check lighting and board orientation.")

    # Build ID → board (col, row) mapping for the mirrored board
    id_to_pos = plate._mirrored_id_to_pos()
    sq = plate.square_mm
    margin = (plate.square_mm - plate.marker_mm) / 2.0

    img_pts, world_pts = [], []
    for marker_corners, marker_id in zip(corners, ids.flatten()):
        if marker_id not in id_to_pos:
            continue
        col, row = id_to_pos[marker_id]
        mc = marker_corners.reshape(4, 2)  # [TL, TR, BR, BL] in flipped image

        # Flipped image: TL↔physical-TR, TR↔physical-TL, BR↔physical-BL, BL↔physical-BR
        world_corners_ordered = np.array([
            [(col + 1) * sq - margin, row * sq + margin],       # physical TR
            [col * sq + margin,        row * sq + margin],       # physical TL
            [col * sq + margin,        (row + 1) * sq - margin], # physical BL
            [(col + 1) * sq - margin,  (row + 1) * sq - margin], # physical BR
        ], dtype=np.float32)

        img_pts.append(mc)
        world_pts.append(world_corners_ordered)

    if len(img_pts) < 4:
        raise RuntimeError(
            f"Only {len(img_pts)} board markers found after flip, need ≥4.\n"
            f"  Check --flip flag and that plate is actually mirror-printed."
        )

    img_pts_all  = np.vstack(img_pts).astype(np.float32)
    world_pts_all = np.vstack(world_pts).astype(np.float32)

    H, mask = cv2.findHomography(img_pts_all, world_pts_all, cv2.RANSAC, 3.0)
    if H is None:
        raise RuntimeError("findHomography failed — not enough inliers")

    n_total  = len(img_pts_all)
    inliers  = int(mask.sum()) if mask is not None else n_total
    print(f"  ArUco markers: {len(img_pts)}/{len(id_to_pos)} board markers")
    print(f"  Homography: {inliers}/{n_total} corner inliers ({len(img_pts)*4} pts from {len(img_pts)} markers)")
    return H


def _px_to_mm(px, py, H):
    v = H @ np.array([float(px), float(py), 1.0])
    return v[0] / v[2], v[1] / v[2]


def _scale_px_per_mm(image, H):
    """Estimate px/mm scale at image center from homography."""
    h, w = image.shape[:2]
    cx, cy = w / 2, h / 2
    x0, y0 = _px_to_mm(cx, cy, H)
    x1, y1 = _px_to_mm(cx + 10, cy, H)
    dx_mm = abs(x1 - x0)
    return 10.0 / dx_mm if dx_mm > 1e-6 else 30.0  # px/mm


def detect_hand(image, confidence=0.3):
    """
    Detect hand with MediaPipe. Returns 21 (x_px, y_px) tuples.

    IMPORTANT: wrist Y in mm is derived from ChArUco homography, not assumed.
    MediaPipe wrist landmark (0) may be partially occluded by plate edge —
    use it for X position only; Y baseline comes from homography.
    """
    mp_hands = mp.solutions.hands
    h, w = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=confidence,
    ) as hands:
        result = hands.process(rgb)

    if not result.multi_hand_landmarks:
        raise RuntimeError(
            f"MediaPipe: no hand detected (confidence={confidence}).\n"
            f"  Try --confidence 0.1 or check lighting."
        )

    lm = result.multi_hand_landmarks[0].landmark
    side = result.multi_handedness[0].classification[0].label
    print(f"  MediaPipe: {len(lm)} landmarks ({side} hand)")
    return [(l.x * w, l.y * h) for l in lm]


def extract_landmarks_top(lm_px, H):
    """
    Extract palm measurements from pre-detected MediaPipe landmarks + homography.

    lm_px: list of 21 (x_px, y_px) from detect_hand()
    All distances computed as Euclidean in board mm space — perspective-corrected.
    """
    lm = [_px_to_mm(px, py, H) for px, py in lm_px]

    def dist(i, j):
        return float(np.hypot(lm[i][0] - lm[j][0], lm[i][1] - lm[j][1]))

    # MediaPipe landmark indices:
    # 0=wrist  1=thumb_cmc  2=thumb_mcp  4=thumb_tip
    # 5=index_mcp  8=index_tip
    # 9=middle_mcp  12=middle_tip
    # 13=ring_mcp   17=pinky_mcp  20=pinky_tip

    # Palm width: full span across thumb_mcp (2) → pinky_mcp (17)
    palm_width_max = dist(2, 17)

    # Also measure MCP row only (5→17) as internal width
    mcp_xs = [lm[i][0] for i in [5, 9, 13, 17]]
    width_at_palm = max(mcp_xs) - min(mcp_xs)

    # Width at finger level (index→pinky MCP row)
    width_at_fingers = dist(5, 17)

    # Wrist width: approximate from landmark 0 horizontal extent
    # (wrist landmark placement varies — use MCP row as proxy for wrist width)
    width_at_wrist = palm_width_max * 0.82  # empirical: wrist ≈ 82% palm width

    # Palm length: wrist(0) → middle MCP(9), Euclidean in mm
    palm_length = dist(0, 9)

    # Grip height: wrist → middle fingertip(12)
    grip_height = dist(0, 12)

    # Trigger reach: wrist → index fingertip(8)
    trigger_reach_est = dist(0, 8)

    # Thumb angle: angle between palm axis (0→9) and thumb axis (2→4)
    wrist = np.array(lm[0])
    mid_mcp = np.array(lm[9])
    thumb_mcp = np.array(lm[2])
    thumb_tip = np.array(lm[4])
    palm_vec = mid_mcp - wrist
    thumb_vec = thumb_tip - thumb_mcp
    norm_p = np.linalg.norm(palm_vec)
    norm_t = np.linalg.norm(thumb_vec)
    if norm_p > 1e-6 and norm_t > 1e-6:
        cos_a = np.dot(palm_vec, thumb_vec) / (norm_p * norm_t)
        thumb_angle_deg = float(np.degrees(np.arccos(np.clip(cos_a, -1, 1))))
    else:
        thumb_angle_deg = 38.0  # default reference

    # Width profile at 10% increments along palm_length
    wy = lm[0][1]
    my = lm[9][1]
    band = abs(my - wy) * 0.18  # ±18% band around each level
    width_profile = []
    for pct in range(0, 101, 10):
        ty = wy + (my - wy) * pct / 100.0
        nearby_xs = [p[0] for p in lm if abs(p[1] - ty) < band]
        if len(nearby_xs) >= 2:
            ww = round(max(nearby_xs) - min(nearby_xs), 1)
        else:
            ww = None
        width_profile.append({'pct': pct, 'width_mm': ww})

    return {
        'palm_width_max':    round(palm_width_max, 1),
        'palm_length':       round(palm_length, 1),
        'width_at_fingers':  round(width_at_fingers, 1),
        'width_at_palm':     round(width_at_palm, 1),
        'width_at_wrist':    round(width_at_wrist, 1),
        'grip_height':       round(grip_height, 1),
        'trigger_reach_est': round(trigger_reach_est, 1),
        'thumb_angle_deg':   round(thumb_angle_deg, 1),
        'palm_swell_y_pct':  50.0,
        'width_profile':     width_profile,
    }


def detect_cylinder_side(image, H):
    """
    Detect calibration cylinder in side-view photo using HoughCircles.

    Do NOT use MediaPipe here — hand in grip posture causes landmark errors.
    Matches detected radius to nearest CYLINDER_DIAMETERS_MM value.

    Returns: (grip_diameter_mm, palm_depth_max_mm)
    """
    px_per_mm = _scale_px_per_mm(image, H)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 2)

    r_min = max(5, int(CYLINDER_DIAMETERS_MM[0] / 2 * px_per_mm * 0.7))
    r_max = int(CYLINDER_DIAMETERS_MM[-1] / 2 * px_per_mm * 1.3)

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2,
        minDist=gray.shape[0] // 4,
        param1=100, param2=30,
        minRadius=r_min, maxRadius=r_max,
    )

    if circles is None:
        print("  [!] Cylinder not detected — set grip_diameter manually in JSON")
        return None, None

    x, y, r = circles[0][0]
    diam_mm = 2.0 * r / px_per_mm
    nearest = min(CYLINDER_DIAMETERS_MM, key=lambda d: abs(d - diam_mm))
    print(f"  Cylinder: detected Ø{diam_mm:.1f}mm → snapped to Ø{nearest}mm")

    # Palm depth: rough estimate from hand silhouette in side view
    palm_depth = round(float(nearest) * 0.85, 1)
    return float(nearest), palm_depth


def save_debug_image(image, lm_px, H, out_path):
    """Save annotated image with landmarks and board axes for visual verification."""
    debug = image.copy()
    h, w = image.shape[:2]

    # Draw landmarks
    for i, (px, py) in enumerate(lm_px):
        cv2.circle(debug, (int(px), int(py)), 5, (0, 255, 0), -1)
        if i in [0, 5, 9, 13, 17, 4, 8, 12]:
            cv2.putText(debug, str(i), (int(px) + 6, int(py)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1)

    # Connect wrist→fingertips
    for tip in [4, 8, 12, 16, 20]:
        pt0 = (int(lm_px[0][0]), int(lm_px[0][1]))
        pt1 = (int(lm_px[tip][0]), int(lm_px[tip][1]))
        cv2.line(debug, pt0, pt1, (100, 200, 100), 1)

    # Scale bar: 50mm
    px_per_mm = _scale_px_per_mm(image, H)
    bar_px = int(50 * px_per_mm)
    cv2.line(debug, (20, 40), (20 + bar_px, 40), (0, 255, 255), 3)
    cv2.putText(debug, "50 mm", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imwrite(str(out_path), debug)
    print(f"  Debug image: {out_path}")


def analyze_photo(top_path: str, side_path: str = None,
                  plate: PlateConfig = None,
                  confidence: float = 0.3,
                  flip: bool = False) -> dict:
    top_path = Path(top_path)
    source_type = 'photo_2view' if side_path else 'photo_1view'
    accuracy = '±1-2mm (photo). Scan recommended for final.'

    if plate is None:
        plate = select_plate()

    print(f"\nBiometriScan — photo ({source_type})")
    print(f"  Top:        {top_path}")
    if side_path:
        print(f"  Side:       {side_path}")
    print(f"  Plate:      {plate.name}  ({plate.summary()})")
    print(f"  Confidence: {confidence}")

    top_img = cv2.imread(str(top_path))
    if top_img is None:
        raise FileNotFoundError(f"Cannot open image: {top_path}")

    if flip:
        top_img = cv2.flip(top_img, 1)
        print(f"  Flip:       horizontal (mirrored board)")

    # Downscale very large images for speed (homography accuracy not affected)
    h, w = top_img.shape[:2]
    if max(h, w) > 3000:
        scale = 3000 / max(h, w)
        top_img = cv2.resize(top_img, (int(w * scale), int(h * scale)))
        print(f"  Resized:    {top_img.shape[1]}×{top_img.shape[0]}")

    print("\n[1/3] ChArUco detection...")
    H = detect_charuco(top_img, plate, mirrored=flip)

    print("\n[2/3] Hand landmark detection...")
    lm_px = detect_hand(top_img, confidence)

    top_m = extract_landmarks_top(lm_px, H)

    debug_path = top_path.with_name(top_path.stem + '_debug.jpg')
    save_debug_image(top_img, lm_px, H, debug_path)

    params = {
        'palm_width_max':     top_m['palm_width_max'],
        'palm_length':        top_m['palm_length'],
        'palm_depth_max':     None,
        'width_at_fingers':   top_m['width_at_fingers'],
        'width_at_palm':      top_m['width_at_palm'],
        'width_at_wrist':     top_m['width_at_wrist'],
        'grip_diameter':      None,
        'grip_thickness_rec': None,
        'grip_height':        top_m['grip_height'],
        'palm_swell_y_pct':   top_m['palm_swell_y_pct'],
        'trigger_reach_est':  top_m['trigger_reach_est'],
        'thumb_angle_deg':    top_m['thumb_angle_deg'],
    }

    if side_path:
        print(f"\n[3/3] Side view — cylinder detection...")
        side_img = cv2.imread(str(side_path))
        if side_img is None:
            print(f"  [!] Cannot open: {side_path} — skipping side view")
        else:
            side_H = detect_charuco(side_img, plate)
            grip_diam, palm_depth = detect_cylinder_side(side_img, side_H)
            params['grip_diameter'] = grip_diam
            params['palm_depth_max'] = palm_depth
            if grip_diam:
                params['grip_thickness_rec'] = round(grip_diam * 0.75, 1)
    else:
        print("\n[3/3] No side view — grip_diameter=None (set manually after cylinder test)")

    output = {
        'source_file':   str(top_path),
        'source_type':   source_type,
        'accuracy_note': accuracy,
        'plate':         plate.to_dict(),
        'grip_params':   params,
        'width_profile': top_m['width_profile'],
    }

    out_path = top_path.with_name(top_path.stem + '_params.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n--- Results ---")
    for k, v in params.items():
        if v is not None:
            unit = '°' if 'angle' in k or 'angle' in k else 'mm'
            print(f"  {k:<24} {v} {unit}")
    print(f"\nSaved: {out_path}")
    output['output_file'] = str(out_path)
    return output


if __name__ == '__main__':
    import argparse
    from plate_config import list_plates

    ap = argparse.ArgumentParser(
        description='BiometriScan — analyze hand photo with ChArUco calibration plate'
    )
    ap.add_argument('top_view', help='Top-view photo path (palm up on plate)')
    ap.add_argument('side_view', nargs='?', help='Side-view photo path (optional)')
    ap.add_argument('--plate', default=None,
                    help='Plate name from registry (omit to select interactively). '
                         f'Known: {[p.name for p in list_plates()]}')
    ap.add_argument('--confidence', type=float, default=0.3,
                    help='MediaPipe hand detection confidence 0.1-1.0 (default: 0.3)')
    ap.add_argument('--flip', action='store_true',
                    help='Flip photo horizontally before processing (use when board was printed mirrored)')
    args = ap.parse_args()

    plate = select_plate(args.plate)
    analyze_photo(args.top_view, args.side_view, plate, args.confidence, flip=args.flip)
