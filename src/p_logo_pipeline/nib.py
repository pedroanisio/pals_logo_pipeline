"""
PAL's Notes Logo Pipeline — Step 2: Nib

Generates the pen nib aesthetic geometry: fan lines, outline, center line
(blue glow), accent nodes, a warm-white junction ball, and an ink emission
origin.

Key structural coordinates (center_x, tip, waist/shoulders, ball position,
slit geometry) are derived from the canonical PLogoSchema.nib — the single
source of truth for nib shape. Aesthetic parameters (fan count, colors,
opacities, thicknesses) come from the palette.

Input:  build/palette.json, PLogoSchema (imported)
Output: build/nib.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

from p_logo import build_schema
from p_logo.types import PLogoSchema


# ──────────────────────────────────────────────
# Schema-derived structural defaults
# ──────────────────────────────────────────────

_SCHEMA = build_schema()

# Structural anchor points — all derived from PLogoSchema.nib
DEFAULT_CENTER_X: float = _SCHEMA.nib.outline[0][0]
DEFAULT_TIP_Y: float = _SCHEMA.nib.outline[0][1]
DEFAULT_TOP_Y: float = _SCHEMA.nib.outline[1][1]
DEFAULT_HALF_WIDTH: float = _SCHEMA.nib.outline[1][0] - _SCHEMA.nib.outline[0][0]

# Aesthetic free parameter (schema has no opinion on fan count)
DEFAULT_FAN_COUNT: int = 3


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate(
    palette: dict,
    fan_count: int = DEFAULT_FAN_COUNT,
) -> list[str]:
    """Validate nib parameters. Returns list of errors (empty = pass)."""
    errors: list[str] = []

    if fan_count < 1:
        errors.append(f"fan_count ({fan_count}) must be >= 1")

    # Check palette has required color keys
    required_colors = {"copper", "amber", "bronze", "blue_glow", "warm_white"}
    if "colors" in palette:
        available = set(palette["colors"].keys())
        missing = required_colors - available
        if missing:
            errors.append(f"Palette missing required colors: {missing}")

    # Check palette has required opacity/sizing keys
    if "opacity_defaults" in palette:
        if "nib_line" not in palette["opacity_defaults"]:
            errors.append("Palette missing opacity_defaults.nib_line")
        if "nib_ball" not in palette["opacity_defaults"]:
            errors.append("Palette missing opacity_defaults.nib_ball")

    if "sizing" in palette:
        if "nib_line_thickness" not in palette["sizing"]:
            errors.append("Palette missing sizing.nib_line_thickness")

    return errors


# ──────────────────────────────────────────────
# Geometry builders
# ──────────────────────────────────────────────

def _build_fan_lines(
    schema_nib,
    fan_count: int,
    palette: dict,
) -> list[dict[str, Any]]:
    """Build symmetric fan lines radiating from tip to upper spread points.

    Tip and shoulder coordinates are derived from schema.nib.outline.
    fan_count lines per side, evenly distributed from the innermost
    fraction of half_width to the full half_width.
    """
    thickness = palette["sizing"]["nib_line_thickness"]["fan"]
    opacity = palette["opacity_defaults"]["nib_line"]["fan"]

    tip = schema_nib.outline[0]
    center_x = tip[0]
    tip_y = tip[1]
    shoulder_y = schema_nib.outline[1][1]
    half_width = schema_nib.outline[1][0] - center_x

    lines: list[dict[str, Any]] = []

    for i in range(fan_count):
        frac = (i + 1) / fan_count

        dx = half_width * frac
        # Outermost lines end slightly beyond the shoulder
        dy_offset = frac * 0.15
        end_y = shoulder_y + dy_offset

        # Right side
        lines.append({
            "x1": center_x,
            "y1": tip_y,
            "x2": center_x + dx,
            "y2": end_y,
            "color": "copper",
            "thickness": thickness,
            "opacity": opacity,
        })

        # Left side (mirror)
        lines.append({
            "x1": center_x,
            "y1": tip_y,
            "x2": center_x - dx,
            "y2": end_y,
            "color": "copper",
            "thickness": thickness,
            "opacity": opacity,
        })

    return lines


def _build_outline(
    schema_nib,
    palette: dict,
) -> list[dict[str, Any]]:
    """Build outline from schema nib vertices.

    The schema outline is a 5-point closed polygon (4 unique vertices):
      tip → right_shoulder → waist_middle → left_shoulder → tip

    This produces 4 line segments matching the schema's kite shape.
    """
    thickness = palette["sizing"]["nib_line_thickness"]["outline"]
    opacity = palette["opacity_defaults"]["nib_line"]["outline"]

    outline = schema_nib.outline  # 5 points (last = first for closure)

    lines: list[dict[str, Any]] = []
    for i in range(4):
        v1 = outline[i]
        v2 = outline[i + 1]
        lines.append({
            "x1": v1[0], "y1": v1[1],
            "x2": v2[0], "y2": v2[1],
            "color": "bronze",
            "thickness": thickness,
            "opacity": opacity,
        })

    return lines


def _build_center_line(
    schema_nib,
    palette: dict,
) -> dict[str, Any]:
    """Center line follows the schema slit geometry (blue glow)."""
    thickness = palette["sizing"]["nib_line_thickness"]["center"]
    opacity = palette["opacity_defaults"]["nib_line"]["center"]

    return {
        "x1": schema_nib.slit_start[0],
        "y1": schema_nib.slit_start[1],
        "x2": schema_nib.slit_end[0],
        "y2": schema_nib.slit_end[1],
        "color": "blue_glow",
        "thickness": thickness,
        "opacity": opacity,
    }


def _build_accent_nodes(
    schema_nib,
    palette: dict,
) -> list[dict[str, Any]]:
    """Accent nodes placed symmetrically on the nib body.

    Positioned relative to schema outline shoulders:
      - Inner pair: at ~50% half_width, just above shoulder y (copper)
      - Outer pair: at full half_width, slightly above inner (amber)
    """
    center_x = schema_nib.outline[0][0]
    shoulder_y = schema_nib.outline[1][1]
    half_width = schema_nib.outline[1][0] - center_x

    nodes: list[dict[str, Any]] = []

    # Inner pair (copper)
    inner_dx = half_width * 0.5
    inner_y = shoulder_y + 0.08
    nodes.append({"x": center_x - inner_dx, "y": inner_y, "color": "copper", "radius": 0.06})
    nodes.append({"x": center_x + inner_dx, "y": inner_y, "color": "copper", "radius": 0.06})

    # Outer pair (amber)
    outer_y = shoulder_y + 0.15
    nodes.append({"x": center_x - half_width, "y": outer_y, "color": "amber", "radius": 0.05})
    nodes.append({"x": center_x + half_width, "y": outer_y, "color": "amber", "radius": 0.05})

    return nodes


def _build_junction_ball(
    schema_nib,
    palette: dict,
) -> dict[str, Any]:
    """Warm-white glowing ball at schema ball_pos (where nib meets the stem)."""
    ball_opacities = palette["opacity_defaults"]["nib_ball"]

    return {
        "x": schema_nib.ball_pos[0],
        "y": schema_nib.ball_pos[1],
        "radius": 0.10,
        "color": "warm_white",
        "opacity": ball_opacities["core"],
        "glow_size": 0.8,
        "glow_color": "warm_white",
        "glow_opacity": ball_opacities["glow"],
        "bloom_size": 1.6,
        "bloom_color": "amber",
        "bloom_opacity": ball_opacities["bloom"],
    }


# ──────────────────────────────────────────────
# Main builder
# ──────────────────────────────────────────────

def build_nib(
    palette: dict,
    schema: PLogoSchema | None = None,
    fan_count: int = DEFAULT_FAN_COUNT,
) -> dict[str, Any]:
    """Build the complete nib geometry from schema structure + palette aesthetics.

    Structural coordinates are derived from schema.nib (the single source
    of truth). The only free aesthetic parameter is fan_count.
    """
    if schema is None:
        schema = _SCHEMA

    snib = schema.nib
    center_x = snib.outline[0][0]
    tip_y = snib.outline[0][1]
    top_y = snib.outline[1][1]
    half_width = snib.outline[1][0] - center_x

    params = {
        "center_x": center_x,
        "tip_y": tip_y,
        "top_y": top_y,
        "half_width": half_width,
        "fan_count": fan_count,
        "ball_x": snib.ball_pos[0],
        "ball_y": snib.ball_pos[1],
        "ball_radius": snib.ball_radius,
        "source": "PLogoSchema",
    }

    fan_lines = _build_fan_lines(snib, fan_count, palette)
    outline_lines = _build_outline(snib, palette)
    center_line = _build_center_line(snib, palette)
    accent_nodes = _build_accent_nodes(snib, palette)
    junction_ball = _build_junction_ball(snib, palette)

    ink_origin = {"x": center_x, "y": tip_y}

    return {
        "_meta": {
            "step": 2,
            "name": "nib",
            "description": "Pen nib geometry — fan lines, outline, "
                           "center line, accent nodes, junction ball, ink origin. "
                           "Structural coordinates derived from PLogoSchema.nib.",
            "version": "2.0",
        },
        "params": params,
        "fan_lines": fan_lines,
        "outline_lines": outline_lines,
        "center_line": center_line,
        "accent_nodes": accent_nodes,
        "junction_ball": junction_ball,
        "ink_origin": ink_origin,
    }


# ──────────────────────────────────────────────
# File writer
# ──────────────────────────────────────────────

def write_nib(
    palette: dict,
    schema: PLogoSchema | None = None,
    fan_count: int = DEFAULT_FAN_COUNT,
) -> Path:
    """Build nib geometry and write to build/nib.json. Returns the output path."""
    nib_data = build_nib(palette, schema=schema, fan_count=fan_count)

    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "nib.json"

    with open(out_path, "w") as f:
        json.dump(nib_data, f, indent=2)

    return out_path


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def main() -> int:
    palette_path = Path(__file__).parent / "build" / "palette.json"
    if not palette_path.exists():
        print("ERROR: build/palette.json not found. Run palette.py first.", file=sys.stderr)
        return 1

    with open(palette_path) as f:
        palette = json.load(f)

    errors = validate(palette)
    if errors:
        print("NIB VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    out_path = write_nib(palette)

    # Load back for summary
    with open(out_path) as f:
        nib = json.load(f)

    print(f"nib.json written to {out_path}")
    print(f"  Source:        PLogoSchema.nib (schema-derived)")
    print(f"  Fan lines:     {len(nib['fan_lines'])} ({nib['params']['fan_count']} per side)")
    print(f"  Outline lines: {len(nib['outline_lines'])}")
    print(f"  Center line:   1 (color: {nib['center_line']['color']})")
    print(f"  Accent nodes:  {len(nib['accent_nodes'])}")
    print(f"  Junction ball: 1 (color: {nib['junction_ball']['color']})")
    print(f"  Ink origin:    ({nib['ink_origin']['x']:.4f}, {nib['ink_origin']['y']:.4f})")
    print("  Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
