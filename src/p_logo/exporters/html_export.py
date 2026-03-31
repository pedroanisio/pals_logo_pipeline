"""
HTML export — generate standalone animated HTML from PLogoSchema.

The geometry (nodes, edges, arcs, nib) is serialized to JSON and
injected into an HTML template containing all Three.js rendering logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from p_logo.types import PLogoSchema


# ── Node color rules ──────────────────────────────────────────
# Applied in order; first match wins.
# Each rule is (predicate_fn, color_key).

def _is_nib_tip(node) -> bool:
    return node.composition_point == "P.CIRC.RECT.V.CENTER"

def _is_corner_accent(node) -> bool:
    return node.composition_point == "P.SQAB.UL" and not node.key_node

def _is_bump_hub(node) -> bool:
    return node.composition_point == "P.BUMP.HUB"

def _is_arc_anchor(node) -> bool:
    if not node.key_node:
        return False
    bronze_points = {
        "P.CA.TANGENT.BOTTOM", "P.CA.TANGENT.RIGHT",
        "P.RECT.LR", "P.RECT.UR",
    }
    return node.composition_point in bronze_points

def _is_key(node) -> bool:
    return node.key_node


_COLOR_RULES = [
    (_is_nib_tip,       "WARMWHT"),
    (_is_corner_accent, "BLUEGLOW"),
    (_is_bump_hub,      "AMBER"),
    (_is_arc_anchor,    "BRONZE"),
    (_is_key,           "AMBER"),
]
_DEFAULT_COLOR = "COPPER"


def _resolve_node_color(node) -> str:
    """Apply color rules to a node, return the color key string."""
    for predicate, color in _COLOR_RULES:
        if predicate(node):
            return color
    return _DEFAULT_COLOR


# ── Arc style config ──────────────────────────────────────────

_ARC_STYLES = [
    {"color": "AMBER",  "opacity": 0.7},   # Green arc → Amber
    {"color": "COPPER", "opacity": 0.6},   # Blue arc  → Copper
    {"color": "BRONZE", "opacity": 0.55},  # Gold arc  → Bronze
]


# ── Schema → JS data ─────────────────────────────────────────

def schema_to_js_data(schema: PLogoSchema) -> dict:
    """
    Convert PLogoSchema to a JSON-serializable dict for HTML injection.

    Returns dict with keys: wireNodes, wireEdges, arcDefs, nib.
    Color assignments use string keys (resolved to THREE.Color in the template).
    """

    # Nodes
    wire_nodes = []
    for node in schema.nodes:
        col = _resolve_node_color(node)
        # N24 (bump hub) is key_node=False in schema but sz=1 in revision HTML
        sz = 1 if node.key_node or node.composition_point == "P.BUMP.HUB" else 0
        wire_nodes.append({
            "x": node.x,
            "y": node.y,
            "col": col,
            "sz": sz,
        })

    # Edges
    wire_edges = [[e.from_id, e.to_id] for e in schema.edges]

    # Arcs
    arc_defs = []
    for i, arc in enumerate(schema.arcs):
        style = _ARC_STYLES[i]
        arc_defs.append({
            "cx": arc.cx,
            "cy": arc.cy,
            "r": arc.radius,
            "startAngle": arc.start_angle,
            "sweep": arc.sweep_angle,
            "color": style["color"],
            "opacity": style["opacity"],
        })

    # Nib
    nib = schema.nib
    waist_y = nib.outline[1][1]  # right shoulder y = Circ.Rect.I top
    nib_data = {
        "tipY": nib.outline[0][1],
        "topY": waist_y,
        "cx": nib.ball_pos[0],
        "left": nib.outline[3][0],   # left shoulder x
        "right": nib.outline[1][0],  # right shoulder x
        "ctrY": nib.ball_pos[1],
        "outline": [list(p) for p in nib.outline],
        "slitStart": list(nib.slit_start),
        "slitEnd": list(nib.slit_end),
        "ballPos": list(nib.ball_pos),
    }

    return {
        "wireNodes": wire_nodes,
        "wireEdges": wire_edges,
        "arcDefs": arc_defs,
        "nib": nib_data,
    }


def export_html(
    schema: PLogoSchema,
    output_path: str,
    template: str = "animated_revision",
    style: dict | None = None,
) -> str:
    """
    Generate a standalone animated HTML file from schema + template.

    Args:
        schema: The PLogoSchema to inject
        output_path: Where to write the HTML
        template: Template name (looks in templates/ directory)
        style: Optional style overrides (reserved for future use)

    Returns:
        The generated HTML string
    """
    templates_dir = Path(__file__).parent / "templates"
    template_path = templates_dir / f"{template}.html"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_html = template_path.read_text(encoding="utf-8")
    data = schema_to_js_data(schema)

    # Inject JSON into placeholders
    replacements = {
        "/* __WIRE_NODES__ */[]": json.dumps(data["wireNodes"], indent=4),
        "/* __WIRE_EDGES__ */[]": json.dumps(data["wireEdges"]),
        "/* __ARC_DEFS__ */[]": json.dumps(data["arcDefs"], indent=4),
        "/* __NIB_DATA__ */{}": json.dumps(data["nib"], indent=4),
    }

    html = template_html
    for placeholder, replacement in replacements.items():
        html = html.replace(placeholder, replacement)

    # Add generation header after <!DOCTYPE html>
    header = (
        f"<!-- GENERATED by p_logo/exporters/html_export.py — DO NOT EDIT geometry sections.\n"
        f"     Schema: {schema.node_count} nodes, {schema.edge_count} edges, {len(schema.arcs)} arcs.\n"
        f"     Regenerate: from p_logo import build_schema; "
        f"from p_logo.exporters.html_export import export_html; "
        f"export_html(build_schema(), '{Path(output_path).name}') -->\n"
    )
    html = html.replace("<!DOCTYPE html>\n", f"<!DOCTYPE html>\n{header}", 1)

    Path(output_path).write_text(html, encoding="utf-8")
    return html
