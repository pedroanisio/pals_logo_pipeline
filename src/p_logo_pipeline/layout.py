"""
PAL's Notes Logo Pipeline — Step 4: Layout

Composes graph, nib, and arcs into a single coordinate space. Applies
a vertical centering offset, computes the bounding box, validates that
nothing clips outside the ring, assigns z-ordering, and produces a flat
element list for the renderer.

Input:  build/palette.json, build/graph.json, build/nib.json, build/arcs.json
Output: build/layout.json
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Z-ordering constants
# ──────────────────────────────────────────────

Z_EDGE          = 0.20
Z_ARC_BLOOM     = 0.28
Z_ARC_MAIN      = 0.32
Z_RUNNER_PATH   = 0.34
Z_NODE          = 0.40
Z_NIB_FAN       = 0.50
Z_NIB_OUTLINE   = 0.51
Z_NIB_CENTER    = 0.52
Z_NIB_ACCENT    = 0.55
Z_JUNCTION_BALL = 0.60
Z_INK_ORIGIN    = 0.50


# ──────────────────────────────────────────────
# Centering
# ──────────────────────────────────────────────

def _compute_center_offset(
    graph: dict, nib: dict
) -> dict[str, float]:
    """Compute the offset needed to vertically center the full composition
    (graph + nib) within the ring.

    The nib extends below the graph's lowest node. We find the vertical
    extents of all geometry and compute the offset that centers the
    midpoint at y=0. X offset is 0 (the composition is already
    horizontally positioned by design).
    """
    # Collect all Y values
    ys = [n["y"] for n in graph["nodes"]]
    ys.append(nib["ink_origin"]["y"])
    ys.append(nib["junction_ball"]["y"])
    for line in nib["fan_lines"]:
        ys.extend([line["y1"], line["y2"]])
    for node in nib["accent_nodes"]:
        ys.append(node["y"])

    min_y = min(ys)
    max_y = max(ys)
    mid_y = (min_y + max_y) / 2

    return {"x": 0.0, "y": -mid_y}


# ──────────────────────────────────────────────
# Element builders
# ──────────────────────────────────────────────

def _offset_xy(x: float, y: float, co: dict) -> tuple[float, float]:
    return (x + co["x"], y + co["y"])


def _build_node_elements(
    graph: dict, co: dict
) -> list[dict[str, Any]]:
    elements = []
    for node in graph["nodes"]:
        x, y = _offset_xy(node["x"], node["y"], co)
        elements.append({
            "type": "node",
            "index": node["index"],
            "x": x,
            "y": y,
            "color": node["color"],
            "radius": node["radius"],
            "degree": node["degree"],
            "z": Z_NODE,
        })
    return elements


def _build_edge_elements(
    graph: dict, co: dict
) -> list[dict[str, Any]]:
    elements = []
    nodes = graph["nodes"]
    for edge in graph["edges"]:
        ax, ay = _offset_xy(nodes[edge["a"]]["x"], nodes[edge["a"]]["y"], co)
        bx, by = _offset_xy(nodes[edge["b"]]["x"], nodes[edge["b"]]["y"], co)
        elements.append({
            "type": "edge",
            "a": edge["a"],
            "b": edge["b"],
            "x1": ax, "y1": ay,
            "x2": bx, "y2": by,
            "color": edge["color"],
            "edge_type": edge.get("type", "mesh"),
            "thickness": graph["edge_thickness"],
            "opacity": graph["edge_opacity"],
            "z": Z_EDGE,
        })
    return elements


def _build_arc_elements(
    arcs: dict, co: dict
) -> list[dict[str, Any]]:
    elements = []
    for arc in arcs["arcs"]:
        offset_points = []
        for pt in arc["points"]:
            px, py = _offset_xy(pt["x"], pt["y"], co)
            offset_pt = dict(pt)
            offset_pt["x"] = px
            offset_pt["y"] = py
            offset_points.append(offset_pt)

        cx, cy = _offset_xy(arc["cx"], arc["cy"], co)
        elements.append({
            "type": "arc",
            "index": arc["index"],
            "cx": cx,
            "cy": cy,
            "radius": arc["radius"],
            "color": arc["color"],
            "points": offset_points,
            "main_thickness": arc["main_thickness"],
            "bloom_thickness": arc["bloom_thickness"],
            "main_opacity": arc["main_opacity"],
            "bloom_opacity": arc["bloom_opacity"],
            "z": Z_ARC_MAIN,
        })
    return elements


def _build_runner_path_elements(
    arcs: dict, co: dict
) -> list[dict[str, Any]]:
    elements = []
    for rp in arcs["runner_paths"]:
        offset_points = []
        for pt in rp["points"]:
            px, py = _offset_xy(pt["x"], pt["y"], co)
            offset_pt = dict(pt)
            offset_pt["x"] = px
            offset_pt["y"] = py
            offset_points.append(offset_pt)

        elements.append({
            "type": "runner_path",
            "arc_index": rp["arc_index"],
            "color": rp["color"],
            "points": offset_points,
            "z": Z_RUNNER_PATH,
        })
    return elements


def _build_nib_line_elements(
    nib: dict, co: dict
) -> list[dict[str, Any]]:
    """Build fan, outline, and center line elements."""
    elements = []

    for line in nib["fan_lines"]:
        x1, y1 = _offset_xy(line["x1"], line["y1"], co)
        x2, y2 = _offset_xy(line["x2"], line["y2"], co)
        elements.append({
            "type": "nib_fan_line",
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "color": line["color"],
            "thickness": line["thickness"],
            "opacity": line["opacity"],
            "z": Z_NIB_FAN,
        })

    for line in nib["outline_lines"]:
        x1, y1 = _offset_xy(line["x1"], line["y1"], co)
        x2, y2 = _offset_xy(line["x2"], line["y2"], co)
        elements.append({
            "type": "nib_outline_line",
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "color": line["color"],
            "thickness": line["thickness"],
            "opacity": line["opacity"],
            "z": Z_NIB_OUTLINE,
        })

    cl = nib["center_line"]
    x1, y1 = _offset_xy(cl["x1"], cl["y1"], co)
    x2, y2 = _offset_xy(cl["x2"], cl["y2"], co)
    elements.append({
        "type": "nib_center_line",
        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "color": cl["color"],
        "thickness": cl["thickness"],
        "opacity": cl["opacity"],
        "z": Z_NIB_CENTER,
    })

    return elements


def _build_nib_node_elements(
    nib: dict, co: dict
) -> list[dict[str, Any]]:
    """Build accent node and junction ball elements."""
    elements = []

    for node in nib["accent_nodes"]:
        x, y = _offset_xy(node["x"], node["y"], co)
        elements.append({
            "type": "nib_accent_node",
            "x": x, "y": y,
            "color": node["color"],
            "radius": node["radius"],
            "z": Z_NIB_ACCENT,
        })

    jb = nib["junction_ball"]
    x, y = _offset_xy(jb["x"], jb["y"], co)
    elements.append({
        "type": "junction_ball",
        "x": x, "y": y,
        "radius": jb["radius"],
        "color": jb["color"],
        "opacity": jb["opacity"],
        "glow_size": jb["glow_size"],
        "glow_color": jb.get("glow_color", jb["color"]),
        "glow_opacity": jb.get("glow_opacity", 0.3),
        "bloom_size": jb["bloom_size"],
        "bloom_color": jb.get("bloom_color", jb["color"]),
        "bloom_opacity": jb.get("bloom_opacity", 0.1),
        "z": Z_JUNCTION_BALL,
    })

    return elements


def _build_nib_ink_element(
    nib: dict, co: dict
) -> dict[str, Any]:
    """Build the ink origin element."""
    io = nib["ink_origin"]
    x, y = _offset_xy(io["x"], io["y"], co)
    return {
        "type": "ink_origin",
        "x": x, "y": y,
        "z": Z_INK_ORIGIN,
    }


def _build_nib_elements(
    nib: dict, co: dict
) -> list[dict[str, Any]]:
    elements = _build_nib_line_elements(nib, co)
    elements.extend(_build_nib_node_elements(nib, co))
    elements.append(_build_nib_ink_element(nib, co))
    return elements


def _build_ring(palette: dict) -> dict[str, Any]:
    """Build ring band definitions from palette sizing."""
    rr = palette["sizing"]["ring_radii"]
    opacities = palette["opacity_defaults"]["ring"]

    bands = [
        {"inner_r": rr["inner_inner"], "outer_r": rr["inner_outer"],
         "opacity": opacities["inner"]},
        {"inner_r": rr["mid_inner"], "outer_r": rr["mid_outer"],
         "opacity": opacities["mid_inner"]},
        {"inner_r": rr["mid2_inner"], "outer_r": rr["mid2_outer"],
         "opacity": opacities["mid_outer"]},
        {"inner_r": rr["outer_inner"], "outer_r": rr["outer_outer"],
         "opacity": opacities["outer"]},
    ]

    return {
        "bands": bands,
        "color": "rose_gold",
        "fill_radius": palette["sizing"]["circle_fill_radius"],
        "fill_color": "deep",
    }


# ──────────────────────────────────────────────
# Bounding box
# ──────────────────────────────────────────────

def _compute_bounding_box(elements: list[dict]) -> dict[str, float]:
    xs: list[float] = []
    ys: list[float] = []

    for el in elements:
        if "x" in el and "y" in el:
            xs.append(el["x"])
            ys.append(el["y"])
        if "x1" in el:
            xs.extend([el["x1"], el["x2"]])
            ys.extend([el["y1"], el["y2"]])
        if "points" in el:
            for pt in el["points"]:
                xs.append(pt["x"])
                ys.append(pt["y"])

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
    }


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate(
    palette: dict, graph: dict, nib: dict, arcs: dict
) -> list[str]:
    errors: list[str] = []

    # Check upstream meta steps
    if graph.get("_meta", {}).get("step") != 1:
        errors.append("graph._meta.step != 1")
    if nib.get("_meta", {}).get("step") != 2:
        errors.append("nib._meta.step != 2")
    if arcs.get("_meta", {}).get("step") != 3:
        errors.append("arcs._meta.step != 3")

    # Check required keys
    if "nodes" not in graph:
        errors.append("graph missing 'nodes'")
    if "edges" not in graph:
        errors.append("graph missing 'edges'")
    if "fan_lines" not in nib:
        errors.append("nib missing 'fan_lines'")
    if "arcs" not in arcs:
        errors.append("arcs missing 'arcs'")

    # Ring fit: quick check that graph nodes fit
    ring_r = palette["sizing"]["ring_radii"]["outer_outer"]
    co = _compute_center_offset(graph, nib)
    for node in graph.get("nodes", []):
        x, y = _offset_xy(node["x"], node["y"], co)
        dist = math.sqrt(x**2 + y**2)
        if dist >= ring_r:
            errors.append(
                f"Node {node['index']} at ({x:.2f},{y:.2f}) dist={dist:.2f} "
                f"outside ring r={ring_r}"
            )

    return errors


# ──────────────────────────────────────────────
# Main builder
# ──────────────────────────────────────────────

def build_layout(
    palette: dict, graph: dict, nib: dict, arcs: dict
) -> dict[str, Any]:
    co = _compute_center_offset(graph, nib)

    # Build all elements
    elements: list[dict[str, Any]] = []
    elements.extend(_build_edge_elements(graph, co))
    elements.extend(_build_arc_elements(arcs, co))
    elements.extend(_build_runner_path_elements(arcs, co))
    elements.extend(_build_node_elements(graph, co))
    elements.extend(_build_nib_elements(nib, co))

    # Bounding box
    bb = _compute_bounding_box(elements)

    # Inventory
    type_counts = Counter(el["type"] for el in elements)
    inventory = dict(sorted(type_counts.items()))

    # Ring
    ring = _build_ring(palette)

    # Upstream references
    nib_lines = (len(nib["fan_lines"]) + len(nib["outline_lines"]) + 1)  # +1 center
    upstream = {
        "graph": 1,
        "nib": 2,
        "arcs": 3,
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"]),
        "nib_lines": nib_lines,
        "arc_count": len(arcs["arcs"]),
    }

    return {
        "_meta": {
            "step": 4,
            "name": "layout",
            "description": "Composed layout — all geometry in a single coordinate "
                           "space with centering, ring, and z-ordering.",
            "version": "1.0",
        },
        "center_offset": co,
        "bounding_box": bb,
        "ring": ring,
        "elements": elements,
        "inventory": inventory,
        "upstream": upstream,
    }


# ──────────────────────────────────────────────
# File writer
# ──────────────────────────────────────────────

def write_layout(
    palette: dict, graph: dict, nib: dict, arcs: dict
) -> Path:
    layout_data = build_layout(palette, graph, nib, arcs)

    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "layout.json"

    with open(out_path, "w") as f:
        json.dump(layout_data, f, indent=2)

    return out_path


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def main() -> int:
    build_dir = Path(__file__).parent / "build"

    # Load all upstream artifacts
    required = {
        "palette.json": None,
        "graph.json": None,
        "nib.json": None,
        "arcs.json": None,
    }
    for name in required:
        path = build_dir / name
        if not path.exists():
            print(f"ERROR: {path} not found. Run upstream steps first.",
                  file=sys.stderr)
            return 1
        with open(path) as f:
            required[name] = json.load(f)

    palette = required["palette.json"]
    graph = required["graph.json"]
    nib = required["nib.json"]
    arcs = required["arcs.json"]

    errors = validate(palette, graph, nib, arcs)
    if errors:
        print("LAYOUT VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    out_path = write_layout(palette, graph, nib, arcs)

    with open(out_path) as f:
        layout = json.load(f)

    co = layout["center_offset"]
    bb = layout["bounding_box"]
    print(f"layout.json written to {out_path}")
    print(f"  Center offset:  ({co['x']:.3f}, {co['y']:.3f})")
    print(f"  Bounding box:   x=[{bb['min_x']:.2f}, {bb['max_x']:.2f}]  "
          f"y=[{bb['min_y']:.2f}, {bb['max_y']:.2f}]")
    print(f"  Ring:           {len(layout['ring']['bands'])} bands, "
          f"fill_r={layout['ring']['fill_radius']}")
    print(f"  Elements:       {len(layout['elements'])} total")
    print(f"  Inventory:      {layout['inventory']}")
    print(f"  Upstream:       {layout['upstream']}")
    print("  Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
