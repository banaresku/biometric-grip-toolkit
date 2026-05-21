#!/usr/bin/env python3
"""
analyze.py — unified entry point for BiometriScan
Dispatches to analyze_photo or analyze_scan based on file type.

Usage:
    python analyze.py hand_scan.ply              # 3D scan
    python analyze.py top_view.jpg               # single photo
    python analyze.py top_view.jpg side_view.jpg # two photos (recommended)
"""

import sys
from pathlib import Path

SCAN_EXTENSIONS  = {'.ply', '.obj', '.pcd', '.xyz'}
PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze.py hand_scan.ply")
        print("  python analyze.py top_view.jpg")
        print("  python analyze.py top_view.jpg side_view.jpg")
        sys.exit(1)

    inputs = [Path(p) for p in sys.argv[1:]]
    for p in inputs:
        if not p.exists():
            print(f"Error: file not found: {p}")
            sys.exit(1)

    ext = inputs[0].suffix.lower()

    if ext in SCAN_EXTENSIONS:
        from analyze_scan import analyze_scan
        result = analyze_scan(str(inputs[0]))

    elif ext in PHOTO_EXTENSIONS:
        from analyze_photo import analyze_photo
        top_view  = str(inputs[0])
        side_view = str(inputs[1]) if len(inputs) > 1 else None
        result = analyze_photo(top_view, side_view)

    else:
        print(f"Error: unsupported file type: {ext}")
        print(f"  Scan:  {', '.join(sorted(SCAN_EXTENSIONS))}")
        print(f"  Photo: {', '.join(sorted(PHOTO_EXTENSIONS))}")
        sys.exit(1)

    print(f"\nNext step: python ../grip_calculator.py {result['output_file']}")


if __name__ == '__main__':
    main()
