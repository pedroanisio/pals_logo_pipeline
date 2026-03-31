"""Export PLogoSchema to JSON — backward compatible with p_logo_schema.json."""

from __future__ import annotations

import json
import math
from pathlib import Path
from p_logo.types import PLogoSchema


def schema_to_dict(schema: PLogoSchema) -> dict:
    """Convert PLogoSchema to the canonical JSON structure."""
    sc = {"x": schema.center[0], "y": schema.center[1]}

    return {
        "coordinate_system": {
            "P.CENTER.A": sc,
            "free_parameters": {
                "R_GREEN": schema.r_green,
                "description": "Single free parameter. All radii derived via \u221a2 chain.",
            },
            "derived_radii": {
                "Circ.D":        {"value": schema.r_blue,  "formula": "R_GREEN / \u221a2", "maps_to": "Blue arc"},
                "Circ.Bounds.A": {"value": schema.r_green, "formula": "free parameter", "maps_to": "Green arc"},
                "Circ.A":        {"value": schema.r_gold,  "formula": "R_GREEN \u00d7 \u221a2", "maps_to": "Gold arc"},
            },
            "derived_constants": {
                "R_VERTEX":     {"value": schema.r_vertex, "formula": "Circ.A - Circ.Bounds.A"},
                "Rect.1.right": {"value": schema.composition["shapes"]["Rect.1"]["vertices"]["upper_right"]["x"],
                                 "formula": "P.SQAB.UL.x + Rect.1.width"},
                "Rect.1.bottom":{"value": schema.composition["shapes"]["Rect.1"]["vertices"]["lower_left"]["y"],
                                 "formula": "P.SQAB.UL.y - Rect.1.height"},
            },
            "composition_scale": schema.r_blue / 100.0,
        },
        "geometry": {
            "shapes": _export_shapes(schema),
            "arcs": [
                {
                    "name": a.name,
                    "center": {"x": a.cx, "y": a.cy},
                    "radius": a.radius,
                    "start_angle": a.start_angle,
                    "sweep_angle": a.sweep_angle,
                    "start_deg": a.start_deg,
                    "end_deg": a.end_deg,
                }
                for a in schema.arcs
            ],
            "tangent_points": {
                "P.CA.TANGENT.BOTTOM": {"x": schema.center[0], "y": schema.center[1] - schema.r_gold, "node": 17},
                "P.CA.TANGENT.RIGHT":  {"x": schema.center[0] + schema.r_gold, "y": schema.center[1], "node": 20},
                "P.CA.TANGENT.TOP":    {"x": schema.center[0], "y": schema.center[1] + schema.r_gold, "node": None, "note": "above arc"},
            },
        },
        "graph": {
            "nodes": [
                {
                    "id": n.id,
                    "x": n.x,
                    "y": n.y,
                    "key_node": n.key_node,
                    "composition_point": n.composition_point,
                    "source": n.source,
                }
                for n in schema.nodes
            ],
            "edges": [
                {"from": e.from_id, "to": e.to_id}
                for e in schema.edges
            ],
        },
    }


def _export_shapes(schema: PLogoSchema) -> dict:
    """Build the geometry.shapes section from schema values."""
    cx, cy = schema.center
    g45 = schema.r_green / math.sqrt(2)
    comp = schema.composition

    return {
        "Circ.A":        {"type": "circle", "center": {"x": cx, "y": cy}, "radius": schema.r_gold, "maps_to": "Gold arc"},
        "Circ.Bounds.A": {"type": "circle", "center": {"x": cx, "y": cy}, "radius": schema.r_green, "maps_to": "Green arc"},
        "Circ.D":        {"type": "circle", "center": {"x": cx, "y": cy}, "radius": schema.r_blue, "maps_to": "Blue arc"},
        "Square.B": {
            "type": "square", "description": "Circumscribed around Circ.A",
            "vertices": {
                "P.SQAB.UL": {"x": cx - schema.r_gold, "y": cy + schema.r_gold},
                "P.SQAB.UR": {"x": cx + schema.r_gold, "y": cy + schema.r_gold},
                "P.SQAB.LL": {"x": cx - schema.r_gold, "y": cy - schema.r_gold},
                "P.SQAB.LR": {"x": cx + schema.r_gold, "y": cy - schema.r_gold},
            },
        },
        "Square.A": {
            "type": "square", "description": "Inscribed in Circ.A (45\u00b0 rotated)",
            "vertices": {
                "P.SQA.V1": {"x": cx + schema.r_green, "y": cy + schema.r_green},
                "P.SQA.V2": {"x": cx - schema.r_green, "y": cy + schema.r_green},
                "P.SQA.V3": {"x": cx - schema.r_green, "y": cy - schema.r_green},
                "P.SQA.V4": {"x": cx + schema.r_green, "y": cy - schema.r_green},
            },
        },
        "Square.D": {
            "type": "square", "description": "Inscribed in Circ.Bounds.A (45\u00b0 rotated) = Green IS",
            "vertices": {
                "P.SQD.D1": {"x": cx + g45, "y": cy + g45},
                "P.SQD.D2": {"x": cx - g45, "y": cy + g45},
                "P.SQD.D3": {"x": cx - g45, "y": cy - g45},
                "P.SQD.D4": {"x": cx + g45, "y": cy - g45},
            },
        },
        "Rect.1": {
            "type": "rectangle", "description": "P pole / stem",
            "vertices": {
                "P.RECT.UL": comp["shapes"]["Rect.1"]["vertices"]["upper_left"],
                "P.RECT.UR": comp["shapes"]["Rect.1"]["vertices"]["upper_right"],
                "P.RECT.LL": comp["shapes"]["Rect.1"]["vertices"]["lower_left"],
                "P.RECT.LR": comp["shapes"]["Rect.1"]["vertices"]["lower_right"],
            },
            "width": comp["shapes"]["Rect.1"]["width"],
            "height": comp["shapes"]["Rect.1"]["height"],
        },
        "Circ.Rect.I": {
            "type": "circle", "description": "Inscribed in Rect.1 at bottom (nib circle)",
            "center": comp["shapes"]["Circ.Rect.I"]["center"],
            "radius": comp["shapes"]["Circ.Rect.I"]["radius"],
        },
        "Circ.Rect.V": {
            "type": "circle", "description": "External vertex circle at Rect.1 bottom",
            "center": comp["shapes"]["Circ.Rect.V"]["center"],
            "radius": comp["shapes"]["Circ.Rect.V"]["radius"],
        },
    }


def export_json(schema: PLogoSchema, path: str) -> None:
    """Export PLogoSchema to a JSON file."""
    data = schema_to_dict(schema)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
