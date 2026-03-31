"""V16 technical drawing renderer — parchment bg, bronze rings, hatching, dimensions."""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from p_logo.types import PLogoSchema
from p_logo.renderers.base import PLogoRenderer


class V16TechnicalRenderer(PLogoRenderer):
    """Renders the P logo as a technical/architectural construction drawing."""

    def render(self, output_path: str, dpi: int = 200, **kwargs) -> None:
        s = self.schema
        cx, cy = s.center
        comp = s.composition

        # Derived geometry
        sq_A_vx = cx + s.r_gold * np.cos(np.radians([45, 135, 225, 315]))
        sq_A_vy = cy + s.r_gold * np.sin(np.radians([45, 135, 225, 315]))
        sq_D_vx = cx + s.r_green * np.cos(np.radians([45, 135, 225, 315]))
        sq_D_vy = cy + s.r_green * np.sin(np.radians([45, 135, 225, 315]))
        vcircs = []
        for vx, vy in zip(sq_A_vx, sq_A_vy):
            dists = [vx - (cx - s.r_gold), (cx + s.r_gold) - vx,
                     vy - (cy - s.r_gold), (cy + s.r_gold) - vy]
            vcircs.append((vx, vy, min(dists)))

        rect = comp["shapes"]["Rect.1"]
        rect_ul = rect["vertices"]["upper_left"]
        rect_ur = rect["vertices"]["upper_right"]
        rect_ll = rect["vertices"]["lower_left"]
        rect_w, rect_h = rect["width"], rect["height"]
        stem_r_x, rect_l_x = rect_ur["x"], rect_ul["x"]

        fig, ax = plt.subplots(1, 1, figsize=(14, 14), facecolor='#f5f0e8')
        ax.set_facecolor('#f5f0e8')
        ax.set_aspect('equal')
        ink = '#1a1a1a'
        lw_h = 2.8
        cc = '#444444'
        clw = 0.45
        con_a = 0.10

        ctx = {"ax": ax, "s": s, "cx": cx, "cy": cy, "comp": comp,
               "ink": ink, "lw_h": lw_h, "cc": cc, "clw": clw, "con_a": con_a,
               "sq_A_vx": sq_A_vx, "sq_A_vy": sq_A_vy,
               "sq_D_vx": sq_D_vx, "sq_D_vy": sq_D_vy, "vcircs": vcircs,
               "rect_ul": rect_ul, "rect_ll": rect_ll,
               "rect_w": rect_w, "rect_h": rect_h,
               "stem_r_x": stem_r_x, "rect_l_x": rect_l_x}

        self._draw_rings(ctx)
        self._draw_grid(ctx)
        self._draw_construction(ctx)
        self._draw_arcs(ctx)
        self._draw_closing_bars(ctx)
        self._draw_edges(ctx)
        self._draw_nib(ctx)
        self._draw_nodes(ctx)
        self._draw_hatching(ctx)
        self._draw_dimensions(ctx)

        ax.set_xlim(-6.5, 6.5)
        ax.set_ylim(-5.8, 5.2)
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='#f5f0e8')
        plt.close(fig)

    def _draw_rings(self, ctx):
        ax = ctx["ax"]
        for col, ro, ri, al in [('#6b6b6b', 4.8, 4.5, 0.75), ('#b87333', 4.5, 4.1, 0.85),
                                 ('#cd8c52', 4.1, 3.9, 0.80), ('#8c8c8c', 3.9, 3.7, 0.65)]:
            ax.add_patch(patches.Wedge((0, 0), ro, 0, 360, width=ro - ri,
                                       facecolor=col, edgecolor='none', alpha=al))
        for r in [4.8, 4.5, 3.9, 3.7]:
            ax.add_patch(plt.Circle((0, 0), r, fill=False, color='#4a4a4a', lw=0.5))

    def _draw_grid(self, ctx):
        ax, gc = ctx["ax"], '#aaaaaa'
        for off in np.arange(-3.5, 3.6, 0.7):
            ax.plot([-3.6, 3.6], [off, off], color=gc, lw=0.25, alpha=0.15)
            ax.plot([off, off], [-3.6, 3.6], color=gc, lw=0.25, alpha=0.15)

    def _draw_construction(self, ctx):
        ax, s = ctx["ax"], ctx["s"]
        cx, cy = ctx["cx"], ctx["cy"]
        cc, clw, con_a = ctx["cc"], ctx["clw"], ctx["con_a"]

        theta_f = np.linspace(0, 2 * np.pi, 360)
        for R in [s.r_gold, s.r_green, s.r_blue]:
            ax.plot(cx + R * np.cos(theta_f), cy + R * np.sin(theta_f),
                    color=cc, lw=clw, alpha=con_a * 0.8, linestyle=':', zorder=-2)

        sb = ctx["comp"]["shapes"]["Square.B"]["vertices"]
        corners = [(sb["upper_left"], sb["upper_right"]), (sb["upper_right"], sb["lower_right"]),
                   (sb["lower_right"], sb["lower_left"]), (sb["lower_left"], sb["upper_left"])]
        for p0, p1 in corners:
            ax.plot([p0["x"], p1["x"]], [p0["y"], p1["y"]],
                    color=cc, lw=clw * 0.8, alpha=con_a * 0.7, linestyle=':', zorder=-3)

        ax.plot(np.append(ctx["sq_A_vx"], ctx["sq_A_vx"][0]),
                np.append(ctx["sq_A_vy"], ctx["sq_A_vy"][0]),
                color=cc, lw=clw, alpha=con_a, linestyle='-', zorder=-2)
        ax.plot(np.append(ctx["sq_D_vx"], ctx["sq_D_vx"][0]),
                np.append(ctx["sq_D_vy"], ctx["sq_D_vy"][0]),
                color=cc, lw=clw * 0.8, alpha=con_a * 0.8, linestyle='-', zorder=-2)

        for vx, vy, vr in ctx["vcircs"]:
            ax.add_patch(plt.Circle((vx, vy), vr, fill=False, color=cc,
                                    lw=clw, alpha=con_a * 1.3, zorder=-2))

        ax.add_patch(patches.Rectangle((ctx["rect_ul"]["x"], ctx["rect_ll"]["y"]),
                     ctx["rect_w"], ctx["rect_h"],
                     linewidth=clw * 0.8, edgecolor=cc, facecolor='none',
                     alpha=con_a * 0.8, linestyle=':', zorder=-3))

        # Center crosshair
        ch = 0.12
        ax.plot([cx - ch, cx + ch], [cy, cy], color=cc, lw=0.5, alpha=0.12, zorder=-1)
        ax.plot([cx, cx], [cy - ch, cy + ch], color=cc, lw=0.5, alpha=0.12, zorder=-1)

    def _draw_arcs(self, ctx):
        ax, s, ink, lw_h = ctx["ax"], ctx["s"], ctx["ink"], ctx["lw_h"]
        for arc in s.arcs:
            ax.add_patch(patches.Arc((arc.cx, arc.cy), 2 * arc.radius, 2 * arc.radius,
                         theta1=arc.start_deg, theta2=arc.end_deg, color=ink, lw=lw_h, zorder=2))

    def _draw_closing_bars(self, ctx):
        ax, s, ink, lw_h = ctx["ax"], ctx["s"], ctx["ink"], ctx["lw_h"]
        cx, cy = ctx["cx"], ctx["cy"]
        for r_val, close_x in [(s.r_gold, ctx["rect_l_x"]),
                                (s.r_green, ctx["stem_r_x"]),
                                (s.r_blue, ctx["stem_r_x"])]:
            top_y, bot_y = cy + r_val, cy - r_val
            ax.plot([close_x, cx], [top_y, top_y], color=ink, lw=lw_h, zorder=2)
            ax.plot([close_x, cx], [bot_y, bot_y], color=ink, lw=lw_h, zorder=2)
            ax.plot([close_x, close_x], [bot_y, top_y], color=ink, lw=lw_h, zorder=2)

    def _draw_edges(self, ctx):
        ax, s, ink, lw_h = ctx["ax"], ctx["s"], ctx["ink"], ctx["lw_h"]
        nodes = [(n.x, n.y) for n in s.nodes]
        for e in s.edges:
            x1, y1 = nodes[e.from_id]
            x2, y2 = nodes[e.to_id]
            ax.plot([x1, x2], [y1, y2], color=ink, lw=lw_h, alpha=1.0,
                    solid_capstyle='round', zorder=2)

    def _draw_nib(self, ctx):
        ax, s, ink = ctx["ax"], ctx["s"], ctx["ink"]
        nib = s.nib
        ax.plot([p[0] for p in nib.outline], [p[1] for p in nib.outline],
                color=ink, lw=2.2, solid_capstyle='round', zorder=2)
        ax.plot([nib.slit_start[0], nib.slit_end[0]],
                [nib.slit_start[1], nib.slit_end[1]],
                color='#f5f0e8', lw=1.2, zorder=3)
        ax.add_patch(plt.Circle(nib.ball_pos, s.r_vertex * 0.12,
                     fc=ink, ec=ink, lw=0.8, zorder=4))

    def _draw_nodes(self, ctx):
        ax, s, ink = ctx["ax"], ctx["s"], ctx["ink"]
        for n in s.nodes:
            if n.id == 14:
                continue
            ax.add_patch(plt.Circle((n.x, n.y), 0.055, fc=ink, ec='#888888',
                         lw=0.4, alpha=0.6, zorder=5))

    def _draw_hatching(self, ctx):
        ax = ctx["ax"]
        def hatch(c, ri, ro, a1, a2, n=12, lw=0.5):
            for a in np.linspace(np.radians(a1), np.radians(a2), n):
                ax.plot([c[0] + ri * np.cos(a), c[0] + ro * np.cos(a)],
                        [c[1] + ri * np.sin(a), c[1] + ro * np.sin(a)],
                        color='#3a3a3a', lw=lw, alpha=0.6)

        ri, ro = 4.9, 5.8
        for s1, s2, n in [(120, 155, 18), (160, 195, 18), (200, 240, 20),
                          (-15, 25, 20), (30, 60, 15), (-60, -25, 18)]:
            hatch((0, 0), ri, ro, s1, s2, n, 0.4)

    def _draw_dimensions(self, ctx):
        ax, s = ctx["ax"], ctx["s"]
        cx, cy = ctx["cx"], ctx["cy"]
        dc, fs = '#4a4a4a', 6.5
        rect_ul, rect_ll = ctx["rect_ul"], ctx["rect_ll"]
        rect_l_x, stem_r_x = ctx["rect_l_x"], ctx["stem_r_x"]
        rect_w, rect_h = ctx["rect_w"], ctx["rect_h"]

        ax.annotate('', xy=(rect_l_x - 0.5, rect_ul["y"]),
                    xytext=(rect_l_x - 0.5, rect_ll["y"]),
                    arrowprops=dict(arrowstyle='<->', color=dc, lw=0.6))
        ax.text(rect_l_x - 0.75, (rect_ul["y"] + rect_ll["y"]) / 2, f'{rect_h:.2f}',
                fontsize=fs, ha='center', rotation=90, color=dc, fontfamily='serif', style='italic')

        ax.annotate('', xy=(stem_r_x + 0.05, rect_ll["y"] - 0.3),
                    xytext=(rect_l_x - 0.05, rect_ll["y"] - 0.3),
                    arrowprops=dict(arrowstyle='<->', color=dc, lw=0.6))
        ax.text((rect_l_x + stem_r_x) / 2, rect_ll["y"] - 0.5, f'{rect_w:.2f}',
                fontsize=fs, ha='center', color=dc, fontfamily='serif', style='italic')

        bw_r = cx + s.r_gold
        ax.annotate('', xy=(bw_r + 0.3, cy + s.r_gold),
                    xytext=(bw_r + 0.3, cy - s.r_gold),
                    arrowprops=dict(arrowstyle='<->', color=dc, lw=0.5))
        ax.text(bw_r + 0.5, cy, f'{2 * s.r_gold:.2f}', fontsize=5.5, ha='left',
                color=dc, fontfamily='serif', style='italic')
