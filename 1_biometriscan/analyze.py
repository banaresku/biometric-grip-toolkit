#!/usr/bin/env python3
"""
analyze.py — unified entry point for BiometriScan
Dispatches to analyze_photo or analyze_scan based on file type.

Usage:
    python analyze.py hand_scan.ply                           # 3D scan
    python analyze.py top_view.jpg                            # single photo (interactive plate selection)
    python analyze.py top_view.jpg side_view.jpg              # two photos
    python analyze.py top_view.jpg --plate 7x9_30mm           # skip plate prompt
    python analyze.py top_view.jpg side_view.jpg --plate A4_15mm
"""

import sys
import argparse
from pathlib import Path

SCAN_EXTENSIONS  = {'.ply', '.obj', '.pcd', '.xyz'}
PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def main():
    ap = argparse.ArgumentParser(
        description='BiometriScan — analyze hand scan or photo'
    )
    ap.add_argument('inputs', nargs='+', help='Input file(s): scan or top-view [side-view]')
    ap.add_argument('--plate', default=None,
                    help='ChArUco plate name (omit to select interactively for photos)')
    ap.add_argument('--confidence', type=float, default=0.3,
                    help='MediaPipe confidence 0.1-1.0 (photos only, default: 0.3)')
    args = ap.parse_args()

    inputs = [Path(p) for p in args.inputs]
    for p in inputs:
        if not p.exists():
            print(f"Error: file not found: {p}")
            sys.exit(1)

    ext = inputs[0].suffix.lower()

    if ext in SCAN_EXTENSIONS:
        from analyze_scan import analyze_scan
        result = analyze_scan(str(inputs[0]))

    elif ext in PHOTO_EXTENSIONS:
        from plate_config import select_plate
        from analyze_photo import analyze_photo

        plate = select_plate(args.plate)
        top_view  = str(inputs[0])
        side_view = str(inputs[1]) if len(inputs) > 1 else None
        result = analyze_photo(top_view, side_view, plate, args.confidence)

    else:
        print(f"Error: unsupported file type: {ext}")
        print(f"  Scan:  {', '.join(sorted(SCAN_EXTENSIONS))}")
        print(f"  Photo: {', '.join(sorted(PHOTO_EXTENSIONS))}")
        sys.exit(1)

    print(f"\nNext step: python ../grip_calculator.py {result['output_file']}")


if __name__ == '__main__':
    main()
