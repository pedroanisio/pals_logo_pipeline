"""
Regression tests for geometric_composition.generate_composition().

Locks the exact output before decomposing the 356-line god function
into focused sub-builders.  Every assertion captures current behavior;
the refactor must not change any output.
"""

import json
import sys
import hashlib
import numpy as np
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(scope="module")
def comp():
    from p_logo.geometric_composition import generate_composition
    return generate_composition()


@pytest.fixture(scope="module")
def comp_scaled():
    from p_logo.geometric_composition import generate_composition
    return generate_composition(scale=2.0, origin_x=100, origin_y=50)


# ── Structure ────────────────────────────────────────────────────

class TestCompositionStructure:
    def test_shape_count(self, comp):
        assert len(comp["shapes"]) == 16

    def test_point_count(self, comp):
        assert len(comp["points"]) == 27

    def test_intersection_count(self, comp):
        assert len(comp["intersections"]) == 10

    def test_metadata(self, comp):
        assert comp["metadata"] == {
            "canvas_width": 1200,
            "canvas_height": 1200,
            "scale": 1.0,
            "origin_x": 0,
            "origin_y": 0,
            "dpi": 100,
        }

    def test_shape_keys(self, comp):
        expected = sorted([
            "Circ.A", "Circ.Bounds.A", "Circ.C", "Circ.C'", "Circ.D",
            "Circ.Rect.I", "Circ.Rect.V", "Circ.V1", "Circ.V2", "Circ.V3",
            "Circ.V4", "Outer.Circle", "Rect.1", "Square.A", "Square.B",
            "Square.D",
        ])
        assert sorted(comp["shapes"].keys()) == expected

    def test_all_shapes_have_type(self, comp):
        for key, shape in comp["shapes"].items():
            assert "type" in shape, f"Shape {key} missing 'type'"

    def test_all_points_have_description(self, comp):
        for key, pt in comp["points"].items():
            assert "description" in pt, f"Point {key} missing 'description'"
            assert "x" in pt and "y" in pt, f"Point {key} missing coordinates"


# ── Geometry values (default scale) ──────────────────────────────

class TestDefaultGeometry:
    def test_circ_a_center(self, comp):
        c = comp["shapes"]["Circ.A"]["center"]
        assert c["x"] == pytest.approx(600.0)
        assert c["y"] == pytest.approx(800.0)

    def test_circ_a_radius(self, comp):
        assert comp["shapes"]["Circ.A"]["radius"] == pytest.approx(200.0)

    def test_outer_circle_radius(self, comp):
        assert comp["shapes"]["Outer.Circle"]["radius"] == pytest.approx(600.0)

    def test_square_b_upper_left(self, comp):
        ul = comp["shapes"]["Square.B"]["vertices"]["upper_left"]
        assert ul["x"] == pytest.approx(400.0)
        assert ul["y"] == pytest.approx(1000.0)

    def test_square_a_vertex_v1(self, comp):
        v1 = comp["shapes"]["Square.A"]["vertices"]["V1_right"]
        expected_x = 600 + 200 * np.cos(np.radians(45))
        expected_y = 800 + 200 * np.sin(np.radians(45))
        assert v1["x"] == pytest.approx(expected_x)
        assert v1["y"] == pytest.approx(expected_y)

    def test_rect_1_dimensions(self, comp):
        rect = comp["shapes"]["Rect.1"]
        assert rect["width"] == pytest.approx(117.15728752538098)
        assert rect["height"] == pytest.approx(600.0)

    def test_circ_d_is_half_r_a(self, comp):
        r_a = comp["shapes"]["Circ.A"]["radius"]
        r_d = comp["shapes"]["Circ.D"]["radius"]
        assert r_d == pytest.approx(r_a / 2)

    def test_circ_bounds_a_inradius(self, comp):
        r_a = comp["shapes"]["Circ.A"]["radius"]
        r_bounds = comp["shapes"]["Circ.Bounds.A"]["radius"]
        assert r_bounds == pytest.approx(r_a / np.sqrt(2))

    def test_center_a_point(self, comp):
        pt = comp["points"]["P.CENTER.A"]
        assert pt["x"] == pytest.approx(600.0)
        assert pt["y"] == pytest.approx(800.0)

    def test_rect_tangent_point(self, comp):
        pt = comp["points"]["P.CIRC.RECT.TANGENT"]
        assert pt["x"] == pytest.approx(458.5786437626905)
        assert pt["y"] == pytest.approx(400.0)


# ── Intersections ────────────────────────────────────────────────

class TestIntersections:
    def test_circ_a_square_a_intersections(self, comp):
        ca_sa = [i for i in comp["intersections"]
                 if "Circ.A" in i["shapes"] and "Square.A" in i["shapes"]]
        assert len(ca_sa) == 4

    def test_circ_a_square_b_tangents(self, comp):
        ca_sb = [i for i in comp["intersections"]
                 if "Circ.A" in i["shapes"] and "Square.B" in i["shapes"]]
        assert len(ca_sb) == 4

    def test_rect_circle_tangents(self, comp):
        rect_tangents = [i for i in comp["intersections"]
                         if "Rect.1" in i["shapes"]]
        assert len(rect_tangents) == 2


# ── Scaling ──────────────────────────────────────────────────────

class TestScaledComposition:
    def test_scaled_shape_count(self, comp_scaled):
        assert len(comp_scaled["shapes"]) == 16

    def test_scaled_circ_a_radius(self, comp_scaled):
        assert comp_scaled["shapes"]["Circ.A"]["radius"] == pytest.approx(400.0)

    def test_scaled_circ_a_center(self, comp_scaled):
        c = comp_scaled["shapes"]["Circ.A"]["center"]
        assert c["x"] == pytest.approx(1300.0)
        assert c["y"] == pytest.approx(1650.0)

    def test_scaled_metadata(self, comp_scaled):
        assert comp_scaled["metadata"]["scale"] == 2.0
        assert comp_scaled["metadata"]["origin_x"] == 100
        assert comp_scaled["metadata"]["origin_y"] == 50


# ── Determinism ──────────────────────────────────────────────────

class TestDeterminism:
    def test_output_is_deterministic(self):
        from p_logo.geometric_composition import generate_composition
        c1 = generate_composition()
        c2 = generate_composition()
        h1 = hashlib.sha256(json.dumps(c1, sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(c2, sort_keys=True).encode()).hexdigest()
        assert h1 == h2

    def test_output_hash_matches_snapshot(self):
        from p_logo.geometric_composition import generate_composition
        comp = generate_composition()
        h = hashlib.sha256(json.dumps(comp, sort_keys=True).encode()).hexdigest()
        assert h[:16] == "e0ea6336fb71e0a5"
