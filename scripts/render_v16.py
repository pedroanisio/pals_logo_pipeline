#!/usr/bin/env python3
"""
Geometric Construction of the Letter 'P' — v16 technical drawing style.

Thin wrapper around p_logo library. Renders parchment background,
bronze rings, hatching, dimension arrows, D-shape closing bars.

Outputs to build/logos/.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from p_logo import build_schema
from p_logo.renderers.v16_technical import V16TechnicalRenderer

LOGOS_DIR = Path(__file__).parent.parent / "build" / "logos"


def main():
    parser = argparse.ArgumentParser(description="Geometric P v16 — technical drawing")
    parser.add_argument("-o", "--output", default=None,
                        help="Output path (default: build/logos/p_logo_v16_technical.png)")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    output = args.output or str(LOGOS_DIR / "p_logo_v16_technical.png")

    schema = build_schema()
    V16TechnicalRenderer(schema).render(output, dpi=args.dpi)

    print(f"√2 CHAIN (from R_GREEN = {schema.r_green:.4f}):")
    print(f"  Blue  = R_GREEN/√2 = {schema.r_blue:.4f}")
    print(f"  Green = R_GREEN    = {schema.r_green:.4f}")
    print(f"  Gold  = R_GREEN×√2 = {schema.r_gold:.4f}")
    print(f"  R_VERTEX = {schema.r_vertex:.4f}")
    print(f"\nGRAPH: {schema.node_count} nodes, {schema.edge_count} edges")
    print(f"ARCS: all π semicircles")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
