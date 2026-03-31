"""Animated GIF export — renders frames with matplotlib and assembles a GIF."""

from __future__ import annotations

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle
from PIL import Image

from p_logo.types import PLogoSchema


def render_frame(
    schema: PLogoSchema,
    phase: float = 0.0,
    size: int = 800,
    dpi: int = 100,
    bg_color: str = "#0e0820",
    palette: dict | None = None,
) -> Image.Image:
    """Render a single animated frame. Returns PIL Image."""
    if palette is None:
        palette = {
            "copper": "#5a9e8c", "amber": "#e8a84c", "bronze": "#b87a4e",
            "rosegold": "#c4876e", "warmwht": "#ffecd2", "blueglow": "#5b8fd4",
        }

    fig_size = size / dpi
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=dpi)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(-5.0, 5.0)
    ax.set_ylim(-5.0, 5.0)
    ax.set_aspect("equal")
    ax.axis("off")

    # Ring
    ax.add_patch(Circle((0, 0), 4.65, fc="none", ec=palette["rosegold"], lw=3.0, alpha=0.85))
    ax.add_patch(Circle((0, 0), 4.55, fc=bg_color, ec="none"))

    arc_colors = [palette["amber"], palette["copper"], palette["bronze"]]

    # Arcs
    for i, arc in enumerate(schema.arcs):
        ax.add_patch(Arc((arc.cx, arc.cy), 2*arc.radius, 2*arc.radius,
                         theta1=arc.start_deg, theta2=arc.end_deg,
                         color=arc_colors[i], lw=2.5, alpha=0.7))
        # Arc runner
        runner_t = (phase * 0.3 + i * 0.33) % 1.0
        angle = arc.start_angle + runner_t * arc.sweep_angle
        rx = arc.cx + arc.radius * np.cos(angle)
        ry = arc.cy + arc.radius * np.sin(angle)
        fade = np.sin(runner_t * np.pi)
        ax.add_patch(Circle((rx, ry), 0.06, fc=arc_colors[i], ec="none", alpha=0.9 * fade))

    # Edges
    for e in schema.edges:
        n1, n2 = schema.node(e.from_id), schema.node(e.to_id)
        pulse = 0.35 + 0.25 * np.sin(phase * 8.0 + e.from_id * 0.5)
        ax.plot([n1.x, n2.x], [n1.y, n2.y], color=palette["copper"], lw=1.8,
                alpha=min(0.9, pulse), solid_capstyle="round", zorder=2)

    # Nib
    nib = schema.nib
    ax.plot([p[0] for p in nib.outline], [p[1] for p in nib.outline],
            color=palette["copper"], lw=1.8, alpha=0.8, solid_capstyle="round", zorder=2)
    ax.plot([nib.slit_start[0], nib.slit_end[0]],
            [nib.slit_start[1], nib.slit_end[1]],
            color=palette["blueglow"], lw=0.8, alpha=0.4, zorder=3)
    ax.add_patch(Circle(nib.ball_pos, 0.05, fc=palette["copper"], ec=palette["copper"], zorder=4))

    # Nodes
    for n in schema.nodes:
        if n.id == 14:
            continue
        pulse = 0.5 + 0.5 * np.sin(phase * 12.0 + n.id * 1.1)
        r = 0.07 if n.key_node else 0.045
        ax.add_patch(Circle((n.x, n.y), r, fc=palette["copper"],
                            ec=palette["copper"], alpha=0.65 + 0.35 * pulse, zorder=5))

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, facecolor=bg_color,
                bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")

    if img.size != (size, size):
        img.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGB", (size, size), (14, 8, 32))
        x = (size - img.width) // 2
        y = (size - img.height) // 2
        canvas.paste(img, (x, y))
        img = canvas

    return img


def export_gif(
    schema: PLogoSchema,
    path: str,
    n_frames: int = 60,
    duration_ms: int = 50,
    size: int = 800,
    dpi: int = 100,
) -> None:
    """Export an animated GIF of the P logo."""
    frames = []
    for i in range(n_frames):
        phase = i / n_frames
        img = render_frame(schema, phase=phase, size=size, dpi=dpi)
        frames.append(img)

    frames[0].save(
        path, save_all=True, append_images=frames[1:],
        duration=duration_ms, loop=0, optimize=True,
    )
