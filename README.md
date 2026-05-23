# Biometric Grip Toolkit — BioGrip Protocol

Every action that depends on how a human hand holds something is constrained by the fit of that interface. A surgeon whose instrument handle doesn't match their hand fatigues faster and loses fine motor precision over a long procedure. An athlete whose equipment was shaped to population averages compensates unconsciously on every movement — not through conscious error, but through the quiet, constant work of muscles correcting for a geometry that was never theirs. A coach in a small club cannot replicate the fitting expertise of a national federation or a hospital ergonomics department.

The gap between a correctly fitted hand interface and an average one is not large in millimeters. It is measurable in performance, in fatigue, and over time, in injury.

Historically, closing that gap required a specialist, expensive equipment, weeks of lead time, and a budget available only to well-funded institutions. The Korean Olympic archery team has had custom 3D-printed grips since 2016 — made possible by Hyundai's industrial resources. A published study at a major research hospital measured 135 surgeons to produce four ergonomic size variants of a laparoscopic grasper handle — XS through L, each parametrically scaled from a single biometric input: palm length. These outcomes were correct. The barrier was access to the technology that could produce them.

That barrier is falling. The same measurement and fabrication pipeline that required institutional backing five years ago now runs on a laptop, a phone camera, a sub-$2,000 handheld scanner, and a desktop 3D printer available at any maker space or school. The expertise that was locked inside proprietary workflows is becoming reproducible.

**This toolkit is the first working definition of BioGrip** — an open methodology describing the action set for translating anatomical measurements into grip geometry. The tools are free and replaceable; the method is what persists. Built initially for precision sport equipment grips, designed to generalize. A coach with a printer, a clinic with a scanner, a maker with a camera: the same method, the same quality of outcome.

→ [Demo results — pipeline running on a real hand photo](demo/)

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

## The Broader Principle

This toolkit is a specific implementation of a general idea:

```
Measure a human body segment  →  Generate geometry from that measurement
                               →  Produce a personalized physical interface
```

Applied here to the hand and a sport equipment grip. The same pipeline — with different measurement targets, different parametric models, different mounting geometry — applies anywhere a hand interface matters: surgical instruments, archery grips, fencing handles, prosthetic interfaces, professional tool handles, gaming peripherals.

This is not a claim that this implementation is a reference standard. It is a working proof of concept for the approach — concrete enough to learn from, open enough to adapt.

**Why this became feasible now.** The components required for this pipeline existed before, but the barrier was cost and integration complexity. That barrier has dropped sharply in the last few years: hand measurement that required a $10,000–50,000 scanner now works from two phone photos, or from an affordable handheld laser scanner ($1,000–2,000). Computer vision that required a research lab (MediaPipe) is now free and runs on a laptop CPU. Parametric CAD (FreeCAD) and desktop FDM printers ($300–600) complete the stack. The Korean Olympic archery team's custom 3D-printed grips required Hyundai's backing in 2016 because the technology demanded it. The same outcome is now reachable by a club with a printer.

See [`docs/application_landscape.md`](docs/application_landscape.md) for a detailed breakdown of domains, precedents, and where the approach transfers directly versus where domain-specific work is needed.

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
Applies organic surface structure to any input mesh using Blender Geometry Nodes, preserving critical solid zones (mounting faces, fastener holes, structural regions) via JSON zone masking. Default output is Voronoi lattice; the same zone-masking approach applies to other generative surface types — Gyroid, honeycomb, biomimetic textures — depending on functional requirements.

**Why open lattice structure for hand interfaces:** not aesthetics. Uniform ventilation eliminates local temperature gradients, distributing perspiration evenly across the contact surface. Rib-only contact prevents sweat film formation that makes solid surfaces slippery when wet. Distributed pressure points improve circulation during prolonged grip. These properties are commercially validated at Olympic competition level.

Applicable to: any mesh where weight reduction, ventilation, or grip texture matters.

---

## Calibration Hardware

Two printable tools:

**ChArUco Calibration Plate** (`1_biometriscan/calibration/charuco_9x11_30mm.svg`)
- Size: 270×330mm (9×11 grid, 30mm squares), 49 ArUco markers — main field plate
- Material: PETG, two-color first-layer print — matte finish eliminates glare for reliable OpenCV detection
- Features: wrist baseline ridge at y=285mm, printed corner orientation labels (LT/RT/LB/RB), full ChArUco pattern
- Rigid construction eliminates paper distortion and wrinkle artifacts
- Legacy A4 (7×9) and 300×300 variants also in the calibration folder

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

The first complete implementation targets **Olympic sport equipment grips** — precision target shooting, archery, fencing — where the interface between hand and equipment directly determines outcome. Commercial options exist (MeshPro, Rink and others), but the model is fundamentally different: a product line with a defined range of variants, selected by approximate hand size. The geometry options are constrained by what makes sense to manufacture and sell at scale — not by what the human hand actually requires. Reviews of commercial grips consistently note that the fitting is superficial — the shell geometry does not change meaningfully between customers.

The goal here is not to replicate a commercial product at lower cost. It is to make the underlying method accessible: how to measure a hand, how to translate that measurement into geometry, how to produce and validate a result. A club, a coach, a clinician — anyone with a printer and this toolkit can build that capability themselves, adapt it to their context, and improve it. The fish is not the point. The fishing is.

---

## Stack — Fully Free

| Tool | Purpose | License |
|---|---|---|
| Docker | Reproducible runtime, zero local install | Apache 2.0 |
| Python 3.11 | Analysis scripts | MIT |
| OpenCV | ChArUco detection, homography | Apache 2.0 |
| MediaPipe | Hand landmarks (Tasks API) | Apache 2.0 |
| Open3D | Point cloud analysis | MIT |
| FreeCAD 0.21+ | Parametric modeling | LGPL |
| Blender 4.x | Lattice / Geometry Nodes | GPL |

No proprietary components in the required path. Fusion 360 is documented as an optional organic surface finishing step — replaceable with FreeCAD Surface workbench.

---

## Quick Start

Requires Docker.

```powershell
# Windows (PowerShell)
git clone <repo>
cd biometric-grip-toolkit

# First run — builds Docker image (~2 min, downloads dependencies + model)
.\scan.ps1 photos\top_view.jpg

# With explicit plate selection
.\scan.ps1 photos\top_view.jpg -Board 9x11_30mm

# Two-view scan (top + side with calibration cylinder)
.\scan.ps1 photos\top_view.jpg photos\side_view.jpg
```

Output: `<photo_stem>_params.json` with all grip measurements, `<photo_stem>_debug.jpg` for visual verification.

---

## Status

```
BiometriScan    ████████████  pipeline working end-to-end, field testing in progress
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

Products and services built using this protocol may identify themselves as **BioGrip-fitted**. Use of this designation implies compliance with the measurement and fitting protocol documented here.

---

## Contributing

Issues and PRs welcome. Particularly looking for:
- Field test reports (any platform, any hand size)
- `mount_points.json` for additional equipment
- Adaptations to non-sport applications
- Protocol translations

---

*All dimensions in mm unless otherwise stated.*
