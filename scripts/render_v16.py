#!/usr/bin/env python3
"""
Geometric Construction of the Letter 'P' — v16 technical drawing style.

Thin wrapper around p_logo library. Renders parchment background,
bronze rings, hatching, dimension arrows, D-shape closing bars.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
from p_logo import build_schema
from p_logo.renderers.v16_technical import V16TechnicalRenderer


def main():
    parser = argparse.ArgumentParser(description="Geometric P v16 — technical drawing")
    parser.add_argument("-o", "--output", default="geometric_p_v16.png")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    schema = build_schema()
    V16TechnicalRenderer(schema).render(args.output, dpi=args.dpi)

    print(f"√2 CHAIN (from R_GREEN = {schema.r_green:.4f}):")
    print(f"  Blue  = R_GREEN/√2 = {schema.r_blue:.4f}")
    print(f"  Green = R_GREEN    = {schema.r_green:.4f}")
    print(f"  Gold  = R_GREEN×√2 = {schema.r_gold:.4f}")
    print(f"  R_VERTEX = {schema.r_vertex:.4f}")
    print(f"\nGRAPH: {schema.node_count} nodes, {schema.edge_count} edges")
    print(f"ARCS: all π semicircles")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
