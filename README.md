# PAL's Notes Logo Pipeline

Deterministic, geometry-driven pipeline for constructing and rendering the PAL's Notes "P" logo. Every visual element is derived from a single free parameter (`R_GREEN`) through a `sqrt(2)` chain — no hand-placed coordinates.

## Disclaimer

This work is subject to the methodological caveats and commitments described in [@DISCLAIMER.md](../DISCLAIMER.md).
> No statement or premise not backed by a real logical definition or verifiable reference should be taken for granted.

## Architecture

The pipeline is split into two layers:

### `p_logo` — Core Geometry Library

Frozen-dataclass schema (`PLogoSchema`) built from two free parameters (`center`, `R_GREEN`). All coordinates derive from a geometric composition via the sqrt(2) chain:

```
R_BLUE  = R_GREEN / sqrt(2)   (inner)
R_GREEN = free parameter       (middle)
R_GOLD  = R_GREEN * sqrt(2)   (outer)
```

The schema contains **25 nodes**, **44 typed edges** (contour, struct, mesh, nib), **3 semicircular arcs**, and pen **nib geometry**.

**Modules:**

| Module | Role |
|--------|------|
| `types.py` | Frozen dataclasses: `Node`, `Edge`, `Arc`, `NibGeometry`, `PLogoSchema` |
| `schema.py` | `build_schema()` — single entry point, derives all geometry |
| `composition.py` | Maps base geometric composition into P-logo coordinate space |
| `geometric_composition.py` | Low-level composition generator (circles, squares, intersections) |
| `overlay.py` | Renders composition shapes onto matplotlib axes |
| `renderers/` | `MatplotlibBWRenderer`, `CairoCraftedRenderer`, `V16TechnicalRenderer` |
| `exporters/` | JSON, SVG, GIF, HTML (Three.js animation) exporters |

### `p_logo_pipeline` — Build Pipeline

A 7-step pipeline that transforms the schema into a self-contained animated HTML logo:

| Step | Module | Input | Output |
|------|--------|-------|--------|
| 0 | `palette.py` | — | `build/palette.json` |
| — | `point_field.py` | — | `build/point_field.json` |
| — | `projection.py` | `point_field.json` | `build/projection.json` |
| 1 | `graph.py` | `palette.json`, `projection.json` | `build/graph.json` |
| 2 | `nib.py` | `palette.json` | `build/nib.json` |
| 3 | `arcs.py` | `palette.json`, `projection.json` | `build/arcs.json` |
| 4 | `layout.py` | `palette.json`, `graph.json`, `nib.json`, `arcs.json` | `build/layout.json` |
| 5 | `animations.py` | `palette.json`, `graph.json`, `arcs.json` | `build/animations.json` |
| 6 | `render.py` | `palette.json`, `layout.json`, `animations.json` | `build/logos/p_logo_pipeline.html` |
| 7 | `validate_step.py` | all `build/` artifacts | pass/fail report |

An additional `render_overlay.py` produces `build/logos/p_logo_pipeline_overlay.html` showing both construction planes (Plane A geometry fading into Plane B logo).

All generated logos are written to the unified `build/logos/` directory.

## All Scripts

### `scripts/` — CLI Wrappers

| Script | Purpose |
|--------|---------|
| `generate_all.py` | Regenerates all outputs (JSON schema, PNGs, SVG, HTML animation, GIF) from `p_logo.build_schema()` |
| `export.py` | Exports a 2000x2000 static PNG (Cairo) + animated GIF |
| `render_bw.py` | B&W matplotlib render (800x800) + composition overlay (2000x2000) + JSON schema |
| `render_cairo.py` | Cairo "crafted logic" render (normal, debug, transparent modes) |
| `render_v16.py` | V16 technical-drawing style (parchment, bronze rings, hatching, dimension arrows) |

### `src/p_logo_pipeline/` — Pipeline Steps (each is also a standalone CLI)

| Module | Step | Purpose |
|--------|------|---------|
| `palette.py` | 0 | 8 named colors, opacity defaults, sizing constants, nebula/star/particle specs |
| `point_field.py` | — | Plane A: all grid crossings (5 x-columns x 8 y-rows + IS vertices + nib points) |
| `projection.py` | — | Plane A to B: selects 25 of ~60+ field points as logo nodes, assigns typed edges |
| `graph.py` | 1 | Adjacency lists, degree stats, palette-derived node radii |
| `nib.py` | 2 | Fountain pen nib: fan lines, diamond outline, center line, accent nodes, junction ball |
| `arcs.py` | 3 | Samples 3 semicircular bowl arcs into 57-point polylines + runner paths |
| `layout.py` | 4 | Composes all geometry into single coordinate space with centering and z-ordering |
| `animations.py` | 5 | 6 animation system configs (wave, pulses, arc runners, breathing, energy rings, ink drops) |
| `render.py` | 6 | Produces self-contained HTML with Three.js r128 + Canvas (~310 renderable objects) |
| `validate_step.py` | 7 | Post-build verification: 15 checks against the design rationale |
| `render_overlay.py` | — | Produces overlay HTML showing Plane A construction fading into Plane B logo |

## How the Pipeline Works

### Layer 1: `p_logo` — Schema Generation

Everything starts from **two free parameters**: `center = (0.3504, 0.8694)` and `R_GREEN = 1.2303`.

#### Step 1: The sqrt(2) chain

Three concentric circles, each related by sqrt(2), emerge from inscribed/circumscribed nesting:

```
Circ.A  (R=200)                          --> Gold arc (outer)
  └─ Square.A inscribed at 45°
       └─ Circ.Bounds.A = inradius = 200/√2 = 141.42  --> Green arc (middle)
            └─ Square.D inscribed at 45°
                 └─ Circ.D = inradius = 141.42/√2 = 100  --> Blue arc (inner)
```

After scaling by `r_blue / 100`:

```
R_BLUE  = R_GREEN / sqrt(2) = 0.8700  (inner arc)
R_GREEN = 1.2303                       (middle arc)
R_GOLD  = R_GREEN * sqrt(2) = 1.7399  (outer arc)
```

#### Step 2: Base geometric composition

`build_schema()` calls `generate_p_composition()` which calls `generate_composition()` — a low-level generator that works on a 1200x1200 abstract canvas centered at (600, 800) with base radius `R_A = 200`. It builds:

| Shape | Construction | Role in P |
|-------|-------------|-----------|
| **Circ.A** | Circle at center, R=200 | Gold arc (outer) |
| **Square.B** | Circumscribes Circ.A, side=400 | Defines stem x-bounds and outer y-bounds |
| **Square.A** | Inscribed in Circ.A at 45° | Vertices on Gold circle; side-lengths give Green radius |
| **Circ.Bounds.A** | Inradius of Square.A = R_A/sqrt(2) | Green arc (middle) |
| **Square.D** | Inscribed in Circ.Bounds.A at 45° | Vertices at 45°/315° become bowl nodes |
| **Circ.D** | Inradius of Square.D = R_A/2 | Blue arc (inner) |
| **Circ.V1-V4** | Circles at Square.A vertices, R = min dist to Square.B | Define R_VERTEX = R_GOLD - R_GREEN |
| **Rect.1** | Width = 2 x R_VERTEX, height = 3 x R_A, at Square.B upper-left | The P's stem rectangle |
| **Circ.Rect.I** | Inscribed circle at Rect.1 bottom | Nib ball position |
| **Circ.Rect.V** | External vertex circle below Rect.1 | Nib tip position |

The composition is scaled into P-logo coordinates via `scale = r_blue / 100`.

#### Step 3: Extracting coordinates from the composition

`build_schema()` reads the scaled composition shapes to derive key coordinates:

- `r_blue`, `r_gold`, `r_vertex` — from circle radii
- `rect_r`, `rect_bot` — stem rectangle right edge and bottom
- `nib_cx`, `nib_circ_cy`, `nib_tip_y` — from Circ.Rect.I and Circ.Rect.V centers

#### Step 4: Building the 25 nodes

Each node is a formula of `cx`, `cy`, and the derived radii — no hand-placed values:

| Node | Coordinates | Source |
|------|------------|--------|
| 0 | `(cx - r_gold, cy + r_gold)` | Square.B upper-left |
| 2 | `(cx + g45, cy + g45)` | Square.D vertex at 45° |
| 5 | `(cx, cy + r_blue)` | Circ.D tangent top |
| 9 | `(cx - r_green, cy - r_green)` | Square.A V3 (junction vertex) |
| 14 | `(nib_cx, nib_tip_y)` | Circ.Rect.V center (nib tip) |

Where `g45 = r_green / sqrt(2)`.

#### Step 5: Edges, arcs, and nib

- **44 typed edges** — hardcoded adjacency with type classification: contour (6), struct (4), nib (14), mesh (20)
- **3 arcs** — all pi-radian semicircles (-90° to +90°) at radii r_green, r_blue, r_gold
- **Nib geometry** — 5-point outline polygon, slit line, and junction ball, derived from nib center and r_vertex

#### Step 6: Frozen output

Everything is assembled into a `PLogoSchema` frozen dataclass — immutable from this point forward. Renderers and the pipeline consume it read-only.

### Layer 2: `p_logo_pipeline` (Build Pipeline)

The pipeline transforms the schema into a self-contained animated HTML file through **two planes** and **7 numbered steps**:

**Plane A — Point Field** (the construction grid):
`point_field.py` generates **all possible** grid crossings: 5 x-columns x 8 y-rows + inscribed-square vertices + nib points + tangent points. This is the "construction paper" — far more points than the logo needs.

**Plane A to Plane B — Projection** (selection):
`projection.py` selects which 25 of the ~60+ field points become logo nodes. Non-nib nodes come from the `p_logo` canonical schema; nib nodes (12, 13, 14, 22, 23, 24) resolve from the point field's stem extension. Assigns colors, regions, typed edges, and arc definitions.

**Step 0 — Palette:**
8 named colors (warm-dominant + 1 cool accent), opacity defaults for 15 element classes, material templates, sizing constants, nebula/star/particle/shimmer specs. Self-validating (color hex, monotonic ring radii, warm/cool ratio).

**Step 1 — Graph:**
Adds adjacency lists, degree stats, palette-derived node radii (junction node 9 gets `0.14`, others `0.09`). Validates 25 nodes, 44 edges, connectivity, junction degree = 6.

**Step 2 — Nib:**
Fountain pen nib geometry: 6 fan lines (3 per side) radiating from the tip, 4 diamond outline segments, 1 blue-glow center line, 4 accent nodes, 1 warm-white junction ball, ink emission origin. All parametric from `tip_y`, `top_y`, `half_width`, `fan_count`.

**Step 3 — Arcs:**
Samples the 3 semicircular bowl arcs (Blue/Green/Gold) into 57-point polylines. Produces arc runner paths for animated particles.

**Step 4 — Layout:**
Composes all geometry into a single coordinate space. Applies vertical centering offset, assigns z-ordering (edges 0.20 to junction ball 0.60), computes bounding box, validates everything fits inside the ring, builds rose-gold ring bands. Produces a flat list of ~100 typed elements.

**Step 5 — Animations:**
Defines 6 animation systems as pure parameter configs (no rendering code):

1. **Wave** — BFS propagation from random node every ~4s
2. **Pulses** — 12 glowing particles traveling along edges
3. **Arc runners** — 6 comet-tailed particles on bowl arcs
4. **Breathing** — subtle +-0.8% sinusoidal scale oscillation
5. **Energy rings** — expanding rings from center, fading out
6. **Ink drops** — 25-pool particles with gravity/drag from nib tip

Plus supplementary: 70 ambient floating particles + 3 shimmer arcs on the ring.

**Step 6 — Render:**
The only step that knows about HTML/CSS/JS. Reads all upstream JSON and produces a self-contained HTML file with Three.js r128 + Canvas rendering. ~310 renderable objects total.

**Step 7 — Validate:**
Post-build verification: counts renderable objects per category, checks graph metrics (25 nodes, 44 edges, connected, max degree 6), verifies HTML structure (no NaN, Three.js present, all 8 palette colors used, brand text present). 15 checks total.

**Overlay:**
Produces an HTML showing both planes: Plane A construction fades in (0-4s) then Plane B highlights (4-8s) then Plane A fades out (8-12s) then normal logo animation runs.

### Data Flow

```
R_GREEN (free parameter)
    |
    +-- p_logo.build_schema() ---- canonical 25N/44E/3A schema
    |         |
    |    [scripts/ use this directly for PNG/SVG/GIF/HTML export]
    |
    +-- point_field.py ---- Plane A: all grid intersections
    |         |
    |    projection.py ---- Plane B: 25 selected nodes + typed edges
    |         |
    |    +----+----------------------------+
    |    |    |                            |
    |  graph.py    arcs.py            palette.py
    |    |    |         |                  |
    |    |    |    nib.py (reads palette)  |
    |    |    |         |                  |
    |    +----+----+----+                  |
    |              |                       |
    |         layout.py <------------------+
    |              |
    |       animations.py
    |              |
    |          render.py --> build/logos/p_logo_pipeline.html
    |              |
    |       validate_step.py --> pass/fail
    |
    +-- render_overlay.py --> build/logos/p_logo_pipeline_overlay.html
```

## Directory Structure

```
pals_logo_pipeline/
  build/
    logos/              # ← Unified output folder for all generated logos
  references/          # Legacy code and reference image
  scripts/             # CLI wrappers for rendering and export
    generate_all.py    #   Regenerate all outputs (JSON, PNG, SVG, HTML, GIF)
    export.py          #   Static PNG + animated GIF export
    render_bw.py       #   B&W matplotlib renderer
    render_cairo.py    #   Cairo crafted-logic renderer
    render_v16.py      #   V16 technical-drawing renderer
  src/
    p_logo/            # Core geometry library (frozen schema)
    p_logo_pipeline/   # Build pipeline (7 steps + overlay)
      build/           # Pipeline intermediate artifacts (JSON)
  tests/
    unit/              # Migration and export tests
```

### Output Naming Convention

All generated logos go to `build/logos/` with the pattern `p_logo_{renderer}_{variant}.{ext}`:

| File | Renderer | Description |
|------|----------|-------------|
| `p_logo_schema.json` | — | Canonical schema |
| `p_logo_bw_dark.png` | `bw` | White logo on black background |
| `p_logo_bw_light.png` | `bw` | Black logo on white background |
| `p_logo_bw_overlay_dark.png` | `bw` | Composition overlay (dark) |
| `p_logo_bw_overlay_light.png` | `bw` | Composition overlay (light) |
| `p_logo_cairo_{size}.png` | `cairo` | Cairo crafted-logic render |
| `p_logo_cairo_{size}_transparent.png` | `cairo` | Transparent background |
| `p_logo_cairo_debug_{size}.png` | `cairo` | Debug construction lines |
| `p_logo_v16_technical.png` | `v16` | Technical drawing style |
| `p_logo_vector.svg` | — | Vector SVG |
| `p_logo_threejs.html` | `threejs` | Three.js animation (exporter) |
| `p_logo_animated.gif` | — | Animated GIF |
| `p_logo_pipeline.html` | `pipeline` | Three.js animation (pipeline) |
| `p_logo_pipeline_overlay.html` | `pipeline` | Plane A→B construction overlay |

## Usage

Generate all outputs from the canonical schema:

```bash
python3 scripts/generate_all.py          # all outputs
python3 scripts/generate_all.py --quick  # skip slow renders
```

Export static PNG and animated GIF:

```bash
python3 scripts/export.py
python3 scripts/export.py --no-gif --static-size 2000
```

Individual renderers:

```bash
python3 scripts/render_bw.py             # B&W 800x800
python3 scripts/render_cairo.py          # Cairo crafted-logic 1200px
python3 scripts/render_v16.py            # V16 technical drawing
```

## Design Principles

- **Single source of truth**: All geometry derives from `build_schema(center, r_green)`.
- **Frozen data**: `PLogoSchema` and all component types are immutable dataclasses.
- **Separation of concerns**: Schema knows nothing about rendering; renderers know nothing about geometry derivation; the pipeline steps are pure data transformations producing JSON.
- **Deterministic**: Same parameters always produce identical output.
