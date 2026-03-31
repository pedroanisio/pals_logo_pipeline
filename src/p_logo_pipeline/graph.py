"""
PAL's Notes Logo Pipeline — Step 1: Graph

Thin consumer of the projection (Plane B). All node positions originate
from the point field (Plane A) via projection.py's selection. Graph.py
adds adjacency computation, degree stats, and palette-derived sizing.

Data flow: point_field.py → projection.py → graph.py

Input:  build/palette.json, build/projection.json
Output: build/graph.json
"""

from __future__ import annotations

import json, math, sys
from collections import Counter
from pathlib import Path
from typing import Any


def _build_adjacency(n: int, edges: list[tuple[int, int] | list[int]]) -> dict[str, list[int]]:
    adj: dict[str, list[int]] = {str(i): [] for i in range(n)}
    for e in edges:
        a, b = e[0], e[1]
        adj[str(a)].append(b)
        adj[str(b)].append(a)
    for k in adj:
        adj[k].sort()
    return adj


def _compute_degrees(n: int, adj: dict[str, list[int]]) -> list[int]:
    return [len(adj[str(i)]) for i in range(n)]


def _is_connected(n: int, adj: dict[str, list[int]]) -> bool:
    if n == 0: return True
    visited = set()
    queue = [0]
    visited.add(0)
    while queue:
        cur = queue.pop(0)
        for nb in adj[str(cur)]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return len(visited) == n


# ── Projection data (loaded once at import, cached) ──
_projection: dict[str, Any] | None = None


def _load_projection() -> dict[str, Any]:
    """Load projection.json once and cache it."""
    global _projection
    if _projection is None:
        p_path = Path(__file__).parent / "build" / "projection.json"
        with open(p_path) as f:
            _projection = json.load(f)
    return _projection


def _extract_from_projection(proj: dict) -> tuple[
    list[tuple[float, float]], list[tuple[int, int]], list[str], int
]:
    """Extract positions, edges, colors, and junction index from projection data."""
    nodes = sorted(proj["nodes"], key=lambda n: n["index"])
    positions = [(n["x"], n["y"]) for n in nodes]
    edges = [(e[0], e[1]) for e in proj["edges"]]
    colors = [n["color"] for n in nodes]
    junction = proj["junction_index"]
    return positions, edges, colors, junction


# Public module-level constants (consumed by test_graph.py, validate, build_graph)
_proj_data = _load_projection()
NODE_POSITIONS, EDGES, NODE_COLORS, JUNCTION_NODE_INDEX = _extract_from_projection(_proj_data)


def validate(palette: dict) -> list[str]:
    errors: list[str] = []
    n, e = len(NODE_POSITIONS), len(EDGES)
    if n != 25: errors.append(f"Expected 25 nodes, found {n}")
    if e != 44: errors.append(f"Expected 44 edges, found {e}")
    if len(NODE_COLORS) != n:
        errors.append(f"NODE_COLORS length {len(NODE_COLORS)} != {n}")
    for i, (a, b) in enumerate(EDGES):
        if a < 0 or a >= n: errors.append(f"Edge {i}: a={a} out of range")
        if b < 0 or b >= n: errors.append(f"Edge {i}: b={b} out of range")
        if a == b: errors.append(f"Edge {i}: self-loop")
    seen = set()
    for i, (a, b) in enumerate(EDGES):
        pair = (min(a, b), max(a, b))
        if pair in seen: errors.append(f"Edge {i}: duplicate {pair}")
        seen.add(pair)
    adj = _build_adjacency(n, EDGES)
    if not _is_connected(n, adj): errors.append("Graph is not connected")
    degrees = _compute_degrees(n, adj)
    if JUNCTION_NODE_INDEX < n:
        jd = degrees[JUNCTION_NODE_INDEX]
        if jd != 6: errors.append(f"Junction degree {jd}, expected 6")
        if jd != max(degrees): errors.append(f"Junction not max degree")
    palette_colors = set(palette.get("colors", {}).keys())
    for i, color in enumerate(NODE_COLORS):
        if color not in palette_colors:
            errors.append(f"Node {i}: color '{color}' not in palette")
    for i, (x, y) in enumerate(NODE_POSITIONS):
        if not (math.isfinite(x) and math.isfinite(y)):
            errors.append(f"Node {i}: non-finite ({x}, {y})")
    return errors


def build_graph(palette: dict) -> dict[str, Any]:
    n = len(NODE_POSITIONS)
    adj = _build_adjacency(n, EDGES)
    degrees = _compute_degrees(n, adj)
    # Canonical degree-based node radii (from node_colors.py √2-chain)
    from p_logo.exporters.node_colors import node_core_radius
    from p_logo.schema import DEFAULT_R_GREEN
    r_green = DEFAULT_R_GREEN

    nodes = []
    for i, (x, y) in enumerate(NODE_POSITIONS):
        nodes.append({
            "index": i, "x": x, "y": y,
            "color": NODE_COLORS[i],
            "radius": round(node_core_radius(r_green, degrees[i]), 6),
            "degree": degrees[i],
        })

    # Typed edges from cached projection (no redundant file read)
    proj = _load_projection()
    typed_edges_raw = proj.get("typed_edges", [])

    # Build edge type lookup
    edge_type_map = {}
    for te in typed_edges_raw:
        key = (min(te["a"], te["b"]), max(te["a"], te["b"]))
        edge_type_map[key] = te["type"]

    edges = []
    for a, b in EDGES:
        key = (min(a, b), max(a, b))
        etype = edge_type_map.get(key, "mesh")
        edges.append({"a": a, "b": b, "color": "copper", "type": etype})

    return {
        "_meta": {
            "step": 1, "name": "graph",
            "description": "Wireframe P — 25 nodes, 44 edges. "
                           "All positions from Plane A → Plane B projection.",
            "version": "3.0",
        },
        "nodes": nodes,
        "edges": edges,
        "adjacency": adj,
        "edge_thickness": palette["sizing"]["edge_thickness"],
        "edge_opacity": palette["opacity_defaults"]["edge"]["base"],
        "stats": {
            "node_count": n,
            "edge_count": len(EDGES),
            "avg_degree": round(sum(degrees) / n, 4),
            "max_degree": max(degrees),
            "junction_index": JUNCTION_NODE_INDEX,
        },
    }


def write_graph(palette: dict) -> Path:
    data = build_graph(palette)
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "graph.json"
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
        print("GRAPH VALIDATION FAILED:", file=sys.stderr)
        for e in errors: print(f"  ✗ {e}", file=sys.stderr)
        return 1
    out_path = write_graph(palette)
    with open(out_path) as f:
        g = json.load(f)
    s = g["stats"]
    print(f"graph.json written to {out_path}")
    print(f"  Source: projection.json (Plane A → Plane B)")
    print(f"  Nodes: {s['node_count']}  Edges: {s['edge_count']}  "
          f"Avg deg: {s['avg_degree']:.4f}  Max deg: {s['max_degree']} (node {s['junction_index']})")
    print(f"  Degree dist: {dict(sorted(Counter(n['degree'] for n in g['nodes']).items()))}")
    print(f"  Color dist:  {dict(sorted(Counter(n['color'] for n in g['nodes']).items()))}")
    print("  Validation: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
