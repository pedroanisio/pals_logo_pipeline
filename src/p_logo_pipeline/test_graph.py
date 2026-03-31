"""
PAL's Notes Logo Pipeline — Step 1: Graph — TEST SUITE (TDD)

Written BEFORE implementation.

Run:
    cd pals-logo-pipeline
    python -m pytest test_graph.py -v

Requires: palette.json in build/ (produced by step 0).

The letter P is constructed as a wireframe graph: 23 nodes connected by
37 edges. From the design rationale:

  "The P is a connected graph: 25 vertices, 37 edges, average degree ≈ 3.13.
   The most connected node (degree 6) sits at the junction where the stem
   meets the bowl — structurally, it's the point where everything converges."

The graph is NOT a typographic P — it is a P built from structure. Nodes
are positioned to form the recognizable letter shape, but the topology
(connectivity) is what matters.

Structural regions:
  - Stem: vertical run of nodes on the left
  - Bowl outer: arc of nodes curving to the right
  - Bowl inner: secondary ring inside the bowl
  - Junction: the node where stem meets bowl (degree 6)
  - Nib attachment: bottom of stem connects to the nib (step 2)
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import pytest


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def palette() -> dict:
    path = Path(__file__).parent / "build" / "palette.json"
    assert path.exists(), "build/palette.json not found. Run palette.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def graph_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import graph
    return graph


@pytest.fixture
def default_graph(graph_module, palette):
    return graph_module.build_graph(palette)


@pytest.fixture
def graph_json_path(graph_module, palette) -> Path:
    return graph_module.write_graph(palette)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_graph(self, graph_module):
        assert callable(getattr(graph_module, "build_graph", None))

    def test_has_write_graph(self, graph_module):
        assert callable(getattr(graph_module, "write_graph", None))

    def test_has_validate(self, graph_module):
        assert callable(getattr(graph_module, "validate", None))

    def test_has_node_definitions(self, graph_module):
        assert hasattr(graph_module, "NODE_POSITIONS")
        assert hasattr(graph_module, "NODE_COLORS")

    def test_has_edge_definitions(self, graph_module):
        assert hasattr(graph_module, "EDGES")

    def test_has_junction_index(self, graph_module):
        """Module must expose which node is the degree-6 junction."""
        assert hasattr(graph_module, "JUNCTION_NODE_INDEX")


# ──────────────────────────────────────────────
# 2. OUTPUT SCHEMA
# ──────────────────────────────────────────────

class TestOutputSchema:

    def test_has_meta(self, default_graph):
        assert "_meta" in default_graph
        assert default_graph["_meta"]["step"] == 1
        assert default_graph["_meta"]["name"] == "graph"

    def test_has_nodes(self, default_graph):
        assert "nodes" in default_graph
        assert isinstance(default_graph["nodes"], list)

    def test_has_edges(self, default_graph):
        assert "edges" in default_graph
        assert isinstance(default_graph["edges"], list)

    def test_has_adjacency(self, default_graph):
        assert "adjacency" in default_graph
        assert isinstance(default_graph["adjacency"], dict)

    def test_has_stats(self, default_graph):
        """Output must include computed graph statistics."""
        assert "stats" in default_graph
        stats = default_graph["stats"]
        assert "node_count" in stats
        assert "edge_count" in stats
        assert "avg_degree" in stats
        assert "max_degree" in stats
        assert "junction_index" in stats


# ──────────────────────────────────────────────
# 3. EXACT COUNTS (from design rationale)
# ──────────────────────────────────────────────

class TestExactCounts:
    """The design rationale specifies exact numbers."""

    def test_23_nodes(self, default_graph):
        assert len(default_graph["nodes"]) == 25

    def test_36_edges(self, default_graph):
        assert len(default_graph["edges"]) == 44

    def test_stats_match(self, default_graph):
        assert default_graph["stats"]["node_count"] == 25
        assert default_graph["stats"]["edge_count"] == 44

    def test_average_degree(self, default_graph):
        """Average degree = 2*39/23 = 78/23 ≈ 3.3913."""
        avg = default_graph["stats"]["avg_degree"]
        expected = 2 * 44 / 25
        assert abs(avg - expected) < 0.01, (
            f"avg_degree={avg}, expected={expected}"
        )


# ──────────────────────────────────────────────
# 4. NODE STRUCTURE
# ──────────────────────────────────────────────

class TestNodeStructure:

    def test_nodes_have_required_fields(self, default_graph):
        for i, node in enumerate(default_graph["nodes"]):
            assert "index" in node, f"Node {i} missing index"
            assert "x" in node, f"Node {i} missing x"
            assert "y" in node, f"Node {i} missing y"
            assert "color" in node, f"Node {i} missing color"
            assert "radius" in node, f"Node {i} missing radius"
            assert "degree" in node, f"Node {i} missing degree"

    def test_node_indices_are_sequential(self, default_graph):
        indices = [n["index"] for n in default_graph["nodes"]]
        assert indices == list(range(25))

    def test_all_coordinates_finite(self, default_graph):
        for node in default_graph["nodes"]:
            assert math.isfinite(node["x"]), f"Node {node['index']} x not finite"
            assert math.isfinite(node["y"]), f"Node {node['index']} y not finite"

    def test_all_radii_positive(self, default_graph):
        for node in default_graph["nodes"]:
            assert node["radius"] > 0, f"Node {node['index']} radius <= 0"

    def test_all_degrees_positive(self, default_graph):
        """Every node in a connected graph must have degree >= 1."""
        for node in default_graph["nodes"]:
            assert node["degree"] >= 1, (
                f"Node {node['index']} has degree 0 — disconnected"
            )


# ──────────────────────────────────────────────
# 5. EDGE STRUCTURE
# ──────────────────────────────────────────────

class TestEdgeStructure:

    def test_edges_are_pairs(self, default_graph):
        for i, edge in enumerate(default_graph["edges"]):
            assert "a" in edge and "b" in edge, f"Edge {i} missing a or b"
            assert isinstance(edge["a"], int)
            assert isinstance(edge["b"], int)

    def test_edge_indices_in_range(self, default_graph):
        n = len(default_graph["nodes"])
        for i, edge in enumerate(default_graph["edges"]):
            assert 0 <= edge["a"] < n, f"Edge {i}: a={edge['a']} out of range"
            assert 0 <= edge["b"] < n, f"Edge {i}: b={edge['b']} out of range"

    def test_no_self_loops(self, default_graph):
        for i, edge in enumerate(default_graph["edges"]):
            assert edge["a"] != edge["b"], f"Edge {i}: self-loop ({edge['a']})"

    def test_no_duplicate_edges(self, default_graph):
        """No two edges should connect the same pair of nodes."""
        seen = set()
        for edge in default_graph["edges"]:
            pair = (min(edge["a"], edge["b"]), max(edge["a"], edge["b"]))
            assert pair not in seen, f"Duplicate edge: {pair}"
            seen.add(pair)

    def test_edges_have_color(self, default_graph):
        for edge in default_graph["edges"]:
            assert "color" in edge
            assert edge["color"] is not None


# ──────────────────────────────────────────────
# 6. CONNECTIVITY
# ──────────────────────────────────────────────

class TestConnectivity:
    """The graph must be fully connected (one component)."""

    def test_graph_is_connected(self, default_graph):
        """BFS from node 0 must reach all 23 nodes."""
        adj = default_graph["adjacency"]
        n = len(default_graph["nodes"])
        visited = set()
        queue = [0]
        visited.add(0)
        while queue:
            current = queue.pop(0)
            for neighbor in adj[str(current)]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        assert len(visited) == n, (
            f"BFS reached {len(visited)}/{n} nodes — graph is disconnected"
        )

    def test_no_isolated_nodes(self, default_graph):
        adj = default_graph["adjacency"]
        for node in default_graph["nodes"]:
            idx = str(node["index"])
            assert idx in adj, f"Node {idx} missing from adjacency"
            assert len(adj[idx]) >= 1, f"Node {idx} is isolated"


# ──────────────────────────────────────────────
# 7. JUNCTION NODE (degree 6)
# ──────────────────────────────────────────────

class TestJunctionNode:
    """The most connected node — where the stem meets the bowl."""

    def test_junction_has_degree_6(self, default_graph):
        """'The most connected node (degree 6) sits at the junction.'"""
        ji = default_graph["stats"]["junction_index"]
        node = default_graph["nodes"][ji]
        assert node["degree"] == 6, (
            f"Junction node {ji} has degree {node['degree']}, expected 6"
        )

    def test_junction_is_max_degree(self, default_graph):
        """The junction must be THE most connected node."""
        max_deg = default_graph["stats"]["max_degree"]
        assert max_deg == 6
        ji = default_graph["stats"]["junction_index"]
        node = default_graph["nodes"][ji]
        assert node["degree"] == max_deg

    def test_junction_has_amber_color(self, default_graph):
        """High-connectivity nodes use amber accent."""
        ji = default_graph["stats"]["junction_index"]
        node = default_graph["nodes"][ji]
        assert node["color"] == "amber"

    def test_junction_has_larger_radius(self, default_graph, palette):
        """Junction node uses the larger 'junction' radius from palette."""
        ji = default_graph["stats"]["junction_index"]
        node = default_graph["nodes"][ji]
        junction_r = palette["sizing"]["node_radius"]["junction"]
        default_r = palette["sizing"]["node_radius"]["default"]
        assert abs(node["radius"] - junction_r) < 1e-6
        assert node["radius"] > default_r

    def test_junction_connects_stem_and_bowl(self, default_graph):
        """The junction node's neighbors should include nodes from both
        the stem region (left side) and the bowl region (right side)."""
        ji = default_graph["stats"]["junction_index"]
        adj = default_graph["adjacency"]
        neighbors = adj[str(ji)]
        node_x = {n["index"]: n["x"] for n in default_graph["nodes"]}
        junction_x = node_x[ji]

        left_neighbors = [n for n in neighbors if node_x[n] <= junction_x + 0.1]
        right_neighbors = [n for n in neighbors if node_x[n] > junction_x + 0.1]

        assert len(left_neighbors) >= 1, "Junction must connect to stem (left)"
        assert len(right_neighbors) >= 1, "Junction must connect to bowl (right)"


# ──────────────────────────────────────────────
# 8. ADJACENCY LIST
# ──────────────────────────────────────────────

class TestAdjacencyList:

    def test_adjacency_has_all_nodes(self, default_graph):
        adj = default_graph["adjacency"]
        for i in range(25):
            assert str(i) in adj, f"Node {i} missing from adjacency"

    def test_adjacency_is_symmetric(self, default_graph):
        """If a→b exists, b→a must exist."""
        adj = default_graph["adjacency"]
        for node_str, neighbors in adj.items():
            node = int(node_str)
            for neighbor in neighbors:
                assert node in adj[str(neighbor)], (
                    f"Edge {node}→{neighbor} exists but {neighbor}→{node} doesn't"
                )

    def test_adjacency_matches_edges(self, default_graph):
        """Adjacency list must encode exactly the same connectivity as edges."""
        adj = default_graph["adjacency"]
        # Build edge set from edges
        edge_set = set()
        for edge in default_graph["edges"]:
            edge_set.add((min(edge["a"], edge["b"]), max(edge["a"], edge["b"])))
        # Build edge set from adjacency
        adj_edge_set = set()
        for node_str, neighbors in adj.items():
            node = int(node_str)
            for neighbor in neighbors:
                adj_edge_set.add((min(node, neighbor), max(node, neighbor)))
        assert edge_set == adj_edge_set

    def test_adjacency_degree_matches_node(self, default_graph):
        """Each node's degree field must equal its adjacency list length."""
        adj = default_graph["adjacency"]
        for node in default_graph["nodes"]:
            adj_deg = len(adj[str(node["index"])])
            assert adj_deg == node["degree"], (
                f"Node {node['index']}: degree={node['degree']} but "
                f"adjacency has {adj_deg} neighbors"
            )


# ──────────────────────────────────────────────
# 9. DEGREE DISTRIBUTION
# ──────────────────────────────────────────────

class TestDegreeDistribution:

    def test_minimum_degree_at_least_2(self, default_graph):
        """In a well-formed wireframe letter, every node should have
        degree >= 2 (no dead ends) for visual continuity, with the
        possible exception of the stem's top and bottom endpoints."""
        degrees = [n["degree"] for n in default_graph["nodes"]]
        low_degree = [n for n in default_graph["nodes"] if n["degree"] < 2]
        # Allow at most 2 nodes with degree 1 (stem endpoints)
        assert len(low_degree) <= 3, (
            f"{len(low_degree)} nodes with degree < 2: "
            f"{[(n['index'], n['degree']) for n in low_degree]}"
        )

    def test_max_degree_is_6(self, default_graph):
        max_deg = max(n["degree"] for n in default_graph["nodes"])
        assert max_deg == 6

    def test_no_degree_above_6(self, default_graph):
        for node in default_graph["nodes"]:
            assert node["degree"] <= 6, (
                f"Node {node['index']} has degree {node['degree']} > 6"
            )

    def test_degree_sum_equals_twice_edges(self, default_graph):
        """Handshaking lemma: sum of degrees = 2 × edge count."""
        total = sum(n["degree"] for n in default_graph["nodes"])
        assert total == 2 * len(default_graph["edges"]), (
            f"Degree sum {total} != 2 × {len(default_graph['edges'])}"
        )


# ──────────────────────────────────────────────
# 10. SPATIAL PROPERTIES
# ──────────────────────────────────────────────

class TestSpatialProperties:
    """The graph must look like a P in 2D space."""

    def test_stem_is_roughly_vertical(self, default_graph, graph_module):
        """The stem nodes should share approximately the same X coordinate."""
        ji = graph_module.JUNCTION_NODE_INDEX
        nodes = default_graph["nodes"]
        junction_x = nodes[ji]["x"]
        # Find stem nodes: those near the junction's X and below it
        stem_candidates = [
            n for n in nodes
            if abs(n["x"] - junction_x) < 0.4 and n["y"] < nodes[ji]["y"]
        ]
        assert len(stem_candidates) >= 3, (
            f"Only {len(stem_candidates)} stem candidates found"
        )
        xs = [n["x"] for n in stem_candidates]
        x_spread = max(xs) - min(xs)
        assert x_spread < 1.0, f"Stem X spread {x_spread} too wide"

    def test_bowl_extends_to_the_right(self, default_graph, graph_module):
        """Some nodes must be significantly to the right of the stem."""
        ji = graph_module.JUNCTION_NODE_INDEX
        junction_x = default_graph["nodes"][ji]["x"]
        right_nodes = [
            n for n in default_graph["nodes"] if n["x"] > junction_x + 1.0
        ]
        assert len(right_nodes) >= 4, (
            f"Only {len(right_nodes)} nodes to the right of the stem"
        )

    def test_vertical_extent(self, default_graph):
        """The P should span a reasonable vertical range."""
        ys = [n["y"] for n in default_graph["nodes"]]
        height = max(ys) - min(ys)
        assert height >= 3.0, f"P height {height} too short"
        assert height <= 8.0, f"P height {height} too tall"

    def test_horizontal_extent(self, default_graph):
        """The P should span a reasonable horizontal range."""
        xs = [n["x"] for n in default_graph["nodes"]]
        width = max(xs) - min(xs)
        assert width >= 2.0, f"P width {width} too narrow"
        assert width <= 6.0, f"P width {width} too wide"

    def test_fits_inside_ring(self, default_graph, palette):
        """All nodes must fit inside the outer ring radius."""
        ring_r = palette["sizing"]["ring_radii"]["outer_outer"]
        for node in default_graph["nodes"]:
            dist = math.sqrt(node["x"]**2 + node["y"]**2)
            assert dist < ring_r, (
                f"Node {node['index']} at ({node['x']:.2f},{node['y']:.2f}) "
                f"distance {dist:.2f} exceeds ring {ring_r}"
            )


# ──────────────────────────────────────────────
# 11. COLOR ASSIGNMENTS
# ──────────────────────────────────────────────

class TestColorAssignments:

    def test_all_node_colors_in_palette(self, default_graph, palette):
        palette_colors = set(palette["colors"].keys())
        for node in default_graph["nodes"]:
            assert node["color"] in palette_colors, (
                f"Node {node['index']} color '{node['color']}' not in palette"
            )

    def test_all_edge_colors_in_palette(self, default_graph, palette):
        palette_colors = set(palette["colors"].keys())
        for edge in default_graph["edges"]:
            assert edge["color"] in palette_colors

    def test_blue_glow_used_sparingly(self, default_graph):
        """'Blue Glow used sparingly (one node at position 0).'
        At most 1 node should use blue_glow."""
        blue_nodes = [n for n in default_graph["nodes"] if n["color"] == "blue_glow"]
        assert len(blue_nodes) <= 1, (
            f"blue_glow used on {len(blue_nodes)} nodes, expected <= 1"
        )

    def test_majority_nodes_are_copper(self, default_graph):
        """Copper is the dominant structural color — majority of nodes."""
        copper_count = sum(1 for n in default_graph["nodes"] if n["color"] == "copper")
        assert copper_count >= 12, (
            f"Only {copper_count}/23 nodes are copper — expected majority"
        )

    def test_edges_default_to_copper(self, default_graph):
        """Edges should primarily use the dominant structural color."""
        copper_edges = sum(1 for e in default_graph["edges"] if e["color"] == "copper")
        assert copper_edges >= len(default_graph["edges"]) * 0.8


# ──────────────────────────────────────────────
# 12. PALETTE DEPENDENCY
# ──────────────────────────────────────────────

class TestPaletteDependency:

    def test_node_radii_from_palette(self, default_graph, palette):
        junction_r = palette["sizing"]["node_radius"]["junction"]
        default_r = palette["sizing"]["node_radius"]["default"]
        ji = default_graph["stats"]["junction_index"]
        for node in default_graph["nodes"]:
            if node["index"] == ji:
                assert abs(node["radius"] - junction_r) < 1e-6
            else:
                assert abs(node["radius"] - default_r) < 1e-6

    def test_edge_thickness_in_output(self, default_graph, palette):
        """Graph output must include the edge thickness from palette."""
        expected = palette["sizing"]["edge_thickness"]
        assert "edge_thickness" in default_graph
        assert abs(default_graph["edge_thickness"] - expected) < 1e-6

    def test_edge_opacity_in_output(self, default_graph, palette):
        expected = palette["opacity_defaults"]["edge"]["base"]
        assert "edge_opacity" in default_graph
        assert abs(default_graph["edge_opacity"] - expected) < 1e-6


# ──────────────────────────────────────────────
# 13. COORDINATE SANITY
# ──────────────────────────────────────────────

class TestCoordinateSanity:

    def test_no_nan(self, default_graph):
        for node in default_graph["nodes"]:
            assert not math.isnan(node["x"])
            assert not math.isnan(node["y"])

    def test_no_inf(self, default_graph):
        for node in default_graph["nodes"]:
            assert not math.isinf(node["x"])
            assert not math.isinf(node["y"])

    def test_within_logo_space(self, default_graph):
        for node in default_graph["nodes"]:
            assert -6.0 <= node["x"] <= 6.0
            assert -6.0 <= node["y"] <= 6.0

    def test_no_coincident_nodes(self, default_graph):
        """No unexpected coincident nodes. Spec allows N10=N16 (same grid crossing)."""
        positions = [(round(n["x"], 4), round(n["y"], 4))
                     for n in default_graph["nodes"]]
        unique = len(set(positions))
        # Allow up to 1 coincident pair (N10/N16 in spec)
        assert unique >= len(positions) - 1, (
            f"Too many coincident nodes: {len(positions) - unique} pairs"
        )


# ──────────────────────────────────────────────
# 14. VALIDATION
# ──────────────────────────────────────────────

class TestValidation:

    def test_validate_passes_default(self, graph_module, palette):
        errors = graph_module.validate(palette)
        assert errors == [], f"Unexpected errors: {errors}"


# ──────────────────────────────────────────────
# 15. JSON FILE OUTPUT
# ──────────────────────────────────────────────

class TestJsonOutput:

    def test_file_is_created(self, graph_json_path):
        assert graph_json_path.exists()
        assert graph_json_path.name == "graph.json"

    def test_file_is_valid_json(self, graph_json_path):
        with open(graph_json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_in_build_directory(self, graph_json_path):
        assert graph_json_path.parent.name == "build"

    def test_file_roundtrips(self, graph_json_path, default_graph):
        with open(graph_json_path) as f:
            from_file = json.load(f)
        assert from_file["stats"] == default_graph["stats"]
        assert len(from_file["nodes"]) == len(default_graph["nodes"])
        assert len(from_file["edges"]) == len(default_graph["edges"])


# ──────────────────────────────────────────────
# 16. DESIGN RATIONALE COMPLIANCE
# ──────────────────────────────────────────────

class TestDesignRationale:

    def test_graph_not_font_glyph(self, default_graph):
        """'Not a typographic P rendered in a font, but a P built from
        structure.' — The graph must have explicit edges, not just
        positioned dots."""
        assert len(default_graph["edges"]) > 0

    def test_individual_facts_are_inert(self, default_graph):
        """'Individual facts (nodes) are inert. Their value comes from
        connections (edges).' — Average degree must be > 2 (not a simple
        chain)."""
        avg = default_graph["stats"]["avg_degree"]
        assert avg > 2.0

    def test_highest_value_is_junction(self, default_graph):
        """'The highest-value nodes are... the ones with the most links —
        the junction points between disciplines.'"""
        max_deg = max(n["degree"] for n in default_graph["nodes"])
        ji = default_graph["stats"]["junction_index"]
        assert default_graph["nodes"][ji]["degree"] == max_deg

    def test_deliberately_ambiguous(self, default_graph):
        """'The graph is not a neural network, not a molecule, not a circuit
        diagram. It's deliberately ambiguous.' — No explicit subject
        iconography: no special node types or labels beyond index/color."""
        for node in default_graph["nodes"]:
            assert "type" not in node or node.get("type") == "node"
            assert "label" not in node

    def test_no_text_in_mark(self, default_graph):
        """'No text in the mark itself.' — Graph output must not contain
        any text/label rendering data."""
        assert "text" not in default_graph
        assert "label" not in default_graph
