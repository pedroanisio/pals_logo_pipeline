"""
Regression tests for LOW priority refactors:
  1. graph.py — unify lazy loading, remove _LazyData
  2. projection.py — defer schema dependency

Locks current behavior before cleanup.
"""

import json
import sys
import hashlib
import math
import pytest
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

BUILD_DIR = ROOT / "src" / "p_logo_pipeline" / "build"


# ──────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def palette():
    with open(BUILD_DIR / "palette.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def field():
    from p_logo_pipeline.point_field import generate_field
    return generate_field()


@pytest.fixture(scope="module")
def graph(palette):
    from p_logo_pipeline.graph import build_graph
    return build_graph(palette)


@pytest.fixture(scope="module")
def proj(field):
    from p_logo_pipeline.projection import project
    return project(field)


# ══════════════════════════════════════════════════════
# 1. graph.py
# ══════════════════════════════════════════════════════

class TestGraphModuleAPI:
    """Module must expose these public constants and functions."""

    def test_has_node_positions(self):
        from p_logo_pipeline.graph import NODE_POSITIONS
        assert len(NODE_POSITIONS) == 25

    def test_has_edges(self):
        from p_logo_pipeline.graph import EDGES
        assert len(EDGES) == 44

    def test_has_node_colors(self):
        from p_logo_pipeline.graph import NODE_COLORS
        assert len(NODE_COLORS) == 25

    def test_has_junction_index(self):
        from p_logo_pipeline.graph import JUNCTION_NODE_INDEX
        assert JUNCTION_NODE_INDEX == 9

    def test_has_build_graph(self):
        from p_logo_pipeline.graph import build_graph
        assert callable(build_graph)

    def test_has_validate(self):
        from p_logo_pipeline.graph import validate
        assert callable(validate)

    def test_has_write_graph(self):
        from p_logo_pipeline.graph import write_graph
        assert callable(write_graph)


class TestGraphOutput:
    def test_node_count(self, graph):
        assert len(graph["nodes"]) == 25

    def test_edge_count(self, graph):
        assert len(graph["edges"]) == 44

    def test_meta_step(self, graph):
        assert graph["_meta"]["step"] == 1

    def test_stats(self, graph):
        s = graph["stats"]
        assert s["node_count"] == 25
        assert s["edge_count"] == 44
        assert s["max_degree"] == 6
        assert s["junction_index"] == 9
        assert s["avg_degree"] == pytest.approx(3.52)

    def test_adjacency_all_nodes(self, graph):
        for i in range(25):
            assert str(i) in graph["adjacency"]

    def test_adjacency_symmetric(self, graph):
        adj = graph["adjacency"]
        for node_str, neighbors in adj.items():
            for nb in neighbors:
                assert int(node_str) in adj[str(nb)]

    def test_edge_types_present(self, graph):
        types = set(e.get("type", "mesh") for e in graph["edges"])
        assert types == {"contour", "struct", "nib", "mesh"}

    def test_has_edge_thickness(self, graph):
        assert "edge_thickness" in graph
        assert graph["edge_thickness"] > 0

    def test_has_edge_opacity(self, graph):
        assert "edge_opacity" in graph
        assert 0 < graph["edge_opacity"] <= 1


class TestGraphValidation:
    def test_validate_passes(self, palette):
        from p_logo_pipeline.graph import validate
        errors = validate(palette)
        assert errors == []


class TestGraphDeterminism:
    def test_output_deterministic(self, palette):
        from p_logo_pipeline.graph import build_graph
        g1 = build_graph(palette)
        g2 = build_graph(palette)
        h1 = hashlib.sha256(json.dumps(g1, sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(g2, sort_keys=True).encode()).hexdigest()
        assert h1 == h2

    def test_hash_matches_snapshot(self, graph):
        h = hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()
        assert h[:16] == "4ef64e24276d6f06"


# ══════════════════════════════════════════════════════
# 2. projection.py
# ══════════════════════════════════════════════════════

class TestProjectionModuleAPI:
    def test_has_project(self):
        from p_logo_pipeline.projection import project
        assert callable(project)

    def test_has_write_projection(self):
        from p_logo_pipeline.projection import write_projection
        assert callable(write_projection)

    def test_has_default_edge_rules(self):
        from p_logo_pipeline.projection import DEFAULT_EDGE_RULES
        assert len(DEFAULT_EDGE_RULES) == 44

    def test_has_node_metadata(self):
        from p_logo_pipeline.projection import NODE_METADATA
        assert len(NODE_METADATA) == 25

    def test_has_default_arc_segments(self):
        from p_logo_pipeline.projection import DEFAULT_ARC_SEGMENTS
        assert len(DEFAULT_ARC_SEGMENTS) == 3


class TestProjectionOutput:
    def test_node_count(self, proj):
        assert len(proj["nodes"]) == 25

    def test_edge_count(self, proj):
        assert len(proj["edges"]) == 44

    def test_typed_edge_count(self, proj):
        assert len(proj["typed_edges"]) == 44

    def test_arc_count(self, proj):
        assert len(proj["arc_definitions"]) == 3

    def test_junction_index(self, proj):
        assert proj["junction_index"] == 9

    def test_node_fields(self, proj):
        for n in proj["nodes"]:
            assert "index" in n
            assert "x" in n and "y" in n
            assert "color" in n
            assert "region" in n
            assert "source_point" in n
            assert "alias" in n

    def test_edge_type_counts(self, proj):
        types = Counter(e["type"] for e in proj["typed_edges"])
        assert types["contour"] == 6
        assert types["struct"] == 4
        assert types["nib"] == 14
        assert types["mesh"] == 20

    def test_arc_radii(self, proj):
        radii = sorted(a["radius"] for a in proj["arc_definitions"])
        assert radii[0] == pytest.approx(0.8700, abs=0.01)
        assert radii[1] == pytest.approx(1.2303, abs=0.01)
        assert radii[2] == pytest.approx(1.7399, abs=0.01)

    def test_all_semicircles(self, proj):
        for arc in proj["arc_definitions"]:
            assert arc["start_angle"] == pytest.approx(-math.pi / 2, abs=1e-4)
            assert arc["end_angle"] == pytest.approx(math.pi / 2, abs=1e-4)


class TestProjectionSchemaAgreement:
    """All node positions and edges must match the canonical p_logo schema."""

    def test_node_positions_match_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        for n in proj["nodes"]:
            sn = schema.nodes[n["index"]]
            assert abs(n["x"] - sn.x) < 0.01, f"Node {n['index']} x: {n['x']} vs {sn.x}"
            assert abs(n["y"] - sn.y) < 0.01, f"Node {n['index']} y: {n['y']} vs {sn.y}"

    def test_edge_set_matches_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        pipe_set = set((e["a"], e["b"]) for e in proj["typed_edges"])
        schema_set = set(e.normalized for e in schema.edges)
        assert pipe_set == schema_set


class TestProjectionDeterminism:
    def test_output_deterministic(self, field):
        from p_logo_pipeline.projection import project
        p1 = project(field)
        p2 = project(field)
        h1 = hashlib.sha256(json.dumps(p1, sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(p2, sort_keys=True).encode()).hexdigest()
        assert h1 == h2

    def test_hash_matches_snapshot(self, proj):
        h = hashlib.sha256(json.dumps(proj, sort_keys=True).encode()).hexdigest()
        assert h[:16] == "e78ee8b00a15a235"
