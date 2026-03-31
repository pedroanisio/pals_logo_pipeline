"""
PAL's Notes Logo Pipeline — Step 6: Render

Reads all upstream data artifacts and produces a single self-contained
HTML file with Three.js + Canvas rendering of the animated logo.

This is the ONLY step that knows about HTML, CSS, JavaScript, or Three.js.
All geometry, colors, and animation parameters are read from upstream JSON —
nothing is hardcoded here except the rendering template structure.

Input:  build/palette.json, build/layout.json, build/animations.json
Output: build/logo.html
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

def validate(
    palette: dict, layout: dict, animations: dict
) -> list[str]:
    errors: list[str] = []
    if layout.get("_meta", {}).get("step") != 4:
        errors.append("layout._meta.step != 4")
    if animations.get("_meta", {}).get("step") != 5:
        errors.append("animations._meta.step != 5")
    if "elements" not in layout:
        errors.append("layout missing 'elements'")
    if "systems" not in animations:
        errors.append("animations missing 'systems'")
    if "colors" not in palette:
        errors.append("palette missing 'colors'")
    return errors


# ──────────────────────────────────────────────
# Data extraction helpers
# ──────────────────────────────────────────────

def _extract_nodes(layout: dict) -> list[dict]:
    return [el for el in layout["elements"] if el["type"] == "node"]

def _extract_edges(layout: dict) -> list[dict]:
    return [el for el in layout["elements"] if el["type"] == "edge"]

def _extract_arcs(layout: dict) -> list[dict]:
    return [el for el in layout["elements"] if el["type"] == "arc"]

def _extract_nib_lines(layout: dict) -> dict[str, list]:
    fan = [el for el in layout["elements"] if el["type"] == "nib_fan_line"]
    outline = [el for el in layout["elements"] if el["type"] == "nib_outline_line"]
    center = [el for el in layout["elements"] if el["type"] == "nib_center_line"]
    accents = [el for el in layout["elements"] if el["type"] == "nib_accent_node"]
    ball = [el for el in layout["elements"] if el["type"] == "junction_ball"]
    ink = [el for el in layout["elements"] if el["type"] == "ink_origin"]
    return {"fan": fan, "outline": outline, "center": center,
            "accents": accents, "ball": ball, "ink": ink}

def _extract_runner_paths(layout: dict) -> list[dict]:
    return [el for el in layout["elements"] if el["type"] == "runner_path"]


# ──────────────────────────────────────────────
# JS data serialization
# ──────────────────────────────────────────────

def _color_map_js(palette: dict) -> str:
    lines = []
    for name, color in palette["colors"].items():
        lines.append(f"  {name}: 0x{color['hex'].lstrip('#')},")
    return "const PAL = {\n" + "\n".join(lines) + "\n};"


def _nodes_js(nodes: list[dict]) -> str:
    entries = []
    for n in sorted(nodes, key=lambda x: x["index"]):
        entries.append(
            f"  [{n['x']:.4f}, {n['y']:.4f}, 0x{_color_hex(n['color'])},"
            f" {n['radius']}, {n['degree']}]"
        )
    return "const NODES = [\n" + ",\n".join(entries) + "\n];"


_COLOR_HEX_CACHE: dict[str, str] = {}

def _color_hex(name: str, palette: dict | None = None) -> str:
    """Map color name to hex without #. Reads from palette on first call."""
    if not _COLOR_HEX_CACHE and palette:
        for cname, cdata in palette["colors"].items():
            _COLOR_HEX_CACHE[cname] = cdata["hex"].lstrip("#")
    return _COLOR_HEX_CACHE.get(name, "6EC4A8")


def _edges_js(edges: list[dict]) -> str:
    entries = []
    for e in edges:
        etype = e.get("edge_type", "mesh")
        entries.append(f"  [{e['a']}, {e['b']}, \"{etype}\"]")
    return "const EDGES = [\n" + ",\n".join(entries) + "\n];"


def _arcs_js(arcs: list[dict]) -> str:
    entries = []
    for a in sorted(arcs, key=lambda x: x["index"]):
        entries.append(
            f"  {{idx:{a['index']}, cx:{a['cx']:.4f}, cy:{a['cy']:.4f},"
            f" r:{a['radius']:.2f},"
            f" color:0x{_color_hex(a['color'])},"
            f" mainTh:{a['main_thickness']}, bloomTh:{a['bloom_thickness']},"
            f" mainOp:{a['main_opacity']}, bloomOp:{a['bloom_opacity']},"
            f" pts:{json.dumps([[round(p['x'],4),round(p['y'],4),round(p.get('nx',0),4),round(p.get('ny',0),4)] for p in a['points']])}"
            f"}}"
        )
    return "const ARCS = [\n" + ",\n".join(entries) + "\n];"


def _nib_js(nib: dict) -> str:
    parts = []
    # Fan lines
    fan_entries = []
    for l in nib["fan"]:
        fan_entries.append(
            f"    {{x1:{l['x1']:.4f},y1:{l['y1']:.4f},x2:{l['x2']:.4f},y2:{l['y2']:.4f},"
            f"color:0x{_color_hex(l['color'])},th:{l['thickness']},op:{l['opacity']}}}"
        )
    parts.append("  fan: [\n" + ",\n".join(fan_entries) + "\n  ]")

    # Outline lines
    out_entries = []
    for l in nib["outline"]:
        out_entries.append(
            f"    {{x1:{l['x1']:.4f},y1:{l['y1']:.4f},x2:{l['x2']:.4f},y2:{l['y2']:.4f},"
            f"color:0x{_color_hex(l['color'])},th:{l['thickness']},op:{l['opacity']}}}"
        )
    parts.append("  outline: [\n" + ",\n".join(out_entries) + "\n  ]")

    # Center line
    c = nib["center"][0]
    parts.append(
        f"  center: {{x1:{c['x1']:.4f},y1:{c['y1']:.4f},x2:{c['x2']:.4f},y2:{c['y2']:.4f},"
        f"color:0x{_color_hex(c['color'])},th:{c['thickness']},op:{c['opacity']}}}"
    )

    # Accent nodes
    acc_entries = []
    for n in nib["accents"]:
        acc_entries.append(
            f"    {{x:{n['x']:.4f},y:{n['y']:.4f},color:0x{_color_hex(n['color'])},r:{n['radius']}}}"
        )
    parts.append("  accents: [\n" + ",\n".join(acc_entries) + "\n  ]")

    # Junction ball
    b = nib["ball"][0]
    parts.append(
        f"  ball: {{x:{b['x']:.4f},y:{b['y']:.4f},r:{b['radius']},"
        f"color:0x{_color_hex(b['color'])},op:{b['opacity']},"
        f"glowSize:{b['glow_size']},glowColor:0x{_color_hex(b.get('glow_color','warm_white'))},"
        f"glowOp:{b.get('glow_opacity',0.3)},"
        f"bloomSize:{b['bloom_size']},bloomColor:0x{_color_hex(b.get('bloom_color','amber'))},"
        f"bloomOp:{b.get('bloom_opacity',0.1)}}}"
    )

    # Ink origin
    ink = nib["ink"][0]
    parts.append(f"  ink: {{x:{ink['x']:.4f},y:{ink['y']:.4f}}}")

    return "const NIB = {\n" + ",\n".join(parts) + "\n};"


def _runner_paths_js(paths: list[dict]) -> str:
    entries = []
    for rp in paths:
        pts = [[round(p["x"],4), round(p["y"],4)] for p in rp["points"]]
        entries.append(
            f"  {{arcIdx:{rp['arc_index']},color:0x{_color_hex(rp['color'])},"
            f"pts:{json.dumps(pts)}}}"
        )
    return "const RUNNER_PATHS = [\n" + ",\n".join(entries) + "\n];"


def _ring_js(ring: dict) -> str:
    bands = []
    for b in ring["bands"]:
        bands.append(f"    {{innerR:{b['inner_r']},outerR:{b['outer_r']},op:{b['opacity']}}}")
    return (
        f"const RING = {{\n"
        f"  fillR: {ring['fill_radius']},\n"
        f"  fillColor: 0x{_color_hex(ring['fill_color'])},\n"
        f"  color: 0x{_color_hex(ring['color'])},\n"
        f"  bands: [\n" + ",\n".join(bands) + "\n  ]\n};"
    )


def _anim_js(animations: dict) -> str:
    s = animations["systems"]
    # Serialize each system as a JS object, omitting adjacency (too large, embed separately)
    w = s["wave"]
    p = s["pulses"]
    ar = s["arc_runners"]
    b = s["breathing"]
    er = s["energy_rings"]
    ink = s["ink_drops"]

    return f"""const ANIM = {{
  wave: {{
    interval: {w['interval']},
    delayPerHop: {w['delay_per_hop']},
    easing: "{w['easing']}",
    duration: {w['duration']},
    intensity: {w['intensity']},
    traversal: "{w['traversal']}",
    nodeCount: {w['node_count']}
  }},
  pulses: {{
    count: {p['count']},
    speedRange: {json.dumps(p['speed_range'])},
    fadeIn: {p['fade_in']},
    fadeOut: {p['fade_out']},
    color: 0x{_color_hex(p['color'])},
    edgeCount: {p['edge_count']},
    corePeakOp: {p['core_peak_opacity']},
    glowPeakOp: {p['glow_peak_opacity']},
    radius: {p['radius']},
    glowSize: {p['glow_size']}
  }},
  arcRunners: {{
    perArc: {ar['per_arc']},
    arcCount: {ar['arc_count']},
    speed: {ar['speed']},
    trailLength: {ar['trail_length']},
    opacityPeakAt: {ar['opacity_peak_at']},
    corePeakOp: {ar['core_peak_opacity']},
    trailPeakOp: {ar['trail_peak_opacity']}
  }},
  breathing: {{
    amplitude: {b['amplitude']},
    frequency: {b['frequency']},
    waveform: "{b['waveform']}"
  }},
  energyRings: {{
    interval: {er['interval']},
    expansionRate: {er['expansion_rate']},
    fadeDuration: {er['fade_duration']},
    initialOpacity: {er['initial_opacity']},
    initialInnerR: {er['initial_inner_r']},
    initialOuterR: {er['initial_outer_r']},
    color: 0x{_color_hex(er['color'])}
  }},
  inkDrops: {{
    poolSize: {ink['pool_size']},
    gravity: {ink['gravity']},
    drag: {ink['drag']},
    spawnRate: {json.dumps(ink['spawn_rate'])},
    lifetimeRange: {json.dumps(ink['lifetime_range'])},
    vxRange: {json.dumps(ink['initial_vx_range'])},
    vyRange: {json.dumps(ink['initial_vy_range'])},
    fadeInFrac: {ink['fade_in_fraction']},
    fadeOutFrac: {ink['fade_out_fraction']},
    peakOp: {ink['peak_opacity']},
    color: 0x{_color_hex(ink['color'])},
    radius: {ink['radius']}
  }}
}};"""


def _adjacency_js(animations: dict) -> str:
    adj = animations["systems"]["wave"]["adjacency"]
    entries = []
    for k in sorted(adj.keys(), key=int):
        entries.append(f"  {k}: {json.dumps(adj[k])}")
    return "const ADJ = {\n" + ",\n".join(entries) + "\n};"


def _nebula_js(palette: dict) -> str:
    nebula = palette["nebula"]
    colors = []
    for nc in nebula["colors"]:
        c = palette["colors"][nc["color"]]
        r, g, b = c["rgb"]
        colors.append(f"    'rgba({r},{g},{b},{nc['alpha']})'")
    return (
        f"const NEBULA_COUNT = {nebula['count']};\n"
        f"const NEBULA_COLORS = [\n" + ",\n".join(colors) + "\n];"
    )


# ──────────────────────────────────────────────
# HTML template
# ──────────────────────────────────────────────

def _build_html(
    palette: dict, layout: dict, animations: dict
) -> str:
    # Initialize color hex cache from palette (the single source of truth)
    _COLOR_HEX_CACHE.clear()
    _color_hex("", palette)

    nodes = _extract_nodes(layout)
    edges = _extract_edges(layout)
    arcs = _extract_arcs(layout)
    nib = _extract_nib_lines(layout)
    runners = _extract_runner_paths(layout)

    co = layout["center_offset"]
    bg_hex = palette["colors"]["background"]["hex"]
    star_count = palette["stars"]["count"]

    # Supplementary configs — no hardcoded values in the renderer
    supp = animations.get("supplementary", {})
    particle_cfg = supp.get("particles", {})
    shimmer_cfg = supp.get("shimmer", {})

    # Sizing from palette
    node_glow_scale = palette["sizing"]["node_glow_scale"]
    node_bloom_scale = palette["sizing"]["node_bloom_scale"]
    node_glow_opacity = palette["opacity_defaults"]["node_glow"]["base"]
    node_bloom_opacity = palette["opacity_defaults"]["node_bloom"]["base"]
    arc_runner_radius = palette["sizing"]["arc_runner_radius"]

    # Build JS data blocks
    js_palette = _color_map_js(palette)
    js_nodes = _nodes_js(nodes)
    js_edges = _edges_js(edges)
    js_arcs = _arcs_js(arcs)
    js_nib = _nib_js(nib)
    js_runners = _runner_paths_js(runners)
    js_ring = _ring_js(layout["ring"])
    js_anim = _anim_js(animations)
    js_adj = _adjacency_js(animations)
    js_nebula = _nebula_js(palette)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PAL's Notes — Logo</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: {bg_hex};
    overflow: hidden;
    width: 100vw; height: 100vh;
    display: flex; align-items: center; justify-content: center;
  }}
  #container {{
    position: relative;
    width: 100vmin; height: 100vmin;
    max-width: 800px; max-height: 800px;
  }}
  #bg-canvas, #star-canvas, #three-canvas {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  }}
  #bg-canvas {{ z-index: 1; }}
  #star-canvas {{ z-index: 2; }}
  #three-canvas {{ z-index: 3; }}
  #brand-text {{
    position: absolute; bottom: 5%; width: 100%; text-align: center;
    z-index: 4;
    font-family: 'Georgia', serif;
    font-size: 1.8vmin; letter-spacing: 0.45em; text-transform: uppercase;
    color: #{_color_hex("rose_gold")};
    opacity: 0; animation: brandFadeIn 2s ease 1.5s forwards;
  }}
  @keyframes brandFadeIn {{ to {{ opacity: 0.9; }} }}
</style>
</head>
<body>
<div id="container">
  <canvas id="bg-canvas"></canvas>
  <canvas id="star-canvas"></canvas>
  <canvas id="three-canvas"></canvas>
  <div id="brand-text">PAL\'s Notes</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{
"use strict";

// ═══ PIPELINE DATA (generated by render.py) ═══
{js_palette}
{js_nodes}
{js_edges}
{js_arcs}
{js_nib}
{js_runners}
{js_ring}
{js_anim}
{js_adj}
{js_nebula}
const STAR_COUNT = {star_count};
const CENTER_OFFSET_Y = {co['y']};

// ═══ HELPERS ═══
function hexToRgb(hex) {{
  return {{ r: (hex >> 16) / 255, g: ((hex >> 8) & 0xFF) / 255, b: (hex & 0xFF) / 255 }};
}}

function createLine(x1, y1, x2, y2, thickness, color, opacity) {{
  const dx = x2-x1, dy = y2-y1, len = Math.sqrt(dx*dx+dy*dy);
  if (len < 0.001) return new THREE.Group();
  const nx = -dy/len*thickness/2, ny = dx/len*thickness/2;
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
    x1+nx,y1+ny,0, x1-nx,y1-ny,0, x2+nx,y2+ny,0, x2-nx,y2-ny,0
  ]), 3));
  geo.setIndex([0,1,2,1,3,2]);
  return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({{
    color, transparent:true, opacity, side:THREE.DoubleSide
  }}));
}}

function createCircle(x, y, r, color, opacity, segs) {{
  const m = new THREE.Mesh(
    new THREE.CircleGeometry(r, segs||24),
    new THREE.MeshBasicMaterial({{color, transparent:true, opacity:opacity||1}})
  );
  m.position.set(x, y, 0);
  return m;
}}

function createGlow(x, y, size, color, opacity) {{
  const c = document.createElement('canvas');
  c.width=64; c.height=64;
  const ctx=c.getContext('2d'), rgb=hexToRgb(color);
  const g=ctx.createRadialGradient(32,32,0,32,32,32);
  g.addColorStop(0,`rgba(${{rgb.r*255|0}},${{rgb.g*255|0}},${{rgb.b*255|0}},${{opacity||0.5}})`);
  g.addColorStop(0.4,`rgba(${{rgb.r*255|0}},${{rgb.g*255|0}},${{rgb.b*255|0}},${{(opacity||0.5)*0.35}})`);
  g.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=g; ctx.fillRect(0,0,64,64);
  const tex=new THREE.CanvasTexture(c);
  const mat=new THREE.SpriteMaterial({{map:tex,transparent:true,depthWrite:false}});
  const s=new THREE.Sprite(mat);
  s.position.set(x,y,0.1); s.scale.set(size,size,1);
  return s;
}}

function createArcStrip(pts, thickness, color, opacity) {{
  const positions=[], indices=[];
  for(let i=0;i<pts.length;i++) {{
    const [x,y,nx,ny]=pts[i];
    positions.push(x+nx*thickness/2,y+ny*thickness/2,0,x-nx*thickness/2,y-ny*thickness/2,0);
    if(i<pts.length-1) {{ const vi=i*2; indices.push(vi,vi+1,vi+2,vi+1,vi+3,vi+2); }}
  }}
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(positions),3));
  geo.setIndex(indices);
  return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({{color,transparent:true,opacity,side:THREE.DoubleSide}}));
}}

// ═══ BACKGROUND ═══
const bgCanvas=document.getElementById('bg-canvas');
const bgCtx=bgCanvas.getContext('2d');
const starCanvas=document.getElementById('star-canvas');
const starCtx=starCanvas.getContext('2d');

function resizeCanvases() {{
  const el=document.getElementById('container');
  bgCanvas.width=el.clientWidth; bgCanvas.height=el.clientHeight;
  starCanvas.width=el.clientWidth; starCanvas.height=el.clientHeight;
}}
resizeCanvases();

// Nebula clouds
const nebulaClouds=[];
for(let i=0;i<NEBULA_COUNT;i++) {{
  nebulaClouds.push({{
    x:0.3+Math.random()*0.4, y:0.3+Math.random()*0.4,
    r:0.2+Math.random()*0.25, color:NEBULA_COLORS[i],
    phaseX:Math.random()*Math.PI*2, phaseY:Math.random()*Math.PI*2,
    speedX:0.15+Math.random()*0.2, speedY:0.12+Math.random()*0.15,
    driftAmp:0.03+Math.random()*0.04,
  }});
}}

// Stars
const stars=[];
for(let i=0;i<STAR_COUNT;i++) {{
  stars.push({{
    x:Math.random(), y:Math.random(),
    size:0.3+Math.random()*1.2,
    brightness:0.2+Math.random()*0.6,
    twinkleSpeed:0.5+Math.random()*1.5,
    twinklePhase:Math.random()*Math.PI*2,
  }});
}}

function drawBackground(t) {{
  const w=bgCanvas.width,h=bgCanvas.height;
  bgCtx.fillStyle='{bg_hex}';
  bgCtx.fillRect(0,0,w,h);
  for(const cloud of nebulaClouds) {{
    const cx=(cloud.x+Math.sin(t*cloud.speedX+cloud.phaseX)*cloud.driftAmp)*w;
    const cy=(cloud.y+Math.sin(t*cloud.speedY+cloud.phaseY)*cloud.driftAmp)*h;
    const r=cloud.r*Math.min(w,h);
    const grad=bgCtx.createRadialGradient(cx,cy,0,cx,cy,r);
    grad.addColorStop(0,cloud.color); grad.addColorStop(1,'rgba(0,0,0,0)');
    bgCtx.fillStyle=grad; bgCtx.fillRect(0,0,w,h);
  }}
  // Vignette
  const vr=Math.min(w,h)*0.7;
  const vg=bgCtx.createRadialGradient(w/2,h/2,vr*0.3,w/2,h/2,vr);
  vg.addColorStop(0,'rgba(7,5,15,0)'); vg.addColorStop(1,'rgba(7,5,15,0.65)');
  bgCtx.fillStyle=vg; bgCtx.fillRect(0,0,w,h);
}}

function drawStars(t) {{
  const w=starCanvas.width,h=starCanvas.height;
  starCtx.clearRect(0,0,w,h);
  for(const s of stars) {{
    const b=s.brightness*(0.5+0.5*Math.sin(t*s.twinkleSpeed+s.twinklePhase));
    starCtx.beginPath();
    starCtx.arc(s.x*w,s.y*h,s.size,0,Math.PI*2);
    starCtx.fillStyle=`rgba(255,240,216,${{b}})`;
    starCtx.fill();
  }}
}}

// ═══ THREE.JS SETUP ═══
const threeCanvas=document.getElementById('three-canvas');
const cont=document.getElementById('container');
const scene=new THREE.Scene();
const frustum=6;
const camera=new THREE.OrthographicCamera(-frustum,frustum,frustum,-frustum,0.1,100);
camera.position.z=10;
const renderer=new THREE.WebGLRenderer({{canvas:threeCanvas,alpha:true,antialias:true}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setClearColor(0x000000,0);

function resizeRenderer() {{
  renderer.setSize(cont.clientWidth,cont.clientHeight);
  resizeCanvases();
}}
resizeRenderer();
window.addEventListener('resize',resizeRenderer);

// ═══ LOGO GROUP ═══
const logoGroup=new THREE.Group();
logoGroup.position.y=CENTER_OFFSET_Y;
scene.add(logoGroup);

// ── Circle fill ──
const circleFill=createCircle(0,0,RING.fillR,RING.fillColor,1.0,64);
circleFill.position.z=-0.5;
logoGroup.add(circleFill);

// ── Ring bands ──
for(const band of RING.bands) {{
  const geo=new THREE.RingGeometry(band.innerR,band.outerR,96);
  const mat=new THREE.MeshBasicMaterial({{color:RING.color,transparent:true,opacity:band.op,side:THREE.DoubleSide}});
  logoGroup.add(new THREE.Mesh(geo,mat));
}}

// ── Shimmer arcs ──
const shimmerArcs=[];
for(let i=0;i<{shimmer_cfg.get('count', 3)};i++) {{
  const geo=new THREE.RingGeometry(RING.bands[0].innerR,RING.bands[3].outerR,32,1,0,Math.PI*{shimmer_cfg.get('arc_sweep_fraction', 0.3)});
  const mat=new THREE.MeshBasicMaterial({{color:PAL.{shimmer_cfg.get('color', 'warm_white')},transparent:true,opacity:{shimmer_cfg.get('base_opacity', 0.04)},side:THREE.DoubleSide}});
  const m=new THREE.Mesh(geo,mat);
  m.rotation.z=(i/{shimmer_cfg.get('count', 3)})*Math.PI*2;
  logoGroup.add(m);
  shimmerArcs.push(m);
}}

// ── Edges (typed opacity) ──
const EDGE_OPACITY = {{contour:1.0, struct:1.0, mesh:0.4, nib:0.5}};
for(const [a,b,etype] of EDGES) {{
  const [x1,y1]=[ NODES[a][0], NODES[a][1] ];
  const [x2,y2]=[ NODES[b][0], NODES[b][1] ];
  const op = EDGE_OPACITY[etype] || 0.4;
  const line=createLine(x1,y1,x2,y2, {layout.get('edge_thickness', palette['sizing']['edge_thickness'])}, PAL.copper, op);
  line.position.z=0.2;
  logoGroup.add(line);
}}

// ── Arcs ──
for(const arc of ARCS) {{
  const main=createArcStrip(arc.pts, arc.mainTh, arc.color, arc.mainOp);
  main.position.z=0.32;
  logoGroup.add(main);
  const bloom=createArcStrip(arc.pts, arc.bloomTh, arc.color, arc.bloomOp);
  bloom.position.z=0.28;
  logoGroup.add(bloom);
}}

// ── Nodes ──
const nodeMeshes=[];
for(let i=0;i<NODES.length;i++) {{
  const [x,y,color,radius,deg]=NODES[i];
  const core=createCircle(x,y,radius,color,0.9,16);
  core.position.z=0.4;
  logoGroup.add(core);
  const glow=createGlow(x,y,radius*{node_glow_scale},color,{node_glow_opacity});
  glow.position.z=0.3;
  logoGroup.add(glow);
  const bloom=createGlow(x,y,radius*{node_bloom_scale},color,{node_bloom_opacity});
  bloom.position.z=0.25;
  logoGroup.add(bloom);
  nodeMeshes.push({{core,glow,bloom,x,y,color,waveIntensity:0}});
}}

// ── Nib ──
for(const l of NIB.fan) {{
  const m=createLine(l.x1,l.y1,l.x2,l.y2,l.th,l.color,l.op);
  m.position.z=0.5; logoGroup.add(m);
}}
for(const l of NIB.outline) {{
  const m=createLine(l.x1,l.y1,l.x2,l.y2,l.th,l.color,l.op);
  m.position.z=0.51; logoGroup.add(m);
}}
{{ const l=NIB.center;
  const m=createLine(l.x1,l.y1,l.x2,l.y2,l.th,l.color,l.op);
  m.position.z=0.52; logoGroup.add(m);
}}
for(const n of NIB.accents) {{
  const c=createCircle(n.x,n.y,n.r,n.color,0.8,12);
  c.position.z=0.55; logoGroup.add(c);
  const g=createGlow(n.x,n.y,n.r*5,n.color,0.25);
  g.position.z=0.52; logoGroup.add(g);
}}
{{ const b=NIB.ball;
  const c=createCircle(b.x,b.y,b.r,b.color,b.op,16);
  c.position.z=0.6; logoGroup.add(c);
  const g=createGlow(b.x,b.y,b.glowSize,b.glowColor,b.glowOp);
  g.position.z=0.55; logoGroup.add(g);
  const bl=createGlow(b.x,b.y,b.bloomSize,b.bloomColor,b.bloomOp);
  bl.position.z=0.5; logoGroup.add(bl);
}}

// ── Ink drops (pooled) ──
const inkDrops=[];
for(let i=0;i<ANIM.inkDrops.poolSize;i++) {{
  const d=createCircle(0,0,ANIM.inkDrops.radius,ANIM.inkDrops.color,0);
  d.position.z=0.5; logoGroup.add(d);
  inkDrops.push({{mesh:d,active:false,x:NIB.ink.x,y:NIB.ink.y,vx:0,vy:0,life:0,maxLife:0}});
}}
let lastInkSpawn=0;
function spawnInkDrop() {{
  for(const d of inkDrops) {{
    if(!d.active) {{
      d.active=true; d.x=NIB.ink.x+(Math.random()-0.5)*0.06; d.y=NIB.ink.y;
      d.vx=ANIM.inkDrops.vxRange[0]+Math.random()*(ANIM.inkDrops.vxRange[1]-ANIM.inkDrops.vxRange[0]);
      d.vy=ANIM.inkDrops.vyRange[0]+Math.random()*(ANIM.inkDrops.vyRange[1]-ANIM.inkDrops.vyRange[0]);
      d.life=0; d.maxLife=ANIM.inkDrops.lifetimeRange[0]+Math.random()*(ANIM.inkDrops.lifetimeRange[1]-ANIM.inkDrops.lifetimeRange[0]);
      return;
    }}
  }}
}}

// ── Traveling pulses ──
const pulses=[];
for(let i=0;i<ANIM.pulses.count;i++) {{
  const core=createCircle(0,0,ANIM.pulses.radius,ANIM.pulses.color,0);
  core.position.z=0.45; logoGroup.add(core);
  const glow=createGlow(0,0,ANIM.pulses.glowSize,ANIM.pulses.color,0);
  glow.position.z=0.42; logoGroup.add(glow);
  pulses.push({{core,glow,edgeIdx:Math.floor(Math.random()*EDGES.length),
    t:Math.random(),speed:ANIM.pulses.speedRange[0]+Math.random()*(ANIM.pulses.speedRange[1]-ANIM.pulses.speedRange[0])}});
}}

// ── Arc runners ──
const arcRunners=[];
for(let ai=0;ai<ARCS.length;ai++) {{
  for(let j=0;j<ANIM.arcRunners.perArc;j++) {{
    const core=createCircle(0,0,{arc_runner_radius},ARCS[ai].color,0);
    core.position.z=0.5; logoGroup.add(core);
    const trail=[];
    for(let k=0;k<ANIM.arcRunners.trailLength;k++) {{
      const sp=createGlow(0,0,0.18-k*0.03,ARCS[ai].color,0);
      sp.position.z=0.48; logoGroup.add(sp);
      trail.push(sp);
    }}
    arcRunners.push({{core,trail,arcIdx:ai,t:j*0.5+Math.random()*0.3,speed:ANIM.arcRunners.speed,positions:[]}});
  }}
}}

// ── Floating particles ──
const particles=[];
for(let i=0;i<{particle_cfg.get('count', 70)};i++) {{
  const angle=Math.random()*Math.PI*2, dist={particle_cfg.get('min_distance', 0.8)}+Math.random()*{particle_cfg.get('max_distance', 4.4) - particle_cfg.get('min_distance', 0.8)};
  const x=Math.cos(angle)*dist, y=Math.sin(angle)*dist;
  const sz={particle_cfg.get('size_range', [0.012, 0.037])[0]}+Math.random()*{particle_cfg.get('size_range', [0.012, 0.037])[1] - particle_cfg.get('size_range', [0.012, 0.037])[0]};
  const p=createCircle(x,y,sz,PAL.{particle_cfg.get('color', 'copper')},{particle_cfg.get('opacity_range', [0.15, 0.40])[0]}+Math.random()*{particle_cfg.get('opacity_range', [0.15, 0.40])[1] - particle_cfg.get('opacity_range', [0.15, 0.40])[0]});
  p.position.z=0.15; logoGroup.add(p);
  particles.push({{mesh:p,baseX:x,baseY:y,
    dAX:{particle_cfg.get('drift_amplitude', [0.04, 0.16])[0]}+Math.random()*{particle_cfg.get('drift_amplitude', [0.04, 0.16])[1] - particle_cfg.get('drift_amplitude', [0.04, 0.16])[0]},dAY:{particle_cfg.get('drift_amplitude', [0.04, 0.16])[0]}+Math.random()*{particle_cfg.get('drift_amplitude', [0.04, 0.16])[1] - particle_cfg.get('drift_amplitude', [0.04, 0.16])[0]},
    sX:{particle_cfg.get('drift_speed', [0.25, 0.90])[0]}+Math.random()*{particle_cfg.get('drift_speed', [0.25, 0.90])[1] - particle_cfg.get('drift_speed', [0.25, 0.90])[0]},sY:{particle_cfg.get('drift_speed', [0.25, 0.90])[0]}+Math.random()*{particle_cfg.get('drift_speed', [0.25, 0.90])[1] - particle_cfg.get('drift_speed', [0.25, 0.90])[0]},
    pX:Math.random()*Math.PI*2,pY:Math.random()*Math.PI*2}});
}}

// ── Energy rings ──
const energyRings=[];
let lastRingSpawn=0;
function spawnEnergyRing() {{
  const geo=new THREE.RingGeometry(ANIM.energyRings.initialInnerR,ANIM.energyRings.initialOuterR,48);
  const mat=new THREE.MeshBasicMaterial({{color:ANIM.energyRings.color,transparent:true,opacity:ANIM.energyRings.initialOpacity,side:THREE.DoubleSide}});
  const m=new THREE.Mesh(geo,mat);
  m.position.z=0.1; logoGroup.add(m);
  energyRings.push({{mesh:m,scale:1,life:0}});
}}

// ═══ BFS WAVE ═══
let waveTimer=2.0;
function triggerWave(t) {{
  const start=Math.floor(Math.random()*ANIM.wave.nodeCount);
  const queue=[{{node:start,depth:0}}];
  const visited=new Set([start]);
  while(queue.length>0) {{
    const {{node,depth}}=queue.shift();
    nodeMeshes[node].waveStart=t+depth*ANIM.wave.delayPerHop;
    for(const nb of ADJ[node]) {{
      if(!visited.has(nb)) {{ visited.add(nb); queue.push({{node:nb,depth:depth+1}}); }}
    }}
  }}
}}

// ═══ ANIMATION LOOP ═══
const clock=new THREE.Clock();
let prevTime=0;

function animate() {{
  requestAnimationFrame(animate);
  const t=clock.getElapsedTime();
  const dt=Math.min(t-prevTime,0.05);
  prevTime=t;

  drawBackground(t);
  drawStars(t);

  // Breathing
  const bs=1.0+Math.sin(t*ANIM.breathing.frequency*2*Math.PI)*ANIM.breathing.amplitude;
  logoGroup.scale.set(bs,bs,1);

  // Shimmer
  for(let i=0;i<shimmerArcs.length;i++) {{
    shimmerArcs[i].rotation.z+={shimmer_cfg.get('rotation_speed', 0.0015)}*(i%2===0?1:-1);
    shimmerArcs[i].material.opacity={shimmer_cfg.get('base_opacity', 0.035)}+Math.sin(t*0.5+i*2)*{shimmer_cfg.get('opacity_amplitude', 0.02)};
  }}

  // Wave
  waveTimer+=dt;
  if(waveTimer>ANIM.wave.interval) {{ waveTimer=0; triggerWave(t); }}
  for(const nm of nodeMeshes) {{
    if(nm.waveStart!==undefined&&t>=nm.waveStart) {{
      const el=t-nm.waveStart;
      if(el<ANIM.wave.duration) {{
        const p=el/ANIM.wave.duration;
        nm.waveIntensity=Math.max(0,Math.pow(2,-10*p)*Math.sin((p-0.1)*5*Math.PI)+1)*ANIM.wave.intensity;
      }} else {{
        nm.waveIntensity*=0.93;
        if(nm.waveIntensity<0.01) {{ nm.waveIntensity=0; nm.waveStart=undefined; }}
      }}
    }}
    const s=1.0+(nm.waveIntensity||0)*0.5;
    nm.core.scale.set(s,s,1); nm.glow.scale.set(s,s,1);
    nm.core.material.opacity=0.9+(nm.waveIntensity||0)*0.1;
    nm.glow.material.opacity=0.3+(nm.waveIntensity||0)*0.35;
  }}

  // Pulses
  for(const pulse of pulses) {{
    pulse.t+=pulse.speed*dt;
    if(pulse.t>=1) {{ pulse.t=0; pulse.edgeIdx=Math.floor(Math.random()*EDGES.length); }}
    const [a,b]=EDGES[pulse.edgeIdx];
    const px=NODES[a][0]+(NODES[b][0]-NODES[a][0])*pulse.t;
    const py=NODES[a][1]+(NODES[b][1]-NODES[a][1])*pulse.t;
    pulse.core.position.set(px,py,0.45);
    pulse.glow.position.set(px,py,0.42);
    const f=pulse.t<ANIM.pulses.fadeIn?pulse.t/ANIM.pulses.fadeIn:
             (pulse.t>ANIM.pulses.fadeOut?(1-pulse.t)/(1-ANIM.pulses.fadeOut):1);
    pulse.core.material.opacity=Math.max(0,f*ANIM.pulses.corePeakOp);
    pulse.glow.material.opacity=Math.max(0,f*ANIM.pulses.glowPeakOp);
  }}

  // Arc runners
  for(const runner of arcRunners) {{
    runner.t+=runner.speed*dt;
    if(runner.t>1) runner.t-=1;
    const arc=ARCS[runner.arcIdx];
    const idx=Math.min(Math.floor(runner.t*arc.pts.length),arc.pts.length-1);
    const [rx,ry]=arc.pts[idx];
    runner.positions.unshift({{x:rx,y:ry}});
    if(runner.positions.length>5) runner.positions.pop();
    runner.core.position.set(rx,ry,0.5);
    const mf=1.0-Math.abs(runner.t-ANIM.arcRunners.opacityPeakAt)*1.6;
    runner.core.material.opacity=Math.max(0,mf*ANIM.arcRunners.corePeakOp);
    for(let k=0;k<runner.trail.length;k++) {{
      const pi=Math.min(k+1,runner.positions.length-1);
      const pos=runner.positions[pi];
      if(pos) {{
        runner.trail[k].position.set(pos.x,pos.y,0.48);
        runner.trail[k].material.opacity=Math.max(0,mf*ANIM.arcRunners.trailPeakOp*(1-k/runner.trail.length));
      }}
    }}
  }}

  // Ink drops
  const spawnInt=ANIM.inkDrops.spawnRate.min_interval+Math.random()*(ANIM.inkDrops.spawnRate.max_interval-ANIM.inkDrops.spawnRate.min_interval);
  if(t-lastInkSpawn>spawnInt) {{ spawnInkDrop(); lastInkSpawn=t; }}
  for(const d of inkDrops) {{
    if(!d.active) continue;
    d.life+=dt;
    d.vy+=ANIM.inkDrops.gravity*dt;
    d.vx*=ANIM.inkDrops.drag; d.vy*=ANIM.inkDrops.drag;
    d.x+=d.vx*dt; d.y+=d.vy*dt;
    d.mesh.position.set(d.x,d.y,0.5);
    const lr=d.life/d.maxLife;
    d.mesh.material.opacity=Math.max(0,
      lr<ANIM.inkDrops.fadeInFrac?lr/ANIM.inkDrops.fadeInFrac*ANIM.inkDrops.peakOp:
      ANIM.inkDrops.peakOp*(1-(lr-ANIM.inkDrops.fadeInFrac)/(1-ANIM.inkDrops.fadeInFrac)));
    if(d.life>=d.maxLife) {{ d.active=false; d.mesh.material.opacity=0; }}
  }}

  // Particles
  for(const p of particles) {{
    p.mesh.position.set(
      p.baseX+Math.sin(t*p.sX+p.pX)*p.dAX,
      p.baseY+Math.sin(t*p.sY+p.pY)*p.dAY, 0.15);
  }}

  // Energy rings
  if(t-lastRingSpawn>ANIM.energyRings.interval) {{ spawnEnergyRing(); lastRingSpawn=t; }}
  for(let i=energyRings.length-1;i>=0;i--) {{
    const ring=energyRings[i];
    ring.life+=dt;
    const s=1+ring.life*ANIM.energyRings.expansionRate;
    ring.mesh.scale.set(s,s,1);
    ring.mesh.material.opacity=Math.max(0,ANIM.energyRings.initialOpacity*(1-ring.life/ANIM.energyRings.fadeDuration));
    if(ring.life>ANIM.energyRings.fadeDuration) {{
      logoGroup.remove(ring.mesh);
      ring.mesh.geometry.dispose(); ring.mesh.material.dispose();
      energyRings.splice(i,1);
    }}
  }}

  renderer.render(scene,camera);
}}

drawBackground(0);
drawStars(0);
animate();
}})();
</script>
</body>
</html>'''


# ──────────────────────────────────────────────
# Main builder
# ──────────────────────────────────────────────

def build_render(
    palette: dict, layout: dict, animations: dict
) -> str:
    """Generate the complete HTML string."""
    return _build_html(palette, layout, animations)


def write_render(
    palette: dict, layout: dict, animations: dict
) -> Path:
    html = build_render(palette, layout, animations)
    out_dir = Path(__file__).parent.parent.parent / "build" / "logos"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "p_logo_pipeline.html"
    with open(out_path, "w") as f:
        f.write(html)
    return out_path


def main() -> int:
    build_dir = Path(__file__).parent / "build"
    deps = {}
    for name in ("palette.json", "layout.json", "animations.json"):
        path = build_dir / name
        if not path.exists():
            print(f"ERROR: {path} not found.", file=sys.stderr)
            return 1
        with open(path) as f:
            deps[name] = json.load(f)

    palette = deps["palette.json"]
    layout = deps["layout.json"]
    animations = deps["animations.json"]

    errors = validate(palette, layout, animations)
    if errors:
        print("RENDER VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    out_path = write_render(palette, layout, animations)
    size_kb = out_path.stat().st_size / 1024
    print(f"p_logo_pipeline.html written to {out_path} ({size_kb:.1f} KB)")
    print("  Validation: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
