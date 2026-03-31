"""
Generate the stylized graph-P logo.

Geometry: 23 nodes + 45 edges ported from logo.html Three.js source.
Circle calibrated against Gemini_Generated_Image_dhpdvadhpdvadhpd.jpeg.

Usage:
  python3 logo.py                          # PNG preview (matplotlib)
  python3 logo.py --svg logo.svg           # Clean BW SVG export
  python3 logo.py --svg logo.svg --png     # Both SVG and PNG
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

# ── Coordinate system ─────────────────────────────────────────
CANVAS = 11.0
SVG_SIZE = 2000

# Circle (JPEG-measured)
CIRCLE_CX, CIRCLE_CY = 5.0, 5.0
CIRCLE_R = 4.52
RING_R = 4.60
RING_WIDTH = 0.10

# Scale from logo.html coords → logo.py coords
# html: camera [-5,5], circle r=4.55 at (0,0)
# logo.py: circle r=4.52 at (5,5)
_S = CIRCLE_R / 4.55


def _h(hx: float, hy: float) -> tuple[float, float]:
    """Convert logo.html coord to logo.py coord."""
    return hx * _S + CIRCLE_CX, hy * _S + CIRCLE_CY


DPI = 300
BG = "#050505"

# ═══════════════════════════════════════════════════════════════
# GEOMETRY — 23 nodes, synced with logo.html
# ═══════════════════════════════════════════════════════════════

_node_data = [
    #    (logo_x, logo_y,   radius, is_key)
    (*_h(-1.50,  2.70), 0.24, True),    # 0  top-left corner
    (*_h( 0.15,  2.70), 0.22, True),    # 1  top-right serif
    (*_h( 1.19,  1.78), 0.14, False),   # 2  bowl upper-right (on green arc)
    (*_h( 0.40,  0.09), 0.14, False),   # 3  bowl bottom
    (*_h(-1.02,  2.12), 0.12, False),   # 4  counter top-left
    (*_h( 0.45,  1.59), 0.12, False),   # 5  counter top-right
    (*_h( 1.04,  0.91), 0.12, False),   # 6  counter mid-right
    (*_h(-1.50,  0.09), 0.22, True),    # 7  junction left
    (*_h(-0.55,  0.09), 0.14, False),   # 8  junction right
    (*_h(-1.03, -0.32), 0.22, True),    # 9  triangle right vertex
    (*_h(-0.55, -1.15), 0.14, False),   # 10 nib shoulder right
    (*_h(-1.50, -1.15), 0.14, False),   # 11 nib shoulder left
    (*_h(-1.03, -1.70), 0.12, False),   # 12 nib waist
    (*_h(-1.03, -2.25), 0.14, False),   # 13 nib ball
    (*_h(-1.03, -2.90), 0.12, False),   # 14 nib tip
    (*_h(-0.52,  1.58), 0.12, False),   # 15 inner D left midpoint
    (*_h(-0.55, -0.88), 0.20, True),    # 16 outer D stem anchor
    (*_h( 0.39, -0.84), 0.20, True),    # 17 gold arc bottom endpoint
    (*_h( 0.39, -0.34), 0.20, True),    # 18 green arc bottom landing
    (*_h( 0.35,  2.12), 0.20, True),    # 19 green arc top departure
    (*_h( 0.48,  1.58), 0.12, False),   # 20 bowl arc departure
    (*_h( 0.36,  0.09), 0.12, False),   # 21 bowl arc landing
    (*_h( 2.08,  0.91), 0.20, True),    # 22 gold arc right tangent
    (*_h( 0.75,  2.55), 0.20, True),    # 23 gold arc top endpoint
]

nodes = [(x, y) for x, y, _, _ in _node_data]
node_radius = [r for _, _, r, _ in _node_data]
node_is_key = [k for _, _, _, k in _node_data]

# Edge definitions — synced with logo.html wireEdges
# Kinds: "contour" = outer P, "mesh" = internal triangulation,
# "struct" = stem/triangle structure, "nib" = pen nib
edges = [
    # ── Outer contour ──
    (0, 1, "contour"),      # top bar
    (7, 0, "contour"),      # left vertical (junction → top-left)
    (11, 7, "contour"),     # left vertical (nib shoulder left → junction)
    (7, 8, "contour"),      # junction horizontal bar
    (3, 8, "contour"),      # bowl bottom → junction right

    # ── Right stem vertical ──
    (16, 10, "contour"),    # stem anchor → nib shoulder right

    # ── Triangle / stem structure ──
    (7, 9, "struct"),       # junction left → triangle vertex
    (16, 9, "struct"),      # stem anchor → triangle vertex
    (9, 10, "struct"),      # triangle vertex → nib shoulder right
    (9, 11, "struct"),      # triangle vertex → nib shoulder left
    (10, 11, "struct"),     # nib shoulders

    # ── Pen nib ──
    (10, 12, "nib"),        # nib shoulder right → waist
    (11, 12, "nib"),        # nib shoulder left → waist
    (12, 13, "nib"),        # waist → ball
    (13, 14, "nib"),        # ball → tip

    # ── Inner counter / D-shape ──
    (4, 9, "mesh"),         # counter top-left → triangle vertex (closes inner D left vertical)
    (4, 19, "mesh"),        # counter top-left → green arc top (horizontal bar)
    (0, 4, "mesh"),         # top-left → counter top-left
    (15, 4, "mesh"),        # inner D left → counter top-left
    (15, 5, "mesh"),        # inner D left → counter top-right (closes inner D)
    (15, 7, "mesh"),        # inner D left → junction left
    (15, 8, "mesh"),        # inner D left → junction right
    (15, 20, "mesh"),       # inner D left → bowl arc departure

    # ── Top bar / serif triangulation ──
    (1, 5, "mesh"),         # top-right → counter top-right
    (1, 19, "mesh"),        # top-right → green arc top departure

    # ── Bowl / arc nodes ──
    (2, 5, "mesh"),         # bowl upper-right → counter top-right
    (2, 6, "mesh"),         # bowl upper-right → counter mid-right
    # (2, 3) removed — straight line cuts through arc area
    (2, 22, "mesh"),        # bowl upper-right → gold arc right tangent
    (19, 5, "mesh"),        # green arc top → counter top-right
    (19, 20, "mesh"),       # green arc top → bowl arc departure
    (5, 20, "mesh"),        # counter top-right → bowl arc departure

    # ── Bottom bowl triangulation ──
        # bowl bottom → gold arc bottom
    (3, 21, "mesh"),        # bowl bottom → bowl arc landing
    (18, 9, "mesh"),        # green arc bottom → triangle vertex
    (17, 16, "mesh"),       # gold arc bottom → stem anchor
    (22, 17, "mesh"),       # gold arc right tangent → gold arc bottom
    (6, 22, "mesh"),        # counter mid-right → gold arc right tangent
    (1, 23, "contour"),     # top-right serif → gold arc top
    (2, 23, "mesh"),        # bowl upper-right → gold arc top
    (23, 19, "mesh"),       # gold arc top → green arc top departure
]

# ── Arc geometry (circle-fitted, from logo.html) ──────────────
# Green arc: center=(0.3498, 0.8897), r=1.2303
ARC_GREEN_CX, ARC_GREEN_CY = _h(0.3498, 0.8897)
ARC_GREEN_R = 1.2303 * _S
ARC_GREEN_START = -1.5381
ARC_GREEN_END = -1.5381 + 3.1088

# Bowl arc (inner D): center=(0.3383, 0.8416), r=0.7519
ARC_BOWL_CX, ARC_BOWL_CY = _h(0.3383, 0.8416)
ARC_BOWL_R = 0.7519 * _S
ARC_BOWL_START = -1.5420
ARC_BOWL_END = -1.5420 + 2.9232

# Gold arc: center=(0.3631, 0.8770), r=1.7172
ARC_GOLD_CX, ARC_GOLD_CY = _h(0.3631, 0.8770)
ARC_GOLD_R = 1.7172 * _S
ARC_GOLD_START = -1.5552
ARC_GOLD_END = -1.5552 + 2.8987


# ─────────────────────────────────────────────────────────────
# Coordinate transforms
# ─────────────────────────────────────────────────────────────
def logo_to_svg(x: float, y: float) -> tuple[float, float]:
    sx = (x + 0.5) / CANVAS * SVG_SIZE
    sy = (CANVAS - 0.5 - y) / CANVAS * SVG_SIZE
    return sx, sy


def logo_r_to_svg(r: float) -> float:
    return r / CANVAS * SVG_SIZE


# ─────────────────────────────────────────────────────────────
# SVG generation (BW)
# ─────────────────────────────────────────────────────────────
def generate_svg() -> str:
    S = SVG_SIZE
    els: list[str] = []

    def add(s: str):
        els.append(s)

    add('<?xml version="1.0" encoding="UTF-8"?>')
    add(f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {S} {S}" width="{S}" height="{S}">')

    # White background
    add(f'  <rect width="{S}" height="{S}" fill="#ffffff"/>')

    # Black circle
    cx, cy = logo_to_svg(CIRCLE_CX, CIRCLE_CY)
    cr = logo_r_to_svg(CIRCLE_R)
    add(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cr:.1f}" fill="#000000"/>')

    # Ring border
    rr = logo_r_to_svg(RING_R)
    rw = logo_r_to_svg(RING_WIDTH)
    add(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" '
        f'fill="none" stroke="#ffffff" stroke-width="{rw:.1f}"/>')

    # Subtle inner ring
    ir = logo_r_to_svg(CIRCLE_R - 0.15)
    add(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ir:.1f}" '
        f'fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.25"/>')

    # --- Arcs (polyline approximation for smooth curves) ---
    def svg_arc_polyline(acx, acy, ar, a_start, a_end, sw, opacity, n_pts=80):
        pts = []
        for i in range(n_pts + 1):
            t = i / n_pts
            angle = a_start + t * (a_end - a_start)
            px, py = acx + ar * math.cos(angle), acy + ar * math.sin(angle)
            sx, sy = logo_to_svg(px, py)
            pts.append(f"{sx:.1f},{sy:.1f}")
        add(f'  <polyline points="{" ".join(pts)}" '
            f'fill="none" stroke="#ffffff" stroke-width="{sw}" '
            f'stroke-opacity="{opacity}" stroke-linecap="round"/>')

    svg_arc_polyline(ARC_GREEN_CX, ARC_GREEN_CY, ARC_GREEN_R,
                     ARC_GREEN_START, ARC_GREEN_END, 5, 0.15)
    svg_arc_polyline(ARC_BOWL_CX, ARC_BOWL_CY, ARC_BOWL_R,
                     ARC_BOWL_START, ARC_BOWL_END, 3, 0.10)
    svg_arc_polyline(ARC_GOLD_CX, ARC_GOLD_CY, ARC_GOLD_R,
                     ARC_GOLD_START, ARC_GOLD_END, 4, 0.08)

    # --- Edge widths ---
    widths = {
        "contour": (logo_r_to_svg(0.10), "0.70"),
        "mesh":    (logo_r_to_svg(0.04), "0.30"),
        "struct":  (logo_r_to_svg(0.08), "0.55"),
        "nib":     (logo_r_to_svg(0.06), "0.60"),
    }

    for (a, b, kind) in edges:
        x1, y1 = logo_to_svg(*nodes[a])
        x2, y2 = logo_to_svg(*nodes[b])
        w, opacity = widths[kind]
        add(f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#ffffff" stroke-width="{w:.1f}" stroke-opacity="{opacity}" '
            f'stroke-linecap="round"/>')

    # Pen nib center slit
    nib_waist = logo_to_svg(*nodes[12])
    nib_tip = logo_to_svg(*nodes[14])
    add(f'  <line x1="{nib_waist[0]:.1f}" y1="{nib_waist[1]:.1f}" '
        f'x2="{nib_tip[0]:.1f}" y2="{nib_tip[1]:.1f}" '
        f'stroke="#000000" stroke-width="2" stroke-opacity="0.5"/>')

    # Draw nodes
    for i, (x, y) in enumerate(nodes):
        sx, sy = logo_to_svg(x, y)
        sr = logo_r_to_svg(node_radius[i])
        opacity = "1.0" if node_is_key[i] else "0.85"
        add(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
            f'fill="#ffffff" fill-opacity="{opacity}"/>')

    add('</svg>')
    return '\n'.join(els)


# ─────────────────────────────────────────────────────────────
# Matplotlib rendering (preview / PNG)
# ─────────────────────────────────────────────────────────────
def render_matplotlib(output_path: str = "p_logo.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 10), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 10.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Circle + ring
    ax.add_patch(plt.Circle((CIRCLE_CX, CIRCLE_CY), CIRCLE_R,
                             fc="#0a1929", ec="none", zorder=0))
    ax.add_patch(plt.Circle((CIRCLE_CX, CIRCLE_CY), RING_R,
                             fill=False, ec="#c8a050", lw=4, zorder=0))

    # Arcs
    for acx, acy, ar, a_s, a_e, lw, alpha in [
        (ARC_GREEN_CX, ARC_GREEN_CY, ARC_GREEN_R, ARC_GREEN_START, ARC_GREEN_END, 10, 0.12),
        (ARC_BOWL_CX, ARC_BOWL_CY, ARC_BOWL_R, ARC_BOWL_START, ARC_BOWL_END, 6, 0.08),
        (ARC_GOLD_CX, ARC_GOLD_CY, ARC_GOLD_R, ARC_GOLD_START, ARC_GOLD_END, 8, 0.06),
    ]:
        theta = np.linspace(a_s, a_e, 200)
        ax.plot(acx + ar * np.cos(theta), acy + ar * np.sin(theta),
                color="#fff", alpha=alpha, lw=lw, solid_capstyle="round", zorder=1)

    # Edges
    edge_styles = {
        "contour": ("#8a8a8a", 5),
        "mesh":    ("#444444", 2),
        "struct":  ("#6a6a6a", 4),
        "nib":     ("#7a7a7a", 3),
    }
    for (a, b, kind) in edges:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]
        col, lw = edge_styles[kind]
        ax.plot([x1, x2], [y1, y2], color=col, lw=lw,
                solid_capstyle="round", zorder=2)

    # Nodes
    for i, (x, y) in enumerate(nodes):
        r = node_radius[i]
        fc = "#f0f0f0" if node_is_key[i] else "#c0c0c0"
        ax.add_patch(plt.Circle((x, y), r, fc=fc, ec="#bbb", lw=0.8, zorder=6))

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=DPI, facecolor=BG,
                bbox_inches="tight", pad_inches=0.05)
    print(f"PNG saved: {output_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate the stylized graph-P logo.",
    )
    parser.add_argument("--svg", default=None, metavar="PATH",
                        help="Export clean BW SVG to this path")
    parser.add_argument("--png", default=None, metavar="PATH", nargs="?",
                        const="p_logo.png",
                        help="Export PNG preview (default: p_logo.png)")
    args = parser.parse_args()

    if args.svg is None and args.png is None:
        args.png = "p_logo.png"

    if args.svg:
        svg_text = generate_svg()
        Path(args.svg).write_text(svg_text, encoding="utf-8")
        print(f"SVG saved: {args.svg}")

    if args.png:
        render_matplotlib(args.png)


if __name__ == "__main__":
    main()
