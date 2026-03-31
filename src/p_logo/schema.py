"""
P Logo Schema — single entry point for all geometry.

build_schema() produces a frozen PLogoSchema with 25 nodes, 44 typed edges,
3 arcs, and nib geometry. All values derived from SC + R_GREEN via the
√2 chain and geometric_composition_final.generate_composition().
"""

from __future__ import annotations

import math
from p_logo.types import Node, Edge, Arc, NibGeometry, PLogoSchema
from p_logo.composition import generate_p_composition

# Default free parameters
DEFAULT_CENTER = (0.3504, 0.8694)
DEFAULT_R_GREEN = 1.2303


def build_schema(
    center: tuple[float, float] = DEFAULT_CENTER,
    r_green: float = DEFAULT_R_GREEN,
) -> PLogoSchema:
    """
    Build the complete P logo schema from two free parameters.

    All geometry is derived from the composition via the √2 chain:
        R_BLUE  = R_GREEN / √2
        R_GREEN = free parameter
        R_GOLD  = R_GREEN × √2
    """
    cx, cy = center

    # ── Derive from composition ───────────────────────────────
    comp = generate_p_composition(center=center, r_green=r_green)

    r_blue = comp["shapes"]["Circ.D"]["radius"]
    r_gold = comp["shapes"]["Circ.A"]["radius"]
    r_vertex = r_gold - r_green
    g45 = r_green / math.sqrt(2)

    rect = comp["shapes"]["Rect.1"]
    rect_r = rect["vertices"]["upper_right"]["x"]
    rect_bot = rect["vertices"]["lower_left"]["y"]
    rect_h = rect["height"]

    circ_ri = comp["shapes"]["Circ.Rect.I"]
    circ_rv = comp["shapes"]["Circ.Rect.V"]
    nib_cx = circ_ri["center"]["x"]
    nib_circ_cy = circ_ri["center"]["y"]
    nib_tip_y = circ_rv["center"]["y"]

    # ── 25 nodes ──────────────────────────────────────────────
    _nodes_raw = [
        (cx - r_gold, cy + r_gold,            False, "P.SQAB.UL",           "Square.B upper-left"),
        (cx,          cy + r_gold,            True,  "P.CENTER.A",          "center x, Square.B top y"),
        (cx + g45,    cy + g45,               False, "P.SQD.D1",            "Square.D vertex 45°"),
        (cx,          cy - r_blue,            False, "P.CA.TANGENT.BOTTOM", "Circ.D tangent bottom"),
        (cx - r_green, cy + r_green,          False, "P.SQA.V2",            "Square.A left x, Circ.Bounds.A tangent top y"),
        (cx,          cy + r_blue,            False, "P.CA.TANGENT.TOP",    "Circ.D tangent top"),
        (cx + r_blue, cy,                     False, "P.CA.TANGENT.RIGHT",  "Circ.D tangent right"),
        (cx - r_gold, cy - r_blue,            True,  "P.SQAB.UL",           "Square.B left x, Circ.D bottom y"),
        (rect_r,      cy - r_blue,            False, "P.RECT.UR",           "Rect.1 right x, Circ.D bottom y"),
        (cx - r_green, cy - r_green,          True,  "P.SQA.V3",            "Square.A left x, Circ.Bounds.A tangent bottom y"),
        (rect_r,      cy - r_gold,            False, "P.RECT.LR",           "Rect.1 right x, Square.B bottom y"),
        (cx - r_gold, cy - r_gold,            True,  "P.SQAB.LL",           "Square.B lower-left"),
        (nib_cx,      nib_circ_cy + r_vertex, False, "P.CIRC.RECT.I",       "Circ.Rect.I top"),
        (nib_cx,      nib_circ_cy,            False, "P.CIRC.RECT.I.CENTER","Circ.Rect.I center"),
        (nib_cx,      nib_tip_y,              False, "P.CIRC.RECT.V.CENTER","Circ.Rect.V center"),
        (rect_r,      cy + r_blue,            False, "P.RECT.UR",           "Rect.1 right x, Circ.D top y"),
        (rect_r,      cy - r_gold,            True,  "P.RECT.LR",           "Rect.1 right x, Circ.A bottom y"),
        (cx,          cy - r_gold,            True,  "P.CA.TANGENT.BOTTOM", "Circ.A tangent bottom"),
        (cx,          cy - r_green,           True,  None,                   "Circ.Bounds.A tangent bottom"),
        (cx,          cy + r_green,           True,  None,                   "Circ.Bounds.A tangent top"),
        (cx + r_gold, cy,                     True,  "P.CA.TANGENT.RIGHT",  "Circ.A tangent right"),
        (cx + g45,    cy - g45,               False, "P.SQD.D4",            "Square.D vertex 315°"),
        (cx - r_gold, nib_circ_cy + r_vertex, False, "P.RECT.LL.WAIST",     "Rect.1 left at Circ.Rect.I top y"),
        (rect_r,      nib_circ_cy + r_vertex, False, "P.RECT.LR.WAIST",     "Rect.1 right at Circ.Rect.I top y"),
        (nib_cx,      (cy - r_gold + nib_circ_cy + r_vertex) / 2, False, "P.BUMP.HUB", "Bump center hub"),
    ]

    nodes = tuple(
        Node(id=i, x=round(x, 4), y=round(y, 4), key_node=key,
             composition_point=pt, source=src)
        for i, (x, y, key, pt, src) in enumerate(_nodes_raw)
    )

    # ── 44 edges with type classification ─────────────────────
    _edges_typed = [
        # Outer contour (6)
        (0, 1, "contour"), (7, 0, "contour"), (11, 7, "contour"),
        (7, 8, "contour"), (3, 8, "contour"), (16, 10, "contour"),
        # Stem/triangle diagonals (4)
        (7, 9, "struct"), (8, 9, "struct"), (9, 10, "struct"), (9, 11, "struct"),
        # Nib — bump pattern (14)
        (11, 22, "nib"), (10, 23, "nib"), (22, 23, "nib"),
        (10, 22, "nib"), (11, 23, "nib"),
        (24, 10, "nib"), (24, 11, "nib"), (24, 22, "nib"), (24, 23, "nib"), (24, 12, "nib"),
        (22, 12, "nib"), (23, 12, "nib"),
        (12, 13, "nib"), (13, 14, "nib"),
        # Inner counter / D-shape (7)
        (4, 9, "mesh"), (4, 19, "mesh"), (0, 4, "mesh"),
        (15, 4, "mesh"), (15, 5, "mesh"), (15, 7, "mesh"), (15, 8, "mesh"),
        # Bowl / arc nodes (3)
        (2, 5, "mesh"), (2, 6, "mesh"), (2, 20, "mesh"),
        # Bottom bowl (6)
        (18, 9, "mesh"), (17, 16, "mesh"),
        (20, 21, "mesh"), (21, 17, "mesh"), (6, 20, "mesh"), (6, 21, "mesh"),
        # Right-side vertical connectors (2)
        (3, 18, "mesh"), (17, 18, "mesh"),
        # Arc-bridge + bowl top (2)
        (2, 21, "mesh"), (21, 3, "mesh"),
    ]

    edges = tuple(
        Edge(from_id=a, to_id=b, edge_type=t)
        for a, b, t in _edges_typed
    )
    assert len(edges) == 44, f"Expected 44 edges, got {len(edges)}"

    # ── 3 arcs (all π semicircles) ────────────────────────────
    arcs = (
        Arc("Green", cx, cy, r_green, -math.pi / 2, math.pi),
        Arc("Blue",  cx, cy, r_blue,  -math.pi / 2, math.pi),
        Arc("Gold",  cx, cy, r_gold,  -math.pi / 2, math.pi),
    )

    # ── Nib geometry ──────────────────────────────────────────
    waist_y = nib_circ_cy + r_vertex
    nib = NibGeometry(
        outline=(
            (nib_cx, nib_tip_y),
            (rect_r, waist_y),
            (nib_cx, waist_y - 0.25),
            (cx - r_gold, waist_y),
            (nib_cx, nib_tip_y),
        ),
        slit_start=(nib_cx, nib_tip_y + 0.05),
        slit_end=(nib_cx, nib_circ_cy + 0.05),
        ball_pos=(nib_cx, nib_circ_cy),
    )

    return PLogoSchema(
        center=center,
        r_green=r_green,
        r_blue=r_blue,
        r_gold=r_gold,
        r_vertex=r_vertex,
        nodes=nodes,
        edges=edges,
        arcs=arcs,
        nib=nib,
        composition=comp,
    )
