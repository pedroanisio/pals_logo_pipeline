"""
PAL's Notes Logo Pipeline — Step 3: Arcs

Reads arc definitions from projection.json. Arc centers and radii originate
from the point field shapes (Circ.A, Circ.D, Circ.Mid) via the projection.

Data flow: point_field.py → projection.py → arcs.py

Input:  build/palette.json, build/projection.json
Output: build/arcs.json
"""

from __future__ import annotations

import json, math, sys
from pathlib import Path
from typing import Any


def _load_arc_defs() -> list[dict[str, Any]]:
    p_path = Path(__file__).parent / "build" / "projection.json"
    with open(p_path) as f:
        proj = json.load(f)
    return proj["arc_definitions"]


DEFAULT_ARC_DEFS: list[dict[str, Any]] = _load_arc_defs()
DEFAULT_SEGMENTS: int = 56


def validate(palette: dict, arc_defs: list[dict[str, Any]] | None = None) -> list[str]:
    errors: list[str] = []
    defs = arc_defs if arc_defs is not None else DEFAULT_ARC_DEFS
    palette_colors = set(palette.get("colors", {}).keys())
    for i, ad in enumerate(defs):
        if ad.get("radius", 0) <= 0:
            errors.append(f"Arc {i}: radius must be positive, got {ad.get('radius')}")
        sa, ea = ad.get("start_angle", 0), ad.get("end_angle", 0)
        if sa >= ea:
            errors.append(f"Arc {i}: start_angle ({sa}) >= end_angle ({ea})")
        if ad.get("color", "") not in palette_colors:
            errors.append(f"Arc {i}: color '{ad.get('color')}' not in palette")
    return errors


def _sample_arc(cx, cy, radius, start_angle, end_angle, segments):
    points = []
    sweep = end_angle - start_angle
    for i in range(segments + 1):
        t = i / segments
        angle = start_angle + sweep * t
        ca, sa = math.cos(angle), math.sin(angle)
        points.append({"x": cx + ca * radius, "y": cy + sa * radius,
                       "nx": ca, "ny": sa, "t": round(t, 8)})
    return points


def build_arcs(palette: dict, arc_defs=None, segments=DEFAULT_SEGMENTS):
    defs = arc_defs if arc_defs is not None else DEFAULT_ARC_DEFS
    main_thickness = palette["sizing"]["arc_main_thickness"]
    bloom_thickness = palette["sizing"]["arc_bloom_thickness"]
    main_opacity = palette["opacity_defaults"]["arc_main"]["base"]
    bloom_opacity = palette["opacity_defaults"]["arc_bloom"]["base"]

    sorted_defs = sorted(enumerate(defs), key=lambda pair: pair[1]["radius"])
    arcs, runner_paths = [], []

    for index, (_, ad) in enumerate(sorted_defs):
        points = _sample_arc(ad["cx"], ad["cy"], ad["radius"],
                             ad["start_angle"], ad["end_angle"], segments)
        arcs.append({
            "index": index,
            "cx": ad["cx"], "cy": ad["cy"], "radius": ad["radius"],
            "start_angle": ad["start_angle"], "end_angle": ad["end_angle"],
            "color": ad["color"], "points": points,
            "main_thickness": main_thickness, "bloom_thickness": bloom_thickness,
            "main_opacity": main_opacity, "bloom_opacity": bloom_opacity,
        })
        runner_paths.append({
            "arc_index": index, "color": ad["color"],
            "points": [{"x": p["x"], "y": p["y"], "t": p["t"]} for p in points],
        })

    arcs.sort(key=lambda a: a["index"])
    runner_paths.sort(key=lambda r: r["arc_index"])

    return {
        "_meta": {
            "step": 3, "name": "arcs",
            "description": "Three bowl arcs from Plane B projection. "
                           "Inner=Circ.D, Mid=Circ.Mid, Outer=Circ.A.",
            "version": "3.0",
        },
        "arcs": arcs,
        "runner_paths": runner_paths,
    }


def write_arcs(palette, arc_defs=None, segments=DEFAULT_SEGMENTS):
    data = build_arcs(palette, arc_defs, segments)
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "arcs.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


def main() -> int:
    p_path = Path(__file__).parent / "build" / "palette.json"
    if not p_path.exists():
        print("ERROR: build/palette.json not found.", file=sys.stderr)
        return 1
    with open(p_path) as f:
        palette = json.load(f)
    errors = validate(palette)
    if errors:
        print("ARCS VALIDATION FAILED:", file=sys.stderr)
        for e in errors: print(f"  ✗ {e}", file=sys.stderr)
        return 1
    out_path = write_arcs(palette)
    with open(out_path) as f:
        data = json.load(f)
    print(f"arcs.json written to {out_path}")
    print(f"  Source: projection.json (Plane A → Plane B)")
    for arc in data["arcs"]:
        sweep_deg = math.degrees(arc["end_angle"] - arc["start_angle"])
        print(f"  Arc {arc['index']}: r={arc['radius']:.4f}  sweep={sweep_deg:.1f}°  "
              f"points={len(arc['points'])}  color={arc['color']}")
    print(f"  Runner paths: {len(data['runner_paths'])}")
    print("  Validation: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
