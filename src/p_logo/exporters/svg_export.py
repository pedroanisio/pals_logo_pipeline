"""SVG export — generates a palette-driven vector SVG from PLogoSchema.

Produces a static SVG that mirrors the Three.js animated render's visual
hierarchy: colored nodes, multi-band ring, arc blooms, glow halos,
nebula clouds, star field, and nib detail — all derived from the shared
palette and color-resolution rules.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from p_logo.types import PLogoSchema
from p_logo.exporters.node_colors import (
    resolve_node_color,
    ARC_STYLES,
    COLOR_KEY_TO_PALETTE,
    EDGE_COLOR,
)
from p_logo_pipeline.palette import (
    COLORS,
    OPACITY_DEFAULTS,
    SIZING,
    NEBULA_SPECS,
    STAR_SPECS,
    SHIMMER_SPECS,
)


# ── Coordinate mapping ───────────────────────────────────────

_CANVAS = 11.0
_CX_LOGO = 5.0
_CY_LOGO = 5.0


def _make_transforms(circle_r: float, size: int):
    """Return (to_svg, r_to_svg) helpers for a given circle radius and SVG size."""
    s_factor = circle_r / 4.55

    def to_svg(x: float, y: float) -> tuple[float, float]:
        lx = x * s_factor + _CX_LOGO
        ly = y * s_factor + _CY_LOGO
        sx = (lx + 0.5) / _CANVAS * size
        sy = (_CANVAS - 0.5 - ly) / _CANVAS * size
        return sx, sy

    def r_to_svg(r: float) -> float:
        return r / _CANVAS * size

    return to_svg, r_to_svg


# ── Color helpers ────────────────────────────────────────────

def _hex(color_key: str) -> str:
    """Resolve a color key (e.g. 'AMBER') to a hex string."""
    palette_name = COLOR_KEY_TO_PALETTE[color_key]
    return COLORS[palette_name].hex


def _palette_hex(name: str) -> str:
    """Get hex directly from a palette color name."""
    return COLORS[name].hex


# ── Edge-type visual properties ──────────────────────────────

EDGE_STYLES: dict[str, tuple[float, float]] = {
    "contour": (0.10, 0.70),
    "mesh":    (0.04, 0.30),
    "struct":  (0.08, 0.55),
    "nib":     (0.06, 0.60),
}


# ── SVG element builders ────────────────────────────────────

def _build_defs(size: int, r_to_svg, to_svg, schema: PLogoSchema) -> list[str]:
    """Build <defs> section: gradients and filters."""
    els: list[str] = []
    els.append("  <defs>")

    # Gaussian blur filter for node glows
    blur_std = r_to_svg(0.25)
    els.append(f'    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">')
    els.append(f'      <feGaussianBlur stdDeviation="{blur_std:.1f}" result="blur"/>')
    els.append(f'    </filter>')

    # Larger blur for arc bloom
    arc_blur = r_to_svg(0.12)
    els.append(f'    <filter id="arc-bloom" x="-30%" y="-30%" width="160%" height="160%">')
    els.append(f'      <feGaussianBlur stdDeviation="{arc_blur:.1f}" result="blur"/>')
    els.append(f'    </filter>')

    # Nebula cloud radial gradients
    for i, nc in enumerate(NEBULA_SPECS["colors"]):
        color = _palette_hex(nc["color"])
        alpha = nc["alpha"]
        els.append(f'    <radialGradient id="nebula-{i}">')
        els.append(f'      <stop offset="0%" stop-color="{color}" stop-opacity="{alpha:.3f}"/>')
        els.append(f'      <stop offset="100%" stop-color="{color}" stop-opacity="0"/>')
        els.append(f'    </radialGradient>')

    els.append("  </defs>")
    return els


def _build_background(size: int) -> list[str]:
    """Background rectangle."""
    return [f'  <rect width="{size}" height="{size}" fill="{_palette_hex("background")}"/>']


def _build_nebula(size: int, to_svg, r_to_svg) -> list[str]:
    """Nebula clouds — radial gradient circles behind the main circle."""
    els: list[str] = []
    rng = random.Random(42)  # deterministic
    pos_min = NEBULA_SPECS["position_range"]["min"]
    pos_max = NEBULA_SPECS["position_range"]["max"]
    rad_min = NEBULA_SPECS["radius_range"]["min"]
    rad_max = NEBULA_SPECS["radius_range"]["max"]

    for i in range(NEBULA_SPECS["count"]):
        # Position in normalized [0,1] space → schema coords
        nx = rng.uniform(pos_min, pos_max)
        ny = rng.uniform(pos_min, pos_max)
        # Map to SVG coords via canvas center
        sx = nx * size
        sy = ny * size
        rad = rng.uniform(rad_min, rad_max) * size
        els.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rad:.1f}" '
                   f'fill="url(#nebula-{i})"/>')
    return els


def _build_circle_fill(to_svg, r_to_svg, circle_r: float) -> list[str]:
    """Dark circle fill."""
    scx, scy = to_svg(0, 0)
    cr = r_to_svg(circle_r)
    return [f'  <circle cx="{scx:.1f}" cy="{scy:.1f}" r="{cr:.1f}" '
            f'fill="{_palette_hex("deep")}"/>']


def _build_star_field(to_svg, r_to_svg, circle_r: float) -> list[str]:
    """Deterministic star field inside the circle."""
    els: list[str] = []
    rng = random.Random(7)  # deterministic seed
    scx, scy = to_svg(0, 0)
    cr = r_to_svg(circle_r)
    color = _palette_hex(STAR_SPECS["color"])
    sz_min = STAR_SPECS["size_range"]["min"]
    sz_max = STAR_SPECS["size_range"]["max"]
    br_min = STAR_SPECS["brightness_range"]["min"]
    br_max = STAR_SPECS["brightness_range"]["max"]

    for _ in range(STAR_SPECS["count"]):
        # Uniform distribution inside circle
        angle = rng.uniform(0, 2 * math.pi)
        dist = math.sqrt(rng.uniform(0, 1)) * cr * 0.95
        sx = scx + dist * math.cos(angle)
        sy = scy + dist * math.sin(angle)
        sr = rng.uniform(sz_min, sz_max)
        brightness = rng.uniform(br_min, br_max)
        els.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
                   f'fill="{color}" fill-opacity="{brightness:.2f}"/>')
    return els


def _build_ring(to_svg, r_to_svg) -> list[str]:
    """Multi-band ring (4 concentric annuli, rose_gold)."""
    els: list[str] = []
    scx, scy = to_svg(0, 0)
    rr = SIZING["ring_radii"]
    color = _palette_hex("rose_gold")
    opacities = OPACITY_DEFAULTS["ring"]

    bands = [
        (rr["inner_inner"], rr["inner_outer"], opacities["inner"]),
        (rr["mid_inner"],   rr["mid_outer"],   opacities["mid_inner"]),
        (rr["mid2_inner"],  rr["mid2_outer"],  opacities["mid_outer"]),
        (rr["outer_inner"], rr["outer_outer"], opacities["outer"]),
    ]

    for r_in, r_out, opacity in bands:
        r_mid = (r_in + r_out) / 2
        width = r_out - r_in
        sr = r_to_svg(r_mid)
        sw = r_to_svg(width)
        els.append(f'  <circle cx="{scx:.1f}" cy="{scy:.1f}" r="{sr:.1f}" '
                   f'fill="none" stroke="{color}" stroke-width="{sw:.1f}" '
                   f'stroke-opacity="{opacity}"/>')
    return els


def _build_shimmer(to_svg, r_to_svg) -> list[str]:
    """Static shimmer arcs on the ring."""
    els: list[str] = []
    scx, scy = to_svg(0, 0)
    r_mid = (SIZING["ring_radii"]["mid_inner"] + SIZING["ring_radii"]["mid_outer"]) / 2
    sr = r_to_svg(r_mid)
    color = _palette_hex(SHIMMER_SPECS["color"])
    sweep = SHIMMER_SPECS["arc_sweep"]

    for i in range(SHIMMER_SPECS["count"]):
        # Distribute evenly around the ring
        start_angle = (2 * math.pi / SHIMMER_SPECS["count"]) * i
        end_angle = start_angle + sweep
        x1 = scx + sr * math.cos(start_angle)
        y1 = scy + sr * math.sin(start_angle)
        x2 = scx + sr * math.cos(end_angle)
        y2 = scy + sr * math.sin(end_angle)
        large_arc = 1 if sweep > math.pi else 0
        els.append(f'  <path d="M {x1:.1f} {y1:.1f} A {sr:.1f} {sr:.1f} 0 '
                   f'{large_arc} 1 {x2:.1f} {y2:.1f}" '
                   f'fill="none" stroke="{color}" stroke-width="3" '
                   f'stroke-opacity="{SHIMMER_SPECS["base_opacity"]:.3f}" '
                   f'stroke-linecap="round"/>')
    return els


def _build_arc_blooms(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Thick semi-transparent arc layer behind main arcs."""
    els: list[str] = []
    bloom_opacity = OPACITY_DEFAULTS["arc_bloom"]["base"]
    bloom_width = r_to_svg(SIZING["arc_bloom_thickness"])

    for i, arc in enumerate(schema.arcs):
        style = ARC_STYLES[i]
        color = _hex(style["color"])
        pts = _arc_polyline_points(arc, to_svg)
        els.append(f'  <polyline points="{" ".join(pts)}" '
                   f'fill="none" stroke="{color}" stroke-width="{bloom_width:.1f}" '
                   f'stroke-opacity="{bloom_opacity}" stroke-linecap="round" '
                   f'filter="url(#arc-bloom)"/>')
    return els


def _build_arcs(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Colored arc strokes."""
    els: list[str] = []
    main_width = r_to_svg(SIZING["arc_main_thickness"])

    for i, arc in enumerate(schema.arcs):
        style = ARC_STYLES[i]
        color = _hex(style["color"])
        opacity = style["opacity"]
        pts = _arc_polyline_points(arc, to_svg)
        els.append(f'  <polyline points="{" ".join(pts)}" '
                   f'fill="none" stroke="{color}" stroke-width="{main_width:.1f}" '
                   f'stroke-opacity="{opacity}" stroke-linecap="round"/>')
    return els


def _arc_polyline_points(arc, to_svg, n_pts: int = 80) -> list[str]:
    """Generate polyline point strings for an arc."""
    pts = []
    for j in range(n_pts + 1):
        t = j / n_pts
        angle = arc.start_angle + t * arc.sweep_angle
        px = arc.cx + arc.radius * math.cos(angle)
        py = arc.cy + arc.radius * math.sin(angle)
        sx, sy = to_svg(px, py)
        pts.append(f"{sx:.1f},{sy:.1f}")
    return pts


def _build_edges(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Edges colored by palette, styled by type."""
    els: list[str] = []
    edge_color = _hex(EDGE_COLOR)

    for edge in schema.edges:
        n1 = schema.node(edge.from_id)
        n2 = schema.node(edge.to_id)
        x1, y1 = to_svg(n1.x, n1.y)
        x2, y2 = to_svg(n2.x, n2.y)
        w_factor, opacity = EDGE_STYLES.get(edge.edge_type, (0.04, 0.30))
        w = r_to_svg(w_factor)
        els.append(f'  <line x1="{x1:.1f}" y1="{y1:.1f}" '
                   f'x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{edge_color}" stroke-width="{w:.1f}" '
                   f'stroke-opacity="{opacity}" stroke-linecap="round"/>')
    return els


def _build_nib(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Nib detail: outline, center line, ball with glow."""
    els: list[str] = []
    nib = schema.nib
    bronze = _hex("BRONZE")
    blue_glow = _hex("BLUEGLOW")
    warm_white = _hex("WARMWHT")

    # Nib outline polygon
    if len(nib.outline) >= 3:
        pts = []
        for px, py in nib.outline:
            sx, sy = to_svg(px, py)
            pts.append(f"{sx:.1f},{sy:.1f}")
        nib_opacity = OPACITY_DEFAULTS["nib_line"]["outline"]
        nib_width = r_to_svg(SIZING["nib_line_thickness"]["outline"])
        els.append(f'  <polygon points="{" ".join(pts)}" '
                   f'fill="none" stroke="{bronze}" stroke-width="{nib_width:.1f}" '
                   f'stroke-opacity="{nib_opacity}" stroke-linejoin="round"/>')

    # Center slit line (blue glow)
    sx1, sy1 = to_svg(*nib.slit_start)
    sx2, sy2 = to_svg(*nib.slit_end)
    center_opacity = OPACITY_DEFAULTS["nib_line"]["center"]
    center_width = r_to_svg(SIZING["nib_line_thickness"]["center"])
    els.append(f'  <line x1="{sx1:.1f}" y1="{sy1:.1f}" '
               f'x2="{sx2:.1f}" y2="{sy2:.1f}" '
               f'stroke="{blue_glow}" stroke-width="{center_width:.1f}" '
               f'stroke-opacity="{center_opacity}"/>')

    # Nib ball — glow halo then core
    bx, by = to_svg(*nib.ball_pos)
    ball_r = r_to_svg(nib.ball_radius)
    glow_r = ball_r * 4
    glow_opacity = OPACITY_DEFAULTS["nib_ball"]["glow"]
    core_opacity = OPACITY_DEFAULTS["nib_ball"]["core"]
    els.append(f'  <circle cx="{bx:.1f}" cy="{by:.1f}" r="{glow_r:.1f}" '
               f'fill="{warm_white}" fill-opacity="{glow_opacity}" filter="url(#glow)"/>')
    els.append(f'  <circle cx="{bx:.1f}" cy="{by:.1f}" r="{ball_r:.1f}" '
               f'fill="{warm_white}" fill-opacity="{core_opacity}"/>')
    return els


def _build_node_glows(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Glow halos behind nodes (filtered gaussian blur)."""
    els: list[str] = []
    glow_scale = SIZING["node_glow_scale"]
    glow_opacity = OPACITY_DEFAULTS["node_glow"]["base"]

    for node in schema.nodes:
        if node.id == 14:
            continue
        color_key = resolve_node_color(node)
        color = _hex(color_key)
        sx, sy = to_svg(node.x, node.y)
        base_r = 0.14 if node.key_node else 0.09
        glow_r = r_to_svg(base_r * glow_scale)
        els.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{glow_r:.1f}" '
                   f'fill="{color}" fill-opacity="{glow_opacity}" filter="url(#glow)"/>')
    return els


def _build_nodes(schema: PLogoSchema, to_svg, r_to_svg) -> list[str]:
    """Colored node circles."""
    els: list[str] = []
    core_opacity = OPACITY_DEFAULTS["node_core"]["base"]

    for node in schema.nodes:
        if node.id == 14:
            continue
        color_key = resolve_node_color(node)
        color = _hex(color_key)
        sx, sy = to_svg(node.x, node.y)
        sr = r_to_svg(0.14 if node.key_node else 0.09)
        els.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
                   f'fill="{color}" fill-opacity="{core_opacity}"/>')
    return els


# ── Main export function ─────────────────────────────────────

def export_svg(
    schema: PLogoSchema,
    path: str,
    size: int = 2000,
) -> str:
    """
    Export PLogoSchema as a palette-driven SVG file.

    Renders colored nodes, multi-band ring, arc blooms, glow halos,
    nebula clouds, star field, and nib detail.
    """
    circle_r = SIZING["circle_fill_radius"]
    to_svg, r_to_svg = _make_transforms(circle_r, size)

    els: list[str] = []

    # Header
    els.append('<?xml version="1.0" encoding="UTF-8"?>')
    els.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">')

    # Layers (back to front)
    els.extend(_build_defs(size, r_to_svg, to_svg, schema))
    els.extend(_build_background(size))
    els.extend(_build_nebula(size, to_svg, r_to_svg))
    els.extend(_build_circle_fill(to_svg, r_to_svg, circle_r))
    els.extend(_build_star_field(to_svg, r_to_svg, circle_r))
    els.extend(_build_ring(to_svg, r_to_svg))
    els.extend(_build_shimmer(to_svg, r_to_svg))
    els.extend(_build_arc_blooms(schema, to_svg, r_to_svg))
    els.extend(_build_arcs(schema, to_svg, r_to_svg))
    els.extend(_build_edges(schema, to_svg, r_to_svg))
    els.extend(_build_nib(schema, to_svg, r_to_svg))
    els.extend(_build_node_glows(schema, to_svg, r_to_svg))
    els.extend(_build_nodes(schema, to_svg, r_to_svg))

    els.append('</svg>')

    svg_text = '\n'.join(els)
    Path(path).write_text(svg_text, encoding="utf-8")
    return svg_text
