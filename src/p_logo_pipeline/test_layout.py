"""
PAL's Notes Logo Pipeline — Step 4: Layout — TEST SUITE (TDD)

Written BEFORE implementation.

Run:
    cd pals-logo-pipeline
    python -m pytest test_layout.py -v

Requires: palette.json, graph.json, nib.json, arcs.json in build/

The layout step is the first integration point. It reads all upstream
geometry (graph, nib, arcs) and composes them into a single coordinate
space with:
  - A vertical centering offset so the full composition (including the
    nib below the stem) is optically centered in the ring
  - A bounding box around all geometry
  - Validation that nothing clips outside the ring
  - Nib-to-stem connection verification (nib top meets stem bottom)
  - A flat element inventory for the renderer
  - Z-ordering assignments for layering

The layout does NOT modify the upstream geometry — it wraps it with
composition metadata.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def build_dir() -> Path:
    return Path(__file__).parent / "build"


@pytest.fixture(scope="session")
def palette(build_dir) -> dict:
    path = build_dir / "palette.json"
    assert path.exists(), "Run palette.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def graph_data(build_dir) -> dict:
    path = build_dir / "graph.json"
    assert path.exists(), "Run graph.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def nib_data(build_dir) -> dict:
    path = build_dir / "nib.json"
    assert path.exists(), "Run nib.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def arcs_data(build_dir) -> dict:
    path = build_dir / "arcs.json"
    assert path.exists(), "Run arcs.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def layout_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import layout
    return layout


@pytest.fixture
def default_layout(layout_module, palette, graph_data, nib_data, arcs_data):
    return layout_module.build_layout(palette, graph_data, nib_data, arcs_data)


@pytest.fixture
def layout_json_path(layout_module, palette, graph_data, nib_data, arcs_data) -> Path:
    return layout_module.write_layout(palette, graph_data, nib_data, arcs_data)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_layout(self, layout_module):
        assert callable(getattr(layout_module, "build_layout", None))

    def test_has_write_layout(self, layout_module):
        assert callable(getattr(layout_module, "write_layout", None))

    def test_has_validate(self, layout_module):
        assert callable(getattr(layout_module, "validate", None))


# ──────────────────────────────────────────────
# 2. OUTPUT SCHEMA
# ──────────────────────────────────────────────

class TestOutputSchema:

    def test_has_meta(self, default_layout):
        assert "_meta" in default_layout
        assert default_layout["_meta"]["step"] == 4
        assert default_layout["_meta"]["name"] == "layout"

    def test_has_center_offset(self, default_layout):
        """The composition offset for vertical centering."""
        assert "center_offset" in default_layout
        co = default_layout["center_offset"]
        assert "x" in co and "y" in co

    def test_has_bounding_box(self, default_layout):
        assert "bounding_box" in default_layout
        bb = default_layout["bounding_box"]
        assert "min_x" in bb and "max_x" in bb
        assert "min_y" in bb and "max_y" in bb

    def test_has_ring(self, default_layout):
        """Ring parameters must be present for the renderer."""
        assert "ring" in default_layout
        ring = default_layout["ring"]
        assert "bands" in ring
        assert "fill_radius" in ring

    def test_has_elements(self, default_layout):
        """Flat list of all renderable elements."""
        assert "elements" in default_layout
        assert isinstance(default_layout["elements"], list)

    def test_has_inventory(self, default_layout):
        """Summary count of elements by type."""
        assert "inventory" in default_layout
        assert isinstance(default_layout["inventory"], dict)

    def test_has_upstream_refs(self, default_layout):
        """Must reference which upstream artifacts were consumed."""
        assert "upstream" in default_layout
        up = default_layout["upstream"]
        assert "graph" in up and "nib" in up and "arcs" in up


# ──────────────────────────────────────────────
# 3. CENTER OFFSET
# ──────────────────────────────────────────────

class TestCenterOffset:

    def test_offset_is_finite(self, default_layout):
        co = default_layout["center_offset"]
        assert math.isfinite(co["x"])
        assert math.isfinite(co["y"])

    def test_offset_is_small(self, default_layout):
        """The offset should be a small correction, not a large shift."""
        co = default_layout["center_offset"]
        assert abs(co["x"]) < 2.0, f"X offset {co['x']} too large"
        assert abs(co["y"]) < 2.0, f"Y offset {co['y']} too large"

    def test_offset_centers_vertically(self, default_layout):
        """After applying the offset, the vertical midpoint of all geometry
        should be near y=0."""
        bb = default_layout["bounding_box"]
        mid_y = (bb["min_y"] + bb["max_y"]) / 2
        # The midpoint should be close to 0 (within tolerance for
        # optical centering which may differ from geometric centering)
        assert abs(mid_y) < 1.5, (
            f"Bounding box midpoint y={mid_y:.2f} too far from center"
        )


# ──────────────────────────────────────────────
# 4. BOUNDING BOX
# ──────────────────────────────────────────────

class TestBoundingBox:

    def test_bb_is_valid(self, default_layout):
        bb = default_layout["bounding_box"]
        assert bb["min_x"] < bb["max_x"]
        assert bb["min_y"] < bb["max_y"]

    def test_bb_values_finite(self, default_layout):
        bb = default_layout["bounding_box"]
        for k in ("min_x", "max_x", "min_y", "max_y"):
            assert math.isfinite(bb[k])

    def test_bb_includes_all_nodes(self, default_layout):
        """Every graph node (after offset) must be inside the bounding box."""
        bb = default_layout["bounding_box"]
        co = default_layout["center_offset"]
        for el in default_layout["elements"]:
            if el["type"] == "node":
                x = el["x"]
                y = el["y"]
                assert bb["min_x"] <= x <= bb["max_x"], (
                    f"Node x={x} outside bb [{bb['min_x']}, {bb['max_x']}]"
                )
                assert bb["min_y"] <= y <= bb["max_y"], (
                    f"Node y={y} outside bb [{bb['min_y']}, {bb['max_y']}]"
                )

    def test_bb_includes_nib(self, default_layout):
        """The nib tip must be inside the bounding box."""
        bb = default_layout["bounding_box"]
        ink_origin = None
        for el in default_layout["elements"]:
            if el["type"] == "ink_origin":
                ink_origin = el
                break
        assert ink_origin is not None, "No ink_origin element found"
        assert bb["min_y"] <= ink_origin["y"] <= bb["max_y"]

    def test_bb_includes_arc_points(self, default_layout):
        """Arc extremes must be inside the bounding box."""
        bb = default_layout["bounding_box"]
        arc_els = [el for el in default_layout["elements"] if el["type"] == "arc"]
        assert len(arc_els) > 0
        for arc in arc_els:
            for pt in arc["points"]:
                assert bb["min_x"] <= pt["x"] <= bb["max_x"] + 0.2
                assert bb["min_y"] <= pt["y"] <= bb["max_y"] + 0.2


# ──────────────────────────────────────────────
# 5. RING-FIT VALIDATION
# ──────────────────────────────────────────────

class TestRingFit:
    """All visible geometry must fit inside the outer ring."""

    def test_all_nodes_inside_ring(self, default_layout, palette):
        ring_r = palette["sizing"]["ring_radii"]["outer_outer"]
        for el in default_layout["elements"]:
            if el["type"] == "node":
                dist = math.sqrt(el["x"]**2 + el["y"]**2)
                assert dist < ring_r, (
                    f"Node at ({el['x']:.2f}, {el['y']:.2f}) dist={dist:.2f} "
                    f"outside ring r={ring_r}"
                )

    def test_nib_inside_ring(self, default_layout, palette):
        ring_r = palette["sizing"]["ring_radii"]["outer_outer"]
        for el in default_layout["elements"]:
            if el["type"] in ("nib_fan_line", "nib_outline_line",
                              "nib_center_line", "nib_accent_node",
                              "junction_ball", "ink_origin"):
                for key_pair in [("x1","y1"), ("x2","y2"), ("x","y")]:
                    if key_pair[0] in el:
                        x, y = el[key_pair[0]], el[key_pair[1]]
                        dist = math.sqrt(x**2 + y**2)
                        assert dist < ring_r, (
                            f"{el['type']} at ({x:.2f},{y:.2f}) dist={dist:.2f} "
                            f"outside ring r={ring_r}"
                        )

    def test_ring_bands_present(self, default_layout):
        ring = default_layout["ring"]
        assert len(ring["bands"]) == 4, "Design rationale specifies 4 ring bands"
        for band in ring["bands"]:
            assert "inner_r" in band and "outer_r" in band
            assert band["outer_r"] > band["inner_r"]


# ──────────────────────────────────────────────
# 6. NIB-TO-STEM CONNECTION
# ──────────────────────────────────────────────

class TestNibStemConnection:
    """The nib's top must align with the stem's bottom node."""

    def test_nib_top_near_stem_bottom(self, default_layout):
        """The junction ball (top of nib) should be near the bottommost
        stem node in the graph."""
        jb = None
        for el in default_layout["elements"]:
            if el["type"] == "junction_ball":
                jb = el
                break
        assert jb is not None, "No junction_ball element found"

        # Find the bottom stem node (lowest-y graph node near the stem x)
        stem_nodes = [
            el for el in default_layout["elements"]
            if el["type"] == "node"
        ]
        assert len(stem_nodes) > 0

        # Bottom stem node = lowest y with x near the nib
        bottom_stem = min(stem_nodes, key=lambda n: n["y"])

        # The junction ball should be close to or below the bottom stem node
        dy = abs(jb["y"] - bottom_stem["y"])
        assert dy < 2.0, (
            f"Junction ball y={jb['y']:.2f} too far from bottom stem "
            f"y={bottom_stem['y']:.2f} (dy={dy:.2f})"
        )

    def test_nib_center_x_matches_stem(self, default_layout, graph_data):
        """The nib's center X should match the stem's X coordinate."""
        jb = None
        for el in default_layout["elements"]:
            if el["type"] == "junction_ball":
                jb = el
                break
        assert jb is not None

        # Stem X from graph: the junction node's x + offset
        co = default_layout["center_offset"]
        ji = graph_data["stats"]["junction_index"]
        stem_x = graph_data["nodes"][ji]["x"] + co["x"]

        assert abs(jb["x"] - stem_x) < 0.5, (
            f"Nib center x={jb['x']:.2f} doesn't match stem x={stem_x:.2f}"
        )


# ──────────────────────────────────────────────
# 7. ELEMENT TYPES
# ──────────────────────────────────────────────

class TestElementTypes:
    """The elements list must contain all expected element types."""

    def _types(self, layout: dict) -> set[str]:
        return set(el["type"] for el in layout["elements"])

    def test_has_node_elements(self, default_layout):
        assert "node" in self._types(default_layout)

    def test_has_edge_elements(self, default_layout):
        assert "edge" in self._types(default_layout)

    def test_has_arc_elements(self, default_layout):
        assert "arc" in self._types(default_layout)

    def test_has_nib_elements(self, default_layout):
        types = self._types(default_layout)
        assert "nib_fan_line" in types
        assert "nib_outline_line" in types
        assert "nib_center_line" in types

    def test_has_accent_nodes(self, default_layout):
        assert "nib_accent_node" in self._types(default_layout)

    def test_has_junction_ball(self, default_layout):
        assert "junction_ball" in self._types(default_layout)

    def test_has_ink_origin(self, default_layout):
        assert "ink_origin" in self._types(default_layout)

    def test_has_runner_path(self, default_layout):
        assert "runner_path" in self._types(default_layout)


# ──────────────────────────────────────────────
# 8. ELEMENT COUNTS
# ──────────────────────────────────────────────

class TestElementCounts:
    """Element counts must match the upstream sources."""

    def test_node_count(self, default_layout, graph_data):
        nodes = [el for el in default_layout["elements"] if el["type"] == "node"]
        assert len(nodes) == len(graph_data["nodes"])

    def test_edge_count(self, default_layout, graph_data):
        edges = [el for el in default_layout["elements"] if el["type"] == "edge"]
        assert len(edges) == len(graph_data["edges"])

    def test_arc_count(self, default_layout, arcs_data):
        arcs = [el for el in default_layout["elements"] if el["type"] == "arc"]
        assert len(arcs) == len(arcs_data["arcs"])

    def test_nib_fan_line_count(self, default_layout, nib_data):
        fans = [el for el in default_layout["elements"] if el["type"] == "nib_fan_line"]
        assert len(fans) == len(nib_data["fan_lines"])

    def test_nib_outline_line_count(self, default_layout, nib_data):
        outlines = [el for el in default_layout["elements"] if el["type"] == "nib_outline_line"]
        assert len(outlines) == len(nib_data["outline_lines"])

    def test_nib_accent_node_count(self, default_layout, nib_data):
        accents = [el for el in default_layout["elements"] if el["type"] == "nib_accent_node"]
        assert len(accents) == len(nib_data["accent_nodes"])

    def test_runner_path_count(self, default_layout, arcs_data):
        rps = [el for el in default_layout["elements"] if el["type"] == "runner_path"]
        assert len(rps) == len(arcs_data["runner_paths"])

    def test_exactly_one_center_line(self, default_layout):
        cls = [el for el in default_layout["elements"] if el["type"] == "nib_center_line"]
        assert len(cls) == 1

    def test_exactly_one_junction_ball(self, default_layout):
        jbs = [el for el in default_layout["elements"] if el["type"] == "junction_ball"]
        assert len(jbs) == 1

    def test_exactly_one_ink_origin(self, default_layout):
        ios = [el for el in default_layout["elements"] if el["type"] == "ink_origin"]
        assert len(ios) == 1


# ──────────────────────────────────────────────
# 9. ELEMENT Z-ORDERING
# ──────────────────────────────────────────────

class TestZOrdering:
    """Elements must have z values for layering."""

    def test_all_elements_have_z(self, default_layout):
        for el in default_layout["elements"]:
            assert "z" in el, f"Element type={el['type']} missing z"
            assert math.isfinite(el["z"])

    def test_nodes_above_edges(self, default_layout):
        """Nodes should render on top of edges."""
        node_zs = [el["z"] for el in default_layout["elements"] if el["type"] == "node"]
        edge_zs = [el["z"] for el in default_layout["elements"] if el["type"] == "edge"]
        assert min(node_zs) > max(edge_zs), (
            f"Node min z={min(node_zs)} not above edge max z={max(edge_zs)}"
        )

    def test_nib_above_arcs(self, default_layout):
        """Nib elements should render above arcs."""
        nib_types = {"nib_fan_line", "nib_outline_line", "nib_center_line",
                     "junction_ball"}
        nib_zs = [el["z"] for el in default_layout["elements"]
                  if el["type"] in nib_types]
        arc_zs = [el["z"] for el in default_layout["elements"]
                  if el["type"] == "arc"]
        if nib_zs and arc_zs:
            assert min(nib_zs) >= min(arc_zs)


# ──────────────────────────────────────────────
# 10. OFFSET APPLICATION
# ──────────────────────────────────────────────

class TestOffsetApplication:
    """The center_offset must be applied to all element coordinates."""

    def test_nodes_have_offset_applied(self, default_layout, graph_data):
        """Node positions in the layout should equal graph positions + offset."""
        co = default_layout["center_offset"]
        nodes_by_idx = {
            el["index"]: el
            for el in default_layout["elements"]
            if el["type"] == "node"
        }
        for gn in graph_data["nodes"]:
            ln = nodes_by_idx[gn["index"]]
            expected_x = gn["x"] + co["x"]
            expected_y = gn["y"] + co["y"]
            assert abs(ln["x"] - expected_x) < 1e-6, (
                f"Node {gn['index']} x: {ln['x']} != {expected_x}"
            )
            assert abs(ln["y"] - expected_y) < 1e-6, (
                f"Node {gn['index']} y: {ln['y']} != {expected_y}"
            )

    def test_nib_has_offset_applied(self, default_layout, nib_data):
        """Nib ink origin should equal nib params + offset."""
        co = default_layout["center_offset"]
        ink = None
        for el in default_layout["elements"]:
            if el["type"] == "ink_origin":
                ink = el
                break
        assert ink is not None
        expected_x = nib_data["ink_origin"]["x"] + co["x"]
        expected_y = nib_data["ink_origin"]["y"] + co["y"]
        assert abs(ink["x"] - expected_x) < 1e-6
        assert abs(ink["y"] - expected_y) < 1e-6

    def test_arcs_have_offset_applied(self, default_layout, arcs_data):
        """Arc center positions should have the offset applied."""
        co = default_layout["center_offset"]
        arc_els = [el for el in default_layout["elements"] if el["type"] == "arc"]
        for arc_el, arc_src in zip(
            sorted(arc_els, key=lambda a: a["index"]),
            sorted(arcs_data["arcs"], key=lambda a: a["index"])
        ):
            expected_cx = arc_src["cx"] + co["x"]
            expected_cy = arc_src["cy"] + co["y"]
            assert abs(arc_el["cx"] - expected_cx) < 1e-6
            assert abs(arc_el["cy"] - expected_cy) < 1e-6


# ──────────────────────────────────────────────
# 11. INVENTORY
# ──────────────────────────────────────────────

class TestInventory:
    """Inventory must summarize element counts by type."""

    def test_inventory_matches_elements(self, default_layout):
        from collections import Counter
        actual = Counter(el["type"] for el in default_layout["elements"])
        inv = default_layout["inventory"]
        for type_name, count in inv.items():
            assert actual.get(type_name, 0) == count, (
                f"Inventory '{type_name}'={count} but actual={actual.get(type_name, 0)}"
            )

    def test_inventory_covers_all_types(self, default_layout):
        from collections import Counter
        actual = Counter(el["type"] for el in default_layout["elements"])
        inv = default_layout["inventory"]
        for type_name in actual:
            assert type_name in inv, f"Type '{type_name}' in elements but not inventory"

    def test_total_element_count(self, default_layout):
        """Total elements should be in a reasonable range for the logo."""
        total = len(default_layout["elements"])
        assert total >= 50, f"Only {total} elements — too few"
        assert total <= 200, f"{total} elements — unexpectedly many"


# ──────────────────────────────────────────────
# 12. COORDINATE SANITY
# ──────────────────────────────────────────────

class TestCoordinateSanity:

    def _all_coords(self, layout: dict) -> list[tuple[str, float]]:
        coords = []
        for el in layout["elements"]:
            t = el["type"]
            if "x" in el and "y" in el:
                coords.append((t, el["x"]))
                coords.append((t, el["y"]))
            if "x1" in el:
                coords.extend([(t, el["x1"]), (t, el["y1"]),
                                (t, el["x2"]), (t, el["y2"])])
            if "points" in el:
                for pt in el["points"]:
                    coords.extend([(t+".pt", pt["x"]), (t+".pt", pt["y"])])
        return coords

    def test_no_nan(self, default_layout):
        for label, val in self._all_coords(default_layout):
            assert not math.isnan(val), f"{label} is NaN"

    def test_no_inf(self, default_layout):
        for label, val in self._all_coords(default_layout):
            assert not math.isinf(val), f"{label} is Inf"

    def test_within_logo_space(self, default_layout):
        for label, val in self._all_coords(default_layout):
            assert -7.0 <= val <= 7.0, f"{label} = {val} outside ±7"


# ──────────────────────────────────────────────
# 13. VALIDATION
# ──────────────────────────────────────────────

class TestValidation:

    def test_validate_passes_default(self, layout_module, palette,
                                     graph_data, nib_data, arcs_data):
        errors = layout_module.validate(palette, graph_data, nib_data, arcs_data)
        assert errors == [], f"Unexpected errors: {errors}"


# ──────────────────────────────────────────────
# 14. JSON FILE OUTPUT
# ──────────────────────────────────────────────

class TestJsonOutput:

    def test_file_is_created(self, layout_json_path):
        assert layout_json_path.exists()
        assert layout_json_path.name == "layout.json"

    def test_file_is_valid_json(self, layout_json_path):
        with open(layout_json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_in_build_directory(self, layout_json_path):
        assert layout_json_path.parent.name == "build"

    def test_file_roundtrips(self, layout_json_path, default_layout):
        with open(layout_json_path) as f:
            from_file = json.load(f)
        assert from_file["center_offset"] == default_layout["center_offset"]
        assert from_file["bounding_box"] == default_layout["bounding_box"]
        assert len(from_file["elements"]) == len(default_layout["elements"])
        assert from_file["inventory"] == default_layout["inventory"]


# ──────────────────────────────────────────────
# 15. UPSTREAM REFERENCE INTEGRITY
# ──────────────────────────────────────────────

class TestUpstreamRefs:
    """Layout must record which upstream steps it consumed."""

    def test_upstream_records_step_numbers(self, default_layout):
        up = default_layout["upstream"]
        assert up["graph"] == 1
        assert up["nib"] == 2
        assert up["arcs"] == 3

    def test_upstream_records_counts(self, default_layout):
        """Should record how many elements came from each source."""
        up = default_layout["upstream"]
        assert "graph_nodes" in up and up["graph_nodes"] == 25
        assert "graph_edges" in up and up["graph_edges"] == 44
        assert "nib_lines" in up
        assert "arc_count" in up and up["arc_count"] == 3
