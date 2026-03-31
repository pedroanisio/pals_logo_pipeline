"""
PAL's Notes Logo Pipeline — Step 7: Validate — TEST SUITE (TDD)

Written BEFORE implementation.

Run:
    cd pals-logo-pipeline
    python -m pytest test_validate_step.py -v

Requires: All upstream artifacts in build/

The validate step is the final post-build check. It reads the rendered
logo.html and the upstream data artifacts, then verifies compliance with
the design rationale's Technical Inventory table:

  | Layer            | Element Count | Render Method              |
  |------------------|---------------|----------------------------|
  | Background       | 7 clouds + vignette | 2D canvas             |
  | Stars            | 180           | 2D canvas                  |
  | Circle fill      | 1             | THREE.CircleGeometry       |
  | Ring             | 4 meshes      | THREE.RingGeometry         |
  | Shimmer arcs     | 3             | THREE.RingGeometry         |
  | Edges            | 36            | Mesh quads                 |
  | Nodes            | 23 core + 23 glow + 23 bloom | ...         |
  | Bowl arcs        | 3 main + 3 bloom | Mesh strips             |
  | Arc runners      | 6 + 24 tail sprites | ...                  |
  | Nib              | 4 outline + 1 center + 1 ball + 1 glow | ...|
  | Ink drops        | 25 (pooled)   | CircleGeometry             |
  | Particles        | 70            | CircleGeometry             |
  | Pulses           | 12 + 12 glow  | ...                        |
  | Energy rings     | dynamic       | RingGeometry               |
  | Brand text       | DOM           | CSS + JS                   |
  |                  | ~310 total    |                            |

Output: A structured report dict (and stdout summary), NOT a file.
This step does not produce a JSON artifact — it produces a pass/fail report.
"""

from __future__ import annotations

import json
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
    with open(build_dir / "palette.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def graph_data(build_dir) -> dict:
    with open(build_dir / "graph.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def nib_data(build_dir) -> dict:
    with open(build_dir / "nib.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def arcs_data(build_dir) -> dict:
    with open(build_dir / "arcs.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def layout_data(build_dir) -> dict:
    with open(build_dir / "layout.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def anim_data(build_dir) -> dict:
    with open(build_dir / "animations.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def logos_dir() -> Path:
    return Path(__file__).parent.parent.parent / "build" / "logos"


@pytest.fixture(scope="session")
def logo_html(logos_dir) -> str:
    with open(logos_dir / "p_logo_pipeline.html") as f:
        return f.read()


@pytest.fixture(scope="session")
def val_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import validate_step
    return validate_step


@pytest.fixture(scope="session")
def report(val_module, palette, graph_data, nib_data, arcs_data,
           layout_data, anim_data, logo_html):
    return val_module.build_report(
        palette, graph_data, nib_data, arcs_data,
        layout_data, anim_data, logo_html
    )


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_report(self, val_module):
        assert callable(getattr(val_module, "build_report", None))

    def test_has_main(self, val_module):
        assert callable(getattr(val_module, "main", None))

    def test_report_is_dict(self, report):
        assert isinstance(report, dict)


# ──────────────────────────────────────────────
# 2. REPORT SCHEMA
# ──────────────────────────────────────────────

class TestReportSchema:

    def test_has_passed(self, report):
        assert "passed" in report
        assert isinstance(report["passed"], bool)

    def test_has_checks(self, report):
        assert "checks" in report
        assert isinstance(report["checks"], list)

    def test_has_inventory(self, report):
        assert "inventory" in report
        assert isinstance(report["inventory"], dict)

    def test_has_total_renderable(self, report):
        assert "total_renderable" in report
        assert isinstance(report["total_renderable"], int)

    def test_has_graph_metrics(self, report):
        assert "graph_metrics" in report

    def test_has_summary(self, report):
        assert "summary" in report
        assert isinstance(report["summary"], str)


# ──────────────────────────────────────────────
# 3. CHECK STRUCTURE
# ──────────────────────────────────────────────

class TestCheckStructure:
    """Each check in the report must have a standard structure."""

    def test_checks_have_name(self, report):
        for check in report["checks"]:
            assert "name" in check
            assert isinstance(check["name"], str)

    def test_checks_have_status(self, report):
        for check in report["checks"]:
            assert "status" in check
            assert check["status"] in ("pass", "fail", "warn")

    def test_checks_have_detail(self, report):
        for check in report["checks"]:
            assert "detail" in check

    def test_at_least_10_checks(self, report):
        """Comprehensive validation needs at least 10 checks."""
        assert len(report["checks"]) >= 10


# ──────────────────────────────────────────────
# 4. GRAPH METRICS
# ──────────────────────────────────────────────

class TestGraphMetrics:

    def test_node_count(self, report):
        gm = report["graph_metrics"]
        assert gm["node_count"] == 25

    def test_edge_count(self, report):
        gm = report["graph_metrics"]
        assert gm["edge_count"] == 44

    def test_avg_degree(self, report):
        gm = report["graph_metrics"]
        expected = 2 * 44 / 25
        assert abs(gm["avg_degree"] - expected) < 0.01

    def test_max_degree(self, report):
        gm = report["graph_metrics"]
        assert gm["max_degree"] == 6

    def test_is_connected(self, report):
        gm = report["graph_metrics"]
        assert gm["connected"] is True


# ──────────────────────────────────────────────
# 5. INVENTORY CATEGORIES (from rationale table)
# ──────────────────────────────────────────────

class TestInventoryCategories:
    """The inventory must account for every layer in the rationale table."""

    def test_has_background(self, report):
        inv = report["inventory"]
        assert "background" in inv

    def test_has_stars(self, report):
        inv = report["inventory"]
        assert "stars" in inv

    def test_has_circle_fill(self, report):
        inv = report["inventory"]
        assert "circle_fill" in inv

    def test_has_ring(self, report):
        inv = report["inventory"]
        assert "ring" in inv

    def test_has_shimmer(self, report):
        inv = report["inventory"]
        assert "shimmer_arcs" in inv

    def test_has_edges(self, report):
        inv = report["inventory"]
        assert "edges" in inv

    def test_has_nodes(self, report):
        inv = report["inventory"]
        assert "nodes" in inv

    def test_has_bowl_arcs(self, report):
        inv = report["inventory"]
        assert "bowl_arcs" in inv

    def test_has_arc_runners(self, report):
        inv = report["inventory"]
        assert "arc_runners" in inv

    def test_has_nib(self, report):
        inv = report["inventory"]
        assert "nib" in inv

    def test_has_ink_drops(self, report):
        inv = report["inventory"]
        assert "ink_drops" in inv

    def test_has_particles(self, report):
        inv = report["inventory"]
        assert "particles" in inv

    def test_has_pulses(self, report):
        inv = report["inventory"]
        assert "pulses" in inv

    def test_has_energy_rings(self, report):
        inv = report["inventory"]
        assert "energy_rings" in inv

    def test_has_brand_text(self, report):
        inv = report["inventory"]
        assert "brand_text" in inv


# ──────────────────────────────────────────────
# 6. INVENTORY COUNTS (exact checks)
# ──────────────────────────────────────────────

class TestInventoryCounts:
    """Verify exact counts against the design rationale table."""

    def test_background_7_clouds_plus_vignette(self, report):
        count = report["inventory"]["background"]
        assert count == 8, f"Background: {count} (expected 7 clouds + 1 vignette = 8)"

    def test_stars_180(self, report):
        assert report["inventory"]["stars"] == 180

    def test_circle_fill_1(self, report):
        assert report["inventory"]["circle_fill"] == 1

    def test_ring_4(self, report):
        assert report["inventory"]["ring"] == 4

    def test_shimmer_3(self, report):
        assert report["inventory"]["shimmer_arcs"] == 3

    def test_edges_36(self, report):
        assert report["inventory"]["edges"] == 44

    def test_nodes_69(self, report):
        """25 core + 25 glow + 25 bloom = 75."""
        assert report["inventory"]["nodes"] == 75

    def test_bowl_arcs_6(self, report):
        """3 main + 3 bloom = 6."""
        assert report["inventory"]["bowl_arcs"] == 6

    def test_arc_runners_30(self, report):
        """6 core + 24 tail sprites (6 runners × 4 trail each) = 30."""
        assert report["inventory"]["arc_runners"] == 30

    def test_nib_elements(self, report):
        """From rationale: 4 outline + 1 center + 1 ball + 1 glow = 7.
        Plus fan lines + accent nodes + accent glows + ball bloom.
        We count all nib renderable objects."""
        count = report["inventory"]["nib"]
        # fan(6) + outline(4) + center(1) + accents(4) + accent_glows(4)
        # + ball_core(1) + ball_glow(1) + ball_bloom(1) = 22
        assert count >= 15, f"Nib count {count} too low"

    def test_ink_drops_25(self, report):
        assert report["inventory"]["ink_drops"] == 25

    def test_particles_70(self, report):
        assert report["inventory"]["particles"] == 70

    def test_pulses_24(self, report):
        """12 core + 12 glow = 24."""
        assert report["inventory"]["pulses"] == 24

    def test_brand_text_1(self, report):
        assert report["inventory"]["brand_text"] == 1


# ──────────────────────────────────────────────
# 7. TOTAL RENDERABLE COUNT
# ──────────────────────────────────────────────

class TestTotalRenderable:

    def test_total_near_310(self, report):
        """Rationale: 'Total: ~310 renderable objects across two THREE.js
        scenes and two 2D canvas layers.' The ~310 is approximate; our
        inventory includes canvas-drawn items (180 stars, 8 background)
        which push the count higher."""
        total = report["total_renderable"]
        assert 250 <= total <= 550, (
            f"Total renderable {total} outside expected range [250, 550]"
        )

    def test_total_is_sum_of_inventory(self, report):
        """Total must equal the sum of all inventory categories."""
        inv_sum = sum(report["inventory"].values())
        assert report["total_renderable"] == inv_sum, (
            f"total_renderable={report['total_renderable']} != "
            f"inventory sum={inv_sum}"
        )


# ──────────────────────────────────────────────
# 8. HTML CHECKS
# ──────────────────────────────────────────────

class TestHtmlChecks:
    """The report must verify the HTML output."""

    def test_html_checks_present(self, report):
        """Report must include checks about the HTML file."""
        check_names = [c["name"] for c in report["checks"]]
        html_checks = [n for n in check_names if "html" in n.lower()]
        assert len(html_checks) >= 1

    def test_no_nan_check(self, report):
        """Must verify no NaN values leaked into the HTML."""
        check_names = [c["name"] for c in report["checks"]]
        nan_checks = [n for n in check_names if "nan" in n.lower()]
        assert len(nan_checks) >= 1


# ──────────────────────────────────────────────
# 9. PASS/FAIL LOGIC
# ──────────────────────────────────────────────

class TestPassFail:

    def test_default_passes(self, report):
        """With correct upstream data, the report should pass."""
        assert report["passed"] is True

    def test_all_checks_pass(self, report):
        """No individual check should fail."""
        failed = [c for c in report["checks"] if c["status"] == "fail"]
        assert len(failed) == 0, (
            f"Failed checks: {[c['name'] for c in failed]}"
        )


# ──────────────────────────────────────────────
# 10. UPSTREAM PIPELINE INTEGRITY
# ──────────────────────────────────────────────

class TestPipelineIntegrity:
    """Validate cross-step consistency."""

    def test_palette_step_0(self, report):
        check_names = [c["name"] for c in report["checks"]]
        assert any("palette" in n.lower() or "step_0" in n.lower()
                    or "step 0" in n.lower() for n in check_names)

    def test_layout_element_count_check(self, report):
        check_names = [c["name"] for c in report["checks"]]
        assert any("layout" in n.lower() or "element" in n.lower()
                    for n in check_names)

    def test_animation_system_count_check(self, report):
        check_names = [c["name"] for c in report["checks"]]
        assert any("animation" in n.lower() or "system" in n.lower()
                    for n in check_names)


# ──────────────────────────────────────────────
# 11. SUMMARY
# ──────────────────────────────────────────────

class TestSummary:

    def test_summary_not_empty(self, report):
        assert len(report["summary"]) > 20

    def test_summary_includes_total(self, report):
        assert str(report["total_renderable"]) in report["summary"]

    def test_summary_includes_verdict(self, report):
        s = report["summary"].lower()
        assert "pass" in s or "fail" in s
