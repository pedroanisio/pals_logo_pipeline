"""
PAL's Notes Logo Pipeline — Projection (Plane B)

25 nodes, 44 typed edges, 3 arcs.

From the schema: the nib is part of the graph — nodes 22/23/24 form
the "bump pattern" connecting the stem bottom to the pen nib. No
separate nib.py geometry needed.

Edge types:
  contour — outer silhouette, rendered at full opacity
  struct  — structural diagonals, full opacity
  mesh    — interior cross-connections, translucent in arc areas
  nib     — nib bump pattern, subtle

All arcs are full π semicircles (−90° to +90°).
"""

from __future__ import annotations

import math
import json
import sys
from pathlib import Path
from typing import Any


# ══════════════════════════════════════════════
# CANONICAL GEOMETRY — from p_logo library
# (single source of truth for edges, arcs, and
#  non-nib node coordinates)
#
# Deferred: schema is built on first access, not at import time.
# ══════════════════════════════════════════════

import sys as _sys
_parent = str(Path(__file__).parent.parent)
if _parent not in _sys.path:
    _sys.path.append(_parent)  # append, not insert — don't override existing paths
from p_logo import build_schema as _build_schema

_SCHEMA = None


def _get_schema():
    """Return the cached canonical schema, building it on first access."""
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = _build_schema()
    return _SCHEMA


# ──────────────────────────────────────────────
# 44 TYPED EDGES — derived from p_logo schema
# ──────────────────────────────────────────────

# Deferred: built on first access
_DEFAULT_EDGE_RULES = None


def _get_default_edge_rules():
    global _DEFAULT_EDGE_RULES
    if _DEFAULT_EDGE_RULES is None:
        s = _get_schema()
        _DEFAULT_EDGE_RULES = [(e.from_id, e.to_id, e.edge_type) for e in s.edges]
    return _DEFAULT_EDGE_RULES


# Eagerly populate for backward compatibility (modules that import the constant).
# The schema is still built only once via _get_schema() caching.
DEFAULT_EDGE_RULES: list[tuple[int, int, str]] = _get_default_edge_rules()

# ──────────────────────────────────────────────
# NODE METADATA — pipeline-specific fields per node
# (region, alias, source_point for provenance)
# ──────────────────────────────────────────────

_NIB_NODE_IDS = {12, 13, 14, 22, 23, 24}

NODE_METADATA: dict[int, dict[str, str]] = {
    0:  {"region": "stem",     "alias": "stem_top",           "source_point": "P.SQB.UL"},
    1:  {"region": "top_bar",  "alias": "top_bar_right",      "source_point": "P.GRID.center_x.sqB_top"},
    2:  {"region": "bowl",     "alias": "green_is_45",        "source_point": "P.SQD.V1"},
    3:  {"region": "bowl",     "alias": "blue_tan_bot",       "source_point": "P.CD.TAN.BOTTOM"},
    4:  {"region": "counter",  "alias": "counter_tl",         "source_point": "P.GRID.sqA_v2_x.green_tan_top"},
    5:  {"region": "bowl",     "alias": "blue_tan_top",       "source_point": "P.CD.TAN.TOP"},
    6:  {"region": "bowl",     "alias": "blue_tan_right",     "source_point": "P.CD.TAN.RIGHT"},
    7:  {"region": "stem",     "alias": "junction_left",      "source_point": "P.GRID.sqB_left.blue_tan_bot"},
    8:  {"region": "counter",  "alias": "counter_br",         "source_point": "P.GRID.rect_right.blue_tan_bot"},
    9:  {"region": "counter",  "alias": "triangle_vertex",    "source_point": "P.GRID.sqA_v2_x.green_tan_bot"},
    10: {"region": "nib_area", "alias": "nib_shoulder_right", "source_point": "P.GRID.rect_right.sqB_bot"},
    11: {"region": "stem",     "alias": "stem_shoulder",      "source_point": "P.SQB.LL"},
    12: {"region": "nib",      "alias": "nib_shoulder",       "source_point": "P.NIB.RECT_I.TOP"},
    13: {"region": "nib",      "alias": "nib_ball",           "source_point": "P.NIB.RECT_I.CENTER"},
    14: {"region": "nib",      "alias": "nib_tip",            "source_point": "P.NIB.RECT_V.CENTER"},
    15: {"region": "counter",  "alias": "counter_tr",         "source_point": "P.GRID.rect_right.blue_tan_top"},
    16: {"region": "nib_area", "alias": "outer_D_stem",       "source_point": "P.GRID.rect_right.sqB_bot"},
    17: {"region": "bowl",     "alias": "gold_tan_bot",       "source_point": "P.CA.TAN.BOTTOM"},
    18: {"region": "bowl",     "alias": "green_tan_bot",      "source_point": "P.CBA.TAN.BOTTOM"},
    19: {"region": "bowl",     "alias": "green_tan_top",      "source_point": "P.CBA.TAN.TOP"},
    20: {"region": "bowl",     "alias": "gold_tan_right",     "source_point": "P.CA.TAN.RIGHT"},
    21: {"region": "bowl",     "alias": "green_is_315",       "source_point": "P.SQD.V4"},
    22: {"region": "nib",      "alias": "waist_left",         "source_point": "P.NIB.WAIST.LEFT"},
    23: {"region": "nib",      "alias": "waist_right",        "source_point": "P.NIB.WAIST.RIGHT"},
    24: {"region": "nib",      "alias": "bump_hub",           "source_point": "P.NIB.BUMP.HUB"},
}

# ──────────────────────────────────────────────
# ROLES
# ──────────────────────────────────────────────

DEFAULT_ROLES: dict[str, Any] = {
    "junction_index": 9,
    "color_overrides": {
        1:  "amber",      7:  "amber",      9:  "amber",
        11: "amber",      16: "amber",      17: "amber",
        18: "amber",      19: "amber",      20: "amber",
        21: "amber",      6:  "blue_glow",
    },
    "default_color": "copper",
}

# ──────────────────────────────────────────────
# ARC METADATA — pipeline color/shape names
# ──────────────────────────────────────────────

ARC_METADATA: dict[str, dict[str, str]] = {
    "Green": {"color": "copper",    "source_shape": "Circ.Bounds.A"},
    "Blue":  {"color": "blue_glow", "source_shape": "Circ.D"},
    "Gold":  {"color": "amber",     "source_shape": "Circ.A"},
}

_DEFAULT_ARC_SEGMENTS = None


def _get_default_arc_segments():
    global _DEFAULT_ARC_SEGMENTS
    if _DEFAULT_ARC_SEGMENTS is None:
        s = _get_schema()
        _DEFAULT_ARC_SEGMENTS = [
            {"source_shape": ARC_METADATA[a.name]["source_shape"],
             "color": ARC_METADATA[a.name]["color"],
             "start_angle": a.start_angle, "end_angle": a.end_angle,
             "_cx": a.cx, "_cy": a.cy, "_radius": a.radius}
            for a in s.arcs
        ]
    return _DEFAULT_ARC_SEGMENTS


DEFAULT_ARC_SEGMENTS: list[dict[str, Any]] = _get_default_arc_segments()


# ──────────────────────────────────────────────
# PROJECTION EXECUTION
# ──────────────────────────────────────────────

def project(
    field: dict[str, Any],
    edge_rules=None,
    roles=None, arc_segments=None,
) -> dict[str, Any]:
    edges = edge_rules if edge_rules is not None else _get_default_edge_rules()
    role_spec = roles or DEFAULT_ROLES
    arc_segs = arc_segments if arc_segments is not None else _get_default_arc_segments()

    fp = field["points"]
    fs = field["shapes"]

    # Build nodes: non-nib from p_logo schema, nib from point_field
    nodes = []
    for i in range(25):
        meta = NODE_METADATA[i]
        color = role_spec["color_overrides"].get(i, role_spec["default_color"])

        if i in _NIB_NODE_IDS:
            # Nib nodes: resolve from field (pipeline's stem extension)
            pt_name = meta["source_point"]
            if pt_name not in fp:
                raise ValueError(
                    f"Node {i} references '{pt_name}' not in field. "
                    f"Available: {sorted(fp.keys())[:10]}..."
                )
            pt = fp[pt_name]
            x, y = pt["x"], pt["y"]
        else:
            # Non-nib nodes: from p_logo canonical schema
            sn = _get_schema().nodes[i]
            x, y = round(sn.x, 6), round(sn.y, 6)

        nodes.append({
            "index": i, "x": x, "y": y,
            "color": color, "region": meta["region"],
            "source_point": meta["source_point"], "alias": meta["alias"],
        })

    # Typed edges
    typed_edges = []
    for a, b, etype in edges:
        typed_edges.append({
            "a": min(a, b), "b": max(a, b), "type": etype,
        })

    # Arc definitions — pre-resolved from schema via DEFAULT_ARC_SEGMENTS
    arc_defs = []
    for seg in arc_segs:
        if "_cx" in seg:
            # Pre-resolved from schema (default path)
            arc_defs.append({
                "cx": seg["_cx"], "cy": seg["_cy"], "radius": seg["_radius"],
                "start_angle": round(seg["start_angle"], 6),
                "end_angle": round(seg["end_angle"], 6),
                "color": seg["color"], "source_shape": seg["source_shape"],
            })
        else:
            # Legacy path: resolve from field shapes
            shape = fs[seg["source_shape"]]
            arc_defs.append({
                "cx": shape["center"]["x"], "cy": shape["center"]["y"],
                "radius": shape["radius"],
                "start_angle": round(seg["start_angle"], 6),
                "end_angle": round(seg["end_angle"], 6),
                "color": seg["color"], "source_shape": seg["source_shape"],
            })

    # Flat edges for backward compatibility
    flat_edges = [(e["a"], e["b"]) for e in typed_edges]

    return {
        "_meta": {"name": "projection",
                  "description": f"Plane B: {len(nodes)} nodes, {len(typed_edges)} edges, "
                                 f"{len(arc_defs)} arcs. Grid + IS + bump nib."},
        "nodes": nodes,
        "edges": flat_edges,
        "typed_edges": typed_edges,
        "junction_index": role_spec["junction_index"],
        "arc_definitions": arc_defs,
        "provenance": {
            "field_points_total": len(fp), "field_shapes_total": len(fs),
            "nodes_selected": len(nodes),
            "selection_ratio": round(len(nodes) / len(fp), 4),
        },
    }


def write_projection(field):
    data = project(field)
    out = Path(__file__).parent / "build"
    out.mkdir(exist_ok=True)
    p = out / "projection.json"
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    return p


def main() -> int:
    fp = Path(__file__).parent / "build" / "point_field.json"
    if not fp.exists():
        print("ERROR: build/point_field.json not found.", file=sys.stderr)
        return 1
    with open(fp) as f:
        field = json.load(f)
    out = write_projection(field)
    with open(out) as f:
        proj = json.load(f)
    prov = proj["provenance"]
    print(f"projection.json written to {out}")
    print(f"  Field: {prov['field_points_total']} points, {prov['field_shapes_total']} shapes")
    print(f"  Selected: {prov['nodes_selected']} nodes ({prov['selection_ratio']*100:.1f}%)")
    print(f"  Edges: {len(proj['typed_edges'])}  Arcs: {len(proj['arc_definitions'])}")

    from collections import Counter
    etype_counts = Counter(e["type"] for e in proj["typed_edges"])
    print(f"  Edge types: {dict(etype_counts)}")
    print(f"  Junction: node {proj['junction_index']}")
    print()
    for n in proj["nodes"]:
        alias = f" ({n['alias']})" if n.get("alias") else ""
        print(f"    N{n['index']:2d} ← {n['source_point']:35s}  ({n['x']:8.4f}, {n['y']:8.4f})  {n['color']}{alias}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
