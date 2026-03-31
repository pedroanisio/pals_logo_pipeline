"""
PAL's Notes Logo Pipeline — projection.py contract test.

Locks the projection output format and counts before refactoring.
"""

from __future__ import annotations
import json
import math
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def projection_module():
    import projection
    return projection


@pytest.fixture(scope="session")
def point_field_module():
    import point_field
    return point_field


@pytest.fixture(scope="session")
def field(point_field_module):
    return point_field_module.generate_field()


@pytest.fixture(scope="session")
def proj(projection_module, field):
    return projection_module.project(field)


# ── Structure ─────────────────────────────────────────────────

class TestProjectionStructure:
    def test_has_nodes(self, proj):
        assert "nodes" in proj
        assert isinstance(proj["nodes"], list)

    def test_has_edges(self, proj):
        assert "edges" in proj

    def test_has_typed_edges(self, proj):
        assert "typed_edges" in proj

    def test_has_arc_definitions(self, proj):
        assert "arc_definitions" in proj

    def test_has_junction_index(self, proj):
        assert "junction_index" in proj

    def test_has_provenance(self, proj):
        assert "provenance" in proj


# ── Counts ────────────────────────────────────────────────────

class TestProjectionCounts:
    def test_25_nodes(self, proj):
        assert len(proj["nodes"]) == 25

    def test_44_typed_edges(self, proj):
        assert len(proj["typed_edges"]) == 44

    def test_44_flat_edges(self, proj):
        assert len(proj["edges"]) == 44

    def test_3_arcs(self, proj):
        assert len(proj["arc_definitions"]) == 3

    def test_junction_index_is_9(self, proj):
        assert proj["junction_index"] == 9


# ── Node fields ───────────────────────────────────────────────

class TestNodeFields:
    def test_all_nodes_have_required_fields(self, proj):
        for n in proj["nodes"]:
            assert "index" in n
            assert "x" in n
            assert "y" in n
            assert "color" in n
            assert "region" in n
            assert "source_point" in n
            assert "alias" in n

    def test_indices_sequential(self, proj):
        indices = sorted(n["index"] for n in proj["nodes"])
        assert indices == list(range(25))

    def test_coordinates_are_finite(self, proj):
        for n in proj["nodes"]:
            assert math.isfinite(n["x"])
            assert math.isfinite(n["y"])


# ── Edge types ────────────────────────────────────────────────

class TestEdgeTypes:
    def test_contour_count(self, proj):
        types = Counter(e["type"] for e in proj["typed_edges"])
        assert types["contour"] == 6

    def test_struct_count(self, proj):
        types = Counter(e["type"] for e in proj["typed_edges"])
        assert types["struct"] == 4

    def test_nib_count(self, proj):
        types = Counter(e["type"] for e in proj["typed_edges"])
        assert types["nib"] == 14

    def test_mesh_count(self, proj):
        types = Counter(e["type"] for e in proj["typed_edges"])
        assert types["mesh"] == 20

    def test_only_four_types(self, proj):
        types = set(e["type"] for e in proj["typed_edges"])
        assert types == {"contour", "struct", "nib", "mesh"}


# ── Arcs ──────────────────────────────────────────────────────

class TestArcs:
    def test_all_semicircles(self, proj):
        for arc in proj["arc_definitions"]:
            assert arc["start_angle"] == pytest.approx(-math.pi / 2, abs=1e-4)
            assert arc["end_angle"] == pytest.approx(math.pi / 2, abs=1e-4)

    def test_arc_radii(self, proj):
        radii = sorted(a["radius"] for a in proj["arc_definitions"])
        assert radii[0] == pytest.approx(0.8700, abs=0.01)   # Blue
        assert radii[1] == pytest.approx(1.2303, abs=0.01)   # Green
        assert radii[2] == pytest.approx(1.7399, abs=0.01)   # Gold

    def test_shared_center(self, proj):
        for arc in proj["arc_definitions"]:
            assert arc["cx"] == pytest.approx(0.3504, abs=1e-3)
            assert arc["cy"] == pytest.approx(0.8694, abs=1e-3)


# ── Provenance ────────────────────────────────────────────────

# ── p_logo schema agreement ───────────────────────────────────

class TestSchemaAgreement:
    """Non-nib nodes, edges, and arcs must match p_logo library."""

    def test_non_nib_nodes_match_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        nib_ids = {12, 13, 14, 22, 23, 24}
        for n in proj["nodes"]:
            if n["index"] in nib_ids:
                continue
            sn = schema.nodes[n["index"]]
            assert abs(n["x"] - sn.x) < 0.001, f"Node {n['index']} x: {n['x']} vs {sn.x}"
            assert abs(n["y"] - sn.y) < 0.001, f"Node {n['index']} y: {n['y']} vs {sn.y}"

    def test_edge_set_matches_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        pipe_set = set((e["a"], e["b"]) for e in proj["typed_edges"])
        schema_set = set(e.normalized for e in schema.edges)
        assert pipe_set == schema_set

    def test_edge_types_match_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        pipe_typed = set((e["a"], e["b"], e["type"]) for e in proj["typed_edges"])
        schema_typed = set((min(e.from_id, e.to_id), max(e.from_id, e.to_id), e.edge_type) for e in schema.edges)
        assert pipe_typed == schema_typed

    def test_arc_radii_match_schema(self, proj):
        from p_logo import build_schema
        schema = build_schema()
        pipe_radii = sorted(a["radius"] for a in proj["arc_definitions"])
        schema_radii = sorted(a.radius for a in schema.arcs)
        for pr, sr in zip(pipe_radii, schema_radii):
            assert abs(pr - sr) < 1e-6

    def test_nib_nodes_diverge_from_schema(self, proj):
        """Document the known nib coordinate divergence (0.808 Y offset).
        This test will FAIL when/if the nib is eventually aligned,
        serving as a canary for intentional alignment."""
        from p_logo import build_schema
        schema = build_schema()
        nib_ids = {12, 13, 14, 22, 23}  # Not 24 (hub has half the offset)
        for n in proj["nodes"]:
            if n["index"] in nib_ids:
                sn = schema.nodes[n["index"]]
                assert abs(n["y"] - sn.y) > 0.5, \
                    f"Node {n['index']}: nib divergence may have been resolved"


# ── Provenance ────────────────────────────────────────────────

class TestProvenance:
    def test_field_points_total(self, proj):
        assert proj["provenance"]["field_points_total"] >= 40

    def test_nodes_selected(self, proj):
        assert proj["provenance"]["nodes_selected"] == 25
