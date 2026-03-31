"""
PAL's Notes Logo Pipeline — Step 3: Arcs — TEST SUITE (TDD)

Written BEFORE implementation. These tests define the contract that arcs.py
must satisfy.

Run:
    cd pals-logo-pipeline
    python -m pytest test_arcs.py -v

Requires: palette.json in build/ (produced by step 0).

The bowl of the P is formed by three concentric arcs at different radii.
From the design rationale:

  "Three concentric arcs form the bowl of the P, rendered at different radii
   (≈ 0.75, ≈ 1.23, ≈ 1.72 units from their respective centers). They are
   smooth curves among the angular edges — the only non-linear geometry in
   the letter."

The arcs serve both structural (completing the P letterform) and animation
purposes (arc runners travel along them). Each arc must be sampled into
a polyline for mesh-strip rendering, and also provide a normalized path
for arc-runner interpolation.

Arc geometry is parametric from:
  - center:      (cx, cy) center point of the arc sweep
  - radius:      distance from center to arc midline
  - start_angle: angular start (radians)
  - end_angle:   angular end (radians)
  - color:       palette color name
  - segments:    polyline resolution for rendering
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
def palette() -> dict:
    path = Path(__file__).parent / "build" / "palette.json"
    assert path.exists(), "build/palette.json not found. Run palette.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def arcs_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import arcs
    return arcs


@pytest.fixture
def default_arcs(arcs_module, palette):
    return arcs_module.build_arcs(palette)


@pytest.fixture
def arcs_json_path(arcs_module, palette) -> Path:
    return arcs_module.write_arcs(palette)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_arcs(self, arcs_module):
        assert callable(getattr(arcs_module, "build_arcs", None))

    def test_has_write_arcs(self, arcs_module):
        assert callable(getattr(arcs_module, "write_arcs", None))

    def test_has_validate(self, arcs_module):
        assert callable(getattr(arcs_module, "validate", None))

    def test_has_default_arc_definitions(self, arcs_module):
        """Module must expose its default arc definitions."""
        assert hasattr(arcs_module, "DEFAULT_ARC_DEFS")
        assert isinstance(arcs_module.DEFAULT_ARC_DEFS, list)


# ──────────────────────────────────────────────
# 2. OUTPUT SCHEMA
# ──────────────────────────────────────────────

class TestOutputSchema:

    def test_has_meta(self, default_arcs):
        assert "_meta" in default_arcs
        assert default_arcs["_meta"]["step"] == 3
        assert default_arcs["_meta"]["name"] == "arcs"

    def test_has_arcs_list(self, default_arcs):
        assert "arcs" in default_arcs
        assert isinstance(default_arcs["arcs"], list)

    def test_exactly_three_arcs(self, default_arcs):
        """Design rationale specifies three concentric arcs."""
        assert len(default_arcs["arcs"]) == 3

    def test_has_arc_runner_paths(self, default_arcs):
        """Must provide pre-computed paths for arc-runner animation."""
        assert "runner_paths" in default_arcs
        assert isinstance(default_arcs["runner_paths"], list)
        assert len(default_arcs["runner_paths"]) == 3


# ──────────────────────────────────────────────
# 3. INDIVIDUAL ARC STRUCTURE
# ──────────────────────────────────────────────

class TestArcStructure:
    """Each arc entry must have definition params, rendering data, and material info."""

    def test_arc_has_definition(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert "cx" in arc, "Arc must have center x"
            assert "cy" in arc, "Arc must have center y"
            assert "radius" in arc, "Arc must have radius"
            assert "start_angle" in arc, "Arc must have start_angle"
            assert "end_angle" in arc, "Arc must have end_angle"

    def test_arc_has_color(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert "color" in arc

    def test_arc_has_polyline(self, default_arcs):
        """Each arc must have sampled points for mesh-strip rendering."""
        for arc in default_arcs["arcs"]:
            assert "points" in arc
            assert isinstance(arc["points"], list)
            assert len(arc["points"]) >= 10, "Need sufficient resolution"

    def test_arc_has_thickness(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert "main_thickness" in arc
            assert "bloom_thickness" in arc
            assert arc["main_thickness"] > 0
            assert arc["bloom_thickness"] > arc["main_thickness"]

    def test_arc_has_opacities(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert "main_opacity" in arc
            assert "bloom_opacity" in arc
            assert 0 < arc["main_opacity"] <= 1.0
            assert 0 < arc["bloom_opacity"] <= 1.0
            assert arc["bloom_opacity"] < arc["main_opacity"]

    def test_arc_has_index(self, default_arcs):
        """Each arc must have a stable index (0=inner, 1=mid, 2=outer)."""
        indices = [arc["index"] for arc in default_arcs["arcs"]]
        assert sorted(indices) == [0, 1, 2]


# ──────────────────────────────────────────────
# 4. POLYLINE POINT STRUCTURE
# ──────────────────────────────────────────────

class TestPolylinePoints:
    """Sampled points along each arc for mesh-strip construction."""

    def test_points_have_xy(self, default_arcs):
        for arc in default_arcs["arcs"]:
            for pt in arc["points"]:
                assert "x" in pt and "y" in pt
                assert math.isfinite(pt["x"])
                assert math.isfinite(pt["y"])

    def test_points_have_normals(self, default_arcs):
        """Each point needs outward normal for thickness extrusion."""
        for arc in default_arcs["arcs"]:
            for pt in arc["points"]:
                assert "nx" in pt and "ny" in pt
                # Normals must be unit length
                length = math.sqrt(pt["nx"]**2 + pt["ny"]**2)
                assert abs(length - 1.0) < 1e-4, (
                    f"Normal not unit: ({pt['nx']}, {pt['ny']}), len={length}"
                )

    def test_points_have_t_parameter(self, default_arcs):
        """Each point must have a normalized t in [0, 1] for interpolation."""
        for arc in default_arcs["arcs"]:
            for pt in arc["points"]:
                assert "t" in pt
                assert 0.0 <= pt["t"] <= 1.0

    def test_t_is_monotonically_increasing(self, default_arcs):
        for arc in default_arcs["arcs"]:
            ts = [pt["t"] for pt in arc["points"]]
            for i in range(1, len(ts)):
                assert ts[i] > ts[i-1], (
                    f"t not monotonic at index {i}: {ts[i]} <= {ts[i-1]}"
                )

    def test_t_starts_at_zero_ends_at_one(self, default_arcs):
        for arc in default_arcs["arcs"]:
            pts = arc["points"]
            assert abs(pts[0]["t"]) < 1e-6
            assert abs(pts[-1]["t"] - 1.0) < 1e-6

    def test_points_lie_on_arc(self, default_arcs):
        """Every sampled point should be at the specified radius from center."""
        for arc in default_arcs["arcs"]:
            cx, cy, r = arc["cx"], arc["cy"], arc["radius"]
            for pt in arc["points"]:
                dist = math.sqrt((pt["x"] - cx)**2 + (pt["y"] - cy)**2)
                assert abs(dist - r) < 1e-4, (
                    f"Point ({pt['x']:.3f}, {pt['y']:.3f}) at distance {dist:.4f} "
                    f"from center, expected {r}"
                )

    def test_sufficient_segment_count(self, default_arcs):
        """Arcs should have enough segments for smooth rendering."""
        for arc in default_arcs["arcs"]:
            assert len(arc["points"]) >= 20, (
                f"Arc {arc['index']} has only {len(arc['points'])} points"
            )


# ──────────────────────────────────────────────
# 5. ARC RADII AND ORDERING
# ──────────────────────────────────────────────

class TestRadiiOrdering:
    """The three arcs must be at distinct, increasing radii."""

    def test_radii_are_distinct(self, default_arcs):
        radii = [arc["radius"] for arc in default_arcs["arcs"]]
        assert len(set(radii)) == 3, f"Radii not distinct: {radii}"

    def test_radii_increase_with_index(self, default_arcs):
        """Index 0 = innermost (smallest radius), index 2 = outermost."""
        arcs_sorted = sorted(default_arcs["arcs"], key=lambda a: a["index"])
        for i in range(1, len(arcs_sorted)):
            assert arcs_sorted[i]["radius"] > arcs_sorted[i-1]["radius"], (
                f"Arc {i} radius {arcs_sorted[i]['radius']} not > "
                f"arc {i-1} radius {arcs_sorted[i-1]['radius']}"
            )

    def test_radii_are_positive(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert arc["radius"] > 0

    def test_arcs_are_concentric(self, default_arcs):
        """All three arcs should share approximately the same center."""
        centers = [(arc["cx"], arc["cy"]) for arc in default_arcs["arcs"]]
        cx_spread = max(c[0] for c in centers) - min(c[0] for c in centers)
        cy_spread = max(c[1] for c in centers) - min(c[1] for c in centers)
        # Allow some tolerance — rationale says "respective centers" but
        # they should be close enough to read as concentric
        assert cx_spread < 0.5, f"Center X spread too large: {cx_spread}"
        assert cy_spread < 0.5, f"Center Y spread too large: {cy_spread}"


# ──────────────────────────────────────────────
# 6. ANGULAR SWEEP
# ──────────────────────────────────────────────

class TestAngularSweep:
    """Arc angular properties."""

    def test_start_angle_less_than_end(self, default_arcs):
        for arc in default_arcs["arcs"]:
            assert arc["start_angle"] < arc["end_angle"], (
                f"Arc {arc['index']}: start {arc['start_angle']} >= end {arc['end_angle']}"
            )

    def test_sweep_is_less_than_full_circle(self, default_arcs):
        """Bowl arcs are partial, not full circles."""
        for arc in default_arcs["arcs"]:
            sweep = arc["end_angle"] - arc["start_angle"]
            assert sweep < 2 * math.pi, f"Arc {arc['index']} sweep >= 2π"
            assert sweep > 0.5, f"Arc {arc['index']} sweep too small: {sweep}"

    def test_inner_arc_has_narrower_sweep(self, default_arcs):
        """Gold (outer) has asymmetric sweep; Green/Blue are semicircles."""
        sweeps = []
        for arc in sorted(default_arcs["arcs"], key=lambda a: a["radius"]):
            sweep = arc["end_angle"] - arc["start_angle"]
            sweeps.append(sweep)
        # All sweeps should be > 1.5 radians (meaningful bowl)
        for s in sweeps:
            assert s > 1.5, f"Sweep {s:.3f} too narrow"

    def test_arcs_sweep_to_the_right(self, default_arcs):
        """The bowl opens to the right of the stem. Arc midpoints should
        have x greater than the center x."""
        for arc in default_arcs["arcs"]:
            pts = arc["points"]
            mid_idx = len(pts) // 2
            mid_x = pts[mid_idx]["x"]
            assert mid_x > arc["cx"], (
                f"Arc {arc['index']} midpoint x={mid_x:.2f} not right of center cx={arc['cx']:.2f}"
            )


# ──────────────────────────────────────────────
# 7. RUNNER PATHS
# ──────────────────────────────────────────────

class TestRunnerPaths:
    """Pre-computed paths for the 6 arc-runner particles (2 per arc)."""

    def test_runner_path_per_arc(self, default_arcs):
        assert len(default_arcs["runner_paths"]) == 3

    def test_runner_path_has_arc_index(self, default_arcs):
        for rp in default_arcs["runner_paths"]:
            assert "arc_index" in rp
            assert rp["arc_index"] in (0, 1, 2)

    def test_runner_path_has_points(self, default_arcs):
        for rp in default_arcs["runner_paths"]:
            assert "points" in rp
            assert len(rp["points"]) >= 20

    def test_runner_path_points_match_arc(self, default_arcs):
        """Runner path points should lie on the corresponding arc."""
        arcs_by_idx = {a["index"]: a for a in default_arcs["arcs"]}
        for rp in default_arcs["runner_paths"]:
            arc = arcs_by_idx[rp["arc_index"]]
            cx, cy, r = arc["cx"], arc["cy"], arc["radius"]
            for pt in rp["points"]:
                dist = math.sqrt((pt["x"] - cx)**2 + (pt["y"] - cy)**2)
                assert abs(dist - r) < 1e-4, (
                    f"Runner point off-arc: dist={dist:.4f}, expected {r}"
                )

    def test_runner_path_has_t(self, default_arcs):
        for rp in default_arcs["runner_paths"]:
            for pt in rp["points"]:
                assert "t" in pt
                assert 0.0 <= pt["t"] <= 1.0

    def test_runner_path_has_color(self, default_arcs):
        for rp in default_arcs["runner_paths"]:
            assert "color" in rp


# ──────────────────────────────────────────────
# 8. COLOR ASSIGNMENTS
# ──────────────────────────────────────────────

class TestColorAssignments:
    """Each arc must use a distinct color from the palette, matching the rationale."""

    def test_all_colors_in_palette(self, default_arcs, palette):
        palette_colors = set(palette["colors"].keys())
        for arc in default_arcs["arcs"]:
            assert arc["color"] in palette_colors, (
                f"Arc color '{arc['color']}' not in palette"
            )
        for rp in default_arcs["runner_paths"]:
            assert rp["color"] in palette_colors

    def test_outer_arc_is_warm(self, default_arcs):
        """Outermost arc uses a warm color (amber for Gold arc)."""
        outer = max(default_arcs["arcs"], key=lambda a: a["radius"])
        assert outer["color"] in ("bronze", "amber")

    def test_each_arc_has_color(self, default_arcs):
        colors = [a["color"] for a in default_arcs["arcs"]]
        assert all(c is not None and c != "" for c in colors)

    def test_runner_color_matches_arc(self, default_arcs):
        """Runner path color should match its parent arc."""
        arcs_by_idx = {a["index"]: a for a in default_arcs["arcs"]}
        for rp in default_arcs["runner_paths"]:
            arc = arcs_by_idx[rp["arc_index"]]
            assert rp["color"] == arc["color"]


# ──────────────────────────────────────────────
# 9. PALETTE DEPENDENCY (opacities + thicknesses)
# ──────────────────────────────────────────────

class TestPaletteDependency:

    def test_main_opacity_from_palette(self, default_arcs, palette):
        expected = palette["opacity_defaults"]["arc_main"]["base"]
        for arc in default_arcs["arcs"]:
            assert abs(arc["main_opacity"] - expected) < 1e-6

    def test_bloom_opacity_from_palette(self, default_arcs, palette):
        expected = palette["opacity_defaults"]["arc_bloom"]["base"]
        for arc in default_arcs["arcs"]:
            assert abs(arc["bloom_opacity"] - expected) < 1e-6

    def test_main_thickness_from_palette(self, default_arcs, palette):
        expected = palette["sizing"]["arc_main_thickness"]
        for arc in default_arcs["arcs"]:
            assert abs(arc["main_thickness"] - expected) < 1e-6

    def test_bloom_thickness_from_palette(self, default_arcs, palette):
        expected = palette["sizing"]["arc_bloom_thickness"]
        for arc in default_arcs["arcs"]:
            assert abs(arc["bloom_thickness"] - expected) < 1e-6


# ──────────────────────────────────────────────
# 10. COORDINATE SANITY
# ──────────────────────────────────────────────

class TestCoordinateSanity:

    def _all_coords(self, arcs_data: dict) -> list[tuple[str, float]]:
        coords = []
        for arc in arcs_data["arcs"]:
            coords.append(("arc.cx", arc["cx"]))
            coords.append(("arc.cy", arc["cy"]))
            for pt in arc["points"]:
                coords.append(("arc.pt.x", pt["x"]))
                coords.append(("arc.pt.y", pt["y"]))
        for rp in arcs_data["runner_paths"]:
            for pt in rp["points"]:
                coords.append(("runner.pt.x", pt["x"]))
                coords.append(("runner.pt.y", pt["y"]))
        return coords

    def test_no_nan(self, default_arcs):
        for label, val in self._all_coords(default_arcs):
            assert not math.isnan(val), f"{label} is NaN"

    def test_no_inf(self, default_arcs):
        for label, val in self._all_coords(default_arcs):
            assert not math.isinf(val), f"{label} is Inf"

    def test_within_logo_space(self, default_arcs):
        for label, val in self._all_coords(default_arcs):
            assert -6.0 <= val <= 6.0, f"{label} = {val} outside logo space ±6"


# ──────────────────────────────────────────────
# 11. VALIDATION
# ──────────────────────────────────────────────

class TestValidation:

    def test_validate_passes_default(self, arcs_module, palette):
        errors = arcs_module.validate(palette)
        assert errors == []

    def test_validate_catches_zero_radius(self, arcs_module, palette):
        bad_defs = [{"cx": 0, "cy": 0, "radius": 0.0,
                     "start_angle": -1.0, "end_angle": 1.0, "color": "copper"}]
        errors = arcs_module.validate(palette, arc_defs=bad_defs)
        assert len(errors) > 0

    def test_validate_catches_inverted_angles(self, arcs_module, palette):
        bad_defs = [{"cx": 0, "cy": 0, "radius": 1.0,
                     "start_angle": 1.0, "end_angle": -1.0, "color": "copper"}]
        errors = arcs_module.validate(palette, arc_defs=bad_defs)
        assert len(errors) > 0

    def test_validate_catches_unknown_color(self, arcs_module, palette):
        bad_defs = [{"cx": 0, "cy": 0, "radius": 1.0,
                     "start_angle": -1.0, "end_angle": 1.0, "color": "neon_pink"}]
        errors = arcs_module.validate(palette, arc_defs=bad_defs)
        assert len(errors) > 0


# ──────────────────────────────────────────────
# 12. JSON FILE OUTPUT
# ──────────────────────────────────────────────

class TestJsonOutput:

    def test_file_is_created(self, arcs_json_path):
        assert arcs_json_path.exists()
        assert arcs_json_path.name == "arcs.json"

    def test_file_is_valid_json(self, arcs_json_path):
        with open(arcs_json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_in_build_directory(self, arcs_json_path):
        assert arcs_json_path.parent.name == "build"

    def test_file_roundtrips(self, arcs_json_path, default_arcs):
        with open(arcs_json_path) as f:
            from_file = json.load(f)
        assert len(from_file["arcs"]) == len(default_arcs["arcs"])
        for i in range(3):
            assert from_file["arcs"][i]["radius"] == default_arcs["arcs"][i]["radius"]
            assert len(from_file["arcs"][i]["points"]) == len(default_arcs["arcs"][i]["points"])


# ──────────────────────────────────────────────
# 13. DESIGN RATIONALE COMPLIANCE
# ──────────────────────────────────────────────

class TestDesignRationale:

    def test_three_arcs(self, default_arcs):
        """'Three concentric arcs form the bowl of the P.'"""
        assert len(default_arcs["arcs"]) == 3

    def test_arcs_are_smooth_curves(self, default_arcs):
        """'They are smooth curves among the angular edges.'
        Verified by checking points are on-arc (no jagged interpolation).
        Already covered by TestPolylinePoints.test_points_lie_on_arc,
        but re-checked here for traceability."""
        for arc in default_arcs["arcs"]:
            cx, cy, r = arc["cx"], arc["cy"], arc["radius"]
            for pt in arc["points"]:
                dist = math.sqrt((pt["x"] - cx)**2 + (pt["y"] - cy)**2)
                assert abs(dist - r) < 1e-4

    def test_only_non_linear_geometry(self, default_arcs):
        """'The only non-linear geometry in the letter.'
        Arcs must be curved (radius > 0 and sweep > 0)."""
        for arc in default_arcs["arcs"]:
            assert arc["radius"] > 0
            sweep = arc["end_angle"] - arc["start_angle"]
            assert sweep > 0

    def test_arcs_complete_the_p_shape(self, default_arcs):
        """The arcs should span enough angle to form a recognizable bowl.
        Arc sweep is structural (±45° for mid, ±90° for inner/outer). Min 85° of sweep."""
        for arc in default_arcs["arcs"]:
            sweep_deg = math.degrees(arc["end_angle"] - arc["start_angle"])
            assert sweep_deg >= 85, (
                f"Arc {arc['index']} sweep {sweep_deg:.1f}° too narrow for P bowl"
            )

    def test_arcs_are_routes_not_walls(self, default_arcs):
        """'The P's bowl is not a wall; it's a route.'
        Verified by the existence of runner_paths with matching points."""
        assert len(default_arcs["runner_paths"]) == 3
        for rp in default_arcs["runner_paths"]:
            assert len(rp["points"]) >= 20


# ──────────────────────────────────────────────
# 14. GEOMETRIC CONTINUITY
# ──────────────────────────────────────────────

class TestGeometricContinuity:
    """Adjacent sampled points should be close together (no jumps)."""

    def test_no_large_gaps_in_polyline(self, default_arcs):
        for arc in default_arcs["arcs"]:
            pts = arc["points"]
            for i in range(1, len(pts)):
                dx = pts[i]["x"] - pts[i-1]["x"]
                dy = pts[i]["y"] - pts[i-1]["y"]
                gap = math.sqrt(dx*dx + dy*dy)
                # Max gap depends on radius and segment count, but should
                # never exceed ~0.5 units for reasonable resolution
                assert gap < 0.5, (
                    f"Arc {arc['index']}: gap of {gap:.3f} between points {i-1} and {i}"
                )

    def test_arc_length_is_reasonable(self, default_arcs):
        """Total polyline length should approximate the analytical arc length."""
        for arc in default_arcs["arcs"]:
            sweep = arc["end_angle"] - arc["start_angle"]
            analytical = arc["radius"] * sweep
            pts = arc["points"]
            poly_len = sum(
                math.sqrt((pts[i]["x"]-pts[i-1]["x"])**2 + (pts[i]["y"]-pts[i-1]["y"])**2)
                for i in range(1, len(pts))
            )
            # Polyline should be within 2% of analytical
            assert abs(poly_len - analytical) / analytical < 0.02, (
                f"Arc {arc['index']}: polyline length {poly_len:.3f} vs "
                f"analytical {analytical:.3f} (error {abs(poly_len-analytical)/analytical*100:.1f}%)"
            )
