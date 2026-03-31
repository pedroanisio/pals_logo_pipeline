"""
Tests to lock current geometric_p_logo.py behavior before refactoring
to consume geometric_composition_final.py as single source of truth.

These tests capture the exact node positions, edge count, arc definitions,
and schema output BEFORE the refactor. The refactor must not change any output.
"""

import json
import sys
import numpy as np
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

# ── Snapshot current schema as ground truth ──────────────────────
@pytest.fixture(scope="module")
def schema():
    schema_path = ROOT / "build" / "p_logo_schema.json"
    assert schema_path.exists(), "Run geometric_p_logo.py first to generate schema"
    with open(schema_path) as f:
        return json.load(f)


class TestSchemaStructure:
    def test_node_count(self, schema):
        assert len(schema["graph"]["nodes"]) == 25

    def test_edge_count(self, schema):
        assert len(schema["graph"]["edges"]) == 44

    def test_arc_count(self, schema):
        assert len(schema["geometry"]["arcs"]) == 3


class TestCoordinateSystem:
    def test_shared_center(self, schema):
        sc = schema["coordinate_system"]["P.CENTER.A"]
        assert sc["x"] == pytest.approx(0.3504, abs=1e-4)
        assert sc["y"] == pytest.approx(0.8694, abs=1e-4)

    def test_r_green(self, schema):
        r = schema["coordinate_system"]["derived_radii"]["Circ.Bounds.A"]["value"]
        assert r == pytest.approx(1.2303, abs=1e-4)

    def test_sqrt2_chain(self, schema):
        radii = schema["coordinate_system"]["derived_radii"]
        r_blue = radii["Circ.D"]["value"]
        r_green = radii["Circ.Bounds.A"]["value"]
        r_gold = radii["Circ.A"]["value"]
        assert r_blue == pytest.approx(r_green / np.sqrt(2), abs=1e-4)
        assert r_gold == pytest.approx(r_green * np.sqrt(2), abs=1e-4)

    def test_r_vertex(self, schema):
        radii = schema["coordinate_system"]["derived_radii"]
        r_green = radii["Circ.Bounds.A"]["value"]
        r_gold = radii["Circ.A"]["value"]
        r_vertex = schema["coordinate_system"]["derived_constants"]["R_VERTEX"]["value"]
        assert r_vertex == pytest.approx(r_gold - r_green, abs=1e-4)


class TestNodePositions:
    """Lock exact node coordinates."""

    EXPECTED_NODES = [
        (0,  -1.3895,  2.6093),  # Square.B UL
        (1,   0.3504,  2.6093),  # center x, SqB top
        (2,   1.2204,  1.7394),  # Green IS 45°
        (3,   0.3504, -0.0006),  # Blue tangent bottom
        (4,  -0.8799,  2.0997),  # SqA V2
        (5,   0.3504,  1.7394),  # Blue tangent top
        (6,   1.2204,  0.8694),  # Blue tangent right
        (7,  -1.3895, -0.0006),  # SqB left, Blue bottom
        (8,  -0.3703, -0.0006),  # Rect right, Blue bottom
        (9,  -0.8799, -0.3609),  # SqA V3
        (10, -0.3703, -0.8705),  # Rect right, SqB bottom
        (11, -1.3895, -0.8705),  # SqB LL
        (12, -0.8799, -1.5912),  # Circ.Rect.I top
        (13, -0.8799, -2.1008),  # Circ.Rect.I center
        (14, -0.8799, -3.1200),  # Circ.Rect.V center
        (15, -0.3703,  1.7394),  # Rect right, Blue top
        (16, -0.3703, -0.8705),  # Rect right, Gold bottom
        (17,  0.3504, -0.8705),  # Gold tangent bottom
        (18,  0.3504, -0.3609),  # Green tangent bottom
        (19,  0.3504,  2.0997),  # Green tangent top
        (20,  2.0903,  0.8694),  # Gold tangent right
        (21,  1.2204, -0.0006),  # Green IS 315°
        (22, -1.3895, -1.5912),  # Rect left, Circ.Rect.I top
        (23, -0.3703, -1.5912),  # Rect right, Circ.Rect.I top
        (24, -0.8799, -1.2308),  # Bump hub
    ]

    @pytest.mark.parametrize("idx,expected_x,expected_y", EXPECTED_NODES)
    def test_node_position(self, schema, idx, expected_x, expected_y):
        node = schema["graph"]["nodes"][idx]
        assert node["x"] == pytest.approx(expected_x, abs=0.002)
        assert node["y"] == pytest.approx(expected_y, abs=0.002)


class TestEdges:
    """Lock the exact edge set."""

    EXPECTED_EDGES = {
        (0,1),(0,4),(0,7),
        (2,5),(2,6),(2,20),(2,21),
        (3,8),(3,18),(3,21),
        (4,9),(4,15),(4,19),
        (5,15),
        (6,20),(6,21),
        (7,8),(7,9),(7,11),(7,15),
        (8,9),(8,15),
        (9,10),(9,11),(9,18),
        (10,16),(10,22),(10,23),(10,24),
        (11,22),(11,23),(11,24),
        (12,13),(12,22),(12,23),(12,24),
        (13,14),
        (16,17),(17,18),(17,21),
        (20,21),
        (22,23),(22,24),
        (23,24),
    }

    def test_edge_set(self, schema):
        actual = set()
        for e in schema["graph"]["edges"]:
            a, b = e["from"], e["to"]
            actual.add((min(a,b), max(a,b)))
        assert actual == self.EXPECTED_EDGES


class TestArcs:
    def test_green_arc(self, schema):
        arc = schema["geometry"]["arcs"][0]
        assert arc["name"] == "Green"
        assert arc["radius"] == pytest.approx(1.2303, abs=1e-4)
        assert arc["start_deg"] == pytest.approx(-90.0, abs=0.1)
        assert arc["end_deg"] == pytest.approx(90.0, abs=0.1)

    def test_blue_arc(self, schema):
        arc = schema["geometry"]["arcs"][1]
        assert arc["name"] == "Blue"
        assert arc["radius"] == pytest.approx(1.2303 / np.sqrt(2), abs=1e-3)
        assert arc["start_deg"] == pytest.approx(-90.0, abs=0.1)
        assert arc["end_deg"] == pytest.approx(90.0, abs=0.1)

    def test_gold_arc(self, schema):
        arc = schema["geometry"]["arcs"][2]
        assert arc["name"] == "Gold"
        assert arc["radius"] == pytest.approx(1.2303 * np.sqrt(2), abs=1e-3)
        assert arc["start_deg"] == pytest.approx(-90.0, abs=0.1)
        assert arc["end_deg"] == pytest.approx(90.0, abs=0.1)


class TestGeometryShapes:
    def test_square_b(self, schema):
        sqb = schema["geometry"]["shapes"]["Square.B"]["vertices"]
        assert sqb["P.SQAB.UL"]["x"] == pytest.approx(-1.3895, abs=0.002)
        assert sqb["P.SQAB.UL"]["y"] == pytest.approx(2.6093, abs=0.002)

    def test_rect1(self, schema):
        rect = schema["geometry"]["shapes"]["Rect.1"]
        assert rect["width"] == pytest.approx(1.0192, abs=0.002)
        assert rect["height"] == pytest.approx(5.2197, abs=0.002)

    def test_circ_rect_i(self, schema):
        ci = schema["geometry"]["shapes"]["Circ.Rect.I"]
        assert ci["center"]["x"] == pytest.approx(-0.8799, abs=0.002)
        assert ci["center"]["y"] == pytest.approx(-2.1008, abs=0.002)

    def test_circ_rect_v(self, schema):
        cv = schema["geometry"]["shapes"]["Circ.Rect.V"]
        assert cv["center"]["x"] == pytest.approx(-0.8799, abs=0.002)
        assert cv["center"]["y"] == pytest.approx(-3.1200, abs=0.002)


class TestCompositionMapping:
    """Verify the composition generates consistent values when scaled to P coords."""

    def test_composition_circ_a_maps_to_gold(self):
        """Circ.A at R=200, scaled to P coords, should equal R_GOLD."""
        from p_logo.geometric_composition import generate_composition
        R_GREEN = 1.2303
        R_BLUE = R_GREEN / np.sqrt(2)
        R_GOLD = R_GREEN * np.sqrt(2)
        CX, CY = 0.3504, 0.8694

        scale = R_BLUE / 100.0
        ox = CX - 600 * scale
        oy = CY - 800 * scale
        comp = generate_composition(scale=scale, origin_x=ox, origin_y=oy)

        circ_a_r = comp["shapes"]["Circ.A"]["radius"]
        assert circ_a_r == pytest.approx(R_GOLD, abs=1e-3)

    def test_composition_circ_bounds_a_maps_to_green(self):
        from p_logo.geometric_composition import generate_composition
        R_GREEN = 1.2303
        R_BLUE = R_GREEN / np.sqrt(2)
        CX, CY = 0.3504, 0.8694

        scale = R_BLUE / 100.0
        ox = CX - 600 * scale
        oy = CY - 800 * scale
        comp = generate_composition(scale=scale, origin_x=ox, origin_y=oy)

        circ_ba_r = comp["shapes"]["Circ.Bounds.A"]["radius"]
        assert circ_ba_r == pytest.approx(R_GREEN, abs=1e-3)

    def test_composition_circ_d_maps_to_blue(self):
        from p_logo.geometric_composition import generate_composition
        R_GREEN = 1.2303
        R_BLUE = R_GREEN / np.sqrt(2)
        CX, CY = 0.3504, 0.8694

        scale = R_BLUE / 100.0
        ox = CX - 600 * scale
        oy = CY - 800 * scale
        comp = generate_composition(scale=scale, origin_x=ox, origin_y=oy)

        circ_d_r = comp["shapes"]["Circ.D"]["radius"]
        assert circ_d_r == pytest.approx(R_BLUE, abs=1e-3)

    def test_composition_rect_width(self):
        from p_logo.geometric_composition import generate_composition
        R_GREEN = 1.2303
        R_BLUE = R_GREEN / np.sqrt(2)
        R_GOLD = R_GREEN * np.sqrt(2)
        R_VERTEX = R_GOLD - R_GREEN
        CX, CY = 0.3504, 0.8694

        scale = R_BLUE / 100.0
        ox = CX - 600 * scale
        oy = CY - 800 * scale
        comp = generate_composition(scale=scale, origin_x=ox, origin_y=oy)

        rect_w = comp["shapes"]["Rect.1"]["width"]
        assert rect_w == pytest.approx(2 * R_VERTEX, abs=1e-3)
