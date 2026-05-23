# Application Landscape — Biometric Hand Fitting Pipeline

---

## Framing

This toolkit is one specific implementation of a general principle:

```
Measure a human body segment
        ↓
Generate geometry from that measurement
        ↓
Produce a physical interface via additive manufacturing
```

Applied here to the hand and a grip interface. The same principle — with different measurement tools, different parametric models, different mounting geometry — applies across a wide range of domains.

This document is not a claim that this implementation is a reference standard. It is an argument that the underlying approach is sound, and that this project can serve as a useful reference point for similar implementations in other domains — sharing the methodology even when the code does not transfer directly.

---

### Why this window is open now

The technology stack required to execute this pipeline has crossed an accessibility threshold in roughly the last 3–5 years. The individual components existed before — the barrier was cost, integration complexity, and the required expertise to combine them.

**What changed:**

| Component | Before (~2020) | Now (~2025) |
|---|---|---|
| Hand measurement | 3D scanner, $5,000–50,000 | Phone camera + photogrammetry (free); or handheld scanner $1,000–2,000 — e.g. Shining3D Einstar 2 (~$1,400, 17-line laser + IR VCSEL, 0.05mm) or Einstar Rockit (~$1,850, 38-line laser + IR VCSEL, 90fps, wireless) |
| Landmark detection | Custom CV pipeline, research lab | MediaPipe, runs on CPU, free, 5 lines of code |
| Parametric CAD | CATIA, NX, seat licenses | FreeCAD, OpenSCAD — free and scriptable |
| Fabrication | Industrial SLS/MJF, service bureau | Desktop FDM $200–600, resin $300–800; local print services everywhere |
| Total barrier | Institutional (Hyundai-level resources) | Club, clinic, individual maker |

The Korean Olympic archery team's custom grips (Hyundai, since 2016) and the French shooting team's grips (Athletics 3D, professional 3D scanner + industrial printer) required institutional backing because the technology demanded it. The same outcome is now achievable at a fraction of the cost.

This is not incremental improvement — it is a category shift in who can execute this pipeline.

---

### What transfers across domains, what doesn't

**Transfers directly:**
- The measurement principle (calibration target + camera → metric space)
- The parametric design approach (biometric parameters → geometry, not manual CAD)
- The fitting protocol logic (objective markers, not subjective feel)
- The adjustment philosophy (modular, measurable, reproducible)

**Requires domain-specific work:**
- Mounting geometry (sport equipment → surgical handle → archery riser → different JSON)
- Regulatory path (sport equipment → medical device → entirely different process)
- Material constraints (PETG for grip → biocompatible PA12 for medical → same print, different validation)
- Measurement scope (hand surface → residual limb volume → different capture method needed)

The principle is portable. The implementation is not a template — it is a proof of concept for the approach.

---

Where the BiometriScan → ParamGrip → VoroShell pipeline (or subsets of it) applies.
Organized by domain. Concrete examples and precedents wherever found.

---

## Competitive Sports — Precision / Aiming

### Target Pistol Shooting (primary use case)
- **Direct precedent**: Athletics 3D (France) — custom 3D-printed grips for Olympic athletes using 3D scanning + Zortrax FDM. French silver medallist Céline Goberville used one at European Championships, scored 391 (tied Olympic record at the time).
- **Commercial equivalent**: MeshPro (Germany) — €260-350, 8-10 weeks, closed algorithm. SmartGrip, Rink (handcraft wood).
- **Pipeline fit**: 100% — this is what the toolkit was built for. Precision pistol/rifle platforms are the first implementation; different `mount_points.json` for each.
- **Other platforms**: Walther LP500, Feinwerkbau 900, Steyr LP50 — same grip geometry problem, different mounting geometry (`mount_points.json`).
- **Rifle shooting**: Air rifle and smallbore free rifle grips are anatomically fitted on the same principle — palm rest, thumb shelf, trigger reach all biometrically driven.
- **Biathlon**: Biathlon rifle grip is held differently (standing, kneeling, prone) — less anatomic customization, but trigger reach and palm shelf still matter.

### Olympic Recurve Archery
- **Direct precedent**: Hyundai has supplied custom 3D-printed recurve grips for the Korean national team since Rio 2016. Korean men's team used them at Tokyo and Paris. Korean team won gold.
- **Process**: Coach manually files down a stock grip until it fits → scan the result → print exact replica in different materials.
- **Europac3D case**: 3D-scanned a grip perfected by a British archer, reproduced it identically for spare bows and replacements.
- **Pipeline fit**: High — grip geometry directly from hand shape. No mounting complexity (grip attaches to riser via standard dovetail). Compound bow has different requirements (wrist sling, release aid), less relevant.

### Fencing
- **Direct precedent**: Leon Paul (UK) — Sub Zer0 pistol grip, 3D printed in titanium via laser powder bed fusion. Generative design, 1/3 weight of aluminium equivalent.
- **Market**: Épée and foil use pistol grips (right/left hand variants exist). Sabre uses French or pistol grip. Strong demand for left-hand variants (traditionally expensive, small production runs).
- **Pipeline fit**: High — épée pistol grip has identical anatomic logic to shooting pistol grip. HEMA swords are a niche extension.

### Paralympic Shooting
- Adaptive grip requirements are more extreme — limited finger mobility, prosthetic interface, one-handed shooting. Standard sizing fails completely.
- Currently: custom orthotic workshops, expensive, slow. Pipeline fits directly.

---

## Competitive Sports — Racket / Bat

### Tennis
- Grip circumference (4"–4¾") directly affects tennis elbow incidence. Too small = excessive muscle activation, too large = reduced wrist mobility.
- Current method: ruler measurement to palm crease, discrete sizes only.
- **Pipeline fit**: Medium — BiometriScan gives precise palm width and length; ParamGrip could generate a custom grip sleeve or replacement handle core. Existing racket frames are not replaced.

### Table Tennis
- Anatomic/flared/straight handle variants. Professional players sometimes sand and reshape handles by hand over years of play.
- Lighter bat = more relevant to micro-ergonomics than in tennis.
- **Pipeline fit**: Medium-high — handle is small and simple, ideal for parametric replacement.

### Squash / Badminton / Pickleball
- Same grip-size injury logic as tennis. Pickleball growing fast, demographic is older (more prone to grip injuries).
- **Pipeline fit**: Medium — same as tennis.

### Baseball / Softball Bat
- Handle diameter and knob shape affect comfort and injury (hamate bone fractures from knob impact).
- Some high-end bat makers offer custom knob geometry. Axe Bat (asymmetric handle) is a commercial example.
- **Pipeline fit**: Medium — handle geometry replaceable; bat barrel is not relevant.

### Cricket Bat
- Handle cross-section (oval, round) and thickness affect grip comfort. Bespoke handles exist but are craft-made.
- **Pipeline fit**: Low-medium — small market, handle is cane+rubber, not FDM-compatible directly.

---

## Competitive Sports — Grip-Critical Weapons / Implements

### Golf
- Club fitting is an established industry. Grip diameter is one of the six standard fitting parameters.
- Current: discrete grip sizes, cork/rubber wraps to adjust. No personalized geometry.
- **Pipeline fit**: Medium — grip core geometry replaceable. Large addressable market (70M+ golfers worldwide).

### Rowing / Ergometers
- Oar handle diameter and shape affect blister formation and power transfer. Concept2 sells one diameter.
- Ergometer (indoor) handles: fixed geometry, repetitive strain injuries common in high-volume training.
- **Pipeline fit**: Low-medium — hydrodynamic/aerodynamic constraints limit customization in on-water rowing. Indoor ergometer handles are an open field.

---

## Medical and Rehabilitation

### Prosthetic Limb Sockets (below-elbow)
- **Direct precedent**: Open Bionics (UK), Victoria Hand Project — 3D printed sockets from scan. V3D system (student project): €30 material cost vs €thousands traditional.
- AI + pressure mapping + 3D printing already combined in some research prototypes (2025-2026).
- **Pipeline fit**: Partial — socket fit is a 3D problem (residual limb volume), not just hand surface. BiometriScan's photogrammetry approach would need extension to the stump. The parametric + print pipeline is directly applicable.

### Surgical Instruments
- **Direct precedent (peer-reviewed)**: MDPI 2018 study — 135 surgeons measured, laparoscopic grasper handle scaled to XS/S/M/L using PLM (palm length) as the single biometric parameter. Each size 3D printed. Ergonomic improvement confirmed.
- Laparoscopic instrument handles: currently one size. Surgeons with smaller hands (disproportionately women, who are underrepresented in instrument ergonomics research) experience higher fatigue and injury rates.
- **Pipeline fit**: High — parametric scaling from a single palm measurement is exactly what ParamGrip does. Regulatory path (MDR/FDA) is the barrier, not the technology.

### Assistive Devices / OT
- Pen holders, cutlery adapters, toothbrush handles, door handle adapters for patients with reduced grip strength or mobility.
- Occupational therapists currently fabricate these by hand from thermoplastic sheets.
- **Pipeline fit**: High — simple geometry, single-person production, exactly the use case for desktop FDM + parametric design.

### Physiotherapy Equipment
- Hand exercise grips, resistance tools, rehabilitation splints with gripping surfaces.
- **Pipeline fit**: Medium — gripping surface geometry is relevant; structural/mechanical constraints need separate validation.

---

## Industrial and Professional Tools

### Power Tools
- Bosch, Makita, Hilti conduct large anthropometric studies for handle design. The result is still a population average, not individual fit.
- Workers using power tools 8h/day have high rates of vibration white finger, carpal tunnel, tennis elbow.
- **Pipeline fit**: Medium — individual consumer customization not viable at scale with current distribution. But for specialist tools (surgical drill, precision torque wrench) used by one person daily, it is viable.

### Precision Handtools (dentistry, watchmaking, jewellery)
- Dental handpieces: scaler, explorer, mirror handles are identical for everyone. Surgeons with small hands use the same instrument as large-handed colleagues.
- **Pipeline fit**: High for niche professional tools. Small object, high daily use, high injury sensitivity.

### Knives (professional kitchen, hunting, military)
- Custom knife handles exist as a craft market. CNC and FDM entry is low.
- Chef's knife: repetitive gripping 6+ hours/day. Handle fit directly affects wrist posture.
- **Pipeline fit**: High — simple geometry, wide material choice, no regulatory barrier.

### Military / Law Enforcement Firearms
- Pistol grip customization for service weapons (M17, Glock, etc.) is an established aftermarket.
- Custom grip panels: VZ Grips, Hogue, Talon — all passive textures, not anatomically fitted.
- **Pipeline fit**: High for agencies that issue personal sidearms. Individual fit → faster target acquisition, reduced grip fatigue in extended training.

---

## Music

### Bowed String Instruments (Violin, Cello, Double Bass)
- Bow grip: no physical interface, just contact. Not applicable.
- Instrument body contact: shoulder rest, chin rest are personally fitted. Different problem.

### Wind Instruments
- Trumpet/clarinet key positioning: players with small hands struggle with reach to certain keys. Some luthiers relocate keys for individual players. Not a grip problem.

### Drumsticks
- Grip diameter and taper affect stick control. ProMark, Vater offer many profiles. No individual biometric fitting exists.
- **Pipeline fit**: Low-medium — small object, high volume, player preference is tactile and hard to measure.

### Conducting Baton
- Professional conductors sometimes commission custom batons. Very small market.
- **Pipeline fit**: Low — market size.

---

## Gaming and Human-Computer Interaction

### Gaming Mice
- Logitech, Finalmouse, Lamzu market mice by hand size (S/M/L). No individual parametric fit.
- Some community projects: 3D-print your own mouse shell to your exact hand dimensions.
- **Pipeline fit**: High — BiometriScan already captures the relevant dimensions (palm length, width, arch height). Mouse shell is a direct parametric output candidate.

### VR / XR Controllers
- Controllers designed for median hand. Users with large or small hands lose precision.
- Growing relevance as VR enters professional simulation (surgical training, military).
- **Pipeline fit**: Medium — controller electronics constrain geometry. Grip overlay is the realistic application.

### Gamepad / Joystick
- Flight sim community: custom throttle and stick grips, HOTAS modifications. Existing community of makers already doing this without biometric tooling.
- **Pipeline fit**: Medium — grip inserts and overlays, not full device replacement.

---

## Summary Table

| Domain | Market Size | Pipeline Fit | Precedent | Main Barrier |
|---|---|---|---|---|
| Target pistol/rifle | Niche, high value | ★★★★★ | Yes (Athletics 3D, MeshPro) | None |
| Olympic archery | Niche, elite | ★★★★★ | Yes (Hyundai/Korea) | None |
| Fencing | Niche | ★★★★☆ | Yes (Leon Paul) | None |
| Laparoscopic surgery | Large, regulated | ★★★★☆ | Yes (MDPI 2018) | MDR/FDA |
| Assistive devices (OT) | Medium | ★★★★☆ | Partial | None |
| Prosthetics | Large, regulated | ★★★☆☆ | Yes (Open Bionics) | MDR/FDA, 3D problem |
| Professional knives | Medium | ★★★★☆ | Craft only | Distribution |
| Gaming mice | Large | ★★★★☆ | DIY community | None |
| Tennis / racket sports | Very large | ★★★☆☆ | None | Racket frame constraints |
| Firearms (LEO/mil) | Large, restricted | ★★★★☆ | Aftermarket only | Procurement |
| Power tools | Very large | ★★☆☆☆ | None | Scale/distribution |
| Golf | Very large | ★★★☆☆ | Fitting industry | Tradition |

---

## Observations

**The pattern that makes a domain high-fit:**
1. One person uses the same grip object daily (not shared equipment)
2. Precision or fatigue matters (sport, medical, professional)
3. The grip interface is separable from the functional core (trigger mechanism, surgical tip, racket strings stay unchanged — only the handle changes)
4. Small production runs are economically viable (no mass-market competitor pressure)

**The realistic entry sequence:**
1. Target shooting — toolkit already built, precedent proven, community exists
2. Olympic archery — same technology, different mount geometry, existing commercial validation
3. Fencing — same, existing commercial validation
4. Professional knives / dental instruments — no regulatory barrier, high daily use
5. Gaming mice — large market, enthusiast community already doing DIY

**The long game:**
Medical (surgical instruments, prosthetics) has the largest impact but requires regulatory navigation. The toolkit as built is the correct technical foundation — regulatory work is separate and domain-specific.
