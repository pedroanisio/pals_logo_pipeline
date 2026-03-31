"""
PAL's Notes Logo Pipeline — Overlay Renderer

Produces a single HTML showing both planes:
  Phase 1 (0–4s):   Plane A draws in — construction circles, squares, points
  Phase 2 (4–8s):   Plane B highlights — selected nodes pulse, edges appear
  Phase 3 (8–12s):  Plane A fades out, Plane B solidifies
  Phase 4 (12s+):   Normal logo animation runs

Input:  build/palette.json, point_field.json, projection.json,
        layout.json, animations.json
Output: build/logo_overlay.html
"""

from __future__ import annotations
import json, math, sys
from pathlib import Path


def build_overlay() -> str:
    build_dir = Path(__file__).parent / "build"
    
    with open(build_dir / "palette.json") as f: palette = json.load(f)
    with open(build_dir / "point_field.json") as f: field = json.load(f)
    with open(build_dir / "projection.json") as f: proj = json.load(f)
    with open(build_dir / "layout.json") as f: layout = json.load(f)
    with open(build_dir / "animations.json") as f: anims = json.load(f)

    # ── Extract data ──
    colors = palette["colors"]
    bg_hex = colors["background"]["hex"]
    meta = field["metadata"]
    
    co = layout["center_offset"]
    
    # Construction shapes for Plane A rendering
    shapes_js = json.dumps(field["shapes"])
    points_js = json.dumps(field["points"])
    
    # Projection mapping: which field points became nodes
    selected_points = {n["source_point"]: n["index"] for n in proj["nodes"]}
    selected_js = json.dumps(selected_points)
    
    # Projection edges
    proj_edges_js = json.dumps(proj["edges"])
    
    # Node data from layout (with offset applied)
    layout_nodes = [el for el in layout["elements"] if el["type"] == "node"]
    layout_nodes.sort(key=lambda n: n["index"])
    nodes_js = json.dumps([{"x": n["x"], "y": n["y"], "color": n["color"],
                            "radius": n["radius"], "degree": n["degree"]}
                           for n in layout_nodes])
    
    # Edges from layout
    layout_edges = [el for el in layout["elements"] if el["type"] == "edge"]
    edges_js = json.dumps([{"x1": e["x1"], "y1": e["y1"], "x2": e["x2"], "y2": e["y2"]}
                           for e in layout_edges])
    
    # Arcs from layout
    layout_arcs = [el for el in layout["elements"] if el["type"] == "arc"]
    layout_arcs.sort(key=lambda a: a["index"])
    
    # Nib elements
    nib_fans = [el for el in layout["elements"] if el["type"] == "nib_fan_line"]
    nib_outlines = [el for el in layout["elements"] if el["type"] == "nib_outline_line"]
    nib_center = [el for el in layout["elements"] if el["type"] == "nib_center_line"]
    nib_accents = [el for el in layout["elements"] if el["type"] == "nib_accent_node"]
    nib_ball = [el for el in layout["elements"] if el["type"] == "junction_ball"]
    
    all_nib = nib_fans + nib_outlines + nib_center + nib_accents + nib_ball
    nib_js = json.dumps(all_nib)
    
    # Arc data for rendering
    arcs_render = []
    for arc in layout_arcs:
        arcs_render.append({
            "cx": arc["cx"], "cy": arc["cy"], "radius": arc["radius"],
            "color": arc["color"],
            "mainTh": arc["main_thickness"], "mainOp": arc["main_opacity"],
            "pts": [[round(p["x"],4), round(p["y"],4),
                     round(p.get("nx",0),4), round(p.get("ny",0),4)]
                    for p in arc["points"]],
        })
    arcs_js = json.dumps(arcs_render)
    
    # Ring data
    ring = layout["ring"]
    ring_js = json.dumps(ring)
    
    # Animation params
    wave = anims["systems"]["wave"]
    adj_js = json.dumps(wave["adjacency"])
    
    supp = anims.get("supplementary", {})
    particle_count = supp.get("particles", {}).get("count", 70)
    shimmer_count = supp.get("shimmer", {}).get("count", 3)
    
    # Color hex map for JS
    color_map = {name: c["hex"].lstrip("#") for name, c in colors.items()}
    color_map_js = json.dumps(color_map)

    star_count = palette["stars"]["count"]
    nebula_colors_js = json.dumps([
        f"rgba({colors[nc['color']]['rgb'][0]},{colors[nc['color']]['rgb'][1]},{colors[nc['color']]['rgb'][2]},{nc['alpha']})"
        for nc in palette["nebula"]["colors"]
    ])

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PAL's Notes — Construction Overlay</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  background: {bg_hex};
  overflow: hidden;
  width: 100vw; height: 100vh;
  display: flex; align-items: center; justify-content: center;
}}
#container {{
  position: relative;
  width: 100vmin; height: 100vmin;
  max-width: 900px; max-height: 900px;
}}
canvas, #three-canvas {{
  position: absolute; top:0; left:0; width:100%; height:100%;
}}
#bg-canvas {{ z-index:1; }}
#star-canvas {{ z-index:2; }}
#construct-canvas {{ z-index:3; }}
#three-canvas {{ z-index:4; }}
#brand-text {{
  position:absolute; bottom:4%; width:100%; text-align:center;
  z-index:5; font-family:'Georgia',serif; font-size:1.6vmin;
  letter-spacing:0.45em; text-transform:uppercase;
  color: #{color_map["rose_gold"]}; opacity:0;
  animation: brandIn 2s ease 13s forwards;
}}
@keyframes brandIn {{ to {{ opacity:0.9; }} }}
#phase-label {{
  position:absolute; top:3%; left:50%; transform:translateX(-50%);
  z-index:6; font-family:'Georgia',serif; font-size:1.4vmin;
  letter-spacing:0.3em; text-transform:uppercase;
  color: #{color_map["rose_gold"]}; opacity:0;
  transition: opacity 1s ease;
}}
</style>
</head>
<body>
<div id="container">
  <canvas id="bg-canvas"></canvas>
  <canvas id="star-canvas"></canvas>
  <canvas id="construct-canvas"></canvas>
  <canvas id="three-canvas"></canvas>
  <div id="brand-text">PAL\\'s Notes</div>
  <div id="phase-label"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{
"use strict";

// ═══ DATA ═══
const CMAP = {color_map_js};
const FIELD_SHAPES = {shapes_js};
const FIELD_POINTS = {points_js};
const SELECTED = {selected_js};
const PROJ_EDGES = {proj_edges_js};
const NODES = {nodes_js};
const EDGES = {edges_js};
const ARCS = {arcs_js};
const NIB = {nib_js};
const RING = {ring_js};
const ADJ = {adj_js};
const NEBULA_COLORS = {nebula_colors_js};
const CO_Y = {co["y"]};

function hexC(name) {{ return parseInt(CMAP[name] || "6EC4A8", 16); }}
function hexS(name) {{ return "#" + (CMAP[name] || "6EC4A8"); }}

// ═══ SIZING ═══
const cont = document.getElementById('container');
const bgC = document.getElementById('bg-canvas');
const starC = document.getElementById('star-canvas');
const conC = document.getElementById('construct-canvas');
const bgCtx = bgC.getContext('2d');
const starCtx = starC.getContext('2d');
const conCtx = conC.getContext('2d');
const phaseLabel = document.getElementById('phase-label');

function resize() {{
  const w = cont.clientWidth, h = cont.clientHeight;
  [bgC,starC,conC].forEach(c => {{ c.width=w; c.height=h; }});
}}
resize();

// ═══ COORDINATE TRANSFORM ═══
// Map logo space (≈ -5..5) to canvas pixels
function toCanvasX(x) {{ return (x / 12 + 0.5) * conC.width; }}
function toCanvasY(y) {{ return (0.5 - y / 12) * conC.height; }}
function toCanvasR(r) {{ return r / 12 * conC.width; }}

// ═══ BACKGROUND ═══
const nebClouds = [];
for (let i=0; i<7; i++) {{
  nebClouds.push({{
    x:0.3+Math.random()*0.4, y:0.3+Math.random()*0.4,
    r:0.2+Math.random()*0.25, color:NEBULA_COLORS[i],
    px:Math.random()*Math.PI*2, py:Math.random()*Math.PI*2,
    sx:0.15+Math.random()*0.2, sy:0.12+Math.random()*0.15,
    da:0.03+Math.random()*0.04,
  }});
}}
const stars = [];
for (let i=0; i<{star_count}; i++) {{
  stars.push({{ x:Math.random(), y:Math.random(), s:0.3+Math.random()*1.2,
    b:0.2+Math.random()*0.6, ts:0.5+Math.random()*1.5, tp:Math.random()*Math.PI*2 }});
}}

function drawBg(t) {{
  const w=bgC.width, h=bgC.height;
  bgCtx.fillStyle='{bg_hex}'; bgCtx.fillRect(0,0,w,h);
  for (const c of nebClouds) {{
    const cx=(c.x+Math.sin(t*c.sx+c.px)*c.da)*w;
    const cy=(c.y+Math.sin(t*c.sy+c.py)*c.da)*h;
    const g=bgCtx.createRadialGradient(cx,cy,0,cx,cy,c.r*Math.min(w,h));
    g.addColorStop(0,c.color); g.addColorStop(1,'rgba(0,0,0,0)');
    bgCtx.fillStyle=g; bgCtx.fillRect(0,0,w,h);
  }}
  const vr=Math.min(w,h)*0.7;
  const vg=bgCtx.createRadialGradient(w/2,h/2,vr*0.3,w/2,h/2,vr);
  vg.addColorStop(0,'rgba(7,5,15,0)'); vg.addColorStop(1,'rgba(7,5,15,0.65)');
  bgCtx.fillStyle=vg; bgCtx.fillRect(0,0,w,h);
}}

function drawStars(t) {{
  const w=starC.width, h=starC.height;
  starCtx.clearRect(0,0,w,h);
  for (const s of stars) {{
    const b=s.b*(0.5+0.5*Math.sin(t*s.ts+s.tp));
    starCtx.beginPath(); starCtx.arc(s.x*w,s.y*h,s.s,0,Math.PI*2);
    starCtx.fillStyle=`rgba(255,240,216,${{b}})`; starCtx.fill();
  }}
}}

// ═══ PLANE A: CONSTRUCTION DRAWING (2D Canvas) ═══
function drawConstruction(t, alpha) {{
  const ctx = conCtx;
  const w = conC.width, h = conC.height;
  ctx.clearRect(0,0,w,h);
  if (alpha < 0.01) return;

  ctx.globalAlpha = alpha;
  ctx.lineWidth = 1;

  // Draw construction circles
  const circleShapes = ["Circ.A", "Circ.D", "Circ.Mid"];
  const circleColors = ["#D09058", "#6EC4A8", "#F0B85C"];
  circleShapes.forEach((name, i) => {{
    const s = FIELD_SHAPES[name];
    if (!s) return;
    ctx.beginPath();
    ctx.strokeStyle = circleColors[i];
    ctx.setLineDash([4, 4]);
    ctx.arc(toCanvasX(s.center.x), toCanvasY(s.center.y + CO_Y),
            toCanvasR(s.radius), 0, Math.PI*2);
    ctx.stroke();
    ctx.setLineDash([]);
  }});

  // Draw vertex circles
  for (let i=1; i<=4; i++) {{
    const s = FIELD_SHAPES["Circ.V"+i];
    if (!s) continue;
    ctx.beginPath();
    ctx.strokeStyle = `rgba(123,168,232,${{alpha*0.5}})`;
    ctx.setLineDash([3, 5]);
    ctx.arc(toCanvasX(s.center.x), toCanvasY(s.center.y + CO_Y),
            toCanvasR(s.radius), 0, Math.PI*2);
    ctx.stroke();
    ctx.setLineDash([]);
  }}

  // Draw Square.B
  const sqB = FIELD_SHAPES["Square.B"];
  if (sqB) {{
    const v = sqB.vertices;
    ctx.beginPath();
    ctx.strokeStyle = `rgba(212,151,110,${{alpha*0.4}})`;
    ctx.setLineDash([6, 4]);
    ctx.moveTo(toCanvasX(v.UL.x), toCanvasY(v.UL.y + CO_Y));
    ctx.lineTo(toCanvasX(v.UR.x), toCanvasY(v.UR.y + CO_Y));
    ctx.lineTo(toCanvasX(v.LR.x), toCanvasY(v.LR.y + CO_Y));
    ctx.lineTo(toCanvasX(v.LL.x), toCanvasY(v.LL.y + CO_Y));
    ctx.closePath(); ctx.stroke();
    ctx.setLineDash([]);
  }}

  // Draw Square.C
  const sqC = FIELD_SHAPES["Square.C"];
  if (sqC) {{
    const v = sqC.vertices;
    const keys = ["V1_TR","V2_TL","V3_BL","V4_BR"];
    ctx.beginPath();
    ctx.strokeStyle = `rgba(110,196,168,${{alpha*0.4}})`;
    ctx.setLineDash([5, 3]);
    keys.forEach((k,i) => {{
      const fn = i===0 ? 'moveTo' : 'lineTo';
      ctx[fn](toCanvasX(v[k].x), toCanvasY(v[k].y + CO_Y));
    }});
    ctx.closePath(); ctx.stroke();
    ctx.setLineDash([]);
  }}

  // Draw ALL field points (small dots)
  const ptKeys = Object.keys(FIELD_POINTS);
  ptKeys.forEach((name, i) => {{
    const pt = FIELD_POINTS[name];
    const isSelected = SELECTED[name] !== undefined;
    const cx = toCanvasX(pt.x);
    const cy = toCanvasY(pt.y + CO_Y);

    // Stagger appearance
    const delay = i * 0.06;
    const ptAlpha = Math.max(0, Math.min(1, (t - delay) * 0.8)) * alpha;
    if (ptAlpha < 0.01) return;

    ctx.globalAlpha = ptAlpha;

    if (isSelected) {{
      // Selected points get a highlight ring
      ctx.beginPath();
      ctx.strokeStyle = '#F0B85C';
      ctx.lineWidth = 2;
      ctx.arc(cx, cy, 6, 0, Math.PI*2);
      ctx.stroke();
      ctx.lineWidth = 1;
    }}

    // Point dot
    ctx.beginPath();
    ctx.fillStyle = isSelected ? '#FFF0D8' : `rgba(110,196,168,${{ptAlpha*0.7}})`;
    ctx.arc(cx, cy, isSelected ? 3 : 2, 0, Math.PI*2);
    ctx.fill();

    // Label (only during construction phase)
    if (alpha > 0.3 && ptAlpha > 0.5) {{
      ctx.font = `${{Math.max(8, conC.width * 0.009)}}px Georgia`;
      ctx.fillStyle = `rgba(212,151,110,${{ptAlpha*0.5}})`;
      ctx.textAlign = 'left';
      ctx.fillText(name.replace('P.',''), cx + 6, cy - 4);
    }}
  }});

  // Draw projection edges (connections between selected points)
  if (t > 5) {{
    const edgeAlpha = Math.min(1, (t - 5) * 0.5) * alpha;
    ctx.globalAlpha = edgeAlpha;
    ctx.strokeStyle = `rgba(110,196,168,${{edgeAlpha*0.3}})`;
    ctx.lineWidth = 1;
    PROJ_EDGES.forEach(([a,b]) => {{
      const na = NODES[a], nb = NODES[b];
      ctx.beginPath();
      ctx.moveTo(toCanvasX(na.x), toCanvasY(na.y));
      ctx.lineTo(toCanvasX(nb.x), toCanvasY(nb.y));
      ctx.stroke();
    }});
  }}

  ctx.globalAlpha = 1;
}}

// ═══ THREE.JS SETUP (PLANE B) ═══
const threeCanvas = document.getElementById('three-canvas');
const scene = new THREE.Scene();
const frustum = 6;
const camera = new THREE.OrthographicCamera(-frustum,frustum,frustum,-frustum,0.1,100);
camera.position.z = 10;
const renderer = new THREE.WebGLRenderer({{canvas:threeCanvas,alpha:true,antialias:true}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setClearColor(0x000000,0);

function resizeR() {{ renderer.setSize(cont.clientWidth,cont.clientHeight); resize(); }}
resizeR(); window.addEventListener('resize',resizeR);

// Helpers
function createLine(x1,y1,x2,y2,th,color,op) {{
  const dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy);
  if(len<0.001) return new THREE.Group();
  const nx=-dy/len*th/2,ny=dx/len*th/2;
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array([
    x1+nx,y1+ny,0,x1-nx,y1-ny,0,x2+nx,y2+ny,0,x2-nx,y2-ny,0]),3));
  geo.setIndex([0,1,2,1,3,2]);
  return new THREE.Mesh(geo,new THREE.MeshBasicMaterial({{color,transparent:true,opacity:op,side:THREE.DoubleSide}}));
}}
function createCircle(x,y,r,color,op,segs) {{
  const m=new THREE.Mesh(new THREE.CircleGeometry(r,segs||24),
    new THREE.MeshBasicMaterial({{color,transparent:true,opacity:op||1}}));
  m.position.set(x,y,0); return m;
}}
function createGlow(x,y,size,color,op) {{
  const c=document.createElement('canvas'); c.width=64;c.height=64;
  const ctx=c.getContext('2d');
  const r=(color>>16)/255,g=((color>>8)&0xFF)/255,b=(color&0xFF)/255;
  const gr=ctx.createRadialGradient(32,32,0,32,32,32);
  gr.addColorStop(0,`rgba(${{r*255|0}},${{g*255|0}},${{b*255|0}},${{op||0.5}})`);
  gr.addColorStop(0.4,`rgba(${{r*255|0}},${{g*255|0}},${{b*255|0}},${{(op||0.5)*0.35}})`);
  gr.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=gr; ctx.fillRect(0,0,64,64);
  const mat=new THREE.SpriteMaterial({{map:new THREE.CanvasTexture(c),transparent:true,depthWrite:false}});
  const s=new THREE.Sprite(mat); s.position.set(x,y,0.1); s.scale.set(size,size,1); return s;
}}
function createArcStrip(pts,th,color,op) {{
  const pos=[],idx=[];
  for(let i=0;i<pts.length;i++) {{
    const [x,y,nx,ny]=pts[i];
    pos.push(x+nx*th/2,y+ny*th/2,0,x-nx*th/2,y-ny*th/2,0);
    if(i<pts.length-1) {{ const vi=i*2; idx.push(vi,vi+1,vi+2,vi+1,vi+3,vi+2); }}
  }}
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(pos),3));
  geo.setIndex(idx);
  return new THREE.Mesh(geo,new THREE.MeshBasicMaterial({{color,transparent:true,opacity:op,side:THREE.DoubleSide}}));
}}

// ═══ BUILD LOGO (Plane B objects) ═══
const logoGroup = new THREE.Group();
scene.add(logoGroup);

// Circle fill + ring
const cfill = createCircle(0,0,RING.fill_radius,hexC(RING.fill_color),1,64);
cfill.position.z=-0.5; logoGroup.add(cfill);
RING.bands.forEach(b => {{
  const m=new THREE.Mesh(new THREE.RingGeometry(b.inner_r,b.outer_r,96),
    new THREE.MeshBasicMaterial({{color:hexC(RING.color),transparent:true,opacity:b.opacity,side:THREE.DoubleSide}}));
  logoGroup.add(m);
}});

// Shimmer
const shimmerArcs=[];
for(let i=0;i<{shimmer_count};i++) {{
  const m=new THREE.Mesh(new THREE.RingGeometry(RING.bands[0].inner_r,RING.bands[3].outer_r,32,1,0,Math.PI*0.3),
    new THREE.MeshBasicMaterial({{color:hexC('warm_white'),transparent:true,opacity:0.04,side:THREE.DoubleSide}}));
  m.rotation.z=(i/{shimmer_count})*Math.PI*2; logoGroup.add(m); shimmerArcs.push(m);
}}

// Edges
EDGES.forEach(e => {{
  const m=createLine(e.x1,e.y1,e.x2,e.y2,0.04,hexC('copper'),0.4);
  m.position.z=0.2; logoGroup.add(m);
}});

// Arcs
ARCS.forEach(a => {{
  const m=createArcStrip(a.pts,a.mainTh,hexC(a.color),a.mainOp);
  m.position.z=0.32; logoGroup.add(m);
  const bl=createArcStrip(a.pts,a.mainTh*3,hexC(a.color),a.mainOp*0.18);
  bl.position.z=0.28; logoGroup.add(bl);
}});

// Nodes
const nodeMeshes=[];
NODES.forEach((n,i) => {{
  const color=hexC(n.color);
  const core=createCircle(n.x,n.y,n.radius,color,0.9,16); core.position.z=0.4; logoGroup.add(core);
  const glow=createGlow(n.x,n.y,n.radius*7,color,0.3); glow.position.z=0.3; logoGroup.add(glow);
  const bloom=createGlow(n.x,n.y,n.radius*12,color,0.1); bloom.position.z=0.25; logoGroup.add(bloom);
  nodeMeshes.push({{core,glow,bloom,x:n.x,y:n.y,color,waveIntensity:0}});
}});

// Nib
NIB.forEach(el => {{
  const c = hexC(el.color || 'copper');
  if (el.type && el.type.includes('line')) {{
    const m=createLine(el.x1,el.y1,el.x2,el.y2,el.thickness||0.03,c,el.opacity||0.5);
    m.position.z=el.z||0.5; logoGroup.add(m);
  }} else if (el.type==='nib_accent_node') {{
    const m=createCircle(el.x,el.y,el.radius,c,0.8,12); m.position.z=0.55; logoGroup.add(m);
    const g=createGlow(el.x,el.y,el.radius*5,c,0.25); g.position.z=0.52; logoGroup.add(g);
  }} else if (el.type==='junction_ball') {{
    const m=createCircle(el.x,el.y,el.radius,hexC('warm_white'),0.95,16); m.position.z=0.6; logoGroup.add(m);
    const g=createGlow(el.x,el.y,0.8,hexC('warm_white'),0.45); g.position.z=0.55; logoGroup.add(g);
    const bl=createGlow(el.x,el.y,1.6,hexC('amber'),0.15); bl.position.z=0.5; logoGroup.add(bl);
  }}
}});

// Ink drops
const inkOrigin = NIB.find(e=>e.type==='ink_origin') || {{x:-1,y:-3.4}};
const inkDrops=[];
for(let i=0;i<25;i++) {{
  const d=createCircle(0,0,0.035,hexC('rose_gold'),0); d.position.z=0.5; logoGroup.add(d);
  inkDrops.push({{mesh:d,active:false,x:0,y:0,vx:0,vy:0,life:0,maxLife:0}});
}}
let lastInk=0;

// Pulses
const pulses=[];
for(let i=0;i<12;i++) {{
  const core=createCircle(0,0,0.045,hexC('copper'),0); core.position.z=0.45; logoGroup.add(core);
  const glow=createGlow(0,0,0.35,hexC('copper'),0); glow.position.z=0.42; logoGroup.add(glow);
  pulses.push({{core,glow,edgeIdx:Math.floor(Math.random()*EDGES.length),t:Math.random(),speed:0.12+Math.random()*0.18}});
}}

// Particles
for(let i=0;i<{particle_count};i++) {{
  const a=Math.random()*Math.PI*2, d=0.8+Math.random()*3.6;
  const p=createCircle(Math.cos(a)*d,Math.sin(a)*d,0.012+Math.random()*0.025,hexC('copper'),0.15+Math.random()*0.25);
  p.position.z=0.15; logoGroup.add(p);
}}

// Energy rings
const energyRings=[]; let lastRing=0;

// ═══ PHASE MANAGEMENT ═══
const PHASE_TIMES = {{ constructIn: 0, highlight: 4, crossfade: 8, logoFull: 12 }};

function getPhaseAlphas(t) {{
  let planeA, planeB;
  if (t < PHASE_TIMES.constructIn + 0.5) {{
    planeA = 0; planeB = 0;
  }} else if (t < PHASE_TIMES.highlight) {{
    planeA = Math.min(1, (t - 0.5) * 0.4);
    planeB = 0;
  }} else if (t < PHASE_TIMES.crossfade) {{
    planeA = 1;
    planeB = Math.min(0.6, (t - PHASE_TIMES.highlight) * 0.15);
  }} else if (t < PHASE_TIMES.logoFull) {{
    const p = (t - PHASE_TIMES.crossfade) / (PHASE_TIMES.logoFull - PHASE_TIMES.crossfade);
    planeA = 1 - p;
    planeB = 0.6 + p * 0.4;
  }} else {{
    planeA = 0;
    planeB = 1;
  }}
  return {{ planeA, planeB }};
}}

function getPhaseLabel(t) {{
  if (t < 0.5) return '';
  if (t < PHASE_TIMES.highlight) return 'PLANE A — CONSTRUCTION FIELD';
  if (t < PHASE_TIMES.crossfade) return 'PLANE B — PROJECTION';
  if (t < PHASE_TIMES.logoFull) return 'MATERIALIZING';
  return '';
}}

// ═══ WAVE ═══
let waveTimer = 99;
function triggerWave(t) {{
  const start=Math.floor(Math.random()*23);
  const queue=[{{node:start,depth:0}}], visited=new Set([start]);
  while(queue.length>0) {{
    const {{node,depth}}=queue.shift();
    nodeMeshes[node].waveStart=t+depth*0.1;
    for(const nb of ADJ[node]) {{ if(!visited.has(nb)) {{ visited.add(nb); queue.push({{node:nb,depth:depth+1}}); }} }}
  }}
}}

// ═══ ANIMATION LOOP ═══
const clock = new THREE.Clock();
let prevTime = 0;

function animate() {{
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  const dt = Math.min(t - prevTime, 0.05);
  prevTime = t;

  drawBg(t);
  drawStars(t);

  const alphas = getPhaseAlphas(t);

  // Phase label
  const label = getPhaseLabel(t);
  phaseLabel.textContent = label;
  phaseLabel.style.opacity = label ? '0.6' : '0';

  // Plane A: Construction overlay
  drawConstruction(t, alphas.planeA);

  // Plane B: Logo
  logoGroup.visible = alphas.planeB > 0.01;
  if (logoGroup.visible) {{
    // Apply opacity to the entire group via material traversal
    logoGroup.traverse(obj => {{
      if (obj.material) {{
        if (obj._baseOpacity === undefined) obj._baseOpacity = obj.material.opacity;
        obj.material.opacity = obj._baseOpacity * alphas.planeB;
      }}
    }});

    const bs = 1.0 + Math.sin(t*0.4)*0.008;
    logoGroup.scale.set(bs,bs,1);

    // Shimmer
    shimmerArcs.forEach((m,i) => {{
      m.rotation.z += 0.0015*(i%2===0?1:-1);
    }});

    // Only run full animations after logo is materialized
    if (t > PHASE_TIMES.logoFull) {{
      // Wave
      waveTimer += dt;
      if (waveTimer > 4) {{ waveTimer=0; triggerWave(t); }}
      nodeMeshes.forEach(nm => {{
        if(nm.waveStart!==undefined&&t>=nm.waveStart) {{
          const el=t-nm.waveStart;
          if(el<0.8) {{ const p=el/0.8; nm.waveIntensity=Math.max(0,Math.pow(2,-10*p)*Math.sin((p-0.1)*5*Math.PI)+1)*0.5; }}
          else {{ nm.waveIntensity*=0.93; if(nm.waveIntensity<0.01){{nm.waveIntensity=0;nm.waveStart=undefined;}} }}
        }}
        const s=1+(nm.waveIntensity||0)*0.5;
        nm.core.scale.set(s,s,1); nm.glow.scale.set(s,s,1);
      }});

      // Pulses
      pulses.forEach(p => {{
        p.t+=p.speed*dt;
        if(p.t>=1){{p.t=0;p.edgeIdx=Math.floor(Math.random()*EDGES.length);}}
        const e=EDGES[p.edgeIdx];
        const px=NODES[PROJ_EDGES[p.edgeIdx]?PROJ_EDGES[p.edgeIdx][0]:0];
        const ex=e.x1+(e.x2-e.x1)*p.t, ey=e.y1+(e.y2-e.y1)*p.t;
        p.core.position.set(ex,ey,0.45);
        p.glow.position.set(ex,ey,0.42);
        const f=p.t<0.15?p.t/0.15:(p.t>0.85?(1-p.t)/0.15:1);
        p.core.material.opacity=Math.max(0,f*0.65);
        p.glow.material.opacity=Math.max(0,f*0.2);
      }});

      // Ink drops
      if(t-lastInk>0.3+Math.random()*0.5) {{
        for(const d of inkDrops) {{
          if(!d.active) {{
            d.active=true; d.x=inkOrigin.x+(Math.random()-0.5)*0.06; d.y=inkOrigin.y;
            d.vx=(Math.random()-0.5)*0.2; d.vy=-0.4-Math.random()*0.6;
            d.life=0; d.maxLife=1+Math.random()*1.2; break;
          }}
        }}
        lastInk=t;
      }}
      inkDrops.forEach(d => {{
        if(!d.active) return;
        d.life+=dt; d.vy-=1.2*dt; d.vx*=0.97; d.vy*=0.97;
        d.x+=d.vx*dt; d.y+=d.vy*dt;
        d.mesh.position.set(d.x,d.y,0.5);
        const lr=d.life/d.maxLife;
        d.mesh.material.opacity=Math.max(0,lr<0.1?lr/0.1*0.6:0.6*(1-(lr-0.1)/0.9));
        if(d.life>=d.maxLife){{d.active=false;d.mesh.material.opacity=0;}}
      }});

      // Energy rings
      if(t-lastRing>4) {{
        const geo=new THREE.RingGeometry(0.3,0.36,48);
        const mat=new THREE.MeshBasicMaterial({{color:hexC('copper'),transparent:true,opacity:0.25,side:THREE.DoubleSide}});
        const m=new THREE.Mesh(geo,mat); m.position.z=0.1; logoGroup.add(m);
        energyRings.push({{mesh:m,life:0}}); lastRing=t;
      }}
      for(let i=energyRings.length-1;i>=0;i--) {{
        const r=energyRings[i]; r.life+=dt;
        const s=1+r.life*3; r.mesh.scale.set(s,s,1);
        r.mesh.material.opacity=Math.max(0,0.25*(1-r.life/2.5));
        if(r.life>2.5){{logoGroup.remove(r.mesh);r.mesh.geometry.dispose();r.mesh.material.dispose();energyRings.splice(i,1);}}
      }}
    }}
  }}

  renderer.render(scene,camera);
}}

drawBg(0); drawStars(0);
animate();
}})();
</script>
</body>
</html>'''


def main() -> int:
    html = build_overlay()
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "logo_overlay.html"
    with open(out_path, "w") as f:
        f.write(html)
    size_kb = out_path.stat().st_size / 1024
    print(f"logo_overlay.html written to {out_path} ({size_kb:.1f} KB)")
    print("  Phase 1 (0–4s):   Plane A draws in")
    print("  Phase 2 (4–8s):   Projection highlights")
    print("  Phase 3 (8–12s):  Cross-fade")
    print("  Phase 4 (12s+):   Logo animates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
