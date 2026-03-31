"""Node color resolution — shared between HTML and SVG exporters.

Applies geometric rules (based on composition_point and key_node) to
assign a color key to each node.  Color keys are upper-case strings
(e.g. "AMBER") that map to palette entries via COLOR_KEY_TO_PALETTE.
"""

from __future__ import annotations

from p_logo.types import Node


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
