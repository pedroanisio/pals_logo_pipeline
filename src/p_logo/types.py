"""P Logo data types — frozen dataclasses consumed by all renderers and exporters."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    id: int
    x: float
    y: float
    key_node: bool = False
    composition_point: str | None = None
    source: str = ""


@dataclass(frozen=True)
class Edge:
    from_id: int
    to_id: int
    edge_type: str = "mesh"  # contour | mesh | struct | nib

    @property
    def normalized(self) -> tuple[int, int]:
        return (min(self.from_id, self.to_id), max(self.from_id, self.to_id))


@dataclass(frozen=True)
class Arc:
    name: str
    cx: float
    cy: float
    radius: float
    start_angle: float  # radians
    sweep_angle: float  # radians

    @property
    def end_angle(self) -> float:
        return self.start_angle + self.sweep_angle

    @property
    def start_deg(self) -> float:
        import math
        return math.degrees(self.start_angle)

    @property
    def end_deg(self) -> float:
        import math
        return math.degrees(self.end_angle)


@dataclass(frozen=True)
class NibGeometry:
    outline: tuple[tuple[float, float], ...]
    slit_start: tuple[float, float]
    slit_end: tuple[float, float]
    ball_pos: tuple[float, float]
    ball_radius: float = 0.06


@dataclass(frozen=True)
class PLogoSchema:
    center: tuple[float, float]
    r_green: float
    r_blue: float
    r_gold: float
    r_vertex: float
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    arcs: tuple[Arc, ...]
    nib: NibGeometry
    composition: dict | None = None

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def node(self, idx: int) -> Node:
        return self.nodes[idx]

    def edges_of_type(self, edge_type: str) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.edge_type == edge_type)

    def neighbors(self, node_id: int) -> tuple[int, ...]:
        result = set()
        for e in self.edges:
            if e.from_id == node_id:
                result.add(e.to_id)
            elif e.to_id == node_id:
                result.add(e.from_id)
        return tuple(sorted(result))

    def degree(self, node_id: int) -> int:
        return len(self.neighbors(node_id))
