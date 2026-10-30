"""Generate assets/hero.svg: an animated 3D banner for the GitHub profile README.

GitHub renders README images through <img>, so no JavaScript runs. The 3D motion is
precomputed here: every frame of a rotating icosahedron (plus an orbiting ring of
data points) is projected to 2D and baked into SMIL <animate> value lists.

Run:  python3 assets/generate_banner.py
"""

import math
from pathlib import Path

W, H = 1200, 420
FRAMES = 90
DUR = "18s"
CX, CY, SCALE = 905, 205, 128
CAMERA = 4.2  # distance of the eye from the origin, for perspective

# --- geometry ---------------------------------------------------------------
phi = (1 + 5 ** 0.5) / 2
verts = []
for a in (-1, 1):
    for b in (-phi, phi):
        verts += [(0, a, b), (a, b, 0), (b, 0, a)]
norm = math.sqrt(1 + phi * phi)
verts = [(x / norm, y / norm, z / norm) for x, y, z in verts]
edges = sorted({
    tuple(sorted((i, j)))
    for i in range(len(verts)) for j in range(len(verts))
    if i != j and abs(math.dist(verts[i], verts[j]) - 2 / norm) < 1e-6
})
assert len(verts) == 12 and len(edges) == 30

ring = [(1.55 * math.cos(2 * math.pi * k / 14), 0.0, 1.55 * math.sin(2 * math.pi * k / 14)) for k in range(14)]


def rotate(p, t):
    """Rotation for loop position t in [0, 1); periodic so the loop is seamless."""
    x, y, z = p
    ay = 2 * math.pi * t
    ax = 0.45 + 0.25 * math.sin(2 * math.pi * t)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    return x, y, z


def rotate_ring(p, t):
    x, y, z = p
    ay = -2 * math.pi * t * 2  # ring spins twice per loop, the other way
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    tilt = 0.32
    y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
    # lean the ring sideways
    lean = -0.35
    x, y = x * math.cos(lean) - y * math.sin(lean), x * math.sin(lean) + y * math.cos(lean)
    return x, y, z


def project(p):
    x, y, z = p
    f = CAMERA / (CAMERA - z)
    return CX + x * SCALE * f, CY + y * SCALE * f, f


def depth_alpha(z, lo=0.18, hi=1.0):
    return lo + (hi - lo) * (z + 1) / 2


fmt = lambda v: f"{v:.1f}"
ts = [k / FRAMES for k in range(FRAMES + 1)]  # last frame == first, closes the loop

# --- per-frame data -----------------------------------------------------------
vframes = [[rotate(v, t) for v in verts] for t in ts]
rframes = [[rotate_ring(r, t) for r in ring] for t in ts]


def anim(attr, values):
    return f'<animate attributeName="{attr}" dur="{DUR}" repeatCount="indefinite" values="{";".join(values)}"/>'


edge_svg = []
for i, j in edges:
    a = [project(vs[i]) for vs in vframes]
    b = [project(vs[j]) for vs in vframes]
    op = [f"{depth_alpha((vs[i][2] + vs[j][2]) / 2, 0.12, 0.95):.2f}" for vs in vframes]
    edge_svg.append(
        f'<line stroke="url(#edge)" stroke-width="1.8" stroke-linecap="round">'
        + anim("x1", [fmt(p[0]) for p in a]) + anim("y1", [fmt(p[1]) for p in a])
        + anim("x2", [fmt(p[0]) for p in b]) + anim("y2", [fmt(p[1]) for p in b])
        + anim("stroke-opacity", op) + "</line>"
    )

vert_svg = []
for i in range(len(verts)):
    p = [project(vs[i]) for vs in vframes]
    vert_svg.append(
        '<circle fill="#e0f2fe" filter="url(#glow)">'
        + anim("cx", [fmt(q[0]) for q in p]) + anim("cy", [fmt(q[1]) for q in p])
        + anim("r", [f"{2.2 + 2.6 * (vs[i][2] + 1) / 2:.2f}" for vs in vframes])
        + anim("fill-opacity", [f"{depth_alpha(vs[i][2], 0.25):.2f}" for vs in vframes])
        + "</circle>"
    )

ring_svg = []
for k in range(len(ring)):
    p = [project(rs[k]) for rs in rframes]
    color = "#f472b6" if k % 3 == 0 else "#a78bfa"
    ring_svg.append(
        f'<circle fill="{color}">'
        + anim("cx", [fmt(q[0]) for q in p]) + anim("cy", [fmt(q[1]) for q in p])
        + anim("r", [f"{1.4 + 2.4 * (rs[k][2] + 1.55) / 3.1:.2f}" for rs in rframes])
        + anim("fill-opacity", [f"{0.15 + 0.85 * (rs[k][2] + 1.55) / 3.1:.2f}" for rs in rframes])
        + "</circle>"
    )

# Ring track: static ellipse approximating the orbit path
track = [project(rotate_ring((1.55 * math.cos(a), 0, 1.55 * math.sin(a)), 0)) for a in [2 * math.pi * s / 64 for s in range(65)]]
track_path = "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y, _ in track)

# --- perspective grid floor ---------------------------------------------------
HORIZON, FLOOR_BOTTOM, VP_X = 300, H, 905
grid = []
for k in range(-14, 15):
    grid.append(f'<line x1="{VP_X}" y1="{HORIZON}" x2="{VP_X + k * 95}" y2="{FLOOR_BOTTOM}"/>')
# horizontal lines that slide toward the viewer; each follows y = h + d^2 spacing
rows = 7
for r in range(rows):
    ys, ops = [], []
    for s in range(21):
        u = (r + s / 20) / rows
        ys.append(fmt(HORIZON + (FLOOR_BOTTOM - HORIZON) * u * u))
        ops.append(f"{min(1, u * 1.6):.2f}")
    vals = ";".join(ys)
    grid.append(
        f'<line x1="0" x2="{W}"><animate attributeName="y1" dur="3s" repeatCount="indefinite" values="{vals}"/>'
        f'<animate attributeName="y2" dur="3s" repeatCount="indefinite" values="{vals}"/>'
        f'<animate attributeName="stroke-opacity" dur="3s" repeatCount="indefinite" values="{";".join(ops)}"/></line>'
    )

# --- typed tagline ------------------------------------------------------------
phrases = [
    "building reliable data systems",
    "shipping evidence-backed AI tools",
    "taking small products idea → release",
]
SLOT = 4.0  # seconds per phrase
TOTAL = SLOT * len(phrases)
typed = []
for n, text in enumerate(phrases):
    width = len(text) * 13.3 + 4
    start, end = n * SLOT / TOTAL, (n + 1) * SLOT / TOTAL
    k = lambda f: f"{start + (end - start) * f:.4f}"
    key_times = f"0;{k(0)};{k(0.45)};{k(0.82)};{k(0.97)};{k(1.0)};1"
    if n == 0:
        key_times = f"0;{k(0.45)};{k(0.82)};{k(0.97)};{k(1.0)};1"
        widths = f"0;{width:.0f};{width:.0f};0;0;0"
    else:
        widths = f"0;0;{width:.0f};{width:.0f};0;0;0"
    typed.append(
        f'<clipPath id="type{n}"><rect x="78" y="244" height="34">'
        f'<animate attributeName="width" dur="{TOTAL:.0f}s" repeatCount="indefinite" '
        f'keyTimes="{key_times}" values="{widths}" calcMode="linear"/></rect></clipPath>'
        f'<text x="80" y="268" clip-path="url(#type{n})" class="mono">{text}</text>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Hi, I'm Ansar. Solutions Engineer building data systems, AI tools and apps.">
<title>Hi, I'm Ansar</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#070b1a"/><stop offset="0.55" stop-color="#0d1330"/><stop offset="1" stop-color="#1a0f2e"/>
  </linearGradient>
  <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#6366f1" stop-opacity="0.45"/><stop offset="0.6" stop-color="#8b5cf6" stop-opacity="0.12"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="0.5" stop-color="#818cf8"/><stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
  <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#f8fafc"/><stop offset="0.6" stop-color="#c7d2fe"/><stop offset="1" stop-color="#f0abfc"/>
  </linearGradient>
  <linearGradient id="floorFade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.45" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="floorMask"><rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#floorFade)"/></mask>
  <linearGradient id="leftFade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#070b1a" stop-opacity="0.95"/><stop offset="0.55" stop-color="#070b1a" stop-opacity="0.6"/><stop offset="0.75" stop-color="#070b1a" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="softglow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 22px; fill: #67e8f9; }}
    .chip {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; fill: #cbd5e1; }}
  </style>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <!-- stars -->
  <g fill="#e2e8f0">
    {"".join(f'<circle cx="{(i * 397) % W}" cy="{(i * 151) % 290}" r="{0.6 + (i % 3) * 0.45:.2f}"><animate attributeName="opacity" dur="4s" begin="-{(i * 0.37) % 4:.2f}s" repeatCount="indefinite" values=".15;.9;.15"/></circle>' for i in range(1, 46))}
  </g>
  <!-- floor -->
  <g stroke="#6366f1" stroke-width="1" stroke-opacity="0.35" mask="url(#floorMask)">{"".join(grid)}</g>
  <!-- 3D object -->
  <ellipse cx="{CX}" cy="{CY}" rx="240" ry="200" fill="url(#halo)"/>
  <ellipse cx="{CX}" cy="{HORIZON + 34}" rx="150" ry="16" fill="#6366f1" fill-opacity="0.25" filter="url(#glow)">
    <animate attributeName="rx" dur="6s" repeatCount="indefinite" values="150;125;150"/>
  </ellipse>
  <path d="{track_path}" fill="none" stroke="#a78bfa" stroke-opacity="0.18" stroke-dasharray="3 6"/>
  <g>
    <animateTransform attributeName="transform" type="translate" dur="6s" repeatCount="indefinite" values="0 0;0 -10;0 0" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/>
    <g filter="url(#softglow)">{"".join(edge_svg)}</g>
    {"".join(vert_svg)}
    {"".join(ring_svg)}
  </g>
  <rect width="{W}" height="{H}" fill="url(#leftFade)"/>
  <!-- text -->
  <g class="sans">
    <text x="80" y="118" font-size="20" fill="#a5b4fc" letter-spacing="4">HELLO, WORLD — I'M</text>
    <text x="76" y="200" font-size="84" font-weight="800" fill="url(#name)" letter-spacing="-2">Ansar</text>
    <g>
      <text x="80" y="268" class="mono" fill-opacity="0.5" style="fill:#64748b">&gt;</text>
      <g transform="translate(22 0)">{"".join(typed)}</g>
    </g>
    <g>
      <rect x="80" y="318" width="232" height="34" rx="17" fill="#1e293b" stroke="#334155"/>
      <circle cx="100" cy="335" r="5" fill="#34d399"><animate attributeName="fill-opacity" dur="2s" repeatCount="indefinite" values="1;.3;1"/></circle>
      <text x="114" y="340" class="chip">Solutions Engineer</text>
      <rect x="324" y="318" width="172" height="34" rx="17" fill="#1e293b" stroke="#334155"/>
      <text x="344" y="340" class="chip">ex-Prime Video</text>
      <rect x="508" y="318" width="118" height="34" rx="17" fill="#1e293b" stroke="#334155"/>
      <text x="528" y="340" class="chip">Canada 🍁</text>
    </g>
  </g>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="#312e81" stroke-opacity="0.8"/>
</svg>
'''

out = Path(__file__).with_name("hero.svg")
out.write_text(svg)
print(f"wrote {out} ({len(svg) / 1024:.0f} KB)")
