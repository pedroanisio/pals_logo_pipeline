# CLAUDE.md — Project Guidelines

## Disclaimer Reference (Required in all READMEs)

Every README file in this repository **must** reference `@DISCLAIMER.md` at the root of the project.

When creating or editing any `README.md`, include:

```markdown
## Disclaimer

This work is subject to the methodological caveats and commitments described in [@DISCLAIMER.md](../DISCLAIMER.md).
> No statement or premise not backed by a real logical definition or verifiable reference should be taken for granted.
```

Adjust the relative path to match depth: root → `./DISCLAIMER.md`, one level → `../DISCLAIMER.md`, two levels → `../../DISCLAIMER.md`. Place after the title, before the first content section. Never omit it.

---

## Project Overview

**PAL's Notes Logo Pipeline** — a deterministic, geometry-driven pipeline for constructing and rendering the PAL's Notes "P" logo. Every visual element derives from a single free parameter (`R_GREEN`) through a `sqrt(2)` chain — no hand-placed coordinates.

```
.
├── CLAUDE.md                # This file — project guidelines for AI agents
├── AGENTS.md                # Agent-specific guidance
├── DISCLAIMER.md            # Methodological caveats (all READMEs must reference)
├── README.md                # Project overview and usage
├── references/              # Legacy code and reference image
│   ├── logo_legacy.py       #   Original logo implementation
│   └── generated_logo.jpeg  #   Reference render
├── scripts/                 # CLI wrappers for rendering and export
│   ├── generate_all.py      #   Regenerate all outputs (JSON, PNG, SVG, HTML, GIF)
│   ├── export.py            #   Static PNG + animated GIF export
│   ├── render_bw.py         #   B&W matplotlib renderer
│   ├── render_cairo.py      #   Cairo crafted-logic renderer
│   └── render_v16.py        #   V16 technical-drawing renderer
├── src/
│   ├── p_logo/              # Core geometry library (frozen schema)
│   │   ├── types.py         #   Frozen dataclasses: Node, Edge, Arc, NibGeometry, PLogoSchema
│   │   ├── schema.py        #   build_schema() — single entry point, derives all geometry
│   │   ├── composition.py   #   Maps base composition into P-logo coordinate space
│   │   ├── geometric_composition.py  # Low-level composition generator
│   │   ├── overlay.py       #   Renders composition shapes onto matplotlib axes
│   │   ├── renderers/       #   MatplotlibBW, CairoCrafted, V16Technical renderers
│   │   │   └── base.py      #   Abstract base class for all renderers
│   │   └── exporters/       #   JSON, SVG, GIF, HTML (Three.js animation) exporters
│   │       └── node_colors.py #  Canonical color resolution + degree-based sizing
│   └── p_logo_pipeline/     # Build pipeline (7 steps + overlay)
│       ├── palette.py       #   Step 0: colors, opacity defaults, sizing constants
│       ├── point_field.py   #   Plane A: all grid crossings
│       ├── projection.py    #   Plane A→B: selects 25 nodes from ~60+ field points
│       ├── graph.py         #   Step 1: adjacency lists, degree stats, node radii
│       ├── nib.py           #   Step 2: fountain pen nib geometry
│       ├── arcs.py          #   Step 3: semicircular bowl arcs → polylines
│       ├── layout.py        #   Step 4: compose all geometry, z-ordering, centering
│       ├── animations.py    #   Step 5: 6 animation system configs
│       ├── render.py        #   Step 6: self-contained HTML with Three.js
│       ├── validate_step.py #   Step 7: post-build verification (15 checks)
│       ├── render_overlay.py#   Overlay: Plane A construction → Plane B logo
│       ├── test_*.py        #   Per-step unit tests
│       └── build/           #   Generated artifacts (JSON, HTML)
└── tests/
    └── unit/                # Migration, export, and geometry tests
```

---

## User Preferences (ranked by priority)

1. **Unbiased over flattering.**
2. **Formalization means research** — concrete and correct math, full data provenance, and references. Never hallucination.
3. **English over Portuguese.**
4. **Markdown over DOCX; TypeScript over JavaScript.**
5. All Markdown documents must include a disclaimer stating that no information should be taken for granted and that any statement not backed by a real logical definition or verifiable reference may be invalid or a hallucination.
6. **Feedback is not a source of truth.** If sound, accept it and improve. If not, refute it and clarify objections.

---

## Core Principles

These principles have zero exceptions:

1. **Fix root causes, never symptoms.** Investigate with 5-Whys before patching. If a test fails, understand why — don't just make it pass.
2. **Test-Driven Development.** Red → Green → Refactor → Cleanup. Write the failing test first. No code ships without tests.
3. **Production-ready code only.** No placeholders, no `TODO: implement later`, no incomplete stubs. Every commit must be deployable.

---

## Development Standards

### Testing
- 80% coverage for libraries, 60% for CLIs
- Unit, integration, and E2E tests
- Tests must be deterministic, isolated, and realistic
- Run tests after every change — don't batch validation to the end

### Code Quality
- Typed errors in libraries, graceful handling in applications
- Automated formatting and linting
- No unnecessary dependencies

### Version Control
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- Semantic versioning for schemas (`major.minor.patch`)
- AI-generated artifacts must be labeled with their source model/tool

### Architecture Decisions
- Document significant decisions with rationale
- When multiple approaches exist, state the trade-offs and ask before proceeding
- When scope is ambiguous ("finish everything", "complete this"), stop and clarify before starting

---

## AI Agent Guidance

### Context Management
- Priority reading order: `CLAUDE.md` → `AGENTS.md` → Tests → Code
- Read existing code before suggesting modifications
- The schema is the single source of truth — all geometry derives from `build_schema(center, r_green)`

### Confidence & Decision Making
- **Proceed** when requirements are clear and approach is obvious
- **State assumptions** when proceeding with medium confidence
- **Ask** when multiple valid approaches exist or scope is ambiguous
- **Never provide time estimates** (hours/days/weeks) — use complexity: XS/S/M/L/XL

### Delivery
- Deliver complete, atomic work — no batching across responses
- Break large work into complete subtasks, each independently useful
- For M/L/XL tasks: plan first, then execute

---

## General Conventions

- All schema files use semantic versioning (`major.minor.patch`)
- Bilingual content (PT-BR + EN-US) is standard for project-level documentation
- AI-generated artifacts must be labeled with their source model/tool in metadata or frontmatter
- Every README linking to sub-directories should also link back up to root `README.md`
- Frozen dataclasses (`PLogoSchema` and all component types) are immutable — never mutate them
- Pipeline steps are pure data transformations producing JSON — keep them side-effect free

---

## Document Relationships

| Document | Audience | Defines |
|----------|----------|---------|
| `DISCLAIMER.md` | Everyone | Epistemic integrity commitments |
| `CLAUDE.md` | AI agents + devs | HOW to build (process, standards, enforcement) |
| `AGENTS.md` | AI agents | Agent-specific operational guidance |
| `README.md` | Humans | WHAT the project does (usage, overview) |
