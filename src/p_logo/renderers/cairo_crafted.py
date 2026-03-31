"""Cairo Crafted Logic renderer — dark bg, copper/amber/bronze palette with glow."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from p_logo.types import PLogoSchema
from p_logo.renderers.base import PLogoRenderer

try:
    import cairo
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False

PALETTE = {
    "bg_deep": (14/255, 8/255, 32/255),
    "bg_circle": (21/255, 13/255, 46/255),
    "rosegold": (196/255, 135/255, 110/255),
    "copper": (90/255, 158/255, 140/255),
    "bronze": (184/255, 122/255, 78/255),
    "amber": (232/255, 168/255, 76/255),
    "blueglow": (91/255, 143/255, 212/255),
    "warmwht": (255/255, 236/255, 210/255),
}

# Per-node color key — maps node id to palette key
NODE_COLORS = {
    0: "blueglow", 1: "amber", 7: "amber", 9: "amber", 11: "amber",
    16: "bronze", 17: "bronze", 18: "amber", 19: "amber", 20: "bronze",
    14: "warmwht", 24: "amber",
}
ARC_COLORS = ["amber", "copper", "bronze"]
ARC_LW = [2.2, 1.8, 2.2]

P_SCALE = 1.28
P_OFFSET_Y = 0.255


class CairoCraftedRenderer(PLogoRenderer):
    """Renders the P logo in the Crafted Logic visual style using pycairo."""

    def render(
        self,
        output_path: str,
        size: int = 1200,
        debug: bool = False,
        transparent: bool = False,
    ) -> None:
        if not HAS_CAIRO:
            raise ImportError("pycairo is required for CairoCraftedRenderer")

        ppu = size / 10.0
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        ctx = cairo.Context(s)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)

        self._draw(ctx, size, ppu, transparent, debug)
        s.write_to_png(output_path)

    def _to_px(self, x, y, ppu, pg=True):
        if pg:
            x, y = x * P_SCALE, (y + P_OFFSET_Y) * P_SCALE
        return (x + 5) * ppu, (5 - y) * ppu

    def _draw(self, ctx, sz, ppu, transparent, debug):
        pal = PALETTE
        s = self.schema

        # Background
        if transparent:
            ctx.set_source_rgba(0, 0, 0, 0)
        else:
            ctx.set_source_rgb(*pal["bg_deep"])
        ctx.paint()

        cx, cy = self._to_px(0, 0, ppu, False)
        rb = 4.55 * ppu

        ctx.arc(cx, cy, rb, 0, 2 * math.pi)
        ctx.set_source_rgb(*pal["bg_circle"])
        ctx.fill()

        # Ring
        rm = (4.55 + 4.72) / 2 * ppu
        ctx.set_line_width((4.72 - 4.55) * ppu)
        ctx.set_source_rgba(*pal["rosegold"], 0.92)
        ctx.arc(cx, cy, rm, 0, 2 * math.pi)
        ctx.stroke()

        # Edges
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for e in s.edges:
            n1, n2 = s.node(e.from_id), s.node(e.to_id)
            c1 = pal[NODE_COLORS.get(e.from_id, "copper")]
            c2 = pal[NODE_COLORS.get(e.to_id, "copper")]
            col = tuple((c1[i] + c2[i]) / 2 for i in range(3))
            x1, y1 = self._to_px(n1.x, n1.y, ppu)
            x2, y2 = self._to_px(n2.x, n2.y, ppu)
            if not debug:
                ctx.set_source_rgba(*col, 0.12)
                ctx.set_line_width(5)
                ctx.move_to(x1, y1)
                ctx.line_to(x2, y2)
                ctx.stroke()
            ctx.set_source_rgba(*col, 0.55 if not debug else 0.4)
            ctx.set_line_width(2.5 if debug else 1.5)
            ctx.move_to(x1, y1)
            ctx.line_to(x2, y2)
            ctx.stroke()

        # Arcs
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for i, arc in enumerate(s.arcs):
            ax, ay = self._to_px(arc.cx, arc.cy, ppu)
            rp = arc.radius * P_SCALE * ppu
            a0 = -(arc.start_angle + arc.sweep_angle)
            a1 = -arc.start_angle
            col = pal[ARC_COLORS[i]]
            if not debug:
                ctx.set_source_rgba(*col, 0.15)
                ctx.set_line_width(ARC_LW[i] + 6)
                ctx.arc(ax, ay, rp, a0, a1)
                ctx.stroke()
            ctx.set_source_rgba(*col, 0.7 if not debug else 0.5)
            ctx.set_line_width(ARC_LW[i])
            ctx.arc(ax, ay, rp, a0, a1)
            ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        # Nib
        nib = s.nib
        pts = [self._to_px(p[0], p[1], ppu) for p in nib.outline]
        if not debug:
            ctx.set_source_rgba(*pal["copper"], 0.15)
            ctx.set_line_width(5)
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.stroke()
        ctx.set_source_rgba(*pal["copper"], 0.8)
        ctx.set_line_width(1.8)
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.stroke()

        # Nib slit + ball
        ctx.set_source_rgba(*pal["blueglow"], 0.4)
        ctx.set_line_width(1.2)
        ctx.move_to(*self._to_px(*nib.slit_start, ppu))
        ctx.line_to(*self._to_px(*nib.slit_end, ppu))
        ctx.stroke()
        nbx, nby = self._to_px(*nib.ball_pos, ppu)
        ctx.set_source_rgb(*pal["copper"])
        ctx.arc(nbx, nby, 4 * P_SCALE, 0, 2 * math.pi)
        ctx.fill()

        # Nodes
        deg = defaultdict(int)
        for e in s.edges:
            deg[e.from_id] += 1
            deg[e.to_id] += 1

        for n in s.nodes:
            px, py = self._to_px(n.x, n.y, ppu)
            col = pal[NODE_COLORS.get(n.id, "copper")]
            cr = (6.0 if n.key_node else 3.8) * P_SCALE * (1.5 if debug else 1.0)

            if not debug:
                gr = (22 if n.key_node else 14) * P_SCALE
                for l in range(8):
                    t = l / 8
                    r = gr * (0.15 + 0.85 * t)
                    a = (0.4 if n.key_node else 0.28) * (1 - t) ** 2
                    pat = cairo.RadialGradient(px, py, 0, px, py, r)
                    pat.add_color_stop_rgba(0, *col, a)
                    pat.add_color_stop_rgba(1, *col, 0)
                    ctx.set_source(pat)
                    ctx.arc(px, py, r, 0, 2 * math.pi)
                    ctx.fill()

            ctx.set_source_rgba(*col, 1.0)
            ctx.arc(px, py, cr, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(1, 1, 1, 0.35 if n.key_node else 0.2)
            ctx.arc(px, py, cr * 0.35, 0, 2 * math.pi)
            ctx.fill()

        # Particles (skip in debug)
        if not debug:
            random.seed(42)
            for _ in range(55):
                ang = random.random() * 2 * math.pi
                rad = 0.6 + random.random() * 3.8
                ppx, ppy = self._to_px(math.cos(ang) * rad, math.sin(ang) * rad, ppu, False)
                dx, dy = ppx - cx, ppy - cy
                if math.sqrt(dx * dx + dy * dy) > rb - 8:
                    continue
                c = random.choice([pal["copper"], pal["amber"], pal["bronze"], pal["warmwht"], pal["blueglow"]])
                ctx.set_source_rgba(*c, 0.12 + random.random() * 0.22)
                ctx.arc(ppx, ppy, 1.0 + random.random() * 2.0, 0, 2 * math.pi)
                ctx.fill()

        # Vignette
        vig = cairo.RadialGradient(cx, cy, rb * 0.45, cx, cy, rb)
        vig.add_color_stop_rgba(0, *pal["bg_circle"], 0)
        vig.add_color_stop_rgba(1, *pal["bg_circle"], 0.15 if debug else 0.35)
        ctx.set_source(vig)
        ctx.arc(cx, cy, rb, 0, 2 * math.pi)
        ctx.fill()
