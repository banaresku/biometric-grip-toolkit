#!/usr/bin/env python3
"""
analyze_scan.py — 3D scan analysis for BiometriScan
Input:  PLY or OBJ point cloud (structured light or photogrammetry)
Output: <stem>_params.json with grip_params matching grip_calculator.py schema

Accuracy: ±0.3-0.5mm
"""

import json
import sys
from pathlib import Path

# TODO: import open3d as o3d
# TODO: import numpy as np


def analyze_scan(scan_path: str) -> dict:
    scan_path = Path(scan_path)
    print(f"\nBiometriScan — 3D scan")
    print(f"  Input: {scan_path}")

    # TODO: pcd = o3d.io.read_point_cloud(str(scan_path))

    # TODO: orient scan to canonical pose
    #   - detect palm plane (RANSAC)
    #   - align wrist→middle-finger axis with Y
    #   - align thumb axis with X

    # TODO: extract measurements from aligned point cloud
    params = {
        'palm_width_max':     None,  # max extent along X
        'palm_length':        None,  # wrist crease → middle MCP joint
        'palm_depth_max':     None,  # max extent along Z
        'width_at_fingers':   None,
        'width_at_palm':      None,
        'width_at_wrist':     None,
        'grip_diameter':      None,  # from calibration cylinder selection (user input)
        'grip_thickness_rec': None,  # derived from palm_depth_max
        'grip_height':        None,
        'palm_swell_y_pct':   None,
        'trigger_reach_est':  None,
        'thumb_angle_deg':    None,
    }

    output = {
        'source_file':   str(scan_path),
        'source_type':   'scan_3d',
        'accuracy_note': '±0.3-0.5mm (scan)',
        'grip_params':   params,
        'width_profile': [],  # TODO: [{y_pct, width_mm}, ...] every 5% of palm_length
    }

    out_path = scan_path.with_name(scan_path.stem + '_params.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {out_path}")
    output['output_file'] = str(out_path)
    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_scan.py hand_scan.ply")
        sys.exit(1)
    analyze_scan(sys.argv[1])
