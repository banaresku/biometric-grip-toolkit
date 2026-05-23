# CLAUDE.md
## Context for Claude Code — Biometric Grip Toolkit

This file gives Claude Code the context needed to continue development without re-explaining the project from scratch.

---

## Project Overview

Three independent open source tools for generating ergonomic grip geometry from hand biometrics:

```
BiometriScan  →  ParamGrip  →  VoroShell
```

Primary target: precision sport equipment grips (ISSF Olympic sport, first implementations).
Designed to generalize to any hand-held object.

Philosophy: open source, free stack, accessible to any club worldwide.
License: CC BY-SA 4.0.

---

## Repository Structure

```
biometric-grip-toolkit/
├── README.md
├── CLAUDE.md                        ← this file
├── LICENSE
│
├── 1_biometriscan/
│   ├── analyze.py                   ← unified entry point (detects file type)
│   ├── analyze_scan.py              ← PLY/OBJ point cloud analysis (Open3D)
│   ├── analyze_photo.py             ← photo + ChArUco analysis (OpenCV + MediaPipe)
│   └── calibration/
│       ├── charuco_A4.svg           ← 210×285mm, 14×19 cells, 15mm, DICT_4X4_250
│       ├── charuco_300x300.svg      ← 300×300mm, 15×15 cells, 20mm, DICT_4X4_250
│       └── cylinder_set.stl         ← ∅28/32/36/40/44/48mm, L=100mm (TODO)
│
├── 2_paramgrip/
│   ├── freecad_load_params.py       ← loads JSON into FreeCAD Spreadsheet
│   ├── templates/
│   │   └── grip_base_template.FCStd ← parametric skeleton (TODO)
│   └── mount_points/
│       └── <device>_mount.json       ← mounting geometry per equipment type
│
├── 3_voroshell/
│   ├── voronoi_apply.py             ← bpy automation with zone masking (TODO)
│   ├── voronoi_params.json          ← default Voronoi parameters
│   └── zones_example.json           ← zone masking example
│
└── docs/
    ├── grip_pipeline_doc.md         ← full pipeline documentation
    ├── modular_grip_concept.md      ← modular adjustable grip + fitting protocol
    └── product_decomposition.md     ← three-tool architecture rationale
```

---

## Tool 1: BiometriScan

### Entry Point
```bash
python analyze.py hand_scan.ply              # 3D scan
python analyze.py top_view.jpg               # single photo
python analyze.py top_view.jpg side_view.jpg # two photos (recommended)
```

### Output Format (grip_params.json)
```json
{
  "source_file": "top_view.jpg",
  "source_type": "photo_2view",
  "accuracy_note": "±1-2mm (photo). Scan recommended for final.",
  "grip_params": {
    "palm_width_max": 87.3,
    "palm_length": 112.5,
    "palm_depth_max": 28.1,
    "width_at_fingers": 79.2,
    "width_at_palm": 87.3,
    "width_at_wrist": 71.4,
    "grip_diameter": 36.0,
    "grip_thickness_rec": 23.9,
    "grip_height": 68.0,
    "palm_swell_y_pct": 52.3,
    "trigger_reach_est": 55.1,
    "thumb_angle_deg": 38.0
  },
  "width_profile": []
}
```

### ChArUco Calibration Plate
- Dictionary: `DICT_4X4_250` (important — 4X4_50 has too few markers for A4 size)
- Wrist baseline: physical ridge printed on plate, known Y position
- Finger axes: index (blue dashed) and thumb (green dashed, 38° reference) printed on plate
- Two-color first-layer print: matte finish eliminates glare for OpenCV detection
- Left-hand variant: mirror in slicer (not regenerated separately)

### Calibration Cylinders
- Diameters: ∅28, 32, 36, 40, 44, 48mm
- Protocol: shooter holds each → selects most comfortable → that IS grip_diameter
- Used in side photo: detected via cv2.HoughCircles for grip depth measurement
- Material: PETG, wall 3mm, length 100mm

### Photo Protocol
**Photo 1 (top view):**
- Palm UP on ChArUco plate
- Wrist crease against baseline ridge
- Fingers slightly spread, natural
- Camera strictly vertical
- Even lighting, no shadows

**Photo 2 (side view):**
- Hand gripping selected cylinder
- ChArUco plate vertical next to hand
- Camera strictly lateral (along thumb axis)
- Full plate + full cylinder in frame

### Key Algorithm Details
- Photo 1: MediaPipe 21 landmarks, homography from ChArUco
- Photo 2: cv2.HoughCircles for cylinder detection (NOT MediaPipe — hand in grip posture reduces accuracy)
- Perspective correction: up to ~40° camera angle tolerated
- Wrist detection: NOT from MediaPipe — from known baseline Y position on plate

---

## Tool 2: ParamGrip

### FreeCAD Spreadsheet Variables
```
# Biometric (from JSON)
palm_width_max, palm_length, palm_depth_max
grip_thickness_rec, palm_swell_y_pct
wrist_width, grip_height, trigger_reach_est

# Mounting geometry (per equipment type — loaded from mount_points/<device>.json)
# screw positions, rail dimensions, face geometry — all equipment-specific
```

### Cross-Sections for Loft (bottom to top)
```
Sketch_Wrist      — wrist area, width=wrist_width
Sketch_PalmLow    — 25% height
Sketch_PalmMid    — palm swell zone (~50%), maximum section
Sketch_PalmHigh   — 75% height
Sketch_Fingers    — finger contact zone
```

### Export
- To Fusion 360: STEP (preserves edges as wires for loft)
- Direct to slicer: STL via Mesh workbench
- Minimum wall: 2.5mm structural, 4.0mm at mounting area

---

## Tool 3: VoroShell

### Zone Masking (zones.json)
```json
{
  "solid_zones": [
    "mounting_face",
    "screw_holes_r6",
    "wrist_structural_base"
  ],
  "lattice_zones": [
    "palm_contact_sides",
    "thumb_shelf_surface",
    "backstrap_panel"
  ]
}
```

### Voronoi Parameters (voronoi_params.json)
```json
{
  "scale": 4.5,
  "randomness": 0.8,
  "wall_thickness_mm": 1.8,
  "solidify_offset": -1.0,
  "transition_width_mm": 3.0
}
```

### Minimum Printable Dimensions
```
Voronoi ribs:    ≥ 1.5mm
Solid walls:     ≥ 2.5mm
Mounting area:   ≥ 4.0mm (solid, no lattice)
```

---

## Modular Adjustable Grip

Six modules, all continuous screw adjustment:

| Module | Movement | Range | Material |
|---|---|---|---|
| M1 Palm shelf | forward/back (X) | 0..+12mm | PETG |
| M2 Thumb rest | height (Y) + angle (Ry) | 0..+15mm / ±20° | PETG |
| M3 Backstrap | depth (Z) | 0..+10mm | PETG |
| M4 Pinky shelf | height (Y) | 0..+10mm | PETG |
| M5 Trigger reach | forward (X) | 0..+8mm | PETG |
| M6 Palm swell | depth (Z) | 0..+8mm | PA12 / TPU 95A |

M6 is the ONLY module using elastic material. All others rigid geometry.
PA12/TPU D70-75 = elastic construction part, NOT soft insert. ISSF compliant.

### Fitting Protocol
Objective coach protocol (no "feels comfortable" — only observable facts):
- M5 first (trigger reach — index finger first phalanx center contact)
- M3 second (backstrap — paper strip test)
- M1 third (thumb lift test)
- M2 fourth (thumb free movement + angle ≤20° from bore axis)
- M4 fifth (pinky horizontal check)
- Final: 5/5 repeated grips all markers nominal

---

## Material Notes

### For ISSF Competition Grips
- PETG or ASA (rigid, no soft inserts)
- M6 insert: PA12 or TPU 95A Shore D70-75 (holds shape = structural part)
- No foam, no rubber pads, no closed-cell inserts

### Voronoi Physics (why it works for wet hands)
- Uniform ventilation → no local temperature gradient → no sweat concentration
- Rib contact only → sweat drains into cells → no lubricating film
- Distributed pressure → no blood flow restriction in prolonged grip
- Commercially validated: MeshPro used by Olympic champions, same principle

### FDM Material Comparison for Grips (wet hand)
```
Ranking (best to worst grip when wet):
1. Voronoi ribs, any material
2. Plain PETG/ABS + sandblast/matte
3. GF/CF composite (rough surface from fibers)
4. Smooth plain plastic
5. GF smooth (worst — glass surface film effect)
```

PBT recommended as base material: low moisture absorption (0.1%), naturally matte,
thermally conductive vs wood, stable surface long-term. Available in stock.

---

## Competitor Context

| | BiometriScan | ParamGrip | VoroShell |
|---|---|---|---|
| MeshPro | Closed AI, photo→size selection | Manual designer work, 8-10 weeks | Closed, MJF PA nylon |
| SmartGrip | None | Discrete plugs only | None |
| Rink | Personal visit required | Handcraft (wood) | None |
| **This toolkit** | **Open algorithm, automatic** | **Parametric, automatic** | **Open recipe** |

MeshPro price: €260-350, 8-10 weeks.
This toolkit target: €30-50 material + 1-3 days, biometrically fitted.

---

## Open Questions / Active TODOs

- [ ] Print and field-test ChArUco plates + cylinder set
- [ ] FreeCAD template: grip_base_template.FCStd
- [ ] Blender script: voronoi_apply.py with zone masking
- [ ] Full Voronoi grip prototype on real equipment
- [ ] Field test: PBT vs PETG on wet hand + Voronoi surface
- [ ] Document results in /docs/field_tests/

---

## Development History

Concept developed through extended dialogue with Claude (Anthropic).
Key sessions covered: pipeline architecture, ChArUco calibration system,
modular grip mechanics, ISSF compliance, material physics,
perspiration biomechanics, patent landscape, product decomposition.

Continue from any TODO above — context is fully captured in this file and docs/.

---

*All dimensions in mm. FDM tolerances: verify fit with test piece before printing full assembly.*
