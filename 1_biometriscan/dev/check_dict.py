#!/usr/bin/env python3
"""Compare SVG marker bits vs actual DICT_4X4_250 marker bits."""
import cv2
import numpy as np

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
board = cv2.aruco.CharucoBoard(
    (7, 9),
    squareLength=0.030,
    markerLength=0.021,
    dictionary=dictionary,
)

img = board.generateImage((630, 810))
cv2.imwrite('/repo/photos/charuco_reference.png', img)
print("Reference image saved: /repo/photos/charuco_reference.png")

# Draw marker 0 at 210x210px (7 cells * 30px, or 6 cells * 35px)
marker0 = dictionary.generateImageMarker(0, 210)
cv2.imwrite('/repo/photos/marker0_ref.png', marker0)
for n_cells in [6, 7]:
    cell = 210 // n_cells
    print(f"\nMarker 0 sampled as {n_cells}x{n_cells} (cell={cell}px):")
    for row in range(n_cells):
        line = ""
        for col in range(n_cells):
            cx = col * cell + cell // 2
            cy = row * cell + cell // 2
            line += "#" if marker0[cy, cx] < 128 else "."
        print(f"  Row {row}: {line}")

# Dictionary format
print(f"\nDICT_4X4_250 bytesList shape: {dictionary.bytesList.shape}")
print(f"Marker 0 bytes: {dictionary.bytesList[0].flatten()}")
# The data bits for marker 0 (4x4 = 16 bits, packed MSB first)
bits = np.unpackbits(dictionary.bytesList[0].flatten())[:16]
print(f"Marker 0 data bits (4x4): {bits.reshape(4,4)}")

# Reference: SVG marker at square (0,0) data region was 4x5 bits
# top_borders=2, so data starts at row 2, stripped side borders:
# ##.#..#   (row 2, strip first/last -> .#..# -> cols 1-5 of 7)
# ###.#.#   (row 3 -> ##.#.# -> cols 1-5)
# ####..#   (row 4 -> ###..# -> cols 1-5)
# ####.##   (row 5 -> ###.## -> cols 1-5)
print("\nSVG marker (0,0) data region (from decode_svg_markers output):")
svg_data = np.array([
    [1, 0, 1, 0, 0],  # row 2 inner
    [1, 1, 0, 1, 0],  # row 3 inner
    [1, 1, 1, 0, 0],  # row 4 inner
    [1, 1, 1, 0, 1],  # row 5 inner
], dtype=np.uint8)
for r in svg_data:
    print("  " + "".join("#" if b else "." for b in r))
val = int("".join(str(b) for b in svg_data.flatten()), 2)
print(f"  Value: {val}")

# Now check: what if it's a 5x5 dict?
print("\nChecking DICT_5X5_250 marker 0:")
d5 = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
bits5 = np.unpackbits(d5.bytesList[0].flatten())[:25]
print(f"Data bits:\n{bits5.reshape(5, 5)}")
m5 = d5.generateImageMarker(0, 210)
cv2.imwrite('/repo/photos/marker0_5x5_ref.png', m5)
