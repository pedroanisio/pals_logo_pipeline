"""Composition wrapper — maps geometric_composition into P-logo coordinates."""

from __future__ import annotations

import math
from p_logo.geometric_composition import generate_composition


def generate_p_composition(
    center: tuple[float, float] = (0.3504, 0.8694),
    r_green: float = 1.2303,
) -> dict:
    """
    Map the base geometric composition into P-logo coordinate space.

    The composition's Circ.D (R=100) maps to the Blue arc (R_GREEN/√2).
    Returns the raw composition dict with scale/origin applied.
    """
    r_blue = r_green / math.sqrt(2)
    scale = r_blue / 100.0
    ox = center[0] - 600 * scale
    oy = center[1] - 800 * scale
    return generate_composition(scale=scale, origin_x=ox, origin_y=oy)
