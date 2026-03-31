"""Composition overlay — renders all geometric_composition_final shapes on a matplotlib axes."""

from __future__ import annotations

import numpy as np
from p_logo.types import PLogoSchema

SHAPE_COLORS = {
    "Circ.A": "#3de8a0", "Outer.Circle": "#e8b84a",
    "Square.B": "#ff4488", "Square.A": "#3de8a0",
    "Circ.V1": "#aa44ff", "Circ.V2": "#aa44ff",
    "Circ.V3": "#aa44ff", "Circ.V4": "#aa44ff",
    "Circ.C": "#ff8844", "Circ.C'": "#cc6633",
    "Circ.Bounds.A": "#4a9ee8", "Square.D": "#cc7733",
    "Circ.D": "#cc3333", "Rect.1": "#4466aa",
    "Circ.Rect.V": "#8833cc", "Circ.Rect.I": "#cc3366",
}


def render_overlay(ax, schema: PLogoSchema, zorder: int = 20) -> None:
    """Draw all composition shapes on an existing matplotlib axes."""
    import matplotlib.pyplot as plt

    comp = schema.composition
    if comp is None:
        return

    for shape_id, shape in comp["shapes"].items():
        col = SHAPE_COLORS.get(shape_id, "#888888")
        lw, alpha = 1.0, 0.45

        if shape["type"] == "circle":
            cx, cy = shape["center"]["x"], shape["center"]["y"]
            r = shape["radius"]
            style = "--" if shape.get("style") == "dotted" else "-"
            t = np.linspace(0, 2 * np.pi, 200)
            ax.plot(cx + r * np.cos(t), cy + r * np.sin(t),
                    color=col, lw=lw, alpha=alpha, linestyle=style, zorder=zorder)

        elif shape["type"] in ("square", "rectangle"):
            verts = shape.get("vertices", {})
            if "upper_left" in verts:
                ul, ur = verts["upper_left"], verts["upper_right"]
                ll, lr = verts["lower_left"], verts["lower_right"]
                xs = [ul["x"], ur["x"], lr["x"], ll["x"], ul["x"]]
                ys = [ul["y"], ur["y"], lr["y"], ll["y"], ul["y"]]
            elif "V1_right" in verts:
                vs = [verts["V1_right"], verts["V2_top_left"],
                      verts["V3_bottom_left"], verts["V4_bottom_right"]]
                xs = [v["x"] for v in vs] + [vs[0]["x"]]
                ys = [v["y"] for v in vs] + [vs[0]["y"]]
            elif "D1_top_right" in verts:
                vs = [verts["D1_top_right"], verts["D2_top_left"],
                      verts["D3_bottom_left"], verts["D4_bottom_right"]]
                xs = [v["x"] for v in vs] + [vs[0]["x"]]
                ys = [v["y"] for v in vs] + [vs[0]["y"]]
            else:
                continue
            style = "--" if shape.get("style") == "dotted" else "-"
            ax.plot(xs, ys, color=col, lw=lw, alpha=alpha, linestyle=style, zorder=zorder)

    # Named points
    for pid, pt in comp["points"].items():
        ax.plot(pt["x"], pt["y"], "+", color="#ffffff", ms=5,
                mew=0.5, alpha=0.3, zorder=zorder + 1)

    # Center crosshair
    sc = schema.center
    ch = 0.25
    ax.plot([sc[0] - ch, sc[0] + ch], [sc[1], sc[1]],
            color="#ffffff", lw=0.8, alpha=0.5, zorder=zorder + 1)
    ax.plot([sc[0], sc[0]], [sc[1] - ch, sc[1] + ch],
            color="#ffffff", lw=0.8, alpha=0.5, zorder=zorder + 1)
    ax.add_patch(plt.Circle(sc, 0.06, fc="none", ec="#ffffff",
                            lw=0.8, alpha=0.5, zorder=zorder + 1))
