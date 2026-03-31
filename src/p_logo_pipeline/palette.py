"""
PAL's Notes Logo Pipeline — Step 0: Palette

Single source of truth for the color system.

Defines:
  - Named colors with hex, RGB, and integer representations
  - Opacity defaults per element class (nodes, edges, glows, arcs, etc.)
  - Material property templates
  - Color role assignments (which color is used where)

Output: build/palette.json

Note from the design rationale:
  "Copper" is labeled patCopper in the code — it is actually a teal-green
  (#6EC4A8), not a copper tone. The naming is a carryover from an earlier
  palette revision. The name is preserved for continuity.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Color definition
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class Color:
    """A named color with hex, role description, and computed derived values."""
    name: str
    hex: str
    role: str

    def __post_init__(self) -> None:
        # Validate hex format
        h = self.hex.lstrip("#")
        if len(h) != 6:
            raise ValueError(f"Color '{self.name}': hex must be 6 chars, got '{self.hex}'")
        try:
            int(h, 16)
        except ValueError:
            raise ValueError(f"Color '{self.name}': invalid hex '{self.hex}'")

    @property
    def rgb(self) -> tuple[int, int, int]:
        h = self.hex.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    @property
    def rgb_float(self) -> tuple[float, float, float]:
        r, g, b = self.rgb
        return (r / 255.0, g / 255.0, b / 255.0)

    @property
    def hex_int(self) -> int:
        """Integer form for Three.js (e.g. 0x6EC4A8)."""
        return int(self.hex.lstrip("#"), 16)

    def to_dict(self) -> dict[str, Any]:
        r, g, b = self.rgb
        rf, gf, bf = self.rgb_float
        return {
            "name": self.name,
            "hex": self.hex,
            "hex_int": self.hex_int,
            "rgb": [r, g, b],
            "rgb_float": [round(rf, 4), round(gf, 4), round(bf, 4)],
            "role": self.role,
        }


# ──────────────────────────────────────────────
# Palette definition (from design rationale)
# ──────────────────────────────────────────────

COLORS: dict[str, Color] = {
    "copper": Color(
        name="copper",
        hex="#6EC4A8",
        role="Dominant structural color. Nodes and edges. "
             "Actually teal-green; name is a carryover from earlier palette revision.",
    ),
    "amber": Color(
        name="amber",
        hex="#F0B85C",
        role="Accent. High-connectivity nodes, bowl arcs.",
    ),
    "bronze": Color(
        name="bronze",
        hex="#D09058",
        role="Secondary warm. Outer bowl arc, nib outline, some nodes.",
    ),
    "rose_gold": Color(
        name="rose_gold",
        hex="#D4976E",
        role="Ring and brand text. The containing boundary element.",
    ),
    "blue_glow": Color(
        name="blue_glow",
        hex="#7BA8E8",
        role="Rare accent. One node (node 0/18), nib center line. "
             "Cool counterpoint to the warm-dominant palette.",
    ),
    "warm_white": Color(
        name="warm_white",
        hex="#FFF0D8",
        role="Nib tip, highlight pulses. The hottest point in the composition.",
    ),
    "deep": Color(
        name="deep",
        hex="#110A20",
        role="Background circle fill. Interior dark field.",
    ),
    "background": Color(
        name="background",
        hex="#07050f",
        role="Page/canvas background. Darkest value in the system.",
    ),
}


# ──────────────────────────────────────────────
# Opacity defaults per element class
# ──────────────────────────────────────────────

OPACITY_DEFAULTS: dict[str, dict[str, float]] = {
    "node_core": {
        "base": 0.9,
        "wave_boost": 0.1,
        "description": "Solid node circle. High base, small wave boost.",
    },
    "node_glow": {
        "base": 0.30,
        "wave_boost": 0.35,
        "description": "Inner glow sprite around nodes. Moderate base, strong wave response.",
    },
    "node_bloom": {
        "base": 0.10,
        "description": "Outer bloom halo. Subtle ambient presence.",
    },
    "edge": {
        "base": 0.40,
        "description": "Graph edges. Subdued so nodes dominate.",
    },
    "arc_main": {
        "base": 0.65,
        "description": "Bowl arc primary stroke.",
    },
    "arc_bloom": {
        "base": 0.12,
        "description": "Bowl arc bloom/glow layer.",
    },
    "ring": {
        "inner": 0.25,
        "mid_inner": 0.65,
        "mid_outer": 0.50,
        "outer": 0.25,
        "description": "Rose-gold ring. 4 concentric bands, brightest at mid layers.",
    },
    "shimmer": {
        "base": 0.035,
        "amplitude": 0.020,
        "description": "Shimmer arcs rotating over the ring. Very subtle.",
    },
    "pulse": {
        "core_peak": 0.65,
        "glow_peak": 0.20,
        "description": "Traveling pulse particles on edges.",
    },
    "arc_runner": {
        "core_peak": 0.75,
        "trail_peak": 0.25,
        "description": "Particles traveling along bowl arcs with comet tails.",
    },
    "ink_drop": {
        "peak": 0.60,
        "description": "Ink drops falling from nib tip.",
    },
    "particle": {
        "min": 0.15,
        "max": 0.40,
        "description": "Ambient floating particles throughout the composition.",
    },
    "energy_ring": {
        "initial": 0.25,
        "description": "Expanding rings from center. Fade to zero.",
    },
    "nib_line": {
        "fan": 0.45,
        "outline": 0.60,
        "center": 0.55,
        "description": "Pen nib line opacities by type.",
    },
    "nib_ball": {
        "core": 0.95,
        "glow": 0.45,
        "bloom": 0.15,
        "description": "Warm-white glowing ball at nib junction.",
    },
    "brand_text": {
        "target": 0.90,
        "description": "PAL's Notes text below the circle.",
    },
}


# ──────────────────────────────────────────────
# Material templates
# ──────────────────────────────────────────────

MATERIAL_TEMPLATES: dict[str, dict[str, Any]] = {
    "solid": {
        "type": "MeshBasicMaterial",
        "transparent": True,
        "side": "DoubleSide",
        "description": "Flat colored mesh. Used for nodes, edges, arcs, ring, nib.",
    },
    "sprite_glow": {
        "type": "SpriteMaterial",
        "transparent": True,
        "depth_write": False,
        "texture": "radial_gradient_64",
        "gradient_stops": [
            {"offset": 0.0, "opacity_factor": 1.0},
            {"offset": 0.4, "opacity_factor": 0.35},
            {"offset": 1.0, "opacity_factor": 0.0},
        ],
        "description": "Glow sprite with radial gradient texture. "
                       "Used for node glows, bloom halos, arc runner trails.",
    },
}


# ──────────────────────────────────────────────
# Geometry sizing constants (color-adjacent)
# ──────────────────────────────────────────────

SIZING: dict[str, Any] = {
    "node_radius": {
        "default": 0.09,
        "junction": 0.14,
        "description": "Core node circle radii. Junction node is larger.",
    },
    "node_glow_scale": 7.0,
    "node_bloom_scale": 12.0,
    "edge_thickness": 0.04,
    "arc_main_thickness": 0.055,
    "arc_bloom_thickness": 0.18,
    "ring_radii": {
        "inner_inner": 4.44,
        "inner_outer": 4.50,
        "mid_inner": 4.50,
        "mid_outer": 4.60,
        "mid2_inner": 4.60,
        "mid2_outer": 4.72,
        "outer_inner": 4.72,
        "outer_outer": 4.78,
        "description": "Four concentric ring bands.",
    },
    "circle_fill_radius": 4.52,
    "nib_line_thickness": {
        "fan": 0.030,
        "outline": 0.030,
        "center": 0.025,
    },
    "pulse_radius": 0.045,
    "pulse_glow_size": 0.35,
    "arc_runner_radius": 0.04,
    "ink_drop_radius": 0.035,
    "particle_radius": {"min": 0.012, "max": 0.037},
    "energy_ring_inner": 0.30,
    "energy_ring_outer": 0.36,
}


# ──────────────────────────────────────────────
# Nebula cloud specifications (background)
# ──────────────────────────────────────────────

NEBULA_SPECS: dict[str, Any] = {
    "count": 7,
    "colors": [
        {"color": "copper",    "alpha": 0.035},
        {"color": "amber",     "alpha": 0.025},
        {"color": "bronze",    "alpha": 0.030},
        {"color": "blue_glow", "alpha": 0.020},
        {"color": "rose_gold", "alpha": 0.025},
        {"color": "copper",    "alpha": 0.025},
        {"color": "amber",     "alpha": 0.020},
    ],
    "position_range": {"min": 0.3, "max": 0.7},
    "radius_range": {"min": 0.20, "max": 0.45},
    "drift_amplitude_range": {"min": 0.03, "max": 0.07},
    "description": "7 radial gradient clouds with sinusoidal drift. "
                   "Colors reference palette entries. Alpha is per-cloud peak.",
}

STAR_SPECS: dict[str, Any] = {
    "count": 180,
    "size_range": {"min": 0.3, "max": 1.5},
    "brightness_range": {"min": 0.2, "max": 0.8},
    "twinkle_speed_range": {"min": 0.5, "max": 2.0},
    "color": "warm_white",
    "description": "Star field layer. 180 twinkling circles.",
}

PARTICLE_SPECS: dict[str, Any] = {
    "count": 70,
    "size_range": {"min": 0.012, "max": 0.037},
    "opacity_range": {"min": 0.15, "max": 0.40},
    "drift_amplitude": {"min": 0.04, "max": 0.16},
    "drift_speed": {"min": 0.25, "max": 0.90},
    "min_distance": 0.8,
    "max_distance": 4.4,
    "color": "copper",
    "description": "Ambient floating particles throughout the composition. "
                   "70 circles with sinusoidal drift. Provide depth "
                   "without competing with foreground elements.",
}

SHIMMER_SPECS: dict[str, Any] = {
    "count": 3,
    "color": "warm_white",
    "base_opacity": 0.035,
    "opacity_amplitude": 0.020,
    "rotation_speed": 0.0015,
    "arc_sweep": 0.3,
    "description": "3 rotating arc segments overlaid on the ring. "
                   "Subtle luminosity variation that prevents the ring "
                   "from reading as static.",
}


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate() -> list[str]:
    """Run all palette validations. Returns list of errors (empty = pass)."""
    errors: list[str] = []

    # 1. All colors parse correctly (already validated in __post_init__)
    for name, color in COLORS.items():
        if name != color.name:
            errors.append(f"Key '{name}' does not match Color.name '{color.name}'")

    # 2. Nebula colors reference valid palette entries
    for i, nc in enumerate(NEBULA_SPECS["colors"]):
        if nc["color"] not in COLORS:
            errors.append(f"Nebula cloud {i}: references unknown color '{nc['color']}'")
        if not (0.0 < nc["alpha"] <= 1.0):
            errors.append(f"Nebula cloud {i}: alpha {nc['alpha']} out of range (0, 1]")

    # 3. Star color references valid palette entry
    if STAR_SPECS["color"] not in COLORS:
        errors.append(f"Star specs: references unknown color '{STAR_SPECS['color']}'")

    # 3b. Particle color references valid palette entry
    if PARTICLE_SPECS["color"] not in COLORS:
        errors.append(f"Particle specs: references unknown color '{PARTICLE_SPECS['color']}'")

    # 3c. Shimmer color references valid palette entry
    if SHIMMER_SPECS["color"] not in COLORS:
        errors.append(f"Shimmer specs: references unknown color '{SHIMMER_SPECS['color']}'")

    # 4. Opacity values are in [0, 1]
    def check_opacities(d: dict, path: str) -> None:
        for k, v in d.items():
            if k == "description":
                continue
            if isinstance(v, (int, float)):
                if not (0.0 <= v <= 1.0):
                    errors.append(f"Opacity {path}.{k} = {v} outside [0, 1]")
            elif isinstance(v, dict):
                check_opacities(v, f"{path}.{k}")

    for class_name, opacities in OPACITY_DEFAULTS.items():
        check_opacities(opacities, f"opacity.{class_name}")

    # 5. Ring radii are monotonically increasing
    rr = SIZING["ring_radii"]
    ring_values = [
        rr["inner_inner"], rr["inner_outer"],
        rr["mid_inner"], rr["mid_outer"],
        rr["mid2_inner"], rr["mid2_outer"],
        rr["outer_inner"], rr["outer_outer"],
    ]
    for i in range(1, len(ring_values)):
        if ring_values[i] < ring_values[i - 1]:
            errors.append(
                f"Ring radii not monotonic at index {i}: "
                f"{ring_values[i]} < {ring_values[i-1]}"
            )

    # 6. Circle fill radius falls within ring bands
    cfr = SIZING["circle_fill_radius"]
    if cfr > rr["outer_outer"]:
        errors.append(f"Circle fill radius {cfr} exceeds outer ring {rr['outer_outer']}")

    # 7. Palette has exactly 8 colors (per design rationale: 7 named + background)
    expected_count = 8
    if len(COLORS) != expected_count:
        errors.append(f"Expected {expected_count} colors, found {len(COLORS)}")

    # 8. Warm-dominant check: at least 3 warm colors, exactly 1 cool accent
    # (Design rationale: "warm-dominant with a single cool accent")
    cool_colors = {"blue_glow"}
    warm_colors = {"copper", "amber", "bronze", "rose_gold", "warm_white"}
    found_cool = [c for c in COLORS if c in cool_colors]
    found_warm = [c for c in COLORS if c in warm_colors]
    if len(found_cool) != 1:
        errors.append(f"Expected exactly 1 cool accent, found {len(found_cool)}: {found_cool}")
    if len(found_warm) < 3:
        errors.append(f"Expected at least 3 warm colors, found {len(found_warm)}: {found_warm}")

    return errors


# ──────────────────────────────────────────────
# Build output
# ──────────────────────────────────────────────

def build_palette() -> dict[str, Any]:
    """Assemble the complete palette JSON structure."""
    return {
        "_meta": {
            "step": 0,
            "name": "palette",
            "description": "PAL's Notes logo color system. Single source of truth.",
            "version": "1.1",
        },
        "colors": {name: color.to_dict() for name, color in COLORS.items()},
        "opacity_defaults": OPACITY_DEFAULTS,
        "material_templates": MATERIAL_TEMPLATES,
        "sizing": SIZING,
        "nebula": NEBULA_SPECS,
        "stars": STAR_SPECS,
        "particles": PARTICLE_SPECS,
        "shimmer": SHIMMER_SPECS,
    }


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def main() -> int:
    errors = validate()

    if errors:
        print("PALETTE VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    palette = build_palette()

    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "palette.json"

    with open(out_path, "w") as f:
        json.dump(palette, f, indent=2)

    # Summary
    print(f"palette.json written to {out_path}")
    print(f"  Colors:    {len(COLORS)}")
    print(f"  Opacities: {len(OPACITY_DEFAULTS)} element classes")
    print(f"  Materials: {len(MATERIAL_TEMPLATES)} templates")
    print(f"  Sizing:    {len(SIZING)} entries")
    print(f"  Nebula:    {NEBULA_SPECS['count']} clouds")
    print(f"  Stars:     {STAR_SPECS['count']}")
    print(f"  Particles: {PARTICLE_SPECS['count']}")
    print(f"  Shimmer:   {SHIMMER_SPECS['count']} arcs")
    print("  Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
