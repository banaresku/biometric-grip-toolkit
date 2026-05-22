#!/usr/bin/env python3
"""
Generate a ChArUco board SVG for printing.

Key fix: DICT_4X4 markers are 6×6 cells (borderBits=1 → 1+4+1=6).
Previous version incorrectly used 7 cells per marker (21mm/7=3mm),
producing a double border row that OpenCV cannot decode.
Correct: 21mm / 6 = 3.5mm per cell.

Usage:
  python gen_charuco_svg.py              # default: 7x9, 30mm squares, 21mm markers
  python gen_charuco_svg.py --out path/to/output.svg
"""

import argparse
import cv2
import numpy as np


def generate_charuco_svg(
    squares_x: int = 7,
    squares_y: int = 9,
    square_mm: float = 30.0,
    marker_mm: float = 21.0,
    dict_id: int = cv2.aruco.DICT_4X4_250,
    out_path: str = "1_biometriscan/calibration/charuco_A4_30mm.svg",
    border_bits: int = 1,
):
    dictionary = cv2.aruco.getPredefinedDictionary(dict_id)

    # DICT_4X4 marker is (4 data + 2 border) × (4 data + 2 border) = 6×6 cells
    n_cells = 4 + 2 * border_bits  # 6 for borderBits=1
    cell_mm = marker_mm / n_cells   # 3.5mm for 21mm/6

    board_w = squares_x * square_mm
    board_h = squares_y * square_mm

    margin = (square_mm - marker_mm) / 2.0  # offset of marker inside square

    # Uniform margin around board; extra space at bottom for info line
    m = 8.0          # side and top margin
    info_h = 6.0     # bottom strip for info text
    total_w = board_w + 2 * m
    total_h = board_h + 2 * m + info_h
    ox = m           # board left edge in SVG coords
    oy = m           # board top edge in SVG coords

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- ChArUco {squares_x}x{squares_y} | {square_mm}mm sq | {marker_mm}mm marker'
        f' | DICT_4X4_250 | borderBits={border_bits} -->',
        f'<!-- LT/RT/LB/RB mark face orientation. Face-down print: labels appear mirrored in slicer. -->',
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {total_w} {total_h}"'
        f' width="{total_w}mm" height="{total_h}mm">',
        f'<rect x="0" y="0" width="{total_w}" height="{total_h}" fill="white"/>',
    ]

    marker_id = 0
    for row in range(squares_y):
        for col in range(squares_x):
            sx = ox + col * square_mm
            sy = oy + row * square_mm

            is_black_square = (col + row) % 2 == 1
            if is_black_square:
                lines.append(
                    f'<rect x="{sx}" y="{sy}"'
                    f' width="{square_mm}" height="{square_mm}" fill="black"/>'
                )
                mx = sx + margin
                my = sy + margin
                lines.append(
                    f'<rect x="{mx:.4f}" y="{my:.4f}"'
                    f' width="{marker_mm}" height="{marker_mm}" fill="white"/>'
                )
                bits = dictionary.generateImageMarker(marker_id, n_cells, borderBits=border_bits)
                for br in range(n_cells):
                    for bc in range(n_cells):
                        if bits[br, bc] == 0:
                            rx = mx + bc * cell_mm
                            ry = my + br * cell_mm
                            lines.append(
                                f'<rect x="{rx:.4f}" y="{ry:.4f}"'
                                f' width="{cell_mm}" height="{cell_mm}" fill="black"/>'
                            )
                marker_id += 1

    # Corner labels in the margin, just outside the board corners
    cf = 3.5  # font-size mm
    gap = 1.0
    corner_labels = [
        ('LT', ox - gap,           oy - gap,             'end',   'auto'),
        ('RT', ox + board_w + gap, oy - gap,             'start', 'auto'),
        ('LB', ox - gap,           oy + board_h + gap,   'end',   'hanging'),
        ('RB', ox + board_w + gap, oy + board_h + gap,   'start', 'hanging'),
    ]
    for label, x, y, anchor, baseline in corner_labels:
        lines.append(
            f'<text x="{x}" y="{y}" font-family="monospace" font-size="{cf}mm"'
            f' font-weight="bold" fill="black"'
            f' text-anchor="{anchor}" dominant-baseline="{baseline}">{label}</text>'
        )

    # Info line centered in the bottom strip
    info = (f'{board_w:.0f}x{board_h:.0f}mm  {squares_x}x{squares_y}sq'
            f'  sq={square_mm:.0f}mm  mk={marker_mm:.0f}mm  DICT_4X4_250')
    info_y = oy + board_h + m + info_h / 2
    lines.append(
        f'<text x="{total_w / 2}" y="{info_y}"'
        f' font-family="monospace" font-size="2.5mm" fill="black"'
        f' text-anchor="middle" dominant-baseline="middle">{info}</text>'
    )

    lines.append('</svg>')
    svg = '\n'.join(lines)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg)

    print(f"Generated: {out_path}")
    print(f"  Board: {squares_x}×{squares_y} squares, {board_w}×{board_h}mm")
    print(f"  Markers: {marker_id} total (IDs 0..{marker_id-1})")
    print(f"  Cells per marker: {n_cells}×{n_cells} ({cell_mm}mm each)")
    print(f"  Marker margin inside square: {margin}mm")


def main():
    p = argparse.ArgumentParser(description="Generate ChArUco SVG for printing")
    p.add_argument('--squares-x', type=int, default=7)
    p.add_argument('--squares-y', type=int, default=9)
    p.add_argument('--square-mm', type=float, default=30.0)
    p.add_argument('--marker-mm', type=float, default=21.0)
    p.add_argument('--out', default='1_biometriscan/calibration/charuco_A4_30mm.svg')
    args = p.parse_args()

    generate_charuco_svg(
        squares_x=args.squares_x,
        squares_y=args.squares_y,
        square_mm=args.square_mm,
        marker_mm=args.marker_mm,
        out_path=args.out,
    )


if __name__ == '__main__':
    main()
