#!/usr/bin/env python3
"""
Generate a print-ready ChArUco calibration board PNG.

OpenCV generates the marker pattern directly — no manual bit logic needed.
Wrist baseline is drawn only inside white chess squares (never over markers).

Board: 7×9 squares × 30mm = 210×270mm (fits A4 width exactly).
Print at 100% scale — do NOT scale to fit page.

Usage:
  python gen_charuco_png.py
  python gen_charuco_png.py --dpi 300 --out calibration/charuco_A4_30mm.png
"""

import argparse
import cv2
import numpy as np


def generate_charuco_png(
    squares_x: int = 7,
    squares_y: int = 9,
    square_mm: float = 30.0,
    marker_mm: float = 21.0,
    wrist_y_mm: float = 195.0,
    dpi: float = 300.0,
    out_path: str = "1_biometriscan/calibration/charuco_A4_30mm.png",
):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    board = cv2.aruco.CharucoBoard(
        (squares_x, squares_y),
        squareLength=square_mm / 1000.0,
        markerLength=marker_mm / 1000.0,
        dictionary=dictionary,
    )

    px_per_mm = dpi / 25.4
    w_px = round(squares_x * square_mm * px_per_mm)
    h_px = round(squares_y * square_mm * px_per_mm)

    img = board.generateImage((w_px, h_px), marginSize=0, borderBits=1)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Wrist baseline through white (marker-background) squares.
    # OpenCV convention for this board: (col+row)%2==1 → white squares with markers.
    # A thin line on white background is visible and doesn't break detection.
    wrist_row = int(wrist_y_mm / square_mm)
    y_px = round(wrist_y_mm * px_per_mm)
    stroke = max(2, round(px_per_mm * 0.5))   # ~0.5mm — thin enough not to hurt detection
    pad_mm = 3.0

    light_cols = [c for c in range(squares_x) if (c + wrist_row) % 2 == 1]

    for col in light_cols:
        x1 = round((col * square_mm + pad_mm) * px_per_mm)
        x2 = round(((col + 1) * square_mm - pad_mm) * px_per_mm)
        cv2.line(img_bgr, (x1, y_px), (x2, y_px), (0, 0, 210), stroke)

    # "WRIST" label in the rightmost light square
    if light_cols:
        last_col = light_cols[-1]
        label_x = round((last_col * square_mm + pad_mm + 1) * px_per_mm)
        label_y = round((wrist_y_mm - 2.5) * px_per_mm)
        font_scale = max(0.3, px_per_mm * 1.8 / 30)
        cv2.putText(
            img_bgr, "WRIST",
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 210),
            max(1, stroke - 1), cv2.LINE_AA,
        )

    cv2.imwrite(out_path, img_bgr)

    n_markers = sum(
        1 for r in range(squares_y) for c in range(squares_x) if (c + r) % 2 == 1
    )
    print(f"Generated: {out_path}")
    print(f"  Image: {w_px}×{h_px}px at {dpi:.0f} DPI")
    print(f"  Board: {squares_x*square_mm:.0f}×{squares_y*square_mm:.0f}mm (A4 width = 210mm)")
    print(f"  Markers: {n_markers} (IDs 0..{n_markers-1}), DICT_4X4_250")
    print(f"  Wrist baseline: y={wrist_y_mm}mm, row {wrist_row}, white cols {light_cols}")
    print(f"  Print at 100% scale — do NOT scale to fit page")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dpi', type=float, default=300.0)
    p.add_argument('--out', default='1_biometriscan/calibration/charuco_A4_30mm.png')
    args = p.parse_args()
    generate_charuco_png(dpi=args.dpi, out_path=args.out)


if __name__ == '__main__':
    main()
