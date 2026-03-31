#!/usr/bin/env python3
"""
Geometric P Logo — B&W renderer + schema exporter.

Thin wrapper around the p_logo library. Outputs to build/logos/:
  - p_logo_bw_dark.png / p_logo_bw_light.png (800×800 clean B&W)
  - p_logo_bw_overlay_dark.png / light.png (2000×2000 with composition overlay)
  - p_logo_schema.json (canonical schema)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

from p_logo import build_schema
from p_logo.exporters.json_export import export_json
from p_logo.exporters.node_colors import compute_degrees, node_core_radius
from p_logo.renderers.matplotlib_bw import MatplotlibBWRenderer
from p_logo.overlay import render_overlay

LOGOS_DIR = Path(__file__).parent.parent / "build" / "logos"


def render_with_overlay(schema, output_path, dpi=600, size=2000):
    """Render B&W logo with composition overlay and node labels."""
    fig, ax = plt.subplots(figsize=(10, 10), dpi=dpi)
    bg = "#000000"
    w = "#ffffff"
    stroke = 3.0

    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(-4.5, 5.0)
    ax.set_ylim(-6.0, 4.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Arcs
    for arc in schema.arcs:
        theta = np.linspace(arc.start_angle, arc.end_angle, 300)
        ax.plot(arc.cx + arc.radius * np.cos(theta),
                arc.cy + arc.radius * np.sin(theta),
                color=w, lw=stroke, alpha=1.0, solid_capstyle="round", zorder=1)

    # Edges
    for e in schema.edges:
        n1, n2 = schema.node(e.from_id), schema.node(e.to_id)
        ax.plot([n1.x, n2.x], [n1.y, n2.y], color=w, lw=stroke,
                alpha=1.0, solid_capstyle="round", zorder=2)

    # Nib
    nib = schema.nib
    ax.plot([p[0] for p in nib.outline], [p[1] for p in nib.outline],
            color=w, lw=stroke, solid_capstyle="round", zorder=2)
    ax.plot([nib.slit_start[0], nib.slit_end[0]],
            [nib.slit_start[1], nib.slit_end[1]],
            color=bg, lw=stroke * 0.5, zorder=3)
    ax.add_patch(plt.Circle(nib.ball_pos, nib.ball_radius, fc=w, ec=w, lw=1.0, zorder=5))

    # Nodes (canonical degree-based sizing)
    degrees = compute_degrees(schema)
    for n in schema.nodes:
        if n.id == 14:
            continue
        r = node_core_radius(schema.r_green, degrees[n.id])
        ax.add_patch(plt.Circle((n.x, n.y), r, fc=w, ec=w, lw=1.2, zorder=6))

    # Overlay: composition shapes
    render_overlay(ax, schema, zorder=20)

    # Node labels
    for n in schema.nodes:
        if n.id == 14:
            continue
        ax.text(n.x, n.y + 0.20, str(n.id), fontsize=5, fontweight="light",
                color=w, ha="center", va="center", zorder=22,
                bbox=dict(boxstyle="round,pad=0.03", fc=bg, ec=w, lw=0.2, alpha=0.75))

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=dpi, facecolor=bg,
                bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def fit_to_canvas(src, out, size=800, bg=(0, 0, 0)):
    img = Image.open(src)
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), bg)
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y))
    canvas.save(out)


def main():
    parser = argparse.ArgumentParser(description="Geometric P Logo — B&W + schema")
    parser.add_argument("--no-overlay", action="store_true", help="Skip overlay render")
    parser.add_argument("--no-schema", action="store_true", help="Skip schema export")
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_schema()

    # Clean B&W renders
    renderer = MatplotlibBWRenderer(schema)
    renderer.render(str(LOGOS_DIR / "p_logo_bw_dark.png"), dpi=args.dpi)
    renderer.render(str(LOGOS_DIR / "p_logo_bw_light.png"), dpi=args.dpi, invert=True)
    print("Done — p_logo_bw_dark.png + p_logo_bw_light.png")

    # Overlay renders
    if not args.no_overlay:
        raw_path = str(LOGOS_DIR / "_p_logo_bw_overlay_raw.png")
        dark_path = str(LOGOS_DIR / "p_logo_bw_overlay_dark.png")
        light_path = str(LOGOS_DIR / "p_logo_bw_overlay_light.png")
        render_with_overlay(schema, raw_path, dpi=args.dpi)
        fit_to_canvas(raw_path, dark_path, size=2000)
        img_ov = Image.open(dark_path)
        ImageChops.invert(img_ov).save(light_path)
        import os
        os.remove(raw_path)
        print("Done — p_logo_bw_overlay_dark/light.png")

    # Schema export
    if not args.no_schema:
        export_json(schema, str(LOGOS_DIR / "p_logo_schema.json"))
        print(f"Schema exported → p_logo_schema.json ({schema.node_count} nodes, {schema.edge_count} edges)")

    print(f"All outputs in {LOGOS_DIR}")


if __name__ == "__main__":
    main()
