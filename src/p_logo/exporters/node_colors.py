"""Node color and sizing resolution — shared between HTML and SVG exporters.

Color: geometric rules (based on composition_point and key_node) assign a
color key to each node.  Keys are upper-case strings (e.g. "AMBER") that
map to palette entries via COLOR_KEY_TO_PALETTE.

Sizing: the canonical model is degree-scaled via a √2-chain derived from
r_green (the single free parameter).  This matches the Three.js animated
render in animated_revision.html.

    R_VERTEX = r_green × (√2 − 1)
    BASE_R   = R_VERTEX × 0.035
    core_r(d) = BASE_R × (√2)^(d − 1)
    glow_r(d) = core_r × GLOW_SCALE
    glow_opacity(d) = GLOW_BASE_OPACITY + GLOW_DEG_BOOST × d
"""

from __future__ import annotations

import math
from collections import Counter

from p_logo.types import Node, PLogoSchema


# ── Color key → palette name ─────────────────────────────────

COLOR_KEY_TO_PALETTE: dict[str, str] = {
    "COPPER":   "copper",
    "AMBER":    "amber",
    "BRONZE":   "bronze",
    "BLUEGLOW": "blue_glow",
    "WARMWHT":  "warm_white",
    "ROSEGOLD": "rose_gold",
}


# ── Predicate functions ──────────────────────────────────────

def _is_nib_tip(node: Node) -> bool:
    return node.composition_point == "P.CIRC.RECT.V.CENTER"


def _is_corner_accent(node: Node) -> bool:
    return node.composition_point == "P.SQAB.UL" and not node.key_node


def _is_bump_hub(node: Node) -> bool:
    return node.composition_point == "P.BUMP.HUB"


def _is_arc_anchor(node: Node) -> bool:
    if not node.key_node:
        return False
    bronze_points = {
        "P.CA.TANGENT.BOTTOM", "P.CA.TANGENT.RIGHT",
        "P.RECT.LR", "P.RECT.UR",
    }
    return node.composition_point in bronze_points


def _is_key(node: Node) -> bool:
    return node.key_node


# Applied in order; first match wins.
_COLOR_RULES: list[tuple] = [
    (_is_nib_tip,       "WARMWHT"),
    (_is_corner_accent, "BLUEGLOW"),
    (_is_bump_hub,      "AMBER"),
    (_is_arc_anchor,    "BRONZE"),
    (_is_key,           "AMBER"),
]

DEFAULT_COLOR: str = "COPPER"


# ── Public API ───────────────────────────────────────────────

def resolve_node_color(node: Node) -> str:
    """Apply color rules to a node, return the color key string."""
    for predicate, color in _COLOR_RULES:
        if predicate(node):
            return color
    return DEFAULT_COLOR


# Arc style config (indexed by position in schema.arcs)
ARC_STYLES: list[dict[str, object]] = [
    {"color": "AMBER",  "opacity": 0.7},   # Green arc → Amber
    {"color": "COPPER", "opacity": 0.6},   # Blue arc  → Copper
    {"color": "BRONZE", "opacity": 0.55},  # Gold arc  → Bronze
]

# Edge color by type
EDGE_COLOR: str = "COPPER"


# ── Canonical degree-based sizing ────────────────────────────
# From animated_revision.html — the single source of truth for
# node radii.  All values derive from r_green via the √2-chain.

_BASE_R_FACTOR = 0.035   # BASE_R = R_VERTEX × this
GLOW_SCALE = 5.0         # glow_r = core_r × this
GLOW_BASE_OPACITY = 0.4  # glow_opacity = this + DEG_BOOST × degree
GLOW_DEG_BOOST = 0.08


def compute_degrees(schema: PLogoSchema) -> list[int]:
    """Compute per-node degree from schema edges."""
    counts: Counter[int] = Counter()
    for e in schema.edges:
        counts[e.from_id] += 1
        counts[e.to_id] += 1
    return [counts.get(i, 0) for i in range(len(schema.nodes))]


def node_core_radius(r_green: float, degree: int) -> float:
    """Canonical core radius for a node of given degree.

    r_core(d) = R_VERTEX × 0.035 × (√2)^(d − 1)
    where R_VERTEX = r_green × (√2 − 1).
    """
    r_vertex = r_green * (math.sqrt(2) - 1)
    base_r = r_vertex * _BASE_R_FACTOR
    return base_r * math.pow(math.sqrt(2), degree - 1)


def node_glow_radius(core_r: float) -> float:
    """Glow radius from core radius."""
    return core_r * GLOW_SCALE


def node_glow_opacity(degree: int) -> float:
    """Per-node glow opacity scaled by degree."""
    return GLOW_BASE_OPACITY + GLOW_DEG_BOOST * degree
