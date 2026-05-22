#!/usr/bin/env python3
"""
Verify whether gen_charuco_svg.py has bit inversion by comparing:
1. OpenCV marker 0 rendered as 6x6 image
2. What gen_charuco_svg.py would draw for that marker
"""
import cv2
import numpy as np

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

# Get the 6x6 pixel map for marker 0
raw = dictionary.generateImageMarker(0, 6, borderBits=1)
print("generateImageMarker(0, 6) raw pixel grid (0=black, 255=white):")
for row in raw:
    print("  " + " ".join(f"{v:3d}" for v in row))

print()
print("Rendered visually:")
for row in raw:
    print("  " + "".join("#" if v == 0 else "." for v in row))

print()
print("gen_charuco_svg draws a black rect where pixel==0:")
for row in raw:
    print("  " + "".join("B" if v == 0 else " " for v in row))

print()
print("Expected ArUco marker 0 visual (from check_dict.py 6x6 sampling):")
print("  ######")
print("  #.#..#")
print("  ##.#.#")
print("  ###..#")
print("  ###.##")
print("  ######")

print()
print("Do they match?", end=" ")
expected_visual = [
    "######",
    "#.#..#",
    "##.#.#",
    "###..#",
    "###.##",
    "######",
]
svg_visual = ["".join("B" if v == 0 else " " for v in row) for row in raw]
svg_as_hash = ["".join("#" if v == 0 else "." for v in row) for row in raw]
if svg_as_hash == expected_visual:
    print("YES - SVG generation is correct, no inversion bug")
else:
    print("NO - mismatch:")
    for e, s in zip(expected_visual, svg_as_hash):
        flag = "" if e == s else "  <-- DIFF"
        print(f"  expected: {e}  got: {s}{flag}")
