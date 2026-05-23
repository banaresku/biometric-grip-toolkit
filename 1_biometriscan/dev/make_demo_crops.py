#!/usr/bin/env python3
"""
Crop demo images to board+hand area using ArUco marker bounding box.
Run from repo root inside Docker.
"""
import sys
import cv2
import numpy as np
from pathlib import Path

PHOTOS = Path("/photos")
DEMO   = Path("/demo")
DEMO.mkdir(exist_ok=True)

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

def detect_markers(img, min_perimeter_rate=0.01):
    """Return (bbox, n_markers) or (None, 0). bbox = (x1,y1,x2,y2)."""
    p = cv2.aruco.DetectorParameters()
    p.adaptiveThreshWinSizeMin  = 3
    p.adaptiveThreshWinSizeMax  = 73
    p.adaptiveThreshWinSizeStep = 10
    p.minMarkerPerimeterRate    = min_perimeter_rate
    det = cv2.aruco.ArucoDetector(DICT, p)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = det.detectMarkers(gray)
    if ids is None or len(ids) == 0:
        return None, 0
    pts = np.vstack([c.reshape(-1, 2) for c in corners])
    x1, y1 = pts.min(axis=0)
    x2, y2 = pts.max(axis=0)
    return (x1, y1, x2, y2), len(ids)

def best_orientation(img, min_perimeter_rate=0.01):
    """Try original and flipped; return (img, bbox) with most markers detected."""
    bbox, n  = detect_markers(img, min_perimeter_rate)
    fimg     = cv2.flip(img, 1)
    fbbox, fn = detect_markers(fimg, min_perimeter_rate)
    if fn > n:
        return fimg, fbbox, fn
    return img, bbox, n

def crop(img, bbox, pad_x_pct=0.18, pad_y_top_pct=0.28, pad_y_bot_pct=0.22):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1
    cx1 = max(0, int(x1 - bw * pad_x_pct))
    cx2 = min(w, int(x2 + bw * pad_x_pct))
    cy1 = max(0, int(y1 - bh * pad_y_top_pct))
    cy2 = min(h, int(y2 + bh * pad_y_bot_pct))
    return img[cy1:cy2, cx1:cx2], (cx1, cy1, cx2, cy2)

def scale_bbox(bbox, src_shape, dst_shape):
    sx = dst_shape[1] / src_shape[1]
    sy = dst_shape[0] / src_shape[0]
    x1, y1, x2, y2 = bbox
    return x1*sx, y1*sy, x2*sx, y2*sy

def save(img, path, quality=90):
    cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    h, w = img.shape[:2]
    print(f"  -> {path.name}  {w}x{h}px")

def maybe_downscale(img, max_side=3000):
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        s = max_side / max(h, w)
        img = cv2.resize(img, (int(w*s), int(h*s)))
    return img


# ─── Step 0: clean board ────────────────────────────────────────────────────

print("--- Step 0: clean board ---")
src_board = PHOTOS / "viber_image_2026-05-22_16-57-51-816.jpg"
if src_board.exists():
    board = maybe_downscale(cv2.imread(str(src_board)))
    board, board_bbox, n = best_orientation(board, min_perimeter_rate=0.005)
    if board_bbox is not None and n >= 3:
        x1, y1, x2, y2 = board_bbox
        print(f"  {n} markers, bbox ({x1:.0f},{y1:.0f}) -> ({x2:.0f},{y2:.0f})")
        c_board, _ = crop(board, board_bbox, pad_x_pct=0.06, pad_y_top_pct=0.06, pad_y_bot_pct=0.06)
        save(c_board, DEMO / "00_board_clean.jpg")
    else:
        print(f"  WARNING: only {n} marker(s) detected — skipping", file=sys.stderr)
else:
    print(f"  Board photo not found: {src_board}", file=sys.stderr)


# ─── Steps 1-3: hand scan ───────────────────────────────────────────────────

print("\n--- Steps 1-3: hand scan ---")
stem = "IMG_20260522_165254"
src_orig  = PHOTOS / f"{stem}.jpg"
src_aruco = PHOTOS / f"{stem}_flipped_aruco.jpg"
src_debug = PHOTOS / f"{stem}_debug.jpg"

for p in [src_orig, src_aruco, src_debug]:
    if not p.exists():
        print(f"Missing: {p}", file=sys.stderr)
        sys.exit(1)

# Original was mirrored (flipped board) — flip for consistent view
orig  = maybe_downscale(cv2.flip(cv2.imread(str(src_orig)), 1))
aruco = maybe_downscale(cv2.imread(str(src_aruco)))
debug = maybe_downscale(cv2.imread(str(src_debug)))

bbox, n = detect_markers(orig)
if bbox is None or n < 2:
    print("Falling back to aruco image for bbox detection")
    bbox, n = detect_markers(aruco)
if bbox is None:
    print("ERROR: no markers detected", file=sys.stderr)
    sys.exit(1)

x1, y1, x2, y2 = bbox
print(f"  {n} markers, bbox ({x1:.0f},{y1:.0f}) -> ({x2:.0f},{y2:.0f})")

orig_shape = orig.shape
c_orig,  _ = crop(orig,  bbox)
c_aruco, _ = crop(aruco, scale_bbox(bbox, orig_shape, aruco.shape))
c_debug, _ = crop(debug, scale_bbox(bbox, orig_shape, debug.shape))

save(c_orig,  DEMO / "01_hand_on_board.jpg")
save(c_aruco, DEMO / "02_aruco_detection.jpg")
save(c_debug, DEMO / "03_landmarks.jpg")

print("\nDone.")
