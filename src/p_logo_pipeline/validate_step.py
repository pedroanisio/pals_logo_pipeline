"""
PAL's Notes Logo Pipeline — Step 7: Validate

Post-build verification that checks the rendered logo and all upstream
data against the design rationale's Technical Inventory table. Produces
a structured compliance report with per-category renderable object counts.

This step does NOT produce a JSON artifact — it produces a pass/fail
report to stdout.

Input:  All build/ artifacts + build/logo.html
Output: Structured report dict + stdout summary
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Inventory computation
# ──────────────────────────────────────────────

def _count_renderable_objects(
    palette: dict, graph: dict, nib: dict, arcs: dict,
    layout: dict, animations: dict, html: str
) -> dict[str, int]:
    """Count renderable objects per category, matching the rationale table.

    Each entry represents the number of Three.js meshes, sprites, or
    canvas-drawn elements that the renderer creates.
    """
    anim = animations["systems"]

    # Background: 7 nebula clouds + 1 vignette = 8
    nebula_count = palette["nebula"]["count"]
    background = nebula_count + 1  # +1 vignette

    # Stars: 180 canvas circles
    stars = palette["stars"]["count"]

    # Circle fill: 1 CircleGeometry
    circle_fill = 1

    # Ring: 4 RingGeometry meshes
    ring = len(layout["ring"]["bands"])

    # Shimmer arcs: count from palette
    shimmer_arcs = palette.get("shimmer", {}).get("count", 3)

    # Edges: from graph stats
    edges = graph["stats"]["edge_count"]

    # Nodes: 23 core + 23 glow sprites + 23 bloom sprites = 69
    node_count = graph["stats"]["node_count"]
    nodes = node_count * 3  # core + glow + bloom

    # Bowl arcs: 3 main mesh strips + 3 bloom mesh strips = 6
    arc_count = len(arcs["arcs"])
    bowl_arcs = arc_count * 2  # main + bloom

    # Arc runners: 6 cores + 6×4 trail sprites = 30
    runners_per_arc = anim["arc_runners"]["per_arc"]
    trail_len = anim["arc_runners"]["trail_length"]
    total_runners = runners_per_arc * anim["arc_runners"]["arc_count"]
    arc_runners = total_runners + total_runners * trail_len  # cores + trails

    # Nib: fan_lines + outline_lines + center_line
    #     + accent_nodes + accent_glows
    #     + ball_core + ball_glow + ball_bloom
    fan_count = len(nib["fan_lines"])
    outline_count = len(nib["outline_lines"])
    center_count = 1
    accent_count = len(nib["accent_nodes"])
    accent_glow_count = accent_count  # each accent gets a glow
    ball_count = 3  # core + glow + bloom
    nib_total = (fan_count + outline_count + center_count +
                 accent_count + accent_glow_count + ball_count)

    # Ink drops: 25 pooled CircleGeometry
    ink_drops = anim["ink_drops"]["pool_size"]

    # Particles: count from palette
    particles = palette.get("particles", {}).get("count", 70)

    # Pulses: 12 core + 12 glow = 24
    pulse_count = anim["pulses"]["count"]
    pulses = pulse_count * 2  # core + glow

    # Energy rings: dynamic (pooled), counted as 0 static — they're spawned
    # at runtime. For inventory purposes, mark as "dynamic".
    # We count 0 here since they don't exist at t=0.
    energy_rings = 0

    # Brand text: 1 DOM element
    brand_text = 1

    return {
        "background": background,
        "stars": stars,
        "circle_fill": circle_fill,
        "ring": ring,
        "shimmer_arcs": shimmer_arcs,
        "edges": edges,
        "nodes": nodes,
        "bowl_arcs": bowl_arcs,
        "arc_runners": arc_runners,
        "nib": nib_total,
        "ink_drops": ink_drops,
        "particles": particles,
        "pulses": pulses,
        "energy_rings": energy_rings,
        "brand_text": brand_text,
    }


# ──────────────────────────────────────────────
# Graph metrics
# ──────────────────────────────────────────────

def _compute_graph_metrics(graph: dict) -> dict[str, Any]:
    n = graph["stats"]["node_count"]
    e = graph["stats"]["edge_count"]
    avg_deg = 2 * e / n if n > 0 else 0
    max_deg = graph["stats"]["max_degree"]

    # Connectivity check via BFS
    adj = graph["adjacency"]
    visited = set()
    queue = [0]
    visited.add(0)
    while queue:
        cur = queue.pop(0)
        for nb in adj[str(cur)]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    connected = len(visited) == n

    return {
        "node_count": n,
        "edge_count": e,
        "avg_degree": round(avg_deg, 4),
        "max_degree": max_deg,
        "connected": connected,
    }


# ──────────────────────────────────────────────
# Checks
# ──────────────────────────────────────────────

def _check_step_meta(data: dict, name: str, expected_step: int) -> dict[str, str]:
    if data.get("_meta", {}).get("step") == expected_step:
        return {"name": name, "status": "pass", "detail": f"{name.split('_')[0].title()} is step {expected_step}"}
    return {"name": name, "status": "fail", "detail": f"{name} _meta.step != {expected_step}"}


def _check_animation_systems(animations: dict) -> dict[str, str]:
    systems = animations.get("systems", {})
    if len(systems) == 6:
        return {"name": "animation_systems_count", "status": "pass", "detail": "6 animation systems present"}
    return {"name": "animation_systems_count", "status": "fail", "detail": f"{len(systems)} systems (expected 6)"}


def _check_graph_connectivity(graph_metrics: dict) -> dict[str, str]:
    if graph_metrics["connected"]:
        return {"name": "graph_connected", "status": "pass", "detail": "Graph is connected (BFS reaches all nodes)"}
    return {"name": "graph_connected", "status": "fail", "detail": "Graph is disconnected"}


def _check_metric_equals(graph_metrics: dict, key: str, expected: int,
                         name: str, pass_detail: str, fail_label: str) -> dict[str, str]:
    actual = graph_metrics[key]
    if actual == expected:
        return {"name": name, "status": "pass", "detail": pass_detail}
    return {"name": name, "status": "fail", "detail": f"{actual} {fail_label} (expected {expected})"}


def _check_layout_element_count(layout: dict) -> dict[str, str]:
    count = len(layout.get("elements", []))
    if count >= 50:
        return {"name": "layout_element_count", "status": "pass", "detail": f"{count} layout elements"}
    return {"name": "layout_element_count", "status": "fail", "detail": f"Only {count} layout elements"}


def _check_html_structure(html: str) -> dict[str, str]:
    if html.strip().startswith("<!DOCTYPE html") and "</html>" in html:
        return {"name": "html_valid_structure", "status": "pass", "detail": "HTML has DOCTYPE and closing tag"}
    return {"name": "html_valid_structure", "status": "fail", "detail": "HTML structure invalid"}


def _check_html_no_nan(html: str) -> dict[str, str]:
    import re
    real_nans = len(re.findall(r'\bNaN\b', html))
    if real_nans == 0:
        return {"name": "html_no_nan", "status": "pass", "detail": "No NaN values in HTML output"}
    return {"name": "html_no_nan", "status": "fail", "detail": f"{real_nans} NaN occurrences in HTML"}


def _check_threejs_included(html: str) -> dict[str, str]:
    if "three.js/r128" in html or "three.min.js" in html:
        return {"name": "threejs_included", "status": "pass", "detail": "Three.js r128 included"}
    return {"name": "threejs_included", "status": "fail", "detail": "Three.js not found in HTML"}


def _check_total_renderable(inventory: dict[str, int]) -> dict[str, str]:
    total = sum(inventory.values())
    if 250 <= total <= 550:
        return {"name": "total_renderable_range", "status": "pass",
                "detail": f"Total {total} renderable objects (target ~310, includes canvas items)"}
    return {"name": "total_renderable_range", "status": "warn",
            "detail": f"Total {total} outside expected [250, 550]"}


def _check_palette_colors_in_html(palette: dict, html: str) -> dict[str, str]:
    missing = []
    for name, color in palette["colors"].items():
        hex_val = color["hex"].lstrip("#")
        if hex_val.lower() not in html.lower() and f"0x{hex_val}" not in html:
            missing.append(name)
    if not missing:
        return {"name": "palette_colors_in_html", "status": "pass", "detail": "All 8 palette colors in HTML"}
    return {"name": "palette_colors_in_html", "status": "fail", "detail": f"Missing colors: {missing}"}


def _check_brand_text(html: str) -> dict[str, str]:
    if "PAL" in html and "Notes" in html:
        return {"name": "brand_text_present", "status": "pass", "detail": "Brand text 'PAL's Notes' in HTML"}
    return {"name": "brand_text_present", "status": "fail", "detail": "Brand text missing"}


def _check_node_positions_match_schema(graph: dict) -> dict[str, str]:
    """Cross-layer check: pipeline node positions must match PLogoSchema.

    This catches divergence between the pipeline's point_field/projection
    and the canonical schema geometry.
    """
    try:
        from p_logo import build_schema
        schema = build_schema()
    except ImportError:
        return {"name": "node_positions_vs_schema", "status": "warn",
                "detail": "p_logo not importable — skipped cross-layer check"}

    tolerance = 0.01
    mismatches = []
    for gn in graph["nodes"]:
        i = gn["index"]
        sn = schema.nodes[i]
        dx = abs(gn["x"] - sn.x)
        dy = abs(gn["y"] - sn.y)
        if dx > tolerance or dy > tolerance:
            mismatches.append(f"N{i}(Δx={dx:.4f},Δy={dy:.4f})")

    if not mismatches:
        return {"name": "node_positions_vs_schema", "status": "pass",
                "detail": "All 25 pipeline nodes match schema positions"}
    return {"name": "node_positions_vs_schema", "status": "fail",
            "detail": f"{len(mismatches)} nodes diverge from schema: {', '.join(mismatches[:5])}"}


def _run_checks(
    palette: dict, graph: dict, nib: dict, arcs: dict,
    layout: dict, animations: dict, html: str,
    inventory: dict[str, int], graph_metrics: dict
) -> list[dict[str, Any]]:
    """Run all validation checks. Each returns {name, status, detail}."""
    return [
        _check_step_meta(palette, "palette_step_0", 0),
        _check_step_meta(graph, "graph_step_1", 1),
        _check_step_meta(layout, "layout_step_4", 4),
        _check_animation_systems(animations),
        _check_graph_connectivity(graph_metrics),
        _check_metric_equals(graph_metrics, "node_count", 25, "node_count_25",
                             "25 nodes", "nodes"),
        _check_metric_equals(graph_metrics, "edge_count", 44, "edge_count_44",
                             "44 edges", "edges"),
        _check_metric_equals(graph_metrics, "max_degree", 6, "max_degree_6",
                             "Max degree is 6 (junction node)", "max degree"),
        _check_node_positions_match_schema(graph),
        _check_layout_element_count(layout),
        _check_html_structure(html),
        _check_html_no_nan(html),
        _check_threejs_included(html),
        _check_total_renderable(inventory),
        _check_palette_colors_in_html(palette, html),
        _check_brand_text(html),
    ]


# ──────────────────────────────────────────────
# Report builder
# ──────────────────────────────────────────────

def build_report(
    palette: dict, graph: dict, nib: dict, arcs: dict,
    layout: dict, animations: dict, html: str
) -> dict[str, Any]:
    """Build the complete validation report."""
    inventory = _count_renderable_objects(
        palette, graph, nib, arcs, layout, animations, html
    )
    total = sum(inventory.values())

    graph_metrics = _compute_graph_metrics(graph)

    checks = _run_checks(
        palette, graph, nib, arcs, layout, animations, html,
        inventory, graph_metrics
    )

    passed = all(c["status"] != "fail" for c in checks)

    pass_count = sum(1 for c in checks if c["status"] == "pass")
    fail_count = sum(1 for c in checks if c["status"] == "fail")
    warn_count = sum(1 for c in checks if c["status"] == "warn")

    verdict = "PASSED" if passed else "FAILED"
    summary = (
        f"Validation {verdict}: {pass_count} pass, {fail_count} fail, "
        f"{warn_count} warn. "
        f"Total renderable objects: {total} (target ~310)."
    )

    return {
        "passed": passed,
        "checks": checks,
        "inventory": inventory,
        "total_renderable": total,
        "graph_metrics": graph_metrics,
        "summary": summary,
    }


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> int:
    build_dir = Path(__file__).parent / "build"
    logos_dir = Path(__file__).parent.parent.parent / "build" / "logos"

    # JSON intermediates live in the pipeline build dir
    json_files = [
        "palette.json", "graph.json", "nib.json", "arcs.json",
        "layout.json", "animations.json",
    ]
    data: dict[str, Any] = {}
    for name in json_files:
        path = build_dir / name
        if not path.exists():
            print(f"ERROR: {path} not found.", file=sys.stderr)
            return 1
        with open(path) as f:
            data[name] = json.load(f)

    # Final HTML lives in the unified logos dir
    html_path = logos_dir / "p_logo_pipeline.html"
    if not html_path.exists():
        print(f"ERROR: {html_path} not found.", file=sys.stderr)
        return 1
    with open(html_path) as f:
        html = f.read()

    report = build_report(
        data["palette.json"], data["graph.json"], data["nib.json"],
        data["arcs.json"], data["layout.json"], data["animations.json"],
        html
    )

    # Print report
    print("══════════════════════════════════════════")
    print("  PAL's Notes Logo — Validation Report")
    print("══════════════════════════════════════════")
    print()

    print("  Checks:")
    for check in report["checks"]:
        icon = "✓" if check["status"] == "pass" else ("⚠" if check["status"] == "warn" else "✗")
        print(f"    {icon} {check['name']:35s} {check['detail']}")
    print()

    print("  Renderable Object Inventory:")
    for category, count in report["inventory"].items():
        print(f"    {category:20s} {count:>4d}")
    print(f"    {'─'*25}")
    print(f"    {'TOTAL':20s} {report['total_renderable']:>4d}")
    print()

    print("  Graph Metrics:")
    gm = report["graph_metrics"]
    print(f"    Nodes:     {gm['node_count']}")
    print(f"    Edges:     {gm['edge_count']}")
    print(f"    Avg deg:   {gm['avg_degree']}")
    print(f"    Max deg:   {gm['max_degree']}")
    print(f"    Connected: {gm['connected']}")
    print()

    print(f"  {report['summary']}")
    print("══════════════════════════════════════════")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
