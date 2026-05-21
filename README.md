# Biometric Grip Toolkit

**Under Development** | Open source tools for generating ergonomic hand interface geometry from biometric measurements.

From hand measurement to printable 3D geometry — for any object where fit to the human hand matters.

---

## What This Is

Three independent, reusable tools that together form a pipeline:

```
BiometriScan  →  ParamGrip  →  VoroShell
  (measure)      (model)       (structure)
```

Each tool solves one problem. Each works standalone. Together they automate what currently costs hundreds of euros and weeks of waiting.

---

## The Tools

### 1. BiometriScan
Extracts hand biometric parameters from 2D photos using a printed ChArUco calibration plate and calibrated cylinders. Corrects for perspective distortion, camera angle, and lens artifacts. Outputs a JSON file of measurements ready for parametric modeling.

**No 3D scanner required.** Two photos and a printed calibration plate are enough for first prototypes.

Applicable to: tool handles, bicycle grips, medical instruments, sports equipment, gaming peripherals, orthotic devices — any object that needs to fit a specific hand.

### 2. ParamGrip
Takes biometric JSON and generates a parametric 3D model using FreeCAD. Mounting interface geometry is fixed as constraints; ergonomic contact geometry is fully parameter-driven. Add a new `mount_points.json` for a different object — the biometric pipeline stays unchanged.

Applicable to: any hand-held object with defined mounting geometry.

### 3. VoroShell
Applies Voronoi / lattice structure to any input mesh using Blender Geometry Nodes, preserving critical solid zones (mounting faces, fastener holes, structural regions) via JSON zone masking.

**Why open lattice structure for hand interfaces:** not aesthetics. Uniform ventilation eliminates local temperature gradients, distributing perspiration evenly across the contact surface. Rib-only contact prevents sweat film formation that makes solid surfaces slippery when wet. Distributed pressure points improve circulation during prolonged grip. These properties are commercially validated at Olympic competition level.

Applicable to: any mesh where weight reduction, ventilation, or grip texture matters.

---

## Calibration Hardware

Two printable tools:

**ChArUco Calibration Plate** (`1_biometriscan/calibration/`)
- Sizes: A4 (210×285mm) or 300×300mm
- Material: PETG, two-color first-layer print — matte finish eliminates glare for reliable OpenCV detection
- Features: wrist baseline ridge, finger orientation reference axes, full ChArUco pattern
- Rigid construction eliminates paper distortion and wrinkle artifacts

**Reference Cylinder Set** (`1_biometriscan/calibration/`)
- Diameters: ∅28 / ∅32 / ∅36 / ∅40 / ∅44 / ∅48mm
- Physical selection method: hold each, choose most comfortable → that diameter is `grip_diameter`
- In side-view photo: detected automatically via cv2.HoughCircles for depth measurement

---

## Modular Adjustable Interface — Concept

A universal physical base with six continuously adjustable modules (screw-driven, not discrete steps):

```
M1 Palm shelf   — forward/back
M2 Thumb rest   — height + angle
M3 Backstrap    — depth
M4 Pinky shelf  — height
M5 Reach        — forward/back
M6 Palm swell   — depth (PA12/TPU 95A, elastic geometry)
```

Physical adjustment replaces biometric modeling for initial fitting. Final module positions are measurable with calipers and exportable as JSON — becoming the biometric profile for the next iteration.

Includes an objective coach fitting protocol: observable anatomical markers only, no subjective "feels comfortable." See `docs/modular_grip_concept.md`.

---

## Demonstrated Application

The first complete implementation targets **Olympic sport equipment grips** — specifically the FWB 800X platform. This is a licensed sport accessory, commercially available from manufacturers including MeshPro (Germany) and Rink. The toolkit automates and open-sources what these services provide at €260-350 with 8-10 week lead times using closed algorithms.

Sport equipment grips are non-functional accessories. They attach to, but do not constitute, any regulated component of the equipment.

---

## Philosophy

Wherever precision fit to a human hand matters, access should not depend on budget. The same fitting quality available to national federations should be available to any club, anywhere.

This toolkit is:
- **Printable** on any FDM printer (PETG or PBT recommended)
- **Reproducible** — open algorithm, documented method, no black box
- **Extensible** — new object type = new `mount_points.json`
- **Teachable** — protocol designed for coaches without software background

---

## Who This Is For

- Sports clubs fitting equipment for athletes of any level
- Coaches needing objective, measurable fitting criteria
- Makers adapting the tools to other ergonomic applications
- Researchers in ergonomics, human factors, or prosthetics
- Anyone building a hand-interface product who wants open biometric tooling

---

## Stack — Fully Free

| Tool | Purpose | License |
|---|---|---|
| Python 3.10+ | Analysis scripts | MIT |
| OpenCV | ChArUco detection, homography | Apache 2.0 |
| MediaPipe | Hand landmarks | Apache 2.0 |
| Open3D | Point cloud analysis | MIT |
| FreeCAD 0.21+ | Parametric modeling | LGPL |
| Blender 4.x | Lattice / Geometry Nodes | GPL |

No proprietary components in the required path. Fusion 360 is documented as an optional organic surface finishing step — replaceable with FreeCAD Surface workbench.

---

## Status

```
BiometriScan    ██████████░░  concept complete, field testing pending
ParamGrip       ████░░░░░░░░  FreeCAD template in progress
VoroShell       ███░░░░░░░░░  Blender script in progress
Modular Grip    ██████░░░░░░  concept + protocol documented, prototyping next
```

---

## Development Process

This project was developed through an extended dialogue with **Claude** (Anthropic) as a thinking partner and technical consultant — covering tool architecture, calibration methodology, biomechanics of perspiration and grip, material selection, patent landscape, fitting protocol design, and product decomposition.

The ideas, decisions, and direction are human. Claude contributed structured thinking, challenged assumptions, and helped translate concepts into implementable form. The result is a collaboration, not a generation.

This is noted not as a disclaimer but as an honest account of how the project came to be — because human-AI collaboration in open source deserves to be visible.

---

## License

**CC BY-SA 4.0** — Use freely, modify freely, distribute freely.  
Modifications must be shared under the same license.  
Commercial use requires attribution and open sourcing of derivatives.

---

## Contributing

Issues and PRs welcome. Particularly looking for:
- Field test reports (any platform, any hand size)
- `mount_points.json` for additional equipment
- Adaptations to non-sport applications
- Protocol translations

---

*All dimensions in mm unless otherwise stated.*
