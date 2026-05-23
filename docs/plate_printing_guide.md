# ChArUco Calibration Plate — Printing Guide

Target: `1_biometriscan/calibration/charuco_9x11_30mm.svg`
Result: 270×330mm rigid plate, 49 ArUco markers, wrist baseline ridge.

---

## Files

| File | Purpose |
|---|---|
| `charuco_9x11_30mm.svg` | Main field plate — print this |
| `charuco_A4_30mm.svg` | Legacy 7×9 A4 plate (mirrored boards only, requires `--flip`) |

---

## Slicer Setup

**Orientation — the critical step.**

The SVG has corner labels: **LT** (left-top), **RT**, **LB**, **RB**. These mark the face side — the side the camera sees during scanning.

- Face-up print (first layer = back): labels appear correct in slicer preview → correct
- Face-down print (first layer = face): labels appear **mirrored** in slicer preview → also correct — this is intentional

When in doubt: print a single-layer test, flip it over, check that LT is top-left when the pattern faces up.

**Size check:** import SVG at 1:1 scale. Verify in slicer: plate = 270×330mm. Most slicers import SVG in px — set DPI to 96 or scale manually.

---

## Two-Color First Layer (recommended)

The pattern requires high contrast. Two-color first layer eliminates glare that single-color matte finishes can't fully prevent.

1. Slice as normal with white filament
2. At layer 1, pause and swap to black
3. Print layer 1 in black (full layer — black squares + marker backgrounds)
4. Swap back to white, continue

If your printer has multi-material: assign black to the first layer only.

**Simpler alternative:** print all in white, paint black squares with matte black spray. Less reliable but works for field testing.

---

## Material

**PETG** — recommended. Dimensionally stable, low warp, matte surface with standard settings.

Avoid: PLA (warps over time, especially in sunlight), silk/glossy finishes (glare kills detection).

Layer height: 0.2mm or finer. Infill: 20%+ for rigidity. No supports needed.

---

## Wrist Baseline Ridge

The SVG includes a red dashed reference line at y=285mm from the board top. This is where the physical ridge goes.

Print options:
- **Integrated ridge in STL**: generate board STL with a 1-2mm raised ridge at y=285mm — cleanest solution, single print
- **Separate ridge piece**: print a thin strip, glue to plate at the reference line
- **Manual marking**: score or paint the line — sufficient for photo protocol (hand is placed by feel anyway)

Ridge height: 2-3mm is enough to feel without blocking the wrist from lying flat.

---

## After Printing — Verification

Run the reference PNG check:

```powershell
docker run --rm -v "${PWD}:/repo" -w /repo --entrypoint python biometric-grip `
    1_biometriscan/gen_charuco_png.py
```

Then open `charuco_9x11_30mm.png` and compare visually with the printed plate.

For a live detection check, photograph the plate alone (no hand) and run:

```powershell
.\scan.ps1 photos\plate_only.jpg
```

Target: **30+ markers detected** with no hand covering the board. If below 20, check contrast and scale.

---

## Scan Protocol (reminder)

Once the plate is ready:

**Photo 1 — top view:**
- Palm **up** on plate, wrist crease against baseline ridge
- Fingers slightly spread, natural position
- Camera strictly vertical, centered over the hand
- Even diffuse lighting — no direct sun, no hard shadows

**Photo 2 — side view (optional, for grip diameter):**
- Hand gripping a calibration cylinder
- Plate vertical next to hand
- Camera strictly lateral (along thumb axis)

```powershell
# Single photo
.\scan.ps1 photos\top_view.jpg

# Two photos
.\scan.ps1 photos\top_view.jpg photos\side_view.jpg
```

No `--flip` needed with correctly printed 9×11 plate.
