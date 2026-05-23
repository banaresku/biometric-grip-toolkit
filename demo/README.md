# Demo — BiometriScan Phase 1

Pipeline working end-to-end from a single top-view photo.

---

## What you're looking at

**`00_board_clean.jpg`** — The ChArUco calibration plate (7×9 grid, 30mm squares, FDM-printed on rigid substrate). 13 ArUco markers visible; the pipeline uses these to compute the homography from pixel space to millimeter space.

**`01_hand_on_board.jpg`** — Input: palm placed on the same plate.

**`02_aruco_detection.jpg`** — Step 1: ArUco markers detected (green outlines), homography computed from marker corners to board millimeter space. 6 markers visible around hand perimeter — enough for metric calibration.

**`03_landmarks.jpg`** — Step 2: MediaPipe hand landmark detection (21 keypoints), projected onto the perspective-corrected coordinate system. Lines connect wrist to each fingertip.

**`04_params_example.json`** — Output: grip parameters in millimeters, ready for ParamGrip.

---

## Output from this scan

```
palm_width_max      106.4 mm   thumb_mcp → pinky_mcp span
palm_length         103.6 mm   wrist → middle MCP
width_at_fingers     67.6 mm   index → pinky MCP row
grip_height         192.0 mm   wrist → middle fingertip
trigger_reach_est   180.4 mm   wrist → index fingertip
thumb_angle_deg      24.3 °    thumb axis relative to palm axis
```

---

## How to reproduce

```powershell
.\scan.ps1 photos\your_photo.jpg
```

First run builds the Docker image (~2 min). Subsequent runs take ~5 seconds.

Board SVG for printing: `1_biometriscan/calibration/charuco_9x11_30mm.svg`
Printing guide: `docs/plate_printing_guide.md`
