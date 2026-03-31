"""
PAL's Notes Logo Pipeline — Step 5: Animations — TEST SUITE (TDD)

Written BEFORE implementation.

Run:
    cd pals-logo-pipeline
    python -m pytest test_animations.py -v

Requires: palette.json, graph.json, arcs.json in build/

The animations step defines all 6 animation systems as pure data configs.
No rendering logic — just serializable parameter sets that step 6 (render)
will consume. From the design rationale:

  "The logo is not a static mark with motion added. The animation *is*
   the logo — without it, you see a wireframe P in a circle. With it,
   you see a living system."

The 6 systems:
  1. Wave propagation — BFS from random node, ~4s interval, elastic easing
  2. Traveling pulses — 12 particles along edges, fade in/out
  3. Arc runners — 6 particles (2 per arc), comet tails
  4. Breathing — ±0.8% scale, slow sinusoidal
  5. Energy rings — expand from center, ~4s interval
  6. Ink drops — 25 pooled, gravity + drag from nib tip
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
def arcs_data(build_dir) -> dict:
    path = build_dir / "arcs.json"
    assert path.exists(), "Run arcs.py first."
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def anim_module():
    sys.path.insert(0, str(Path(__file__).parent))
    import animations
    return animations


@pytest.fixture
def default_anims(anim_module, palette, graph_data, arcs_data):
    return anim_module.build_animations(palette, graph_data, arcs_data)


@pytest.fixture
def anims_json_path(anim_module, palette, graph_data, arcs_data) -> Path:
    return anim_module.write_animations(palette, graph_data, arcs_data)


# ──────────────────────────────────────────────
# 1. MODULE INTERFACE
# ──────────────────────────────────────────────

class TestModuleInterface:

    def test_has_build_animations(self, anim_module):
        assert callable(getattr(anim_module, "build_animations", None))

    def test_has_write_animations(self, anim_module):
        assert callable(getattr(anim_module, "write_animations", None))

    def test_has_validate(self, anim_module):
        assert callable(getattr(anim_module, "validate", None))


# ──────────────────────────────────────────────
# 2. OUTPUT SCHEMA
# ──────────────────────────────────────────────

class TestOutputSchema:

    def test_has_meta(self, default_anims):
        assert "_meta" in default_anims
        assert default_anims["_meta"]["step"] == 5
        assert default_anims["_meta"]["name"] == "animations"

    def test_has_all_six_systems(self, default_anims):
        """Design rationale defines exactly 6 animation systems."""
        required = {"wave", "pulses", "arc_runners", "breathing",
                    "energy_rings", "ink_drops"}
        actual = set(default_anims["systems"].keys())
        missing = required - actual
        assert not missing, f"Missing animation systems: {missing}"

    def test_no_extra_systems(self, default_anims):
        allowed = {"wave", "pulses", "arc_runners", "breathing",
                   "energy_rings", "ink_drops"}
        actual = set(default_anims["systems"].keys())
        extra = actual - allowed
        assert not extra, f"Unexpected animation systems: {extra}"

    def test_has_systems_key(self, default_anims):
        assert "systems" in default_anims
        assert isinstance(default_anims["systems"], dict)


# ──────────────────────────────────────────────
# 3. WAVE PROPAGATION
# ──────────────────────────────────────────────

class TestWave:
    """BFS wave from random node, ~4s interval, elastic easing."""

    def test_wave_has_required_params(self, default_anims):
        w = default_anims["systems"]["wave"]
        assert "interval" in w
        assert "delay_per_hop" in w
        assert "easing" in w
        assert "duration" in w
        assert "intensity" in w

    def test_interval_approximately_4s(self, default_anims):
        """'Every ~4 seconds, a wave triggers from a random node.'"""
        interval = default_anims["systems"]["wave"]["interval"]
        assert 3.0 <= interval <= 5.0, f"Wave interval {interval} not ~4s"

    def test_delay_per_hop(self, default_anims):
        """'Staggered delay (0.1s per hop).'"""
        delay = default_anims["systems"]["wave"]["delay_per_hop"]
        assert 0.05 <= delay <= 0.2, f"Hop delay {delay} outside expected range"

    def test_easing_is_elastic(self, default_anims):
        """'The falloff uses an elastic easing function.'"""
        easing = default_anims["systems"]["wave"]["easing"]
        assert "elastic" in easing.lower(), f"Easing '{easing}' is not elastic"

    def test_uses_bfs(self, default_anims):
        """'Propagates through the graph via breadth-first traversal.'"""
        w = default_anims["systems"]["wave"]
        assert "traversal" in w
        assert w["traversal"] == "bfs"

    def test_wave_has_adjacency(self, default_anims):
        """Wave system needs the adjacency list for BFS."""
        w = default_anims["systems"]["wave"]
        assert "adjacency" in w
        adj = w["adjacency"]
        assert isinstance(adj, dict)
        assert len(adj) == 25  # all nodes

    def test_wave_duration_positive(self, default_anims):
        w = default_anims["systems"]["wave"]
        assert w["duration"] > 0

    def test_wave_intensity_in_range(self, default_anims):
        w = default_anims["systems"]["wave"]
        assert 0 < w["intensity"] <= 1.0


# ──────────────────────────────────────────────
# 4. TRAVELING PULSES
# ──────────────────────────────────────────────

class TestPulses:
    """12 particles traveling along edges."""

    def test_pulses_has_required_params(self, default_anims):
        p = default_anims["systems"]["pulses"]
        assert "count" in p
        assert "speed_range" in p
        assert "fade_in" in p
        assert "fade_out" in p
        assert "color" in p

    def test_pulse_count_is_12(self, default_anims):
        """'12 small glowing particles travel along randomly selected edges.'"""
        assert default_anims["systems"]["pulses"]["count"] == 12

    def test_speed_range_valid(self, default_anims):
        sr = default_anims["systems"]["pulses"]["speed_range"]
        assert isinstance(sr, list) and len(sr) == 2
        assert sr[0] > 0
        assert sr[1] > sr[0]

    def test_fade_values_in_01(self, default_anims):
        p = default_anims["systems"]["pulses"]
        assert 0 < p["fade_in"] < 0.5
        assert 0.5 < p["fade_out"] < 1.0

    def test_has_edge_list_ref(self, default_anims):
        """Pulses need to know which edges exist."""
        p = default_anims["systems"]["pulses"]
        assert "edge_count" in p
        assert p["edge_count"] == 44

    def test_has_opacity_params(self, default_anims):
        p = default_anims["systems"]["pulses"]
        assert "core_peak_opacity" in p
        assert "glow_peak_opacity" in p
        assert 0 < p["core_peak_opacity"] <= 1.0
        assert 0 < p["glow_peak_opacity"] <= 1.0


# ──────────────────────────────────────────────
# 5. ARC RUNNERS
# ──────────────────────────────────────────────

class TestArcRunners:
    """6 particles (2 per arc) with comet tails."""

    def test_arc_runners_has_required_params(self, default_anims):
        ar = default_anims["systems"]["arc_runners"]
        assert "per_arc" in ar
        assert "speed" in ar
        assert "trail_length" in ar
        assert "arc_count" in ar

    def test_2_per_arc(self, default_anims):
        """'6 particles (2 per arc) travel along the bowl curves.'"""
        ar = default_anims["systems"]["arc_runners"]
        assert ar["per_arc"] == 2

    def test_3_arcs(self, default_anims):
        ar = default_anims["systems"]["arc_runners"]
        assert ar["arc_count"] == 3

    def test_total_is_6(self, default_anims):
        ar = default_anims["systems"]["arc_runners"]
        assert ar["per_arc"] * ar["arc_count"] == 6

    def test_speed_positive(self, default_anims):
        """'Their speed is constant (~0.08 units/s).'"""
        speed = default_anims["systems"]["arc_runners"]["speed"]
        assert 0.05 <= speed <= 0.15

    def test_trail_length_is_4(self, default_anims):
        """'Comet-like tails (4-sprite trail).'"""
        assert default_anims["systems"]["arc_runners"]["trail_length"] == 4

    def test_has_opacity_profile(self, default_anims):
        """'Opacity peaks at the midpoint of each arc.'"""
        ar = default_anims["systems"]["arc_runners"]
        assert "opacity_peak_at" in ar
        assert abs(ar["opacity_peak_at"] - 0.5) < 0.1


# ──────────────────────────────────────────────
# 6. BREATHING
# ──────────────────────────────────────────────

class TestBreathing:
    """Slow sinusoidal scale oscillation."""

    def test_breathing_has_required_params(self, default_anims):
        b = default_anims["systems"]["breathing"]
        assert "amplitude" in b
        assert "frequency" in b
        assert "waveform" in b

    def test_amplitude_is_0_008(self, default_anims):
        """'The entire P group scales subtly (±0.8%).'"""
        amp = default_anims["systems"]["breathing"]["amplitude"]
        assert abs(amp - 0.008) < 0.002

    def test_waveform_is_sinusoidal(self, default_anims):
        """'On a slow sinusoidal cycle.'"""
        wf = default_anims["systems"]["breathing"]["waveform"]
        assert wf == "sinusoidal"

    def test_frequency_is_slow(self, default_anims):
        """'If you notice the breathing, it's too strong.'
        Frequency should be well below 1 Hz."""
        freq = default_anims["systems"]["breathing"]["frequency"]
        assert 0.01 < freq < 0.5


# ──────────────────────────────────────────────
# 7. ENERGY RINGS
# ──────────────────────────────────────────────

class TestEnergyRings:
    """Expanding rings from center."""

    def test_energy_rings_has_required_params(self, default_anims):
        er = default_anims["systems"]["energy_rings"]
        assert "interval" in er
        assert "expansion_rate" in er
        assert "fade_duration" in er
        assert "initial_opacity" in er
        assert "initial_radius" in er

    def test_interval_approximately_4s(self, default_anims):
        """'A ring expands outward from the center every ~4 seconds.'"""
        interval = default_anims["systems"]["energy_rings"]["interval"]
        assert 3.0 <= interval <= 5.0

    def test_expansion_rate_positive(self, default_anims):
        er = default_anims["systems"]["energy_rings"]
        assert er["expansion_rate"] > 0

    def test_fade_duration_positive(self, default_anims):
        er = default_anims["systems"]["energy_rings"]
        assert er["fade_duration"] > 0

    def test_initial_opacity_from_palette(self, default_anims, palette):
        expected = palette["opacity_defaults"]["energy_ring"]["initial"]
        actual = default_anims["systems"]["energy_rings"]["initial_opacity"]
        assert abs(actual - expected) < 1e-6

    def test_initial_radius_from_palette(self, default_anims, palette):
        expected_inner = palette["sizing"]["energy_ring_inner"]
        expected_outer = palette["sizing"]["energy_ring_outer"]
        er = default_anims["systems"]["energy_rings"]
        assert "initial_inner_r" in er
        assert "initial_outer_r" in er
        assert abs(er["initial_inner_r"] - expected_inner) < 1e-6
        assert abs(er["initial_outer_r"] - expected_outer) < 1e-6


# ──────────────────────────────────────────────
# 8. INK DROPS
# ──────────────────────────────────────────────

class TestInkDrops:
    """Pooled particles with gravity and drag."""

    def test_ink_drops_has_required_params(self, default_anims):
        ink = default_anims["systems"]["ink_drops"]
        assert "pool_size" in ink
        assert "gravity" in ink
        assert "drag" in ink
        assert "spawn_rate" in ink
        assert "lifetime_range" in ink

    def test_pool_size_is_25(self, default_anims):
        """'25 (pooled)' from the technical inventory."""
        assert default_anims["systems"]["ink_drops"]["pool_size"] == 25

    def test_gravity_is_negative(self, default_anims):
        """Gravity pulls drops downward (negative Y direction)."""
        g = default_anims["systems"]["ink_drops"]["gravity"]
        assert g < 0

    def test_drag_in_01(self, default_anims):
        """Drag coefficient should be in (0, 1) for damping."""
        drag = default_anims["systems"]["ink_drops"]["drag"]
        assert 0 < drag < 1.0

    def test_spawn_rate_has_min_max(self, default_anims):
        sr = default_anims["systems"]["ink_drops"]["spawn_rate"]
        assert isinstance(sr, dict)
        assert "min_interval" in sr
        assert "max_interval" in sr
        assert sr["min_interval"] > 0
        assert sr["max_interval"] > sr["min_interval"]

    def test_lifetime_range_valid(self, default_anims):
        lr = default_anims["systems"]["ink_drops"]["lifetime_range"]
        assert isinstance(lr, list) and len(lr) == 2
        assert lr[0] > 0
        assert lr[1] > lr[0]

    def test_has_velocity_params(self, default_anims):
        ink = default_anims["systems"]["ink_drops"]
        assert "initial_vx_range" in ink
        assert "initial_vy_range" in ink

    def test_has_fade_profile(self, default_anims):
        """'They fade in quickly and fade out slowly.'"""
        ink = default_anims["systems"]["ink_drops"]
        assert "fade_in_fraction" in ink
        assert "fade_out_fraction" in ink
        assert ink["fade_in_fraction"] < ink["fade_out_fraction"]

    def test_has_color(self, default_anims):
        ink = default_anims["systems"]["ink_drops"]
        assert "color" in ink

    def test_has_radius(self, default_anims):
        ink = default_anims["systems"]["ink_drops"]
        assert "radius" in ink
        assert ink["radius"] > 0


# ──────────────────────────────────────────────
# 9. PALETTE DEPENDENCY
# ──────────────────────────────────────────────

class TestPaletteDependency:

    def test_pulse_opacities_from_palette(self, default_anims, palette):
        p = default_anims["systems"]["pulses"]
        po = palette["opacity_defaults"]["pulse"]
        assert abs(p["core_peak_opacity"] - po["core_peak"]) < 1e-6
        assert abs(p["glow_peak_opacity"] - po["glow_peak"]) < 1e-6

    def test_arc_runner_opacities_from_palette(self, default_anims, palette):
        ar = default_anims["systems"]["arc_runners"]
        aro = palette["opacity_defaults"]["arc_runner"]
        assert abs(ar["core_peak_opacity"] - aro["core_peak"]) < 1e-6
        assert abs(ar["trail_peak_opacity"] - aro["trail_peak"]) < 1e-6

    def test_ink_drop_radius_from_palette(self, default_anims, palette):
        ink = default_anims["systems"]["ink_drops"]
        expected = palette["sizing"]["ink_drop_radius"]
        assert abs(ink["radius"] - expected) < 1e-6

    def test_ink_drop_opacity_from_palette(self, default_anims, palette):
        ink = default_anims["systems"]["ink_drops"]
        expected = palette["opacity_defaults"]["ink_drop"]["peak"]
        assert abs(ink["peak_opacity"] - expected) < 1e-6

    def test_pulse_radius_from_palette(self, default_anims, palette):
        p = default_anims["systems"]["pulses"]
        assert abs(p["radius"] - palette["sizing"]["pulse_radius"]) < 1e-6

    def test_pulse_glow_size_from_palette(self, default_anims, palette):
        p = default_anims["systems"]["pulses"]
        assert abs(p["glow_size"] - palette["sizing"]["pulse_glow_size"]) < 1e-6


# ──────────────────────────────────────────────
# 10. NO RENDERING LOGIC
# ──────────────────────────────────────────────

class TestNoRenderingLogic:
    """The animations output must be pure data — no code, no functions."""

    def test_json_serializable(self, default_anims):
        """Must be fully JSON-serializable (no functions, no objects)."""
        serialized = json.dumps(default_anims)
        roundtripped = json.loads(serialized)
        assert roundtripped == default_anims

    def test_no_callable_values(self, default_anims):
        """Walk the entire structure — no value should be callable."""
        def walk(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")
            else:
                assert not callable(obj), f"Callable at {path}"
        walk(default_anims)


# ──────────────────────────────────────────────
# 11. GRAPH DEPENDENCY
# ──────────────────────────────────────────────

class TestGraphDependency:
    """Wave system must carry graph topology for BFS."""

    def test_adjacency_matches_graph(self, default_anims, graph_data):
        wave_adj = default_anims["systems"]["wave"]["adjacency"]
        graph_adj = graph_data["adjacency"]
        assert set(wave_adj.keys()) == set(graph_adj.keys())
        for k in wave_adj:
            assert sorted(wave_adj[k]) == sorted(graph_adj[k])

    def test_node_count_in_wave(self, default_anims):
        w = default_anims["systems"]["wave"]
        assert "node_count" in w
        assert w["node_count"] == 25


# ──────────────────────────────────────────────
# 12. ARCS DEPENDENCY
# ──────────────────────────────────────────────

class TestArcsDependency:

    def test_arc_count_matches(self, default_anims, arcs_data):
        ar = default_anims["systems"]["arc_runners"]
        assert ar["arc_count"] == len(arcs_data["arcs"])


# ──────────────────────────────────────────────
# 13. VALIDATION
# ──────────────────────────────────────────────

class TestValidation:

    def test_validate_passes_default(self, anim_module, palette,
                                     graph_data, arcs_data):
        errors = anim_module.validate(palette, graph_data, arcs_data)
        assert errors == []


# ──────────────────────────────────────────────
# 14. JSON FILE OUTPUT
# ──────────────────────────────────────────────

class TestJsonOutput:

    def test_file_is_created(self, anims_json_path):
        assert anims_json_path.exists()
        assert anims_json_path.name == "animations.json"

    def test_file_is_valid_json(self, anims_json_path):
        with open(anims_json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_in_build_directory(self, anims_json_path):
        assert anims_json_path.parent.name == "build"

    def test_file_roundtrips(self, anims_json_path, default_anims):
        with open(anims_json_path) as f:
            from_file = json.load(f)
        assert set(from_file["systems"].keys()) == set(default_anims["systems"].keys())
        for name in default_anims["systems"]:
            assert from_file["systems"][name] == default_anims["systems"][name]


# ──────────────────────────────────────────────
# 15. DESIGN RATIONALE COMPLIANCE
# ──────────────────────────────────────────────

class TestDesignRationale:

    def test_animation_is_the_logo(self, default_anims):
        """'The animation *is* the logo.' — All 6 systems must exist."""
        assert len(default_anims["systems"]) == 6

    def test_wave_is_bfs_not_random(self, default_anims):
        """'The BFS traversal is not accidental; it's the actual algorithm
        you'd use to model information diffusion in a network.'"""
        assert default_anims["systems"]["wave"]["traversal"] == "bfs"

    def test_pulses_are_granular(self, default_anims):
        """'These are faster and more granular than the waves.'
        Pulse speed range min should be > 0.1."""
        sr = default_anims["systems"]["pulses"]["speed_range"]
        assert sr[0] >= 0.1

    def test_breathing_is_imperceptible(self, default_anims):
        """'If you notice the breathing, it's too strong.'
        Amplitude must be ≤ 1%."""
        amp = default_anims["systems"]["breathing"]["amplitude"]
        assert amp <= 0.01

    def test_ink_physics_intentionally_imprecise(self, default_anims):
        """'The physics are intentionally imprecise — this is suggestion,
        not simulation.' — Gravity should be approximate, not 9.81."""
        g = abs(default_anims["systems"]["ink_drops"]["gravity"])
        assert g != 9.81, "Gravity should be approximate, not physical"
        assert g > 0.5, "But gravity must be noticeable"

    def test_energy_rings_connect_p_to_boundary(self, default_anims):
        """'It connects the P (foreground) to the circle boundary (edge).'
        Expansion rate × fade_duration should produce visible growth."""
        er = default_anims["systems"]["energy_rings"]
        max_scale = er["expansion_rate"] * er["fade_duration"]
        assert max_scale >= 2.0, (
            f"Ring only expands {max_scale}× — too small to reach boundary"
        )

    def test_arc_runners_emphasize_paths(self, default_anims):
        """'These emphasize the arcs as paths, not just shapes.
        The P's bowl is not a wall; it's a route.' — Speed must be > 0."""
        assert default_anims["systems"]["arc_runners"]["speed"] > 0
