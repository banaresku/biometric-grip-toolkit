#!/usr/bin/env python3
"""
Decode ArUco marker bit patterns directly from the ChArUco SVG file.
The SVG encodes markers as small black rects. This script:
  1. Parses the SVG, extracts marker bit grids per square
  2. Tries to identify the ArUco dictionary and marker IDs
  3. Prints the board layout and detected IDs

Usage:
  python decode_svg_markers.py charuco_A4_30mm.svg
"""

import re
import sys
import numpy as np
from pathlib import Path


def parse_svg_bits(svg_path):
    """
    Parse all small black rects from the SVG.
    Returns list of (x_mm, y_mm) for each bit cell center.
    Ignores large rects (chess squares, background).
    """
    text = Path(svg_path).read_text(encoding='utf-8')

    # Extract board dimensions from viewBox
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    board_w, board_h = float(vb.group(1)), float(vb.group(2))

    # Extract comment metadata
    meta = re.search(r'<!--.*?-->', text)
    print(f"SVG metadata: {meta.group(0) if meta else 'none'}")
    print(f"Board: {board_w}mm × {board_h}mm")

    # Find all rect elements
    rects = re.findall(
        r'<rect\s+x="([\d.]+)"\s+y="([\d.]+)"\s+width="([\d.]+)"\s+height="([\d.]+)"\s+fill="black"',
        text
    )

    # Separate chess squares (large) from marker bits (small)
    # Heuristic: small rects have width < 10mm
    bits = []
    chess_squares = []
    for x, y, w, h in rects:
        x, y, w, h = float(x), float(y), float(w), float(h)
        if w < 10:
            # Bit center
            bits.append((x + w/2, y + h/2, w))
        else:
            chess_squares.append((x, y, w, h))

    print(f"Chess squares: {len(chess_squares)}")
    print(f"Marker bits (cells): {len(bits)}")

    if bits:
        cell_size = bits[0][2]
        print(f"Bit cell size: {cell_size}mm")

    return bits, chess_squares, board_w, board_h


def group_bits_by_square(bits, chess_squares, square_size=30.0):
    """Group marker bits by which chess square they belong to."""
    from collections import defaultdict
    squares = defaultdict(list)

    for bx, by, bsize in bits:
        # Which square?
        col = int(bx / square_size)
        row = int(by / square_size)
        # Local coords within the square
        lx = bx - col * square_size
        ly = by - row * square_size
        squares[(col, row)].append((lx, ly))

    return squares


def extract_bit_grid(local_bits, marker_mm=21.0, square_mm=30.0):
    """Convert local bit coords to a 2D grid."""
    if not local_bits:
        return None

    margin = (square_mm - marker_mm) / 2  # 4.5mm
    xs = sorted(set(round(x, 1) for x, y in local_bits))
    ys = sorted(set(round(y, 1) for x, y in local_bits))
    ncols = len(xs)
    nrows = len(ys)

    x_idx = {x: i for i, x in enumerate(xs)}
    y_idx = {y: i for i, y in enumerate(ys)}

    grid = np.zeros((nrows, ncols), dtype=np.uint8)
    for x, y in local_bits:
        xr = round(x, 1)
        yr = round(y, 1)
        if xr in x_idx and yr in y_idx:
            grid[y_idx[yr], x_idx[xr]] = 1

    return grid


def grid_to_aruco_bits(grid):
    """
    Extract the ArUco marker ID from a bit grid.
    Assumes standard ArUco format: outer ring = border (all 1s),
    inner NxN = data bits read row by row, MSB first.

    Works for 6×6 (4×4 data) and 7×7 (5×5 data) grids.
    """
    n = grid.shape[0]
    if grid.shape[0] != grid.shape[1]:
        return None, None

    # Detect how many rows are the "header" border
    # Standard: row 0 = all 1, row N-1 = all 1
    # Non-standard (this board): row 0,1 = all 1, row N-1 = all 1
    top_borders = 0
    for i in range(n):
        if grid[i].sum() == n:  # all-black row
            top_borders += 1
        else:
            break
    bot_borders = 0
    for i in range(n-1, -1, -1):
        if grid[i].sum() == n:
            bot_borders += 1
        else:
            break

    data_rows = grid[top_borders:n-bot_borders, 1:-1]  # strip side borders too
    n_data_rows, n_data_cols = data_rows.shape

    print(f"  Grid {n}×{n}: top_borders={top_borders} bot_borders={bot_borders} "
          f"data={n_data_rows}×{n_data_cols}")

    # Convert data bits to integer (MSB first, row by row)
    bits_flat = data_rows.flatten()
    value = int(''.join(str(b) for b in bits_flat), 2)

    return value, bits_flat


def try_match_opencv_dict(data_value, n_data_bits):
    """Try to match data value to OpenCV ArUco dictionary."""
    import cv2

    # Try all 4×4 dictionaries (data region is 4×4 = 16 bits by default in OpenCV)
    for dname, did in [
        ('4X4_50', cv2.aruco.DICT_4X4_50),
        ('4X4_100', cv2.aruco.DICT_4X4_100),
        ('4X4_250', cv2.aruco.DICT_4X4_250),
    ]:
        d = cv2.aruco.getPredefinedDictionary(did)
        n_markers = d.bytesList.shape[0]
        # Each marker is stored as compressed bits in bytesList
        # bytesList[i] has shape (4, 1) for 4×4 markers
        # The data bits are encoded as bytes, reading LSB first by column
        # This is complex to decode; let's try brute force

    return None


def main():
    svg_path = sys.argv[1] if len(sys.argv) > 1 else \
        '1_biometriscan/calibration/charuco_A4_30mm.svg'

    bits, chess_squares, bw, bh = parse_svg_bits(svg_path)

    # Detect cell size
    cell_sizes = [b[2] for b in bits]
    cell_size = round(np.median(cell_sizes), 2)

    squares_dict = group_bits_by_square(bits, chess_squares)
    print(f"\nMarker squares found: {len(squares_dict)}")

    # Analyze first few markers
    sorted_squares = sorted(squares_dict.keys())
    print(f"\nFirst marker positions: {sorted_squares[:6]}")

    for sq in sorted_squares[:4]:
        local_bits = squares_dict[sq]
        print(f"\nSquare {sq}: {len(local_bits)} bit cells")
        grid = extract_bit_grid(local_bits)
        if grid is not None:
            print(f"  Grid shape: {grid.shape}")
            for row in grid:
                print('  ' + ''.join('#' if b else '.' for b in row))
            value, bits_flat = grid_to_aruco_bits(grid)
            if value is not None:
                print(f"  Data value (MSB): {value} ({bin(value)})")


if __name__ == '__main__':
    main()
