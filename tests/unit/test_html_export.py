"""
HTML export — Phase 1: schema_to_js_data conversion tests.

Verifies the Python→JS data bridge produces correct geometry
that matches both the canonical schema and the current HTML file.
"""

import math
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(scope="module")
def js_data():
    from p_logo import build_schema
    from p_logo.exporters.html_export import schema_to_js_data
    return schema_to_js_data(build_schema())


@pytest.fixture(scope="module")
def schema():
    from p_logo import build_schema
    return build_schema()


# ── Node tests ────────────────────────────────────────────────

class TestWireNodes:
    def test_count(self, js_data):
        assert len(js_data["wireNodes"]) == 25

    def test_node_0_position(self, js_data):
        n = js_data["wireNodes"][0]
        assert n["x"] == pytest.approx(-1.3895, abs=0.002)
        assert n["y"] == pytest.approx(2.6093, abs=0.002)

    def test_node_14_position(self, js_data):
        n = js_data["wireNodes"][14]
        assert n["x"] == pytest.approx(-0.8799, abs=0.002)
        assert n["y"] == pytest.approx(-3.12, abs=0.01)

    def test_node_24_position(self, js_data):
        n = js_data["wireNodes"][24]
        assert n["x"] == pytest.approx(-0.8799, abs=0.002)
        assert n["y"] == pytest.approx(-1.2308, abs=0.002)

    def test_all_nodes_have_required_keys(self, js_data):
        for n in js_data["wireNodes"]:
            assert "x" in n
            assert "y" in n
            assert "col" in n
            assert "sz" in n

    def test_sz_matches_key_node(self, js_data, schema):
        for i, n in enumerate(js_data["wireNodes"]):
            # N24 (bump hub) is key_node=False in schema but sz=1 in revision HTML
            is_bump_hub = schema.node(i).composition_point == "P.BUMP.HUB"
            expected_sz = 1 if schema.node(i).key_node or is_bump_hub else 0
            assert n["sz"] == expected_sz, f"Node {i}: sz={n['sz']} expected={expected_sz}"


# ── Node color assignment tests ───────────────────────────────

class TestNodeColors:
    def test_node_0_blueglow(self, js_data):
        """Node 0 (Square.B UL, corner accent) → BLUEGLOW."""
        assert js_data["wireNodes"][0]["col"] == "BLUEGLOW"

    def test_node_1_amber(self, js_data):
        """Node 1 (key_node, not tangent) → AMBER."""
        assert js_data["wireNodes"][1]["col"] == "AMBER"

    def test_node_3_copper(self, js_data):
        """Node 3 (not key, Circ.D tangent) → COPPER."""
        assert js_data["wireNodes"][3]["col"] == "COPPER"

    def test_node_14_warmwht(self, js_data):
        """Node 14 (nib tip) → WARMWHT."""
        assert js_data["wireNodes"][14]["col"] == "WARMWHT"

    def test_node_17_bronze(self, js_data):
        """Node 17 (key, Circ.A tangent bottom) → BRONZE."""
        assert js_data["wireNodes"][17]["col"] == "BRONZE"

    def test_node_20_bronze(self, js_data):
        """Node 20 (key, Circ.A tangent right) → BRONZE."""
        assert js_data["wireNodes"][20]["col"] == "BRONZE"

    def test_node_16_bronze(self, js_data):
        """Node 16 (key, Rect.1 right at Circ.A bottom) → BRONZE."""
        assert js_data["wireNodes"][16]["col"] == "BRONZE"

    def test_node_24_amber(self, js_data):
        """Node 24 (bump hub, key_node in revision HTML) → AMBER."""
        # N24 has key_node=False in schema but sz=1 in revision HTML
        # The color should follow the revision: AMBER for bump hub
        assert js_data["wireNodes"][24]["col"] == "AMBER"


# ── Edge tests ────────────────────────────────────────────────

class TestWireEdges:
    def test_count(self, js_data):
        assert len(js_data["wireEdges"]) == 44

    def test_first_edge(self, js_data):
        assert js_data["wireEdges"][0] == [0, 1]

    def test_last_edge_is_arc_bridge(self, js_data):
        """Edge (21, 3) should be present (arc-bridge)."""
        edges_set = set(tuple(e) for e in js_data["wireEdges"])
        assert (21, 3) in edges_set or (3, 21) in edges_set

    def test_edge_pairs_match_schema(self, js_data, schema):
        js_set = set(tuple(sorted(e)) for e in js_data["wireEdges"])
        schema_set = set(e.normalized for e in schema.edges)
        assert js_set == schema_set


# ── Arc tests ─────────────────────────────────────────────────

class TestArcDefs:
    def test_count(self, js_data):
        assert len(js_data["arcDefs"]) == 3

    def test_green_arc_radius(self, js_data):
        assert js_data["arcDefs"][0]["r"] == pytest.approx(1.2303, abs=1e-4)

    def test_blue_arc_radius(self, js_data):
        assert js_data["arcDefs"][1]["r"] == pytest.approx(1.2303 / math.sqrt(2), abs=1e-3)

    def test_gold_arc_radius(self, js_data):
        assert js_data["arcDefs"][2]["r"] == pytest.approx(1.2303 * math.sqrt(2), abs=1e-3)

    def test_all_semicircles(self, js_data):
        for a in js_data["arcDefs"]:
            assert a["startAngle"] == pytest.approx(-math.pi / 2, abs=1e-6)
            assert a["sweep"] == pytest.approx(math.pi, abs=1e-6)

    def test_arc_colors(self, js_data):
        assert js_data["arcDefs"][0]["color"] == "AMBER"
        assert js_data["arcDefs"][1]["color"] == "COPPER"
        assert js_data["arcDefs"][2]["color"] == "BRONZE"

    def test_arc_opacities(self, js_data):
        assert js_data["arcDefs"][0]["opacity"] == pytest.approx(0.7)
        assert js_data["arcDefs"][1]["opacity"] == pytest.approx(0.6)
        assert js_data["arcDefs"][2]["opacity"] == pytest.approx(0.55)

    def test_shared_center(self, js_data):
        for a in js_data["arcDefs"]:
            assert a["cx"] == pytest.approx(0.3504, abs=1e-4)
            assert a["cy"] == pytest.approx(0.8694, abs=1e-4)


# ── Nib tests ─────────────────────────────────────────────────

# ── HTML generation tests ─────────────────────────────────────

class TestHtmlGeneration:
    @pytest.fixture(scope="class")
    def generated_html(self, tmp_path_factory):
        from p_logo import build_schema
        from p_logo.exporters.html_export import export_html
        out = str(tmp_path_factory.mktemp("html") / "test.html")
        return export_html(build_schema(), out)

    def test_valid_html(self, generated_html):
        assert generated_html.startswith("<!DOCTYPE html>")
        assert "</html>" in generated_html

    def test_contains_threejs(self, generated_html):
        assert "three.js" in generated_html

    def test_no_placeholders_remain(self, generated_html):
        for ph in ["__WIRE_NODES__", "__WIRE_EDGES__", "__ARC_DEFS__", "__NIB_DATA__"]:
            assert ph not in generated_html, f"Placeholder {ph} still in output"

    def test_node_count_in_output(self, generated_html):
        import re
        # Count "x": occurrences in the wireNodes JSON block
        nodes_match = re.search(r'const _wireNodesRaw = (\[.*?\]);', generated_html, re.DOTALL)
        assert nodes_match, "wireNodes block not found"
        import json
        nodes = json.loads(nodes_match.group(1))
        assert len(nodes) == 25

    def test_edge_count_in_output(self, generated_html):
        import re, json
        edges_match = re.search(r'const wireEdges = (\[.*?\]);', generated_html, re.DOTALL)
        assert edges_match, "wireEdges block not found"
        edges = json.loads(edges_match.group(1))
        assert len(edges) == 44

    def test_arc_count_in_output(self, generated_html):
        import re, json
        arcs_match = re.search(r'const arcDefs = (\[.*?\]);', generated_html, re.DOTALL)
        assert arcs_match, "arcDefs block not found"
        arcs = json.loads(arcs_match.group(1))
        assert len(arcs) == 3

    def test_standalone_no_python_imports(self, generated_html):
        """No Python import statements inside <script> tags."""
        import re
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', generated_html, re.DOTALL)
        for script in scripts:
            assert "import p_logo" not in script
            assert "from p_logo import" not in script

    def test_coordinates_match_current_html(self, generated_html):
        """Spot-check: generated node coordinates match the revision HTML values."""
        import re, json
        nodes_match = re.search(r'const _wireNodesRaw = (\[.*?\]);', generated_html, re.DOTALL)
        nodes = json.loads(nodes_match.group(1))

        # Node 0: (-1.3895, 2.6093)
        assert abs(nodes[0]["x"] - (-1.3895)) < 0.002
        assert abs(nodes[0]["y"] - 2.6093) < 0.002
        # Node 20: (2.0903, 0.8694)
        assert abs(nodes[20]["x"] - 2.0903) < 0.002
        assert abs(nodes[20]["y"] - 0.8694) < 0.002
        # Node 24: (-0.8799, -1.2308)
        assert abs(nodes[24]["x"] - (-0.8799)) < 0.002
        assert abs(nodes[24]["y"] - (-1.2308)) < 0.002


# ── Nib tests ─────────────────────────────────────────────────

class TestNibData:
    def test_has_required_keys(self, js_data):
        nib = js_data["nib"]
        for key in ["tipY", "topY", "cx", "left", "right", "ctrY",
                     "outline", "slitStart", "slitEnd", "ballPos"]:
            assert key in nib, f"Missing nib key: {key}"

    def test_outline_has_5_points(self, js_data):
        assert len(js_data["nib"]["outline"]) == 5

    def test_tip_y_matches_node_14(self, js_data, schema):
        assert js_data["nib"]["tipY"] == pytest.approx(schema.node(14).y, abs=0.01)

    def test_cx_matches_nib_ball(self, js_data, schema):
        assert js_data["nib"]["cx"] == pytest.approx(schema.nib.ball_pos[0], abs=0.002)

    def test_ctr_y_matches_nib_ball(self, js_data, schema):
        assert js_data["nib"]["ctrY"] == pytest.approx(schema.nib.ball_pos[1], abs=0.002)
