"""SVG export — generates a clean vector SVG from PLogoSchema."""

from __future__ import annotations

import math
from pathlib import Path
from p_logo.types import PLogoSchema


# Edge-type visual properties: (stroke_width_factor, opacity)
EDGE_STYLES = {
    "contour": (0.10, 0.70),
    "mesh":    (0.04, 0.30),
    "struct":  (0.08, 0.55),
    "nib":     (0.06, 0.60),
}


def export_svg(
    schema: PLogoSchema,
    path: str,
    size: int = 2000,
    bg: str = "#000000",
    fg: str = "#ffffff",
    circle_r: float = 4.52,
    ring_r: float = 4.60,
) -> str:
    """
    Export PLogoSchema as a clean SVG file.

    The SVG uses a centered coordinate system mapped from the schema's
    P-logo coordinates into an SVG viewBox of [0, size].
    """
    canvas = 11.0
    cx_logo, cy_logo = 5.0, 5.0
    s_factor = circle_r / 4.55  # scale from schema coords to logo.py coords

    def to_svg(x: float, y: float) -> tuple[float, float]:
        lx = x * s_factor + cx_logo
        ly = y * s_factor + cy_logo
        sx = (lx + 0.5) / canvas * size
        sy = (canvas - 0.5 - ly) / canvas * size
        return sx, sy

    def r_to_svg(r: float) -> float:
        return r / canvas * size

    els: list[str] = []

    els.append('<?xml version="1.0" encoding="UTF-8"?>')
    els.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">')

    # Background
    els.append(f'  <rect width="{size}" height="{size}" fill="{bg}"/>')

    # Circle
    scx, scy = to_svg(0, 0)
    cr = r_to_svg(circle_r)
    fill = fg if bg == "#ffffff" else "#0a1929"
    els.append(f'  <circle cx="{scx:.1f}" cy="{scy:.1f}" r="{cr:.1f}" fill="{fill}"/>')

    # Ring
    rr = r_to_svg(ring_r)
    rw = r_to_svg(0.10)
    els.append(f'  <circle cx="{scx:.1f}" cy="{scy:.1f}" r="{rr:.1f}" '
               f'fill="none" stroke="{fg}" stroke-width="{rw:.1f}"/>')

    # Arcs (polyline approximation)
    for arc in schema.arcs:
        pts = []
        n_pts = 80
        for i in range(n_pts + 1):
            t = i / n_pts
            angle = arc.start_angle + t * arc.sweep_angle
            px = arc.cx + arc.radius * math.cos(angle)
            py = arc.cy + arc.radius * math.sin(angle)
            sx, sy = to_svg(px, py)
            pts.append(f"{sx:.1f},{sy:.1f}")
        els.append(f'  <polyline points="{" ".join(pts)}" '
                   f'fill="none" stroke="{fg}" stroke-width="4" '
                   f'stroke-opacity="0.12" stroke-linecap="round"/>')

    # Edges with type-based styling
    for edge in schema.edges:
        n1 = schema.node(edge.from_id)
        n2 = schema.node(edge.to_id)
        x1, y1 = to_svg(n1.x, n1.y)
        x2, y2 = to_svg(n2.x, n2.y)
        w_factor, opacity = EDGE_STYLES.get(edge.edge_type, (0.04, 0.30))
        w = r_to_svg(w_factor)
        els.append(f'  <line x1="{x1:.1f}" y1="{y1:.1f}" '
                   f'x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{fg}" stroke-width="{w:.1f}" '
                   f'stroke-opacity="{opacity}" stroke-linecap="round"/>')

    # Nib slit
    sx1, sy1 = to_svg(*schema.nib.slit_start)
    sx2, sy2 = to_svg(*schema.nib.slit_end)
    els.append(f'  <line x1="{sx1:.1f}" y1="{sy1:.1f}" '
               f'x2="{sx2:.1f}" y2="{sy2:.1f}" '
               f'stroke="{bg}" stroke-width="2" stroke-opacity="0.5"/>')

    # Nodes
    for node in schema.nodes:
        if node.id == 14:
            continue
        sx, sy = to_svg(node.x, node.y)
        sr = r_to_svg(0.14 if node.key_node else 0.09)
        opacity = "1.0" if node.key_node else "0.85"
        els.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
                   f'fill="{fg}" fill-opacity="{opacity}"/>')

    els.append('</svg>')

    svg_text = '\n'.join(els)
    Path(path).write_text(svg_text, encoding="utf-8")
    return svg_text
