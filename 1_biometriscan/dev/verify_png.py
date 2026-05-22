#!/usr/bin/env python3
import cv2

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
board = cv2.aruco.CharucoBoard((7, 9), 0.030, 0.021, dictionary)
detector = cv2.aruco.CharucoDetector(board)

img = cv2.imread("1_biometriscan/calibration/charuco_A4_30mm.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cc, ci, mc, mi = detector.detectBoard(gray)
n_m = len(mi) if mi is not None else 0
n_c = len(ci) if ci is not None else 0
print(f"Markers: {n_m}/31")
print(f"ChArUco corners: {n_c}/48")
if mi is not None:
    print(f"IDs: {sorted(mi.flatten().tolist())}")
