"""
PAL's Notes Logo Pipeline — Step 2: Nib

Generates the pen nib geometry: a fountain pen nib at the bottom of the
P's stem, consisting of fan lines radiating from the tip, a diamond
outline, a center line (blue glow), accent nodes, a warm-white junction
ball, and an ink emission origin.

The nib is parametric from four values:
  - tip_y:      Y coordinate of the nib's lowest point
  - top_y:      Y coordinate where the nib meets the stem
  - half_width: half the lateral span at the widest point
  - fan_count:  number of fan lines per side (excluding center line)

Input:  build/palette.json
Output: build/nib.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Default parameters
# ──────────────────────────────────────────────

DEFAULT_TIP_Y: float = -4.0
DEFAULT_TOP_Y: float = -3.1
DEFAULT_HALF_WIDTH: float = 0.55
DEFAULT_FAN_COUNT: int = 3

# Center X derived from the point field (stem_x = x_sqB_left)
from pathlib import Path as _P
import json as _json
_ff = _P(__file__).parent / "build" / "point_field.json"
if _ff.exists():
    with open(_ff) as _f:
        _meta = _json.load(_f)["metadata"]
        DEFAULT_CENTER_X: float = _meta["derived"].get("x_sqA_v2",
                                   _meta["derived"].get("stem_x", -0.88))
else:
    DEFAULT_CENTER_X: float = -0.88


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate(
    palette: dict,
    tip_y: float = DEFAULT_TIP_Y,
    top_y: float = DEFAULT_TOP_Y,
    half_width: float = DEFAULT_HALF_WIDTH,
    fan_count: int = DEFAULT_FAN_COUNT,
) -> list[str]:
    """Validate nib parameters. Returns list of errors (empty = pass)."""
    errors: list[str] = []

    if tip_y >= top_y:
        errors.append(
            f"tip_y ({tip_y}) must be below top_y ({top_y}) — inverted or equal"
        )

    if half_width <= 0:
        errors.append(f"half_width ({half_width}) must be positive")

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
    center_x: float,
    tip_y: float,
    top_y: float,
    half_width: float,
    fan_count: int,
    palette: dict,
) -> list[dict[str, Any]]:
    """Build symmetric fan lines radiating from tip to upper spread points.

    fan_count lines per side, evenly distributed from the innermost
    fraction of half_width to the full half_width.
    """
    thickness = palette["sizing"]["nib_line_thickness"]["fan"]
    opacity = palette["opacity_defaults"]["nib_line"]["fan"]

    lines: list[dict[str, Any]] = []

    for i in range(fan_count):
        # Fraction from 0 (innermost) to 1 (outermost)
        frac = (i + 1) / fan_count

        dx = half_width * frac
        # Outermost lines end slightly lower than innermost
        dy_offset = frac * 0.15
        end_y = top_y + dy_offset

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


def _build_diamond_outline(
    center_x: float,
    tip_y: float,
    top_y: float,
    half_width: float,
    palette: dict,
) -> list[dict[str, Any]]:
    """Build the diamond (rhombus) outline of the nib.

    Four vertices:
      - Top:    (center_x, top_y)
      - Right:  (center_x + half_width, mid_y + offset)
      - Bottom: (center_x, bottom_diamond_y)  — between tip and top
      - Left:   (center_x - half_width, mid_y + offset)
    """
    thickness = palette["sizing"]["nib_line_thickness"]["outline"]
    opacity = palette["opacity_defaults"]["nib_line"]["outline"]

    mid_y = (tip_y + top_y) / 2
    # Diamond waist sits slightly above geometric midpoint
    waist_y = mid_y + (top_y - tip_y) * 0.1
    # Bottom vertex sits between tip and top
    bottom_y = mid_y - (top_y - tip_y) * 0.15

    top_vertex = (center_x, top_y)
    right_vertex = (center_x + half_width, waist_y)
    bottom_vertex = (center_x, bottom_y)
    left_vertex = (center_x - half_width, waist_y)

    def make_line(v1: tuple, v2: tuple) -> dict:
        return {
            "x1": v1[0], "y1": v1[1],
            "x2": v2[0], "y2": v2[1],
            "color": "bronze",
            "thickness": thickness,
            "opacity": opacity,
        }

    return [
        make_line(top_vertex, right_vertex),
        make_line(right_vertex, bottom_vertex),
        make_line(bottom_vertex, left_vertex),
        make_line(left_vertex, top_vertex),
    ]


def _build_center_line(
    center_x: float,
    tip_y: float,
    top_y: float,
    palette: dict,
) -> dict[str, Any]:
    """Vertical center line through the nib, using blue_glow color."""
    thickness = palette["sizing"]["nib_line_thickness"]["center"]
    opacity = palette["opacity_defaults"]["nib_line"]["center"]

    return {
        "x1": center_x,
        "y1": tip_y,
        "x2": center_x,
        "y2": top_y,
        "color": "blue_glow",
        "thickness": thickness,
        "opacity": opacity,
    }


def _build_accent_nodes(
    center_x: float,
    top_y: float,
    half_width: float,
    palette: dict,
) -> list[dict[str, Any]]:
    """Accent nodes placed symmetrically on the nib body.

    Two pairs:
      - Inner pair: at ~50% half_width, copper colored
      - Outer pair: at full half_width (diamond waist), amber colored
    """
    nodes: list[dict[str, Any]] = []

    # Inner pair (copper)
    inner_dx = half_width * 0.5
    inner_y = top_y + 0.08
    nodes.append({"x": center_x - inner_dx, "y": inner_y, "color": "copper", "radius": 0.06})
    nodes.append({"x": center_x + inner_dx, "y": inner_y, "color": "copper", "radius": 0.06})

    # Outer pair (amber)
    outer_y = top_y + 0.15
    nodes.append({"x": center_x - half_width, "y": outer_y, "color": "amber", "radius": 0.05})
    nodes.append({"x": center_x + half_width, "y": outer_y, "color": "amber", "radius": 0.05})

    return nodes


def _build_junction_ball(
    center_x: float,
    top_y: float,
    palette: dict,
) -> dict[str, Any]:
    """Warm-white glowing ball at the top of the nib where it meets the stem."""
    ball_opacities = palette["opacity_defaults"]["nib_ball"]

    return {
        "x": center_x,
        "y": top_y - 0.05,
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
    tip_y: float = DEFAULT_TIP_Y,
    top_y: float = DEFAULT_TOP_Y,
    half_width: float = DEFAULT_HALF_WIDTH,
    fan_count: int = DEFAULT_FAN_COUNT,
    center_x: float = DEFAULT_CENTER_X,
) -> dict[str, Any]:
    """Build the complete nib geometry from parameters and palette."""
    params = {
        "tip_y": tip_y,
        "top_y": top_y,
        "half_width": half_width,
        "fan_count": fan_count,
        "center_x": center_x,
    }

    fan_lines = _build_fan_lines(center_x, tip_y, top_y, half_width, fan_count, palette)
    outline_lines = _build_diamond_outline(center_x, tip_y, top_y, half_width, palette)
    center_line = _build_center_line(center_x, tip_y, top_y, palette)
    accent_nodes = _build_accent_nodes(center_x, top_y, half_width, palette)
    junction_ball = _build_junction_ball(center_x, top_y, palette)

    ink_origin = {"x": center_x, "y": tip_y}

    return {
        "_meta": {
            "step": 2,
            "name": "nib",
            "description": "Pen nib geometry — fan lines, diamond outline, "
                           "center line, accent nodes, junction ball, ink origin.",
            "version": "1.0",
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
    tip_y: float = DEFAULT_TIP_Y,
    top_y: float = DEFAULT_TOP_Y,
    half_width: float = DEFAULT_HALF_WIDTH,
    fan_count: int = DEFAULT_FAN_COUNT,
    center_x: float = DEFAULT_CENTER_X,
) -> Path:
    """Build nib geometry and write to build/nib.json. Returns the output path."""
    nib_data = build_nib(palette, tip_y, top_y, half_width, fan_count, center_x)

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
    print(f"  Fan lines:     {len(nib['fan_lines'])} ({nib['params']['fan_count']} per side)")
    print(f"  Outline lines: {len(nib['outline_lines'])}")
    print(f"  Center line:   1 (color: {nib['center_line']['color']})")
    print(f"  Accent nodes:  {len(nib['accent_nodes'])}")
    print(f"  Junction ball: 1 (color: {nib['junction_ball']['color']})")
    print(f"  Ink origin:    ({nib['ink_origin']['x']}, {nib['ink_origin']['y']})")
    print("  Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
