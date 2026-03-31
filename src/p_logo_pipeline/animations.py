"""
PAL's Notes Logo Pipeline — Step 5: Animations

Defines all 6 animation systems as serializable parameter configs.
No rendering logic — pure specification consumed by step 6 (render).

Input:  build/palette.json, build/graph.json, build/arcs.json
Output: build/animations.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# System builders
# ──────────────────────────────────────────────

def _build_wave(palette: dict, graph: dict) -> dict[str, Any]:
    """Wave propagation — BFS from random node.

    From the rationale:
      'Every ~4 seconds, a wave triggers from a random node and propagates
       through the graph via breadth-first traversal. Each node brightens
       and scales up, then the signal passes to its neighbors with a
       staggered delay (0.1s per hop). The falloff uses an elastic easing
       function.'
    """
    return {
        "interval": 4.0,
        "delay_per_hop": 0.1,
        "easing": "elastic",
        "duration": 0.8,
        "intensity": 0.5,
        "traversal": "bfs",
        "node_count": len(graph["nodes"]),
        "adjacency": graph["adjacency"],
    }


def _build_pulses(palette: dict, graph: dict) -> dict[str, Any]:
    """Traveling pulses — 12 particles along edges.

    From the rationale:
      '12 small glowing particles travel along randomly selected edges,
       fading in and out as they traverse.'
    """
    po = palette["opacity_defaults"]["pulse"]
    return {
        "count": 12,
        "speed_range": [0.12, 0.30],
        "fade_in": 0.15,
        "fade_out": 0.85,
        "color": "copper",
        "edge_count": len(graph["edges"]),
        "core_peak_opacity": po["core_peak"],
        "glow_peak_opacity": po["glow_peak"],
        "radius": palette["sizing"]["pulse_radius"],
        "glow_size": palette["sizing"]["pulse_glow_size"],
    }


def _build_arc_runners(palette: dict, arcs: dict) -> dict[str, Any]:
    """Arc runners — 6 particles (2 per arc) with comet tails.

    From the rationale:
      '6 particles (2 per arc) travel along the bowl curves with
       comet-like tails (4-sprite trail). Their speed is constant
       (~0.08 units/s) and their opacity peaks at the midpoint
       of each arc.'
    """
    aro = palette["opacity_defaults"]["arc_runner"]
    return {
        "per_arc": 2,
        "arc_count": len(arcs["arcs"]),
        "speed": 0.08,
        "trail_length": 4,
        "opacity_peak_at": 0.5,
        "core_peak_opacity": aro["core_peak"],
        "trail_peak_opacity": aro["trail_peak"],
    }


def _build_breathing() -> dict[str, Any]:
    """Breathing — subtle sinusoidal scale oscillation.

    From the rationale:
      'The entire P group scales subtly (±0.8%) on a slow sinusoidal cycle.
       This is purely perceptual — it makes the logo feel alive without
       drawing attention to any specific element. If you notice the
       breathing, it's too strong.'
    """
    return {
        "amplitude": 0.008,
        "frequency": 0.4 / (2 * 3.14159265),  # maps to ~0.4 rad/s ≈ 0.064 Hz
        "waveform": "sinusoidal",
    }


def _build_energy_rings(palette: dict) -> dict[str, Any]:
    """Energy rings — expanding from center, fading out.

    From the rationale:
      'A ring expands outward from the center every ~4 seconds,
       scaling up and fading. This is the simplest animation and
       serves a compositional purpose: it connects the P (foreground)
       to the circle boundary (edge).'
    """
    return {
        "interval": 4.0,
        "expansion_rate": 3.0,
        "fade_duration": 2.5,
        "initial_opacity": palette["opacity_defaults"]["energy_ring"]["initial"],
        "initial_radius": palette["sizing"]["energy_ring_inner"],
        "initial_inner_r": palette["sizing"]["energy_ring_inner"],
        "initial_outer_r": palette["sizing"]["energy_ring_outer"],
        "color": "copper",
    }


def _build_ink_drops(palette: dict) -> dict[str, Any]:
    """Ink drops — pooled particles with gravity and drag.

    From the rationale:
      'Particles emit from the nib tip with randomized velocity vectors,
       subject to simulated gravity and drag. They fade in quickly and
       fade out slowly. The physics are intentionally imprecise — this
       is suggestion, not simulation.'
    """
    return {
        "pool_size": 25,
        "gravity": -1.2,
        "drag": 0.97,
        "spawn_rate": {
            "min_interval": 0.25,
            "max_interval": 0.75,
        },
        "lifetime_range": [1.0, 2.2],
        "initial_vx_range": [-0.2, 0.2],
        "initial_vy_range": [-1.0, -0.4],
        "fade_in_fraction": 0.1,
        "fade_out_fraction": 0.9,
        "peak_opacity": palette["opacity_defaults"]["ink_drop"]["peak"],
        "color": "rose_gold",
        "radius": palette["sizing"]["ink_drop_radius"],
    }


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate(
    palette: dict, graph: dict, arcs: dict
) -> list[str]:
    errors: list[str] = []

    if graph.get("_meta", {}).get("step") != 1:
        errors.append("graph._meta.step != 1")
    if arcs.get("_meta", {}).get("step") != 3:
        errors.append("arcs._meta.step != 3")

    if "adjacency" not in graph:
        errors.append("graph missing 'adjacency'")
    if "edges" not in graph:
        errors.append("graph missing 'edges'")
    if "arcs" not in arcs:
        errors.append("arcs missing 'arcs'")

    # Palette keys
    required_opacity_keys = {"pulse", "arc_runner", "ink_drop", "energy_ring"}
    for k in required_opacity_keys:
        if k not in palette.get("opacity_defaults", {}):
            errors.append(f"palette missing opacity_defaults.{k}")

    required_sizing_keys = {
        "pulse_radius", "pulse_glow_size", "ink_drop_radius",
        "energy_ring_inner", "energy_ring_outer",
    }
    for k in required_sizing_keys:
        if k not in palette.get("sizing", {}):
            errors.append(f"palette missing sizing.{k}")

    return errors


# ──────────────────────────────────────────────
# Main builder
# ──────────────────────────────────────────────

def build_animations(
    palette: dict, graph: dict, arcs: dict
) -> dict[str, Any]:
    return {
        "_meta": {
            "step": 5,
            "name": "animations",
            "description": "Six animation system configs — wave, pulses, "
                           "arc runners, breathing, energy rings, ink drops. "
                           "Plus supplementary visual configs for particles and shimmer.",
            "version": "1.1",
        },
        "systems": {
            "wave": _build_wave(palette, graph),
            "pulses": _build_pulses(palette, graph),
            "arc_runners": _build_arc_runners(palette, arcs),
            "breathing": _build_breathing(),
            "energy_rings": _build_energy_rings(palette),
            "ink_drops": _build_ink_drops(palette),
        },
        "supplementary": {
            "particles": {
                "count": palette["particles"]["count"],
                "size_range": [
                    palette["particles"]["size_range"]["min"],
                    palette["particles"]["size_range"]["max"],
                ],
                "opacity_range": [
                    palette["particles"]["opacity_range"]["min"],
                    palette["particles"]["opacity_range"]["max"],
                ],
                "drift_amplitude": [
                    palette["particles"]["drift_amplitude"]["min"],
                    palette["particles"]["drift_amplitude"]["max"],
                ],
                "drift_speed": [
                    palette["particles"]["drift_speed"]["min"],
                    palette["particles"]["drift_speed"]["max"],
                ],
                "min_distance": palette["particles"]["min_distance"],
                "max_distance": palette["particles"]["max_distance"],
                "color": palette["particles"]["color"],
                "description": "Ambient floating particles. Not one of the 6 animation "
                               "systems — these are ambient decoration with sinusoidal drift.",
            },
            "shimmer": {
                "count": palette["shimmer"]["count"],
                "color": palette["shimmer"]["color"],
                "base_opacity": palette["shimmer"]["base_opacity"],
                "opacity_amplitude": palette["shimmer"]["opacity_amplitude"],
                "rotation_speed": palette["shimmer"]["rotation_speed"],
                "arc_sweep_fraction": palette["shimmer"]["arc_sweep"],
                "description": "Rotating arc segments on the ring. Not one of the 6 "
                               "animation systems — subtle luminosity variation.",
            },
        },
    }


# ──────────────────────────────────────────────
# File writer
# ──────────────────────────────────────────────

def write_animations(
    palette: dict, graph: dict, arcs: dict
) -> Path:
    data = build_animations(palette, graph, arcs)
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "animations.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> int:
    build_dir = Path(__file__).parent / "build"
    deps = {}
    for name in ("palette.json", "graph.json", "arcs.json"):
        path = build_dir / name
        if not path.exists():
            print(f"ERROR: {path} not found.", file=sys.stderr)
            return 1
        with open(path) as f:
            deps[name] = json.load(f)

    palette = deps["palette.json"]
    graph = deps["graph.json"]
    arcs = deps["arcs.json"]

    errors = validate(palette, graph, arcs)
    if errors:
        print("ANIMATIONS VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    out_path = write_animations(palette, graph, arcs)

    with open(out_path) as f:
        data = json.load(f)

    print(f"animations.json written to {out_path}")
    for name, system in data["systems"].items():
        keys = [k for k in system.keys() if k != "adjacency"]
        print(f"  {name:14s}  {len(system)} params  [{', '.join(keys[:5])}{'...' if len(keys) > 5 else ''}]")
    for name, supp in data.get("supplementary", {}).items():
        print(f"  {name:14s}  {len(supp)} params  (supplementary)")
    print("  Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
