"""B&W matplotlib renderer — uniform stroke, pure black/white."""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

from p_logo.types import PLogoSchema
from p_logo.renderers.base import PLogoRenderer


class MatplotlibBWRenderer(PLogoRenderer):
    """Renders the P logo in pure B&W with uniform stroke weight."""

    def render(
        self,
        output_path: str,
        dpi: int = 600,
        size: int = 800,
        bg: str = "#000000",
        stroke: float = 3.0,
        invert: bool = False,
    ) -> None:
        fig, ax = plt.subplots(figsize=(10, 10), dpi=dpi)
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.set_xlim(-3.2, 3.7)
        ax.set_ylim(-4.4, 4.2)
        ax.set_aspect("equal")
        ax.axis("off")

        w = "#ffffff"
        s = self.schema

        # Arcs
        for arc in s.arcs:
            theta = np.linspace(arc.start_angle, arc.end_angle, 300)
            ax.plot(arc.cx + arc.radius * np.cos(theta),
                    arc.cy + arc.radius * np.sin(theta),
                    color=w, lw=stroke, alpha=1.0,
                    solid_capstyle="round", zorder=1)

        # Edges
        for e in s.edges:
            n1, n2 = s.node(e.from_id), s.node(e.to_id)
            ax.plot([n1.x, n2.x], [n1.y, n2.y], color=w, lw=stroke,
                    alpha=1.0, solid_capstyle="round", zorder=2)

        # Nib
        nib = s.nib
        xs = [p[0] for p in nib.outline]
        ys = [p[1] for p in nib.outline]
        ax.plot(xs, ys, color=w, lw=stroke, solid_capstyle="round", zorder=2)
        ax.plot([nib.slit_start[0], nib.slit_end[0]],
                [nib.slit_start[1], nib.slit_end[1]],
                color=bg, lw=stroke * 0.5, zorder=3)
        ax.add_patch(plt.Circle(nib.ball_pos, nib.ball_radius,
                                fc=w, ec=w, lw=1.0, zorder=5))

        # Nodes
        r_node = 0.09
        for n in s.nodes:
            if n.id == 14:
                continue
            ax.add_patch(plt.Circle((n.x, n.y), r_node, fc=w, ec=w,
                                    lw=1.2, zorder=6))

        plt.tight_layout(pad=0)
        plt.savefig(output_path + "_raw.png", dpi=dpi, facecolor=bg,
                    bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)

        # Fit to canvas
        img = Image.open(output_path + "_raw.png")
        img.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGB", (size, size), (0, 0, 0))
        x = (size - img.width) // 2
        y = (size - img.height) // 2
        canvas.paste(img, (x, y))

        if invert:
            canvas = ImageChops.invert(canvas)

        canvas.save(output_path)
        import os
        os.remove(output_path + "_raw.png")
