#!/usr/bin/env python3
"""
Check what world positions ChArUco assigns to found corners,
and verify that custom ids= parameter works in CharucoBoard.
"""
import sys, cv2, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from plate_config import get_plate

plate = get_plate('7x9_30mm')
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

# Print mirrored IDs
ids = plate._mirrored_ids()
print("Mirrored IDs array (first 10):", ids[:10].tolist())
print("Expected: [2, 1, 0, 6, 5, 4, 3, 9, 8, 7]")

std_board   = plate.build_board(mirrored=False)
mir_board   = plate.build_board(mirrored=True)

# Verify marker IDs in both boards
print("\nStandard board marker IDs:", std_board.getIds()[:6].flatten().tolist())
print("Mirrored board marker IDs:", mir_board.getIds()[:6].flatten().tolist())

params = cv2.aruco.DetectorParameters()
params.adaptiveThreshWinSizeMin  = 3
params.adaptiveThreshWinSizeMax  = 73
params.adaptiveThreshWinSizeStep = 10
params.minMarkerPerimeterRate    = 0.01
params.errorCorrectionRate       = 0.8

cp = cv2.aruco.CharucoParameters()
cp.tryRefineMarkers = True

path = "photos/viber_image_2026-05-22_16-57-51-816.jpg"
img = cv2.flip(cv2.imread(path), 1)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

for label, board in [("standard", std_board), ("mirrored", mir_board)]:
    det = cv2.aruco.CharucoDetector(board, cp, params)
    cc, ci, mc, mi = det.detectBoard(gray)
    n_c = len(ci) if ci is not None else 0
    n_m = len(mi) if mi is not None else 0
    print(f"\n{label}: {n_m} markers, {n_c} corners")
    if mi is not None:
        print(f"  marker IDs found: {sorted(mi.flatten().tolist())}")
    if ci is not None and n_c > 0:
        print(f"  corner IDs: {ci.flatten().tolist()[:8]}")
        # World positions of found corners
        world = np.zeros(((plate.squares_y-1)*(plate.squares_x-1), 2), np.float32)
        nx = plate.squares_x - 1
        for r in range(plate.squares_y - 1):
            for c in range(plate.squares_x - 1):
                world[r * nx + c] = [c * plate.square_mm, r * plate.square_mm]
        for corner_id in ci.flatten()[:4]:
            wpt = world[corner_id]
            print(f"    corner {corner_id} → world ({wpt[0]:.0f}, {wpt[1]:.0f}) mm")
