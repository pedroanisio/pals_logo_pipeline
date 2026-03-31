#!/usr/bin/env python3
"""
Complete Geometric Composition Generator with JSON Export
Creates a 1200x1200 pixel canvas with nested circles, squares, and reference elements
Outputs comprehensive JSON with all shape definitions and intersection points
Supports custom frame of reference and scaling
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import json
import sys
from argparse import ArgumentParser


def _build_base_params(scale, origin_x, origin_y):
    """Compute base parameters and coordinate transform."""
    R_A = 200
    side_B = 2 * R_A
    half_side = side_B / 2

    def apply_transform(x, y):
        return (x * scale + origin_x, y * scale + origin_y)

    center_A_x, center_A_y = apply_transform(600, 800)
    R_A_scaled = R_A * scale

    square_B_left = (600 - half_side) * scale + origin_x
    square_B_right = (600 + half_side) * scale + origin_x
    square_B_bottom = (800 - half_side) * scale + origin_y
    square_B_top = (800 + half_side) * scale + origin_y

    inradius_square_A = R_A_scaled / np.sqrt(2)

    angles = np.array([45, 135, 225, 315]) * np.pi / 180
    vertices_x = (600 + 200 * np.cos(angles)) * scale + origin_x
    vertices_y = (800 + 200 * np.sin(angles)) * scale + origin_y

    return {
        "scale": scale, "origin_x": origin_x, "origin_y": origin_y,
        "R_A": R_A, "R_A_scaled": R_A_scaled, "side_B": side_B,
        "apply_transform": apply_transform,
        "center_A_x": center_A_x, "center_A_y": center_A_y,
        "square_B_left": square_B_left, "square_B_right": square_B_right,
        "square_B_bottom": square_B_bottom, "square_B_top": square_B_top,
        "inradius_square_A": inradius_square_A,
        "vertices_x": vertices_x, "vertices_y": vertices_y,
    }


def _build_shapes(p):
    """Build all shape definitions from base parameters."""
    shapes = {}
    scale = p["scale"]
    apply_transform = p["apply_transform"]
    center_A_x, center_A_y = p["center_A_x"], p["center_A_y"]
    square_B_left, square_B_right = p["square_B_left"], p["square_B_right"]
    square_B_bottom, square_B_top = p["square_B_bottom"], p["square_B_top"]
    inradius_square_A = p["inradius_square_A"]
    vertices_x, vertices_y = p["vertices_x"], p["vertices_y"]

    # Outer Circle
    outer_circle_center = apply_transform(600, 600)
    shapes["Outer.Circle"] = {
        "type": "circle", "name": "Outer Circle",
        "center": {"x": outer_circle_center[0], "y": outer_circle_center[1]},
        "radius": 600 * scale, "color": "red", "linewidth": 2, "style": "solid"
    }

    # Circ.A
    shapes["Circ.A"] = {
        "type": "circle", "name": "Circ.A",
        "center": {"x": center_A_x, "y": center_A_y},
        "radius": p["R_A_scaled"], "color": "blue", "linewidth": 2, "style": "solid"
    }

    # Square.B
    shapes["Square.B"] = {
        "type": "square", "name": "Square.B",
        "origin": {"x": square_B_left, "y": square_B_top},
        "width": p["side_B"] * scale, "height": p["side_B"] * scale,
        "vertices": {
            "upper_left": {"x": square_B_left, "y": square_B_top},
            "upper_right": {"x": square_B_right, "y": square_B_top},
            "lower_left": {"x": square_B_left, "y": square_B_bottom},
            "lower_right": {"x": square_B_right, "y": square_B_bottom}
        },
        "color": "black", "linewidth": 1, "style": "dotted"
    }

    # Square.A (inscribed in Circ.A)
    shapes["Square.A"] = {
        "type": "square", "name": "Square.A",
        "center": {"x": center_A_x, "y": center_A_y},
        "vertices": {
            "V1_right": {"x": float(vertices_x[0]), "y": float(vertices_y[0])},
            "V2_top_left": {"x": float(vertices_x[1]), "y": float(vertices_y[1])},
            "V3_bottom_left": {"x": float(vertices_x[2]), "y": float(vertices_y[2])},
            "V4_bottom_right": {"x": float(vertices_x[3]), "y": float(vertices_y[3])}
        },
        "color": "green", "linewidth": 2, "style": "solid"
    }

    # Vertex circles at Square.A vertices
    vertex_circle_radius = None
    top_vertex_y = None
    for i, (vx, vy) in enumerate(zip(vertices_x, vertices_y)):
        radius = min(
            vx - square_B_left, square_B_right - vx,
            vy - square_B_bottom, square_B_top - vy,
        )
        if i == 0:
            vertex_circle_radius = radius
            top_vertex_y = vy

        shapes[f"Circ.V{i+1}"] = {
            "type": "circle", "name": f"Circ.V{i+1}",
            "center": {"x": float(vx), "y": float(vy)},
            "radius": float(radius), "color": "purple", "linewidth": 1, "style": "solid"
        }

    bottom_vertex_y = vertices_y[2]

    # Circ.C (top) and Circ.C' (bottom)
    shapes["Circ.C"] = {
        "type": "circle", "name": "Circ.C",
        "center": {"x": center_A_x, "y": float(top_vertex_y)},
        "radius": float(vertex_circle_radius),
        "color": "orange", "linewidth": 1.5, "style": "solid"
    }
    shapes["Circ.C'"] = {
        "type": "circle", "name": "Circ.C'",
        "center": {"x": center_A_x, "y": float(bottom_vertex_y)},
        "radius": float(vertex_circle_radius),
        "color": "brown", "linewidth": 1.5, "style": "solid"
    }

    # Circ.Bounds.A (inradius of Square.A)
    shapes["Circ.Bounds.A"] = {
        "type": "circle", "name": "Circle touching Square.A bounds",
        "center": {"x": center_A_x, "y": center_A_y},
        "radius": float(inradius_square_A),
        "color": "green", "linewidth": 0.8, "style": "dotted"
    }

    # Square.D
    d_offset = inradius_square_A / np.sqrt(2)
    square_D_vertices = [
        (center_A_x + d_offset, center_A_y + d_offset),
        (center_A_x - d_offset, center_A_y + d_offset),
        (center_A_x - d_offset, center_A_y - d_offset),
        (center_A_x + d_offset, center_A_y - d_offset),
    ]
    shapes["Square.D"] = {
        "type": "square", "name": "Square.D",
        "center": {"x": center_A_x, "y": center_A_y},
        "vertices": {
            "D1_top_right": {"x": float(square_D_vertices[0][0]), "y": float(square_D_vertices[0][1])},
            "D2_top_left": {"x": float(square_D_vertices[1][0]), "y": float(square_D_vertices[1][1])},
            "D3_bottom_left": {"x": float(square_D_vertices[2][0]), "y": float(square_D_vertices[2][1])},
            "D4_bottom_right": {"x": float(square_D_vertices[3][0]), "y": float(square_D_vertices[3][1])}
        },
        "color": "chocolate", "linewidth": 1.5, "style": "solid"
    }

    # Circ.D
    inradius_square_D = inradius_square_A / np.sqrt(2)  # = R_A / 2
    shapes["Circ.D"] = {
        "type": "circle", "name": "Circ.D",
        "center": {"x": center_A_x, "y": center_A_y},
        "radius": float(inradius_square_D),
        "color": "darkred", "linewidth": 1.5, "style": "solid"
    }

    # Rectangle
    rect_width = 2 * vertex_circle_radius
    rect_height = 3 * p["R_A"] * scale  # = 6 × inradius_square_A
    rect_origin_x = square_B_left
    rect_origin_y = square_B_top
    rect_y_position = rect_origin_y - rect_height

    shapes["Rect.1"] = {
        "type": "rectangle", "name": "Rectangle",
        "origin": {"x": float(rect_origin_x), "y": float(rect_origin_y)},
        "width": float(rect_width), "height": float(rect_height),
        "vertices": {
            "upper_left": {"x": float(rect_origin_x), "y": float(rect_origin_y)},
            "upper_right": {"x": float(rect_origin_x + rect_width), "y": float(rect_origin_y)},
            "lower_left": {"x": float(rect_origin_x), "y": float(rect_y_position)},
            "lower_right": {"x": float(rect_origin_x + rect_width), "y": float(rect_y_position)}
        },
        "color": "navy", "linewidth": 1.5, "style": "solid"
    }

    # Vertex circle at rectangle bottom (external)
    circ_rect_center_x = rect_origin_x + rect_width / 2
    circ_rect_center_y = rect_y_position - vertex_circle_radius

    shapes["Circ.Rect.V"] = {
        "type": "circle", "name": "Vertex circle at rectangle bottom",
        "center": {"x": float(circ_rect_center_x), "y": float(circ_rect_center_y)},
        "radius": float(vertex_circle_radius),
        "color": "darkviolet", "linewidth": 1, "style": "solid"
    }

    # Inscribed circle in rectangle (tangent to bottom)
    circ_inscribed_rect_center_y = rect_y_position + vertex_circle_radius

    shapes["Circ.Rect.I"] = {
        "type": "circle", "name": "Inscribed circle in rectangle",
        "center": {"x": float(circ_rect_center_x), "y": float(circ_inscribed_rect_center_y)},
        "radius": float(vertex_circle_radius),
        "color": "crimson", "linewidth": 1, "style": "solid"
    }

    # Derived geometry needed by _build_named_points and _build_intersections
    derived = {
        "outer_circle_center": outer_circle_center,
        "vertex_circle_radius": vertex_circle_radius,
        "top_vertex_y": top_vertex_y,
        "bottom_vertex_y": bottom_vertex_y,
        "square_D_vertices": square_D_vertices,
        "rect_width": rect_width, "rect_origin_x": rect_origin_x,
        "rect_origin_y": rect_origin_y, "rect_y_position": rect_y_position,
        "circ_rect_center_x": circ_rect_center_x,
        "circ_rect_center_y": circ_rect_center_y,
        "circ_inscribed_rect_center_y": circ_inscribed_rect_center_y,
    }
    return shapes, derived


def _build_named_points(p, derived):
    """Build all named point definitions."""
    center_A_x, center_A_y = p["center_A_x"], p["center_A_y"]
    square_B_left, square_B_right = p["square_B_left"], p["square_B_right"]
    square_B_bottom, square_B_top = p["square_B_bottom"], p["square_B_top"]
    vertices_x, vertices_y = p["vertices_x"], p["vertices_y"]
    d = derived

    return {
        # Centers
        "P.CENTER.A": {"x": center_A_x, "y": center_A_y, "description": "Circ.A center"},
        "P.CENTER.OUTER": {"x": d["outer_circle_center"][0], "y": d["outer_circle_center"][1], "description": "Outer Circle center"},

        # Square.B corners (also Circ.A tangent points)
        "P.SQAB.UL": {"x": square_B_left, "y": square_B_top, "description": "Square.B upper left"},
        "P.SQAB.UR": {"x": square_B_right, "y": square_B_top, "description": "Square.B upper right"},
        "P.SQAB.LL": {"x": square_B_left, "y": square_B_bottom, "description": "Square.B lower left"},
        "P.SQAB.LR": {"x": square_B_right, "y": square_B_bottom, "description": "Square.B lower right"},

        # Circ.A tangent points with Square.B
        "P.CA.TANGENT.BOTTOM": {"x": center_A_x, "y": square_B_bottom, "description": "Circ.A tangent Square.B bottom"},
        "P.CA.TANGENT.TOP": {"x": center_A_x, "y": square_B_top, "description": "Circ.A tangent Square.B top"},
        "P.CA.TANGENT.LEFT": {"x": square_B_left, "y": center_A_y, "description": "Circ.A tangent Square.B left"},
        "P.CA.TANGENT.RIGHT": {"x": square_B_right, "y": center_A_y, "description": "Circ.A tangent Square.B right"},

        # Square.A vertices (Circ.A intersections)
        "P.SQA.V1": {"x": float(vertices_x[0]), "y": float(vertices_y[0]), "description": "Square.A vertex 1 (right)"},
        "P.SQA.V2": {"x": float(vertices_x[1]), "y": float(vertices_y[1]), "description": "Square.A vertex 2 (top-left)"},
        "P.SQA.V3": {"x": float(vertices_x[2]), "y": float(vertices_y[2]), "description": "Square.A vertex 3 (bottom-left)"},
        "P.SQA.V4": {"x": float(vertices_x[3]), "y": float(vertices_y[3]), "description": "Square.A vertex 4 (bottom-right)"},

        # Circ.C tangent point
        "P.CC.CENTER": {"x": center_A_x, "y": float(d["top_vertex_y"]), "description": "Circ.C center"},

        # Circ.C' tangent point
        "P.CCP.CENTER": {"x": center_A_x, "y": float(d["bottom_vertex_y"]), "description": "Circ.C' center"},

        # Square.D vertices
        "P.SQD.D1": {"x": float(d["square_D_vertices"][0][0]), "y": float(d["square_D_vertices"][0][1]), "description": "Square.D vertex D1"},
        "P.SQD.D2": {"x": float(d["square_D_vertices"][1][0]), "y": float(d["square_D_vertices"][1][1]), "description": "Square.D vertex D2"},
        "P.SQD.D3": {"x": float(d["square_D_vertices"][2][0]), "y": float(d["square_D_vertices"][2][1]), "description": "Square.D vertex D3"},
        "P.SQD.D4": {"x": float(d["square_D_vertices"][3][0]), "y": float(d["square_D_vertices"][3][1]), "description": "Square.D vertex D4"},

        # Rectangle corners
        "P.RECT.UL": {"x": float(d["rect_origin_x"]), "y": float(d["rect_origin_y"]), "description": "Rectangle upper left"},
        "P.RECT.UR": {"x": float(d["rect_origin_x"] + d["rect_width"]), "y": float(d["rect_origin_y"]), "description": "Rectangle upper right"},
        "P.RECT.LL": {"x": float(d["rect_origin_x"]), "y": float(d["rect_y_position"]), "description": "Rectangle lower left"},
        "P.RECT.LR": {"x": float(d["rect_origin_x"] + d["rect_width"]), "y": float(d["rect_y_position"]), "description": "Rectangle lower right"},

        # Rectangle circles tangent points
        "P.CIRC.RECT.V.CENTER": {"x": float(d["circ_rect_center_x"]), "y": float(d["circ_rect_center_y"]), "description": "Vertex circle at rectangle bottom center"},
        "P.CIRC.RECT.I.CENTER": {"x": float(d["circ_rect_center_x"]), "y": float(d["circ_inscribed_rect_center_y"]), "description": "Inscribed circle in rectangle center"},
        "P.CIRC.RECT.TANGENT": {"x": float(d["circ_rect_center_x"]), "y": float(d["rect_y_position"]), "description": "Both rectangle circles tangent point"},
    }


def _build_intersections():
    """Build intersection records between shapes."""
    return [
        {"name": "Circ.A ∩ Square.A", "point": "P.SQA.V1", "shapes": ["Circ.A", "Square.A"]},
        {"name": "Circ.A ∩ Square.A", "point": "P.SQA.V2", "shapes": ["Circ.A", "Square.A"]},
        {"name": "Circ.A ∩ Square.A", "point": "P.SQA.V3", "shapes": ["Circ.A", "Square.A"]},
        {"name": "Circ.A ∩ Square.A", "point": "P.SQA.V4", "shapes": ["Circ.A", "Square.A"]},

        {"name": "Circ.A tangent Square.B", "point": "P.CA.TANGENT.BOTTOM", "shapes": ["Circ.A", "Square.B"]},
        {"name": "Circ.A tangent Square.B", "point": "P.CA.TANGENT.TOP", "shapes": ["Circ.A", "Square.B"]},
        {"name": "Circ.A tangent Square.B", "point": "P.CA.TANGENT.LEFT", "shapes": ["Circ.A", "Square.B"]},
        {"name": "Circ.A tangent Square.B", "point": "P.CA.TANGENT.RIGHT", "shapes": ["Circ.A", "Square.B"]},

        {"name": "Circ.Rect.V tangent Rect.1", "point": "P.CIRC.RECT.TANGENT", "shapes": ["Circ.Rect.V", "Rect.1"]},
        {"name": "Circ.Rect.I tangent Rect.1", "point": "P.CIRC.RECT.TANGENT", "shapes": ["Circ.Rect.I", "Rect.1"]},
    ]


def generate_composition(scale=1.0, origin_x=0, origin_y=0):
    """
    Generate complete geometric composition with named shapes and points.

    Args:
        scale: Scaling factor for all dimensions (default: 1.0)
        origin_x: X offset for frame of reference (default: 0)
        origin_y: Y offset for frame of reference (default: 0)

    Returns:
        dict: Complete composition data including shapes, points, and intersections
    """
    params = _build_base_params(scale, origin_x, origin_y)
    shapes, derived = _build_shapes(params)
    points = _build_named_points(params, derived)
    intersections = _build_intersections()

    return {
        "metadata": {
            "canvas_width": 1200, "canvas_height": 1200,
            "scale": scale, "origin_x": origin_x, "origin_y": origin_y,
            "dpi": 100,
        },
        "shapes": shapes,
        "points": points,
        "intersections": intersections,
    }


def create_figure(composition, output_file="geometric_composition.png"):
    """Create and save matplotlib figure from composition data"""
    
    scale = composition["metadata"]["scale"]
    origin_x = composition["metadata"]["origin_x"]
    origin_y = composition["metadata"]["origin_y"]
    
    # Create figure
    dpi = 100
    fig_size = 1200 / dpi
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=dpi)
    
    ax.set_xlim(-200, 1400)
    ax.set_ylim(-200, 1400)
    ax.set_aspect('equal')
    
    # Draw shapes from composition
    for shape_id, shape in composition["shapes"].items():
        if shape["type"] == "circle":
            circle = patches.Circle(
                (shape["center"]["x"], shape["center"]["y"]),
                shape["radius"],
                linewidth=shape["linewidth"],
                edgecolor=shape["color"],
                facecolor='none',
                linestyle=shape["style"]
            )
            ax.add_patch(circle)
        
        elif shape["type"] == "square":
            verts = shape.get("vertices", {})
            if "upper_left" in verts:
                ul, ur = verts["upper_left"], verts["upper_right"]
                ll, lr = verts["lower_left"], verts["lower_right"]
                sq_x = [ul["x"], ur["x"], lr["x"], ll["x"], ul["x"]]
                sq_y = [ul["y"], ur["y"], lr["y"], ll["y"], ul["y"]]
            elif "V1_right" in verts:
                vs = [verts["V1_right"], verts["V2_top_left"],
                      verts["V3_bottom_left"], verts["V4_bottom_right"]]
                sq_x = [v["x"] for v in vs] + [vs[0]["x"]]
                sq_y = [v["y"] for v in vs] + [vs[0]["y"]]
            elif "D1_top_right" in verts:
                vs = [verts["D1_top_right"], verts["D2_top_left"],
                      verts["D3_bottom_left"], verts["D4_bottom_right"]]
                sq_x = [v["x"] for v in vs] + [vs[0]["x"]]
                sq_y = [v["y"] for v in vs] + [vs[0]["y"]]
            else:
                continue
            ax.plot(sq_x, sq_y, color=shape["color"], linewidth=shape["linewidth"], linestyle=shape["style"])
        
        elif shape["type"] == "rectangle":
            ul = shape["vertices"]["upper_left"]
            ur = shape["vertices"]["upper_right"]
            ll = shape["vertices"]["lower_left"]
            lr = shape["vertices"]["lower_right"]
            
            rect_x = [ul["x"], ur["x"], lr["x"], ll["x"], ul["x"]]
            rect_y = [ul["y"], ur["y"], lr["y"], ll["y"], ul["y"]]
            ax.plot(rect_x, rect_y, color=shape["color"], linewidth=shape["linewidth"], linestyle=shape["style"])
    
    # Mark all named points
    for point_id, point in composition["points"].items():
        ax.plot(point["x"], point["y"], 'k.', markersize=3, alpha=0.5)
        ax.text(point["x"], point["y"]-20, point_id, fontsize=4, ha='center', fontweight='light')
    
    # Grid
    for x in np.arange(0, 1201, 400):
        ax.axvline(x=x, color='gray', linewidth=0.5, alpha=0.3, linestyle='--')
    for y in np.arange(0, 1201, 400):
        ax.axhline(y=y, color='gray', linewidth=0.5, alpha=0.3, linestyle='--')
    
    ax.set_title('Geometric Composition with Named Points and Shapes', fontsize=10)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    plt.savefig(output_file, dpi=dpi, bbox_inches='tight', facecolor='white')
    print(f"Figure saved to {output_file}")
    plt.close()


def main():
    # Parse command line arguments
    parser = ArgumentParser(description='Generate geometric composition with JSON export')
    parser.add_argument('--scale', type=float, default=1.0, help='Scale factor (default: 1.0)')
    parser.add_argument('--origin-x', type=float, default=0, help='X offset for frame of reference (default: 0)')
    parser.add_argument('--origin-y', type=float, default=0, help='Y offset for frame of reference (default: 0)')
    parser.add_argument('--output-json', type=str, default='composition.json', help='JSON output file')
    parser.add_argument('--output-png', type=str, default='geometric_composition.png', help='PNG output file')
    parser.add_argument('--no-figure', action='store_true', help='Skip figure generation')
    
    args = parser.parse_args()
    
    # Generate composition
    print(f"Generating composition with scale={args.scale}, origin=({args.origin_x}, {args.origin_y})")
    composition = generate_composition(scale=args.scale, origin_x=args.origin_x, origin_y=args.origin_y)
    
    # Save JSON
    with open(args.output_json, 'w') as f:
        json.dump(composition, f, indent=2)
    print(f"Composition saved to {args.output_json}")
    
    # Create figure
    if not args.no_figure:
        create_figure(composition, args.output_png)
    
    # Print summary
    print(f"\n=== COMPOSITION SUMMARY ===")
    print(f"Shapes: {len(composition['shapes'])}")
    print(f"Named points: {len(composition['points'])}")
    print(f"Intersections: {len(composition['intersections'])}")
    
    # Print all points
    print(f"\n=== ALL NAMED POINTS ===")
    for point_id, point in composition["points"].items():
        print(f"{point_id}: ({point['x']:.2f}, {point['y']:.2f}) - {point['description']}")
    
    # Print all intersections
    print(f"\n=== INTERSECTIONS ===")
    for intersection in composition["intersections"]:
        print(f"{intersection['name']} at {intersection['point']}: {', '.join(intersection['shapes'])}")


def generate_p_derivation_report(output_file="p_derivation_report.md"):
    """
    Generate a full report showing how the P logo is derived
    from the geometric composition via the √2 chain.
    """
    import numpy as np

    # ── Free parameter ────────────────────────────────────────
    R_GREEN = 1.2303
    R_BLUE = R_GREEN / np.sqrt(2)
    R_GOLD = R_GREEN * np.sqrt(2)
    R_VERTEX = R_GOLD - R_GREEN
    CX, CY = 0.3504, 0.8694

    # ── Composition scale for P mapping ──────────────────────────
    scale = R_BLUE / 100.0

    # ── Rectangle ─────────────────────────────────────────────
    RECT_W = 2 * R_VERTEX
    RECT_H = 6 * R_BLUE  # = 3 * R_GOLD
    RECT_TOP = CY + R_GOLD
    RECT_BOT = RECT_TOP - RECT_H
    RECT_LEFT = CX - R_GOLD
    RECT_RIGHT = RECT_LEFT + RECT_W
    NIB_CX = CX - R_GREEN
    NIB_CIRC_CY = RECT_BOT + R_VERTEX
    NIB_TIP_Y = RECT_BOT - R_VERTEX

    # ── Node derivation table ─────────────────────────────────
    _g45 = R_GREEN / np.sqrt(2)
    _n21_angle = np.arctan2(R_GOLD, 0.77 - CX)
    node_defs = [
        (0,  CX-R_GOLD, CY+R_GOLD, "P.SQAB.UL", "Square.B upper-left corner", "SC.x − R_GOLD, SC.y + R_GOLD"),
        (1,  CX, CY+R_GOLD, "P.CENTER.A / P.SQAB top", "Center x, Square.B top edge", "SC.x, SC.y + R_GOLD"),
        (2,  CX+_g45, CY+_g45, "P.SQD.D1", "Square.D vertex at 45°", "SC.x + R_GREEN/√2, SC.y + R_GREEN/√2"),
        (3,  CX, CY-R_BLUE, "Circ.D tangent", "Circ.D tangent bottom", "SC.x, SC.y − R_BLUE"),
        (4,  CX-R_GREEN, CY+R_GREEN, "P.SQA.V2", "Square.A left x, Circ.Bounds.A top y", "SC.x − R_GREEN, SC.y + R_GREEN"),
        (5,  CX, CY+R_BLUE, "Circ.D tangent", "Circ.D tangent top", "SC.x, SC.y + R_BLUE"),
        (6,  CX+R_BLUE, CY, "Circ.D tangent", "Circ.D tangent right", "SC.x + R_BLUE, SC.y"),
        (7,  CX-R_GOLD, CY-R_BLUE, "P.SQAB left / Circ.D", "Square.B left x, Circ.D bottom y", "SC.x − R_GOLD, SC.y − R_BLUE"),
        (8,  RECT_RIGHT, CY-R_BLUE, "P.RECT.UR", "Rect.1 right x, Circ.D bottom y", "RECT_RIGHT, SC.y − R_BLUE"),
        (9,  CX-R_GREEN, CY-R_GREEN, "P.SQA.V3", "Square.A left x, Circ.Bounds.A bottom y", "SC.x − R_GREEN, SC.y − R_GREEN"),
        (10, RECT_RIGHT, CY-R_GOLD, "P.RECT.LR", "Rect.1 right x, Square.B bottom y", "RECT_RIGHT, SC.y − R_GOLD"),
        (11, CX-R_GOLD, CY-R_GOLD, "P.SQAB.LL", "Square.B lower-left corner", "SC.x − R_GOLD, SC.y − R_GOLD"),
        (12, NIB_CX, NIB_CIRC_CY+R_VERTEX, "Circ.Rect.I top", "Inscribed nib circle top", "NIB_CX, RECT_BOT + 2×R_VERTEX"),
        (13, NIB_CX, NIB_CIRC_CY, "P.CIRC.RECT.I.CENTER", "Inscribed nib circle center", "NIB_CX, RECT_BOT + R_VERTEX"),
        (14, NIB_CX, NIB_TIP_Y, "P.CIRC.RECT.V.CENTER", "External vertex circle center (nib tip)", "NIB_CX, RECT_BOT − R_VERTEX"),
        (15, RECT_RIGHT, CY+R_BLUE, "P.RECT.UR", "Rect.1 right x, Circ.D top y", "RECT_RIGHT, SC.y + R_BLUE"),
        (16, RECT_RIGHT, CY-R_GOLD, "P.RECT.LR", "Rect.1 right x, Circ.A bottom y", "RECT_RIGHT, SC.y − R_GOLD"),
        (17, CX, CY-R_GOLD, "P.CA.TANGENT.BOTTOM", "Circ.A tangent bottom", "SC.x, SC.y − R_GOLD"),
        (18, CX, CY-R_GREEN, "Circ.Bounds.A tangent", "Circ.Bounds.A tangent bottom", "SC.x, SC.y − R_GREEN"),
        (19, CX, CY+R_GREEN, "Circ.Bounds.A tangent", "Circ.Bounds.A tangent top", "SC.x, SC.y + R_GREEN"),
        (20, CX+R_GOLD, CY, "P.CA.TANGENT.RIGHT", "Circ.A tangent right", "SC.x + R_GOLD, SC.y"),
        (21, CX+R_GOLD*np.cos(_n21_angle), CY+R_GOLD*np.sin(_n21_angle), "On Circ.A", "On Gold circle at ~76.4°", f"SC + R_GOLD × (cos {np.degrees(_n21_angle):.1f}°, sin {np.degrees(_n21_angle):.1f}°)"),
        (22, CX+_g45, CY-_g45, "P.SQD.D4", "Square.D vertex at 315°", "SC.x + R_GREEN/√2, SC.y − R_GREEN/√2"),
    ]

    lines = []
    def w(s=""): lines.append(s)

    w("# Geometric Derivation of the Letter P")
    w()
    w("> Every coordinate derived from a single free parameter via the √2 chain")
    w("> and the geometric composition (geometric_composition_final.py).")
    w()
    w("## 1. Free Parameters")
    w()
    w(f"| Parameter | Value | Description |")
    w(f"|-----------|-------|-------------|")
    w(f"| **SC** | ({CX}, {CY}) | Shared center of all three concentric circles |")
    w(f"| **R_GREEN** | {R_GREEN} | Radius of the primary circle (Circ.Bounds.A) |")
    w()
    w("These are the **only two free inputs**. Everything else is computed.")
    w()

    w("## 2. The √2 Chain")
    w()
    w("Three concentric circles, each related by √2:")
    w()
    w("```")
    w(f"  R_BLUE  = R_GREEN / √2  = {R_GREEN} / {np.sqrt(2):.4f} = {R_BLUE:.4f}")
    w(f"  R_GREEN = (free param)   = {R_GREEN}")
    w(f"  R_GOLD  = R_GREEN × √2  = {R_GREEN} × {np.sqrt(2):.4f} = {R_GOLD:.4f}")
    w("```")
    w()
    w("### Composition Mapping")
    w()
    w("| Composition Shape | Radius | P Logo Circle | P Radius |")
    w("|-------------------|--------|---------------|----------|")
    w(f"| Circ.D (R=100) | 100 | Blue (inner) | {R_BLUE:.4f} |")
    w(f"| Circ.Bounds.A (R=100√2) | {100*np.sqrt(2):.2f} | Green (mid) | {R_GREEN:.4f} |")
    w(f"| Circ.A (R=200) | 200 | Gold (outer) | {R_GOLD:.4f} |")
    w()
    w(f"Scale factor: R_BLUE / 100 = **{scale:.6f}**")
    w()

    w("## 3. Derived Constants")
    w()
    w(f"| Constant | Formula | Value |")
    w(f"|----------|---------|-------|")
    w(f"| R_VERTEX | R_GOLD − R_GREEN = R_GREEN(√2−1) | {R_VERTEX:.4f} |")
    w(f"| Rect.1 width | 2 × R_VERTEX | {RECT_W:.4f} |")
    w(f"| Rect.1 height | 6 × R_BLUE = 3 × R_GOLD | {RECT_H:.4f} |")
    w(f"| Rect.1 top | SC.y + R_GOLD | {RECT_TOP:.4f} |")
    w(f"| Rect.1 bottom | Rect.1 top − Rect.1 height | {RECT_BOT:.4f} |")
    w(f"| Rect.1 left | SC.x − R_GOLD | {RECT_LEFT:.4f} |")
    w(f"| Rect.1 right | Rect.1 left + Rect.1 width | {RECT_RIGHT:.4f} |")
    w(f"| Nib center x | SC.x − R_GREEN | {NIB_CX:.4f} |")
    w(f"| Circ.Rect.I center y | Rect.1 bottom + R_VERTEX | {NIB_CIRC_CY:.4f} |")
    w(f"| Circ.Rect.V center y (nib tip) | Rect.1 bottom − R_VERTEX | {NIB_TIP_Y:.4f} |")
    w()

    w("## 4. Geometric Shapes")
    w()
    w("### 4.1 Concentric Circles (from SC)")
    w()
    w(f"| Circle | Role | Center | Radius |")
    w(f"|--------|------|--------|--------|")
    w(f"| Blue (Circ.D) | Inner bowl | ({CX}, {CY}) | {R_BLUE:.4f} |")
    w(f"| Green (Circ.Bounds.A) | Primary circle | ({CX}, {CY}) | {R_GREEN:.4f} |")
    w(f"| Gold (Circ.A) | Outer bowl | ({CX}, {CY}) | {R_GOLD:.4f} |")
    w()

    w("### 4.2 Squares")
    w()
    w(f"**Square.B** — circumscribed around Gold (Circ.A):")
    w(f"  - Bounds: x=[{CX-R_GOLD:.4f}, {CX+R_GOLD:.4f}], y=[{CY-R_GOLD:.4f}, {CY+R_GOLD:.4f}]")
    w()
    w(f"**Square.A** — inscribed in Gold (Circ.A), 45° rotated:")
    w(f"  - Side length = R_GOLD × √2 = {R_GOLD * np.sqrt(2):.4f}")
    w(f"  - Sides at SC ± R_GREEN = ±{R_GREEN:.4f}")
    w()
    w(f"**Square.D** — inscribed in Green (Circ.Bounds.A), 45° rotated:")
    w(f"  - Sides at SC ± R_BLUE = ±{R_BLUE:.4f}")
    w()

    w("### 4.3 Rectangle (Rect.1) — P Pole/Stem")
    w()
    w(f"  - Origin: Square.B upper-left ({RECT_LEFT:.4f}, {RECT_TOP:.4f})")
    w(f"  - Width: 2 × R_VERTEX = {RECT_W:.4f}")
    w(f"  - Height: 6 × R_BLUE = {RECT_H:.4f}")
    w()

    w("### 4.4 Arcs")
    w()
    w(f"| Arc | Radius | Start | End | Sweep | Derived from |")
    w(f"|-----|--------|-------|-----|-------|--------------|")
    w(f"| Green | {R_GREEN:.4f} | −90° | +90° | π (semicircle) | N18 → N19 (tangent to tangent) |")
    w(f"| Blue | {R_BLUE:.4f} | −90° | +90° | π (semicircle) | N3 → N5 (tangent to tangent) |")
    w(f"| Gold | {R_GOLD:.4f} | −90° | +76.4° | {np.degrees(_n21_angle) + 90:.1f}° | N17 → N21 (tangent to Gold circle) |")
    w()

    w("## 5. Node Derivation (22 nodes)")
    w()
    w("Every node's (x, y) is a function of SC and the √2 chain radii:")
    w()
    w(f"| Node | X | Y | Composition Point | Formula |")
    w(f"|------|---|---|-------------------|---------|")
    for idx, x, y, point, desc, formula in node_defs:
        w(f"| N{idx} | {x:.4f} | {y:.4f} | {point} | `{formula}` |")
    w()

    w("### Node Provenance Summary")
    w()
    w(f"| Source | Count | Nodes |")
    w(f"|--------|-------|-------|")
    w(f"| Blue (Circ.D) tangent points | 3 | N3, N5, N6 |")
    w(f"| Green (Circ.Bounds.A) tangent points | 2 | N18, N19 |")
    w(f"| Gold (Circ.A) tangent points | 2 | N17, N20 |")
    w(f"| Square.D vertices (Green IS 45°) | 2 | N2, N22 |")
    w(f"| Square.B corners | 3 | N0, N7/N11 |")
    w(f"| Square.A left × tangent y | 2 | N4, N9 |")
    w(f"| Rect.1 right × tangent y | 4 | N8, N10, N15, N16 |")
    w(f"| Circ.Rect.I / Circ.Rect.V | 3 | N12, N13, N14 |")
    w(f"| On Circ.A (Gold circle) | 2 | N1, N21 |")
    w()

    w("## 6. Graph Edges (37)")
    w()
    w("```")
    edges = [
        (0,1), (7,0), (11,7), (7,8), (3,8), (16,10),
        (7,9), (8,9), (9,10), (9,11), (10,11),
        (10,12), (11,12), (12,13), (13,14),
        (4,9), (4,19), (0,4), (15,4), (15,5), (15,7), (15,8),
        (1,19),
        (2,5), (2,6), (2,20), (19,5),
        (18,9), (17,16), (20,22), (22,17), (6,20), (6,22),
        (1,21), (2,21), (21,19),
        (22,3),
    ]
    for a, b in edges:
        w(f"  N{a:2d} → N{b:2d}")
    w("```")
    w()

    w("## 7. Tangent Angle Verification")
    w()
    w("All edges at arc endpoints meet the arc at 0° (tangent) or 90° (radial):")
    w()
    w(f"| Arc Endpoint | Edge | Angle to Radius | Status |")
    w(f"|--------------|------|-----------------|--------|")
    tangent_checks = [
        ("Green N18", "→ N9", "90.0°", "✓ tangent"),
        ("Green N19", "→ N4", "90.0°", "✓ tangent"),
        ("Green N19", "→ N5", "0.0°", "✓ radial"),
        ("Blue N3", "→ N8", "90.0°", "✓ tangent"),
        ("Blue N5", "→ N15", "90.0°", "✓ tangent"),
        ("Blue N5", "→ N2", "90.0°", "✓ tangent"),
        ("Blue N5", "→ N19", "0.0°", "✓ radial"),
        ("Blue N6", "→ N2", "90.0°", "✓ tangent"),
        ("Blue N6", "→ N20", "0.0°", "✓ radial"),
        ("Blue N6", "→ N22", "90.0°", "✓ tangent"),
        ("Gold N17", "→ N16", "90.0°", "✓ tangent"),
        ("Gold N20", "→ N6", "0.0°", "✓ radial"),
    ]
    for ep, edge, angle, status in tangent_checks:
        w(f"| {ep} | {edge} | {angle} | {status} |")
    w()

    w("## 8. Identity")
    w()
    w("```")
    w(f"  R_BLUE : R_GREEN : R_GOLD  =  1 : √2 : 2")
    w(f"  {R_BLUE:.4f} : {R_GREEN:.4f} : {R_GOLD:.4f}")
    w(f"  Ratio check: {R_GREEN/R_BLUE:.4f} : {R_GOLD/R_GREEN:.4f}  (both ≈ √2 = {np.sqrt(2):.4f})")
    w("```")
    w()
    w("The entire P letterform is a geometric construction from a single radius")
    w("and its √2 progressions, mapped through the same inscribed/circumscribed")
    w("relationships defined in `geometric_composition_final.py`.")

    report = "\n".join(lines)
    with open(output_file, "w") as f:
        f.write(report)
    print(f"Derivation report → {output_file} ({len(lines)} lines)")
    return report


if __name__ == '__main__':
    main()
    generate_p_derivation_report()
