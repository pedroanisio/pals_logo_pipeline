"""
PAL's Notes Logo Pipeline — Step 2: Nib — TEST SUITE (TDD)

Written BEFORE implementation. These tests define the contract that nib.py
must satisfy.

Run:
    cd pals-logo-pipeline
    python -m pytest test_nib.py -v

Requires: palette.json in build/ (produced by step 0).

The pen nib is the most literal element in the logo — a fountain pen nib
anchoring the abstract graph to the physical act of writing. From the
design rationale:

  "The stem of the P terminates in a pen nib — a diamond shape with a
   central line and a glowing ball at the junction. Ink drops fall from
   the tip."

From Image 4 (the annotated blueprint): the nib is a V/fan of converging
lines radiating from the tip upward, with teal accent nodes on the sides,
amber nodes at the fan tips, and a warm-white glowing ball at the top
junction.

Nib geometry is parametric from four values:
  - tip_y:      Y coordinate of the nib's lowest point (the writing tip)
  - top_y:      Y coordinate where the nib meets the stem
  - half_width: half the lateral span at the widest point
  - fan_count:  number of fan lines per side (excluding center line)
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
    """Load palette.json. Fails fast if step 0 hasn't been run."""
    path = Path(__file__).parent / "build" / "palette.json"
    assert path.exists(), (
        "build/palette.json not found. Run `python palette.py` first."
    )
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def nib_module():
    """Import nib module."""
    sys.path.insert(0, str(Path(__file__).parent))
    import nib
    return nib


@pytest.fixture
def default_nib(nib_module, palette):
    """Build nib geometry with default parameters."""
    return nib_module.build_nib(palette)


@pytest.fixture
def custom_nib(nib_module, palette):
    """Build nib geometry with custom parameters."""
    return nib_module.build_nib(
        palette,
        tip_y=-5.0,
        top_y=-3.5,
        half_width=0.8,
        fan_count=4,
    )


@pytest.fixture
def nib_json_path(nib_module, palette) -> Path:
    """Run the full pipeline step and return the output path."""
    return nib_module.write_nib(palette)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:
    """nib.py must expose specific public functions."""

    def test_has_build_nib(self, nib_module):
        assert callable(getattr(nib_module, "build_nib", None))

    def test_has_write_nib(self, nib_module):
        assert callable(getattr(nib_module, "write_nib", None))

    def test_has_validate(self, nib_module):
        assert callable(getattr(nib_module, "validate", None))

    def test_has_default_params(self, nib_module):
        """Module must expose its default parameter values."""
        assert hasattr(nib_module, "DEFAULT_TIP_Y")
        assert hasattr(nib_module, "DEFAULT_TOP_Y")
        assert hasattr(nib_module, "DEFAULT_HALF_WIDTH")
        assert hasattr(nib_module, "DEFAULT_FAN_COUNT")


# ──────────────────────────────────────────────
# 2. OUTPUT SCHEMA
# ──────────────────────────────────────────────

class TestOutputSchema:
    """The returned dict (and JSON) must have a well-defined structure."""

    def test_has_meta(self, default_nib):
        assert "_meta" in default_nib
        assert default_nib["_meta"]["step"] == 2
        assert default_nib["_meta"]["name"] == "nib"

    def test_has_params(self, default_nib):
        """Output must record the parameters used to generate it."""
        params = default_nib["params"]
        assert "tip_y" in params
        assert "top_y" in params
        assert "half_width" in params
        assert "fan_count" in params

    def test_has_fan_lines(self, default_nib):
        assert "fan_lines" in default_nib
        assert isinstance(default_nib["fan_lines"], list)
        assert len(default_nib["fan_lines"]) > 0

    def test_has_outline_lines(self, default_nib):
        assert "outline_lines" in default_nib
        assert isinstance(default_nib["outline_lines"], list)

    def test_has_center_line(self, default_nib):
        assert "center_line" in default_nib

    def test_has_accent_nodes(self, default_nib):
        assert "accent_nodes" in default_nib
        assert isinstance(default_nib["accent_nodes"], list)

    def test_has_junction_ball(self, default_nib):
        assert "junction_ball" in default_nib

    def test_has_ink_origin(self, default_nib):
        """Must specify the point from which ink drops emit."""
        assert "ink_origin" in default_nib
        origin = default_nib["ink_origin"]
        assert "x" in origin
        assert "y" in origin


# ──────────────────────────────────────────────
# 3. LINE GEOMETRY STRUCTURE
# ──────────────────────────────────────────────

class TestLineGeometry:
    """Every line (fan, outline, center) must have endpoints and material info."""

    def _check_line(self, line: dict) -> None:
        assert "x1" in line and "y1" in line, "Line must have start point"
        assert "x2" in line and "y2" in line, "Line must have end point"
        assert "color" in line, "Line must reference a palette color"
        assert "thickness" in line, "Line must specify thickness"
        assert "opacity" in line, "Line must specify opacity"
        # Coordinates must be finite
        for k in ("x1", "y1", "x2", "y2"):
            assert math.isfinite(line[k]), f"Line coord {k} is not finite: {line[k]}"
        # Thickness and opacity must be positive
        assert line["thickness"] > 0
        assert 0 < line["opacity"] <= 1.0

    def test_fan_lines_structure(self, default_nib):
        for line in default_nib["fan_lines"]:
            self._check_line(line)

    def test_outline_lines_structure(self, default_nib):
        for line in default_nib["outline_lines"]:
            self._check_line(line)

    def test_center_line_structure(self, default_nib):
        self._check_line(default_nib["center_line"])


# ──────────────────────────────────────────────
# 4. FAN LINE PROPERTIES
# ──────────────────────────────────────────────

class TestFanLines:
    """Fan lines radiate from the tip upward in a symmetric spread."""

    def test_fan_count_matches_parameter(self, default_nib):
        """Total fan lines = 2 * fan_count (symmetric left + right)."""
        fan_count = default_nib["params"]["fan_count"]
        assert len(default_nib["fan_lines"]) == 2 * fan_count

    def test_custom_fan_count(self, custom_nib):
        fan_count = custom_nib["params"]["fan_count"]
        assert len(custom_nib["fan_lines"]) == 2 * fan_count

    def test_all_fan_lines_originate_at_tip(self, default_nib):
        """Every fan line starts at the nib tip."""
        tip_x = default_nib["params"]["center_x"]
        tip_y = default_nib["params"]["tip_y"]
        for line in default_nib["fan_lines"]:
            assert abs(line["x1"] - tip_x) < 1e-6, f"Fan line x1={line['x1']} != tip_x={tip_x}"
            assert abs(line["y1"] - tip_y) < 1e-6, f"Fan line y1={line['y1']} != tip_y={tip_y}"

    def test_fan_lines_are_symmetric(self, default_nib):
        """For every fan line ending at (cx + dx, y), there must be one at (cx - dx, y)."""
        cx = default_nib["params"]["center_x"]
        lines = default_nib["fan_lines"]
        endpoints = [(line["x2"] - cx, line["y2"]) for line in lines]
        for dx, y in endpoints:
            mirror = (-dx, y)
            matches = [
                (ex, ey) for ex, ey in endpoints
                if abs(ex - mirror[0]) < 1e-6 and abs(ey - mirror[1]) < 1e-6
            ]
            assert len(matches) >= 1, (
                f"No symmetric mirror for fan endpoint ({cx + dx:.3f}, {y:.3f})"
            )

    def test_fan_lines_end_above_tip(self, default_nib):
        """Fan line endpoints must be above (greater Y than) the tip."""
        tip_y = default_nib["params"]["tip_y"]
        for line in default_nib["fan_lines"]:
            assert line["y2"] > tip_y, (
                f"Fan line endpoint y2={line['y2']} is not above tip_y={tip_y}"
            )

    def test_fan_spread_within_half_width(self, default_nib):
        """Fan line endpoints must not exceed half_width from center."""
        cx = default_nib["params"]["center_x"]
        hw = default_nib["params"]["half_width"]
        for line in default_nib["fan_lines"]:
            dx = abs(line["x2"] - cx)
            assert dx <= hw + 1e-6, (
                f"Fan line endpoint dx={dx} exceeds half_width={hw}"
            )

    def test_fan_lines_spread_evenly(self, default_nib):
        """Fan line endpoints should be evenly distributed across the half-width."""
        cx = default_nib["params"]["center_x"]
        hw = default_nib["params"]["half_width"]
        fan_count = default_nib["params"]["fan_count"]
        lines = default_nib["fan_lines"]

        # Collect right-side endpoints (positive dx), sorted
        right_dxs = sorted([
            line["x2"] - cx for line in lines if line["x2"] > cx + 1e-6
        ])

        if len(right_dxs) >= 2:
            # Check spacing is roughly uniform
            spacings = [right_dxs[i+1] - right_dxs[i] for i in range(len(right_dxs) - 1)]
            if len(spacings) >= 2:
                avg_spacing = sum(spacings) / len(spacings)
                for s in spacings:
                    assert abs(s - avg_spacing) < avg_spacing * 0.5 + 1e-6, (
                        f"Fan spacing not uniform: {spacings}"
                    )


# ──────────────────────────────────────────────
# 5. DIAMOND OUTLINE
# ──────────────────────────────────────────────

class TestDiamondOutline:
    """The nib has a diamond (rhombus) outline connecting 4 cardinal points."""

    def test_outline_has_four_lines(self, default_nib):
        """A diamond has 4 edges."""
        assert len(default_nib["outline_lines"]) == 4

    def test_outline_forms_closed_path(self, default_nib):
        """The 4 outline lines must form a closed polygon (each endpoint
        is shared by exactly 2 lines)."""
        lines = default_nib["outline_lines"]
        points: list[tuple[float, float]] = []
        for line in lines:
            points.append((round(line["x1"], 6), round(line["y1"], 6)))
            points.append((round(line["x2"], 6), round(line["y2"], 6)))

        # Each unique point should appear exactly 2 times
        from collections import Counter
        counts = Counter(points)
        for pt, count in counts.items():
            assert count == 2, (
                f"Diamond vertex {pt} appears {count} times (expected 2 for closed path)"
            )

    def test_outline_is_symmetric(self, default_nib):
        """Diamond must be left-right symmetric about center_x."""
        cx = default_nib["params"]["center_x"]
        lines = default_nib["outline_lines"]
        all_x = [line["x1"] for line in lines] + [line["x2"] for line in lines]
        # For every x offset, its mirror must exist
        offsets = [round(x - cx, 6) for x in all_x]
        for dx in offsets:
            assert -dx in offsets or abs(dx) < 1e-6, (
                f"Diamond outline not symmetric: dx={dx} has no mirror"
            )

    def test_outline_top_vertex_at_top_y(self, default_nib):
        """The topmost vertex of the diamond should be at or near top_y."""
        top_y = default_nib["params"]["top_y"]
        lines = default_nib["outline_lines"]
        all_y = [line["y1"] for line in lines] + [line["y2"] for line in lines]
        max_y = max(all_y)
        assert abs(max_y - top_y) < 0.3, (
            f"Diamond top vertex y={max_y} too far from top_y={top_y}"
        )

    def test_outline_bottom_vertex_between_tip_and_top(self, default_nib):
        """The bottommost diamond vertex should be between tip_y and top_y."""
        tip_y = default_nib["params"]["tip_y"]
        top_y = default_nib["params"]["top_y"]
        lines = default_nib["outline_lines"]
        all_y = [line["y1"] for line in lines] + [line["y2"] for line in lines]
        min_y = min(all_y)
        mid_y = (tip_y + top_y) / 2
        assert tip_y < min_y < top_y, (
            f"Diamond bottom vertex y={min_y} not between tip_y={tip_y} and top_y={top_y}"
        )

    def test_outline_width_matches_half_width(self, default_nib):
        """The widest points of the diamond should be at ±half_width from center."""
        cx = default_nib["params"]["center_x"]
        hw = default_nib["params"]["half_width"]
        lines = default_nib["outline_lines"]
        all_x = [line["x1"] for line in lines] + [line["x2"] for line in lines]
        max_dx = max(abs(x - cx) for x in all_x)
        assert abs(max_dx - hw) < 1e-6, (
            f"Diamond max half-width={max_dx} doesn't match half_width={hw}"
        )


# ──────────────────────────────────────────────
# 6. CENTER LINE
# ──────────────────────────────────────────────

class TestCenterLine:
    """A single line running vertically through the nib center (blue glow)."""

    def test_center_line_is_vertical(self, default_nib):
        cl = default_nib["center_line"]
        assert abs(cl["x1"] - cl["x2"]) < 1e-6, "Center line must be vertical"

    def test_center_line_on_center_x(self, default_nib):
        cx = default_nib["params"]["center_x"]
        cl = default_nib["center_line"]
        assert abs(cl["x1"] - cx) < 1e-6

    def test_center_line_spans_tip_to_top(self, default_nib):
        """Center line must span from tip to at or above top_y."""
        tip_y = default_nib["params"]["tip_y"]
        top_y = default_nib["params"]["top_y"]
        cl = default_nib["center_line"]
        min_y = min(cl["y1"], cl["y2"])
        max_y = max(cl["y1"], cl["y2"])
        assert min_y <= tip_y + 1e-6, f"Center line bottom {min_y} doesn't reach tip {tip_y}"
        assert max_y >= top_y - 0.2, f"Center line top {max_y} doesn't reach top {top_y}"

    def test_center_line_uses_blue_glow(self, default_nib):
        """Design rationale: nib center line uses the blue_glow color."""
        cl = default_nib["center_line"]
        assert cl["color"] == "blue_glow"


# ──────────────────────────────────────────────
# 7. ACCENT NODES
# ──────────────────────────────────────────────

class TestAccentNodes:
    """Small colored dots placed on the nib body."""

    def test_accent_nodes_have_required_fields(self, default_nib):
        for node in default_nib["accent_nodes"]:
            assert "x" in node and "y" in node
            assert "color" in node
            assert "radius" in node
            assert math.isfinite(node["x"])
            assert math.isfinite(node["y"])
            assert node["radius"] > 0

    def test_accent_nodes_are_symmetric(self, default_nib):
        """Accent nodes must be left-right symmetric about center_x."""
        cx = default_nib["params"]["center_x"]
        nodes = default_nib["accent_nodes"]
        offsets = [(round(n["x"] - cx, 6), round(n["y"], 6)) for n in nodes]
        for dx, y in offsets:
            if abs(dx) < 1e-6:
                continue  # on-center node, no mirror needed
            mirror = (-dx, y)
            matches = [
                (ex, ey) for ex, ey in offsets
                if abs(ex - mirror[0]) < 1e-6 and abs(ey - mirror[1]) < 1e-6
            ]
            assert len(matches) >= 1, (
                f"Accent node at ({cx + dx:.3f}, {y:.3f}) has no symmetric mirror"
            )

    def test_accent_nodes_within_nib_bounds(self, default_nib):
        """All accent nodes must be geometrically within the nib area."""
        cx = default_nib["params"]["center_x"]
        hw = default_nib["params"]["half_width"]
        tip_y = default_nib["params"]["tip_y"]
        top_y = default_nib["params"]["top_y"]
        for node in default_nib["accent_nodes"]:
            assert abs(node["x"] - cx) <= hw + 0.1, (
                f"Accent node x={node['x']} outside nib width"
            )
            assert tip_y - 0.1 <= node["y"] <= top_y + 0.3, (
                f"Accent node y={node['y']} outside nib vertical range"
            )

    def test_accent_node_count_is_even(self, default_nib):
        """Symmetry requires an even number of accent nodes
        (or odd if one sits on center_x)."""
        cx = default_nib["params"]["center_x"]
        nodes = default_nib["accent_nodes"]
        off_center = [n for n in nodes if abs(n["x"] - cx) > 1e-6]
        assert len(off_center) % 2 == 0, (
            f"Off-center accent nodes must come in pairs, found {len(off_center)}"
        )


# ──────────────────────────────────────────────
# 8. JUNCTION BALL
# ──────────────────────────────────────────────

class TestJunctionBall:
    """The warm-white glowing ball where the nib meets the stem."""

    def test_junction_ball_fields(self, default_nib):
        jb = default_nib["junction_ball"]
        assert "x" in jb and "y" in jb
        assert "radius" in jb
        assert "color" in jb
        assert "glow_size" in jb
        assert "bloom_size" in jb

    def test_junction_ball_on_center_x(self, default_nib):
        cx = default_nib["params"]["center_x"]
        jb = default_nib["junction_ball"]
        assert abs(jb["x"] - cx) < 1e-6

    def test_junction_ball_near_top(self, default_nib):
        """The ball sits at or just above the top_y of the nib."""
        top_y = default_nib["params"]["top_y"]
        jb = default_nib["junction_ball"]
        assert abs(jb["y"] - top_y) < 0.3, (
            f"Junction ball y={jb['y']} too far from top_y={top_y}"
        )

    def test_junction_ball_uses_warm_white(self, default_nib):
        """Design rationale: glowing ball is warm white."""
        assert default_nib["junction_ball"]["color"] == "warm_white"

    def test_junction_ball_glow_larger_than_core(self, default_nib):
        jb = default_nib["junction_ball"]
        assert jb["glow_size"] > jb["radius"]
        assert jb["bloom_size"] > jb["glow_size"]


# ──────────────────────────────────────────────
# 9. INK ORIGIN
# ──────────────────────────────────────────────

class TestInkOrigin:
    """The point from which ink drops are emitted."""

    def test_ink_origin_at_tip(self, default_nib):
        """Ink drops emit from the nib tip."""
        cx = default_nib["params"]["center_x"]
        tip_y = default_nib["params"]["tip_y"]
        origin = default_nib["ink_origin"]
        assert abs(origin["x"] - cx) < 1e-6
        assert abs(origin["y"] - tip_y) < 1e-6


# ──────────────────────────────────────────────
# 10. PARAMETRIC BEHAVIOR
# ──────────────────────────────────────────────

class TestParametric:
    """Changing input parameters must produce correspondingly changed geometry."""

    def test_wider_half_width_produces_wider_fan(self, nib_module, palette):
        narrow = nib_module.build_nib(palette, half_width=0.4)
        wide = nib_module.build_nib(palette, half_width=1.0)

        narrow_max_dx = max(
            abs(l["x2"] - narrow["params"]["center_x"])
            for l in narrow["fan_lines"]
        )
        wide_max_dx = max(
            abs(l["x2"] - wide["params"]["center_x"])
            for l in wide["fan_lines"]
        )
        assert wide_max_dx > narrow_max_dx

    def test_deeper_tip_produces_longer_center_line(self, nib_module, palette):
        shallow = nib_module.build_nib(palette, tip_y=-3.5, top_y=-3.0)
        deep = nib_module.build_nib(palette, tip_y=-5.0, top_y=-3.0)

        def cl_length(nib_data):
            cl = nib_data["center_line"]
            return abs(cl["y2"] - cl["y1"])

        assert cl_length(deep) > cl_length(shallow)

    def test_more_fan_lines(self, nib_module, palette):
        few = nib_module.build_nib(palette, fan_count=2)
        many = nib_module.build_nib(palette, fan_count=5)
        assert len(many["fan_lines"]) > len(few["fan_lines"])

    def test_params_recorded_in_output(self, custom_nib):
        assert custom_nib["params"]["tip_y"] == -5.0
        assert custom_nib["params"]["top_y"] == -3.5
        assert custom_nib["params"]["half_width"] == 0.8
        assert custom_nib["params"]["fan_count"] == 4


# ──────────────────────────────────────────────
# 11. PALETTE DEPENDENCY
# ──────────────────────────────────────────────

class TestPaletteDependency:
    """All color references in nib output must resolve to palette entries."""

    def _collect_colors(self, nib_data: dict) -> set[str]:
        colors = set()
        for line in nib_data.get("fan_lines", []):
            colors.add(line["color"])
        for line in nib_data.get("outline_lines", []):
            colors.add(line["color"])
        colors.add(nib_data["center_line"]["color"])
        for node in nib_data.get("accent_nodes", []):
            colors.add(node["color"])
        colors.add(nib_data["junction_ball"]["color"])
        if "glow_color" in nib_data["junction_ball"]:
            colors.add(nib_data["junction_ball"]["glow_color"])
        if "bloom_color" in nib_data["junction_ball"]:
            colors.add(nib_data["junction_ball"]["bloom_color"])
        return colors

    def test_all_colors_exist_in_palette(self, default_nib, palette):
        used = self._collect_colors(default_nib)
        available = set(palette["colors"].keys())
        missing = used - available
        assert not missing, f"Colors referenced but not in palette: {missing}"

    def test_opacities_sourced_from_palette(self, default_nib, palette):
        """Nib opacities must match the values defined in palette opacity_defaults."""
        nib_line_opacities = palette["opacity_defaults"]["nib_line"]
        nib_ball_opacities = palette["opacity_defaults"]["nib_ball"]

        # Fan lines use the 'fan' opacity
        for line in default_nib["fan_lines"]:
            assert abs(line["opacity"] - nib_line_opacities["fan"]) < 1e-6, (
                f"Fan line opacity {line['opacity']} != palette fan {nib_line_opacities['fan']}"
            )

        # Outline lines use the 'outline' opacity
        for line in default_nib["outline_lines"]:
            assert abs(line["opacity"] - nib_line_opacities["outline"]) < 1e-6

        # Center line uses the 'center' opacity
        assert abs(
            default_nib["center_line"]["opacity"] - nib_line_opacities["center"]
        ) < 1e-6

        # Junction ball uses nib_ball opacities
        jb = default_nib["junction_ball"]
        assert abs(jb["opacity"] - nib_ball_opacities["core"]) < 1e-6

    def test_thicknesses_sourced_from_palette(self, default_nib, palette):
        """Line thicknesses must match palette sizing."""
        sizing = palette["sizing"]["nib_line_thickness"]

        for line in default_nib["fan_lines"]:
            assert abs(line["thickness"] - sizing["fan"]) < 1e-6

        for line in default_nib["outline_lines"]:
            assert abs(line["thickness"] - sizing["outline"]) < 1e-6

        assert abs(
            default_nib["center_line"]["thickness"] - sizing["center"]
        ) < 1e-6


# ──────────────────────────────────────────────
# 12. COORDINATE SANITY
# ──────────────────────────────────────────────

class TestCoordinateSanity:
    """No NaN, no Inf, no coordinates wildly outside expected bounds."""

    def _all_coords(self, nib_data: dict) -> list[tuple[str, float]]:
        coords = []
        for line in nib_data.get("fan_lines", []):
            coords.extend([("fan.x1", line["x1"]), ("fan.y1", line["y1"]),
                           ("fan.x2", line["x2"]), ("fan.y2", line["y2"])])
        for line in nib_data.get("outline_lines", []):
            coords.extend([("outline.x1", line["x1"]), ("outline.y1", line["y1"]),
                           ("outline.x2", line["x2"]), ("outline.y2", line["y2"])])
        cl = nib_data["center_line"]
        coords.extend([("center.x1", cl["x1"]), ("center.y1", cl["y1"]),
                        ("center.x2", cl["x2"]), ("center.y2", cl["y2"])])
        for node in nib_data.get("accent_nodes", []):
            coords.extend([("accent.x", node["x"]), ("accent.y", node["y"])])
        jb = nib_data["junction_ball"]
        coords.extend([("ball.x", jb["x"]), ("ball.y", jb["y"])])
        origin = nib_data["ink_origin"]
        coords.extend([("ink.x", origin["x"]), ("ink.y", origin["y"])])
        return coords

    def test_no_nan(self, default_nib):
        for label, val in self._all_coords(default_nib):
            assert not math.isnan(val), f"{label} is NaN"

    def test_no_inf(self, default_nib):
        for label, val in self._all_coords(default_nib):
            assert not math.isinf(val), f"{label} is Inf"

    def test_coords_within_logo_space(self, default_nib):
        """All coordinates should be within the logo's ±6 unit space."""
        for label, val in self._all_coords(default_nib):
            assert -6.0 <= val <= 6.0, f"{label} = {val} outside logo space ±6"


# ──────────────────────────────────────────────
# 13. VALIDATION FUNCTION
# ──────────────────────────────────────────────

class TestValidation:
    """nib.validate() must catch bad inputs."""

    def test_validate_passes_on_default(self, nib_module, palette):
        errors = nib_module.validate(palette)
        assert errors == [], f"Unexpected validation errors: {errors}"

    def test_validate_catches_inverted_y(self, nib_module, palette):
        """tip_y must be below top_y (smaller Y value)."""
        errors = nib_module.validate(palette, tip_y=-2.0, top_y=-3.0)
        assert len(errors) > 0
        assert any("tip_y" in e or "top_y" in e or "inverted" in e.lower() for e in errors)

    def test_validate_catches_zero_width(self, nib_module, palette):
        errors = nib_module.validate(palette, half_width=0.0)
        assert len(errors) > 0

    def test_validate_catches_negative_width(self, nib_module, palette):
        errors = nib_module.validate(palette, half_width=-0.5)
        assert len(errors) > 0

    def test_validate_catches_zero_fan_count(self, nib_module, palette):
        errors = nib_module.validate(palette, fan_count=0)
        assert len(errors) > 0


# ──────────────────────────────────────────────
# 14. JSON FILE OUTPUT
# ──────────────────────────────────────────────

class TestJsonOutput:
    """write_nib() must produce a valid, parseable JSON file."""

    def test_file_is_created(self, nib_json_path):
        assert nib_json_path.exists()
        assert nib_json_path.name == "nib.json"

    def test_file_is_valid_json(self, nib_json_path):
        with open(nib_json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_in_build_directory(self, nib_json_path):
        assert nib_json_path.parent.name == "build"

    def test_file_roundtrips(self, nib_json_path, default_nib):
        """JSON file content must match the in-memory build result."""
        with open(nib_json_path) as f:
            from_file = json.load(f)
        # Compare a stable subset (params and counts)
        assert from_file["params"] == default_nib["params"]
        assert len(from_file["fan_lines"]) == len(default_nib["fan_lines"])
        assert len(from_file["outline_lines"]) == len(default_nib["outline_lines"])


# ──────────────────────────────────────────────
# 15. DESIGN RATIONALE COMPLIANCE
# ──────────────────────────────────────────────

class TestDesignRationale:
    """Tests derived directly from statements in the design rationale document."""

    def test_nib_is_active_not_ornamental(self, default_nib):
        """'The ink drops are not decorative. They establish that the nib
        is active, not ornamental.' — ink_origin must exist."""
        assert default_nib["ink_origin"] is not None

    def test_blue_glow_used_sparingly(self, default_nib):
        """'The blue exists to break the warmth... It is used sparingly
        (one node at position 0 and the nib's center line).'
        Only the center line should use blue_glow in the nib."""
        blue_uses = []
        for line in default_nib["fan_lines"]:
            if line["color"] == "blue_glow":
                blue_uses.append("fan_line")
        for line in default_nib["outline_lines"]:
            if line["color"] == "blue_glow":
                blue_uses.append("outline_line")
        if default_nib["center_line"]["color"] == "blue_glow":
            blue_uses.append("center_line")
        for node in default_nib["accent_nodes"]:
            if node["color"] == "blue_glow":
                blue_uses.append("accent_node")
        if default_nib["junction_ball"]["color"] == "blue_glow":
            blue_uses.append("junction_ball")

        assert blue_uses == ["center_line"], (
            f"blue_glow should only appear in center_line, found in: {blue_uses}"
        )

    def test_warm_white_is_hottest_point(self, default_nib):
        """'Warm White: Tip of nib, highlight pulses. Hottest point.'
        Junction ball must be warm_white."""
        assert default_nib["junction_ball"]["color"] == "warm_white"
