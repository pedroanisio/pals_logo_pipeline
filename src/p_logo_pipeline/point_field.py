"""
PAL's Notes Logo Pipeline — Point Field (Plane A)

Architecture from the geometric spec:

  FREE PARAMETER: R_GREEN (middle circle radius)
  √2 CHAIN: R_D = R_GREEN/√2 (inner/Blue)
             R_GREEN = middle (Green)
             R_A = R_GREEN×√2 (outer/Gold)

  GRID SYSTEM: Nodes sit at intersections of x-columns and y-rows.
    X-columns: SqB.left | SqA.V2.x | Rect.right | center_x
    Y-rows:    SqB.top | Green.tan.top | Blue.tan.top | center_y |
               Blue.tan.bottom | Green.tan.bottom | SqB.bottom

  Each grid crossing where two shapes' coordinates meet is a named point.
  The projection selects which crossings become logo nodes.
"""

from __future__ import annotations

import math
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldParams:
    """Free parameter: R_GREEN (middle circle). Everything else derived."""
    cx: float = 0.3504
    cy: float = 0.8694
    R_GREEN: float = 1.2303
    scale: float = 1.0
    origin_x: float = 0.0
    origin_y: float = 0.0


def _compute_derived(P: FieldParams):
    """Compute all derived geometry from the free parameter."""
    cx, cy, RG = P.cx, P.cy, P.R_GREEN
    R_D = RG / math.sqrt(2)
    R_A = RG * math.sqrt(2)
    R_VERTEX = R_A - RG

    def tx(x, y):
        return (round(x * P.scale + P.origin_x, 6),
                round(y * P.scale + P.origin_y, 6))

    x_sqB_left  = cx - R_A
    x_sqA_v2    = cx - RG
    x_rect_right = x_sqB_left + 2 * R_VERTEX
    x_center    = cx
    x_sqB_right = cx + R_A

    y_sqB_top       = cy + R_A
    y_green_tan_top = cy + RG
    y_blue_tan_top  = cy + R_D
    y_center        = cy
    y_blue_tan_bot  = cy - R_D
    y_green_tan_bot = cy - RG
    y_sqB_bot       = cy - R_A

    rect_width = 2 * R_VERTEX
    nib_center_x = x_sqA_v2
    rect_bottom = y_sqB_bot - rect_width * 2.5
    circ_rect_i_cy = rect_bottom + R_VERTEX
    circ_rect_i_top = circ_rect_i_cy + R_VERTEX
    circ_rect_v_cy = rect_bottom - R_VERTEX

    return {
        "cx": cx, "cy": cy, "RG": RG, "R_D": R_D, "R_A": R_A,
        "R_VERTEX": R_VERTEX, "tx": tx,
        "x_sqB_left": x_sqB_left, "x_sqA_v2": x_sqA_v2,
        "x_rect_right": x_rect_right, "x_center": x_center,
        "x_sqB_right": x_sqB_right,
        "y_sqB_top": y_sqB_top, "y_green_tan_top": y_green_tan_top,
        "y_blue_tan_top": y_blue_tan_top, "y_center": y_center,
        "y_blue_tan_bot": y_blue_tan_bot, "y_green_tan_bot": y_green_tan_bot,
        "y_sqB_bot": y_sqB_bot,
        "rect_width": rect_width, "nib_center_x": nib_center_x,
        "rect_bottom": rect_bottom, "circ_rect_i_cy": circ_rect_i_cy,
        "circ_rect_i_top": circ_rect_i_top, "circ_rect_v_cy": circ_rect_v_cy,
        "P": P,
    }


def _build_field_shapes(d: dict) -> dict[str, dict]:
    """Build all shape definitions from derived geometry."""
    cx, cy, tx = d["cx"], d["cy"], d["tx"]
    P = d["P"]
    shapes: dict[str, dict] = {}

    for name, r, role in [
        ("Circ.A",       d["R_A"], "Gold arc (outer). R = R_GREEN×√2."),
        ("Circ.Bounds.A", d["RG"], "Green arc (middle). R = R_GREEN (free parameter)."),
        ("Circ.D",       d["R_D"], "Blue arc (inner). R = R_GREEN/√2."),
    ]:
        ct = tx(cx, cy)
        shapes[name] = {
            "type": "circle", "name": name,
            "center": {"x": ct[0], "y": ct[1]},
            "radius": round(r * P.scale, 6), "role": role,
        }

    shapes["Square.B"] = {
        "type": "square", "name": "Square.B",
        "vertices": {
            "UL": {"x": tx(d["x_sqB_left"], d["y_sqB_top"])[0], "y": tx(d["x_sqB_left"], d["y_sqB_top"])[1]},
            "UR": {"x": tx(d["x_sqB_right"], d["y_sqB_top"])[0], "y": tx(d["x_sqB_right"], d["y_sqB_top"])[1]},
            "LL": {"x": tx(d["x_sqB_left"], d["y_sqB_bot"])[0], "y": tx(d["x_sqB_left"], d["y_sqB_bot"])[1]},
            "LR": {"x": tx(d["x_sqB_right"], d["y_sqB_bot"])[0], "y": tx(d["x_sqB_right"], d["y_sqB_bot"])[1]},
        },
        "role": "Circumscribes Circ.A. Defines stem_x and outer y-rows.",
    }

    for name, r, desc in [
        ("Square.A", d["R_A"], "Inscribed in Circ.A at 45°"),
        ("Square.D", d["RG"],  "Inscribed in Circ.Bounds.A at 45° (Green IS)"),
    ]:
        half = r / math.sqrt(2)
        shapes[name] = {
            "type": "square", "name": name,
            "vertices": {
                "V1": {"x": tx(cx+half, cy+half)[0], "y": tx(cx+half, cy+half)[1]},
                "V2": {"x": tx(cx-half, cy+half)[0], "y": tx(cx-half, cy+half)[1]},
                "V3": {"x": tx(cx-half, cy-half)[0], "y": tx(cx-half, cy-half)[1]},
                "V4": {"x": tx(cx+half, cy-half)[0], "y": tx(cx+half, cy-half)[1]},
            },
            "role": desc,
        }

    shapes["Rect.1"] = {
        "type": "rectangle", "name": "Rect.1",
        "vertices": {
            "UL": {"x": tx(d["x_sqB_left"], d["y_sqB_top"])[0], "y": tx(d["x_sqB_left"], d["y_sqB_top"])[1]},
            "UR": {"x": tx(d["x_rect_right"], d["y_sqB_top"])[0], "y": tx(d["x_rect_right"], d["y_sqB_top"])[1]},
            "LL": {"x": tx(d["x_sqB_left"], d["rect_bottom"])[0], "y": tx(d["x_sqB_left"], d["rect_bottom"])[1]},
            "LR": {"x": tx(d["x_rect_right"], d["rect_bottom"])[0], "y": tx(d["x_rect_right"], d["rect_bottom"])[1]},
        },
        "width": round(d["rect_width"] * P.scale, 6),
        "role": "Stem rectangle. Width = 2×R_VERTEX.",
    }

    shapes["Circ.Rect.I"] = {
        "type": "circle", "name": "Circ.Rect.I",
        "center": {"x": tx(d["nib_center_x"], d["circ_rect_i_cy"])[0],
                   "y": tx(d["nib_center_x"], d["circ_rect_i_cy"])[1]},
        "radius": round(d["R_VERTEX"] * P.scale, 6),
        "role": "Inscribed circle in Rect.1 at bottom (nib circle).",
    }
    shapes["Circ.Rect.V"] = {
        "type": "circle", "name": "Circ.Rect.V",
        "center": {"x": tx(d["nib_center_x"], d["circ_rect_v_cy"])[0],
                   "y": tx(d["nib_center_x"], d["circ_rect_v_cy"])[1]},
        "radius": round(d["R_VERTEX"] * P.scale, 6),
        "role": "External vertex circle at Rect.1 bottom.",
    }

    return shapes


def _build_field_points(d: dict) -> tuple[dict[str, dict], list[dict]]:
    """Build all named points from derived geometry."""
    cx, cy, tx = d["cx"], d["cy"], d["tx"]
    R_D, RG, R_A = d["R_D"], d["RG"], d["R_A"]
    R_VERTEX = d["R_VERTEX"]
    nib_center_x = d["nib_center_x"]
    circ_rect_i_top = d["circ_rect_i_top"]
    circ_rect_i_cy = d["circ_rect_i_cy"]
    circ_rect_v_cy = d["circ_rect_v_cy"]

    points: dict[str, dict] = {}
    intersections: list[dict] = []

    def add(name, x, y, desc, tags=None):
        t = tx(x, y)
        points[name] = {"x": t[0], "y": t[1], "description": desc, "tags": tags or []}

    waist_y = circ_rect_i_top
    bump_hub_y = (d["y_sqB_bot"] + waist_y) / 2

    # Grid definition
    x_cols = {
        "sqB_left":   (d["x_sqB_left"],   "Square.B left"),
        "sqA_v2_x":   (d["x_sqA_v2"],     "Square.A V2/V3 x"),
        "rect_right":  (d["x_rect_right"], "Rect.1 right"),
        "center_x":   (d["x_center"],      "Center x"),
        "sqB_right":  (d["x_sqB_right"],   "Square.B right"),
    }
    y_rows = {
        "sqB_top":       (d["y_sqB_top"],       "Square.B top / Gold TAN top"),
        "green_tan_top": (d["y_green_tan_top"], "Green tangent top"),
        "blue_tan_top":  (d["y_blue_tan_top"],  "Blue tangent top"),
        "center_y":      (d["y_center"],         "Center y"),
        "blue_tan_bot":  (d["y_blue_tan_bot"],  "Blue tangent bottom"),
        "green_tan_bot": (d["y_green_tan_bot"], "Green tangent bottom"),
        "sqB_bot":       (d["y_sqB_bot"],       "Square.B bottom / Gold TAN bottom"),
        "waist_y":       (waist_y,          "Circ.Rect.I top / nib waist"),
    }

    # Generate ALL grid crossings
    for xname, (xval, xdesc) in x_cols.items():
        for yname, (yval, ydesc) in y_rows.items():
            ptname = f"P.GRID.{xname}.{yname}"
            add(ptname, xval, yval,
                f"Grid: {xdesc} × {ydesc}",
                ["grid", xname, yname])

    # ── Tangent points (explicit, for clarity) ──
    # These are specific grid crossings, but named by their geometric meaning
    for circ_name, r, prefix in [("A", R_A, "CA"), ("Bounds.A", RG, "CBA"), ("D", R_D, "CD")]:
        add(f"P.{prefix}.TAN.TOP",    cx, cy + r, f"Circ.{circ_name} tangent top",
            ["tangent", f"circ_{circ_name}", "top"])
        add(f"P.{prefix}.TAN.BOTTOM", cx, cy - r, f"Circ.{circ_name} tangent bottom",
            ["tangent", f"circ_{circ_name}", "bottom"])
        add(f"P.{prefix}.TAN.RIGHT",  cx + r, cy, f"Circ.{circ_name} tangent right",
            ["tangent", f"circ_{circ_name}", "right"])
        add(f"P.{prefix}.TAN.LEFT",   cx - r, cy, f"Circ.{circ_name} tangent left",
            ["tangent", f"circ_{circ_name}", "left"])

    # ── Inscribed square vertices (on circles at 45°) ──
    for circ_name, r, prefix in [("A", R_A, "SQA"), ("Bounds.A", RG, "SQD"), ("D", R_D, "SQD_inner")]:
        half = r / math.sqrt(2)
        for angle_deg, label in [(45, "V1"), (135, "V2"), (225, "V3"), (315, "V4")]:
            angle = math.radians(angle_deg)
            vx = cx + r * math.cos(angle)
            vy = cy + r * math.sin(angle)
            add(f"P.{prefix}.{label}", vx, vy,
                f"Circ.{circ_name} IS vertex {label} ({angle_deg}°)",
                ["vertex", f"is_{circ_name}", f"angle_{angle_deg}"])

    # ── Square.B corners ──
    x_sqB_left, x_sqB_right = d["x_sqB_left"], d["x_sqB_right"]
    y_sqB_top, y_sqB_bot = d["y_sqB_top"], d["y_sqB_bot"]
    x_rect_right = d["x_rect_right"]
    add("P.SQB.UL", x_sqB_left, y_sqB_top, "Square.B upper-left", ["corner", "sq_B"])
    add("P.SQB.UR", x_sqB_right, y_sqB_top, "Square.B upper-right", ["corner", "sq_B"])
    add("P.SQB.LL", x_sqB_left, y_sqB_bot, "Square.B lower-left", ["corner", "sq_B"])
    add("P.SQB.LR", x_sqB_right, y_sqB_bot, "Square.B lower-right", ["corner", "sq_B"])

    # ── Center ──
    add("P.CENTER", cx, cy, "Shared center of all circles", ["center"])

    # ── Nib geometry ──
    add("P.NIB.RECT_I.TOP", nib_center_x, circ_rect_i_top,
        "Circ.Rect.I top (nib shoulder)", ["nib", "circ_rect_i"])
    add("P.NIB.RECT_I.CENTER", nib_center_x, circ_rect_i_cy,
        "Circ.Rect.I center (nib waist)", ["nib", "circ_rect_i"])
    add("P.NIB.RECT_V.CENTER", nib_center_x, circ_rect_v_cy,
        "Circ.Rect.V center (nib tip)", ["nib", "circ_rect_v"])

    # ── Bump pattern points (nib as graph nodes) ──
    add("P.NIB.WAIST.LEFT", x_sqB_left, waist_y,
        "Grid: sqB_left × waist_y (Rect.1 left at nib waist)", ["nib", "grid", "waist"])
    add("P.NIB.WAIST.RIGHT", x_rect_right, waist_y,
        "Grid: rect_right × waist_y (Rect.1 right at nib waist)", ["nib", "grid", "waist"])
    add("P.NIB.BUMP.HUB", nib_center_x, bump_hub_y,
        "Bump center hub (midpoint SqB.bottom ↔ waist_y)", ["nib", "hub", "bump"])

    # ── Gold arc top endpoint (asymmetric, ~76.4°) ──
    gold_end_angle = math.radians(76.44)
    gold_top_x = cx + R_A * math.cos(gold_end_angle)
    gold_top_y = cy + R_A * math.sin(gold_end_angle)
    add("P.GOLD.ARC.TOP", gold_top_x, gold_top_y,
        "Gold arc top endpoint (~76.4° on Circ.A)", ["arc_endpoint", "circ_A"])

    return points, intersections


def generate_field(params: FieldParams | None = None) -> dict[str, Any]:
    if params is None:
        params = FieldParams()

    d = _compute_derived(params)
    shapes = _build_field_shapes(d)
    points, intersections = _build_field_points(d)

    metadata = {
        "root": {"cx": d["cx"], "cy": d["cy"], "R_GREEN": d["RG"]},
        "derived": {
            "R_D": round(d["R_D"], 6), "R_A": round(d["R_A"], 6),
            "R_VERTEX": round(d["R_VERTEX"], 6),
            "x_sqB_left": round(d["x_sqB_left"], 6),
            "x_sqA_v2": round(d["x_sqA_v2"], 6),
            "x_rect_right": round(d["x_rect_right"], 6),
            "x_center": round(d["x_center"], 6),
        },
        "counts": {"shapes": len(shapes), "points": len(points),
                   "intersections": len(intersections)},
    }

    return {
        "_meta": {"name": "point_field",
                  "description": "Plane A: Grid intersection system. "
                                 "4 x-columns × 7 y-rows + IS vertices + nib."},
        "metadata": metadata, "shapes": shapes,
        "points": points, "intersections": intersections,
    }


def write_field(params=None):
    data = generate_field(params)
    out = Path(__file__).parent / "build"
    out.mkdir(exist_ok=True)
    p = out / "point_field.json"
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    return p


def main() -> int:
    data = generate_field()
    p = write_field()
    m = data["metadata"]
    print(f"point_field.json written to {p}")
    print(f"  Root: R_GREEN={m['root']['R_GREEN']}, center=({m['root']['cx']}, {m['root']['cy']})")
    print(f"  √2 chain: R_D={m['derived']['R_D']}, R_GREEN={m['root']['R_GREEN']}, R_A={m['derived']['R_A']}")
    print(f"  Grid columns: sqB_left={m['derived']['x_sqB_left']:.4f}, sqA_v2={m['derived']['x_sqA_v2']:.4f}, "
          f"rect_right={m['derived']['x_rect_right']:.4f}, center={m['derived']['x_center']}")
    print(f"  Shapes: {m['counts']['shapes']}  Points: {m['counts']['points']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
