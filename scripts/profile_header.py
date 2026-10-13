#!/usr/bin/env python3
"""Gera o cabeçalho do perfil: o nome e, ao lado, a curva de ζ(½ + it).

Uso: python3 scripts/profile_header.py (precisa do fontTools; veja design.py).
Gera versões claras/escuras para desktop e celular em assets/profile-*.svg.

A curva é ζ(½ + it) no plano complexo para 0 ≤ t ≤ 50. Um cometa percorre a
curva sem parar e, cada vez que passa pela origem (um zero não trivial), a
origem pulsa; ao mesmo tempo, um ponto sobe a reta crítica Re(s) = ½ e cruza
as marcas dos zeros no mesmo instante. A cor codifica t nas duas vistas.
"""

import math

from design import ASSETS, THEMES, Type, gradient_stops, grain_filter, keyframes, path_d, spectrum

T_MAX = 50.0
BERNOULLI = (1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6)  # B₂ … B₁₄
DRAW, LOOP = 5.0, 26.0  # segundos: desenho inicial e volta do cometa


def zeta(s, n=30):
    """ζ(s) por Euler–Maclaurin: soma direta até n − 1 e correção pela cauda."""
    total = sum(k ** -s for k in range(1, n)) + n ** (1 - s) / (s - 1) + 0.5 * n ** -s
    term, fact = s * n ** (-s - 1), 2
    for j, b in enumerate(BERNOULLI, 1):
        total += b / fact * term
        term *= (s + 2 * j - 1) * (s + 2 * j) / n ** 2
        fact *= (2 * j + 1) * (2 * j + 2)
    return total


def critical(t):
    return zeta(complex(0.5, t))


def refine_zero(a, b):
    """Mínimo de |ζ(½ + it)| em [a, b] por seção áurea: o zero com várias casas."""
    g = (math.sqrt(5) - 1) / 2
    for _ in range(60):
        c, d = b - g * (b - a), a + g * (b - a)
        if abs(critical(c)) < abs(critical(d)):
            b = d
        else:
            a = c
    return (a + b) / 2


def sample(tol):
    """Amostra adaptativa de t ↦ ζ(½ + it): subdivide onde a curva entorta mais que tol."""
    base = [i * 0.2 for i in range(int(T_MAX / 0.2) + 1)]
    coarse = [(t, critical(t)) for t in base]
    zeros = [refine_zero(coarse[i - 1][0], coarse[i + 1][0]) for i in range(1, len(coarse) - 1)
             if abs(coarse[i][1]) < 0.35 and abs(coarse[i][1]) <= min(abs(coarse[i - 1][1]), abs(coarse[i + 1][1]))]
    knots = sorted({*base, *zeros})

    out = []

    def split(t0, z0, t1, z1, depth=0):
        tm = (t0 + t1) / 2
        zm = critical(tm)
        chord = z1 - z0
        dev = abs((zm - z0).imag * chord.real - (zm - z0).real * chord.imag) / (abs(chord) or 1)
        if depth < 12 and (dev > tol or abs(chord) > 40 * tol):
            split(t0, z0, tm, zm, depth + 1)
            split(tm, zm, t1, z1, depth + 1)
        else:
            out.append((t1, z1))

    first = (knots[0], critical(knots[0]))
    out.append(first)
    prev = first
    for t in knots[1:]:
        cur = (t, critical(t))
        split(*prev, *cur)
        prev = cur
    return out, zeros


class Curve:
    """A curva já projetada na tela, com comprimento de arco acumulado."""

    def __init__(self, ox, oy, scale):
        samples, self.zeros = sample(0.12 / scale)
        self.ts = [t for t, _ in samples]
        self.pts = [(round(ox + z.real * scale, 1), round(oy - z.imag * scale, 1)) for _, z in samples]
        self.arc = [0.0]
        for (x0, y0), (x1, y1) in zip(self.pts, self.pts[1:]):
            self.arc.append(self.arc[-1] + math.hypot(x1 - x0, y1 - y0))
        self.length = self.arc[-1]

    def d(self, a=0, b=None):
        return path_d(self.pts[a:b])

    def fraction_at(self, t):
        """Fração do comprimento de arco em que a curva está no parâmetro t."""
        i = min(range(len(self.ts)), key=lambda k: abs(self.ts[k] - t))
        return self.arc[i] / self.length

    def t_at(self, u):
        target = u * self.length
        lo, hi = 0, len(self.arc) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if self.arc[mid] <= target else (lo, mid)
        span = self.arc[hi] - self.arc[lo] or 1
        return self.ts[lo] + (self.ts[hi] - self.ts[lo]) * (target - self.arc[lo]) / span

    def segments(self, stops, step=7.0):
        """Fatia a curva em trechos curtos, cada um com a cor do seu t."""
        out, start = [], 0
        for i in range(1, len(self.pts)):
            if self.arc[i] - self.arc[start] >= step or i == len(self.pts) - 1:
                color = spectrum(stops, (self.ts[start] + self.ts[i]) / 2 / T_MAX)
                out.append(f'<path d="{self.d(start, i + 1)}" stroke="{color}"/>')
                start = i
        return "".join(out)


def pulse_frames(fractions):
    """A origem acende quando o cometa chega a ela, e o anel se expande e some."""
    rest = "transform:scale(.3);opacity:0"
    frames = [(0, rest)]
    for k, f in enumerate(fractions):
        p = f * 100
        nxt = fractions[k + 1] * 100 if k + 1 < len(fractions) else 100
        if p - 0.05 > frames[-1][0]:
            frames.append((p - 0.05, rest))
        frames += [(p, "transform:scale(.45);opacity:1"), (min(p + 3.2, nxt - 0.2), "transform:scale(2.6);opacity:0")]
    return frames + [(100, rest)]


LAYOUTS = {
    "desktop": dict(
        W=1000, H=340, rx=20, pad=48,
        eyebrow=(52, 66), name=(48, 158, 88), name_lines=False,
        subtitle=(53, 196, 17, ["Ciência da Computação  ·  UFPel"]),
        formula=(52, 244, 25), note=(53, 276), meta=(53, 306), rule=None,
        plot=(430, 28, 420, 272), strip=(912, 58, 240),
        caption=(470, 318, True),
    ),
    "mobile": dict(
        W=480, H=420, rx=18, pad=24,
        eyebrow=(24, 46), name=(21, 116, 58), name_lines=True,
        subtitle=(25, 206, 14, ["Ciência da Computação", "UFPel  ·  Pelotas, RS"]),
        formula=(24, 340, 22), note=(25, 364), meta=(25, 394), rule=(24, 292),
        plot=(192, 50, 272, 210), strip=None,
        caption=(262, 276, False),
    ),
}


def render(theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    W, H, pad = L["W"], L["H"], L["pad"]
    stops = c["spectrum"]
    mid = spectrum(stops, 0.5)

    # ---- plano complexo -------------------------------------------------
    px, py, pw, ph = L["plot"]
    re0, re1, im0, im1 = -1.6, 3.8, -2.45, 2.3
    scale = min(pw / (re1 - re0), ph / (im1 - im0))
    ox = px + (pw - (re1 - re0) * scale) / 2 - re0 * scale
    oy = py + (ph - (im1 - im0) * scale) / 2 + im1 * scale
    curve = Curve(ox, oy, scale)
    zero_fracs = [curve.fraction_at(t) for t in curve.zeros]

    rings = "".join(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r * scale:.1f}"/>' for r in (1, 2, 3))
    ticks = "".join(
        f'<path d="M{ox + k * scale:.1f},{oy - 3:.1f}v6"/>' for k in range(-1, 4) if k
    ) + "".join(f'<path d="M{ox - 3:.1f},{oy - k * scale:.1f}h6"/>' for k in range(-2, 3) if k)
    axes = (f'<path d="M{ox + re0 * scale:.1f},{oy:.1f}H{ox + re1 * scale:.1f}'
            f'M{ox:.1f},{oy - im1 * scale:.1f}V{oy - im0 * scale:.1f}"/>')

    start = curve.pts[0]
    hot = spectrum(stops, 0.8)
    comet_layers = [(0.060, 10, 0.08, mid), (0.038, 6, 0.18, hot), (0.020, 3.4, 0.55, hot),
                    (0.009, 2.2, 0.95, c["comet"]), (0.0012, 4.4, 1, c["comet"])]
    comets = "".join(
        f'<use href="#zc" class="comet c{i}" stroke="{color}" stroke-width="{w}" opacity="{o}" '
        f'stroke-dasharray="{length} 2"/>'
        for i, (length, w, o, color) in enumerate(comet_layers))
    comet_css = "".join(
        f".c{i}{{animation:c{i} {LOOP}s linear {DRAW}s infinite both}}"
        + keyframes(f"c{i}", [(0, f"stroke-dashoffset:{length}"), (100, f"stroke-dashoffset:{length - 1:.4f}")])
        for i, (length, *_rest) in enumerate(comet_layers))

    # ---- reta crítica (só no desktop) -----------------------------------
    strip_svg, strip_css = "", ""
    if L["strip"]:
        sx, sy0, sh = L["strip"]
        unit = 22
        y_of = lambda t: sy0 + sh - sh * t / T_MAX
        zero_marks = "".join(
            f'<path d="M{sx - 5},{y_of(z):.1f}h10" stroke="{spectrum(stops, z / T_MAX)}" stroke-width="1.4"/>'
            for z in curve.zeros)
        rider = keyframes("ride", [(k, f"transform:translate(0,{y_of(curve.t_at(k / 100)) - y_of(0):.2f}px)")
                                   for k in range(0, 101)])
        strip_css = f".rider{{animation:ride {LOOP}s linear {DRAW}s infinite both}}{rider}"
        strip_svg = f'''
<g>
  <rect x="{sx - unit / 2}" y="{sy0 - 8}" width="{unit}" height="{sh + 16}" fill="url(#band)" opacity=".55"/>
  <path d="M{sx - unit / 2},{sy0 - 8}V{sy0 + sh + 8}M{sx + unit / 2},{sy0 - 8}V{sy0 + sh + 8}" stroke="{c["grid"]}" stroke-dasharray="2 3"/>
  <rect x="{sx - 0.7}" y="{sy0 - 14}" width="1.4" height="{sh + 22}" fill="url(#line)"/>
  {zero_marks}
  <g class="rider"><circle cx="{sx}" cy="{y_of(0):.1f}" r="6.5" fill="none" stroke="{c["ink"]}" stroke-width="1" opacity=".55"/><circle cx="{sx}" cy="{y_of(0):.1f}" r="2.6" fill="{c["ink"]}"/></g>
  {ty.text(sx, sy0 - 24, "½ + it", "italic", 14, c["muted"], anchor="middle")}
  {ty.text(sx - unit / 2, sy0 + sh + 26, "0", "mono", 9.5, c["muted"], anchor="middle")}
  {ty.text(sx + unit / 2, sy0 + sh + 26, "1", "mono", 9.5, c["muted"], anchor="middle")}
</g>'''

    # ---- tipografia -----------------------------------------------------
    ex, ey = L["eyebrow"]
    eyebrow = (f'<rect x="{ex}" y="{ey - 4.75}" width="22" height="1.5" fill="url(#accent)"/>'
               + ty.text(ex + 32, ey, "MATEMÁTICA × COMPUTAÇÃO", "mono", 10.5, c["muted"], tracking=0.16))

    nx, ny, ns = L["name"]
    indent = ns * 0.14 if L["name_lines"] else ty.width("Luiz", "serif", ns, -0.01) + ns * 0.24
    name = (ty.text(nx, ny, "Luiz", "serif", ns, c["ink"], tracking=-0.01)
            + ty.text(nx + indent, ny + (ns * 0.92 if L["name_lines"] else 0), "Felipe", "italic", ns,
                      "url(#nameGrad)", tracking=-0.01))
    felipe_units = ty.width("Felipe", "italic", Type.face("italic").upm, -0.01)

    sx_, sy_, ss, lines = L["subtitle"]
    subtitle = "".join(ty.text(sx_, sy_ + i * ss * 1.45, line, "sans", ss, c["text"] if i == 0 else c["muted"],
                               tracking=-0.005) for i, line in enumerate(lines))
    rule = ""
    if L["rule"]:
        rx_, ry_ = L["rule"]
        rule = f'<rect x="{rx_}" y="{ry_}" width="{W - 2 * rx_}" height="1" fill="{c["grid"]}"/>'

    fx, fy, fs = L["formula"]
    formula, _ = ty.runs(fx, fy, [
        ("ζ", "italic", 1, 0), ("(", "serif", 1, 0), ("s", "italic", 1, 0), (")  =  ", "serif", 1, 0),
        ("Σ", "serif", 1.18, 0.06), ("n", "italic", 0.5, 0.34), ("≥1", "serif", 0.5, 0.34), (" ", "serif", 1, 0),
        ("n", "italic", 1, 0), ("−", "serif", 0.62, -0.4), ("s", "italic", 0.66, -0.4), ("  =  ", "serif", 1, 0),
        ("Π", "serif", 1.18, 0.06), ("p", "italic", 0.5, 0.34), ("  (1 − ", "serif", 1, 0),
        ("p", "italic", 1, 0), ("−", "serif", 0.62, -0.4), ("s", "italic", 0.66, -0.4), (")", "serif", 1, 0),
        ("−1", "serif", 0.62, -0.42),
    ], fs, c["ink"])
    note_x, note_y = L["note"]
    note = ty.text(note_x, note_y, "EULER, 1737  ·  RIEMANN, 1859", "mono", 9.5, c["muted"], tracking=0.14)

    mx, my = L["meta"]
    meta_items = ["ANÁLISE", "ARQUITETURA", "SISTEMAS"]
    meta, x = [], mx
    for i, item in enumerate(meta_items):
        if i:
            meta.append(f'<circle cx="{x + 9:.1f}" cy="{my - 3.6:.1f}" r="1.6" fill="{spectrum(stops, i / 2)}"/>')
            x += 18
        meta.append(ty.text(x, my, item, "mono", 10.5, c["text"], tracking=0.16))
        x += ty.width(item, "mono", 10.5, 0.16)

    cx_, cy_, full = L["caption"]
    detail = f"0 ≤ t ≤ {T_MAX:g}" + (f"  ·  {len(curve.zeros)} ZEROS" if full else "")
    caption = (ty.text(cx_, cy_, "FIG. 1", "mono", 9.5, c["muted"], tracking=0.14)
               + ty.text(cx_ + 52, cy_, "ζ(½ + it)", "italic", 15, c["text"])
               + ty.text(cx_ + 52 + ty.width("ζ(½ + it)", "italic", 15) + 10, cy_,
                         detail, "mono", 9.5, c["muted"], tracking=0.08))

    labels = (ty.text(ox + re1 * scale - 2, oy + 19, "Re", "italic", 13, c["muted"], anchor="end")
              + ty.text(ox + 8, oy - im1 * scale + 12, "Im", "italic", 13, c["muted"]))

    corner = 12
    marks = "".join(
        f'<path d="M{x + dx * corner},{y}H{x}V{y + dy * corner}"/>'
        for x, y, dx, dy in ((pad / 2, pad / 2, 1, 1), (W - pad / 2, pad / 2, -1, 1),
                             (pad / 2, H - pad / 2, 1, -1), (W - pad / 2, H - pad / 2, -1, -1)))

    aurora = [
        (ox + 0.6 * scale, oy, 2.9 * scale, stops[1]),
        (ox + 2.6 * scale, oy + 1.6 * scale, 2.2 * scale, stops[-1]),
        (ox - 0.8 * scale, oy - 1.9 * scale, 2.0 * scale, stops[0]),
    ]
    aurora_defs = "".join(
        f'<radialGradient id="au{i}"><stop offset="0" stop-color="{col}" stop-opacity="{c["aurora"]}"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
        for i, (*_xy, _r, col) in enumerate(aurora))
    aurora_svg = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#au{i})"/>'
                         for i, (x, y, r, _col) in enumerate(aurora))

    pulse_css = f".pulse{{transform-box:fill-box;transform-origin:center;animation:pulse {LOOP}s linear {DRAW}s infinite both}}" \
                + keyframes("pulse", pulse_frames(zero_fracs))

    css = (
        f".reveal{{stroke-dasharray:1 1;stroke-dashoffset:1;animation:draw {DRAW}s cubic-bezier(.5,0,.15,1) .2s forwards}}"
        "@keyframes draw{to{stroke-dashoffset:0}}"
        + comet_css + pulse_css + strip_css
        + "@media (prefers-reduced-motion:reduce){.reveal{animation:none;stroke-dashoffset:0}"
          ".comet,.pulse,.rider{animation:none;visibility:hidden}}"
    )

    title = "Luiz Felipe · Ciência da Computação · UFPel"
    desc = ("Cabeçalho com o nome Luiz Felipe em tipografia serifada e, ao lado, a curva da função zeta de Riemann "
            f"ζ(½ + it) no plano complexo para 0 ≤ t ≤ {T_MAX:g}, que passa pela origem a cada zero não trivial "
            f"({', '.join(f'{z:.2f}' for z in curve.zeros[:5])}…). Abaixo, a fórmula ζ(s) = Σ n⁻ˢ = Π (1 − p⁻ˢ)⁻¹.")

    body = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{title}</title>
<desc id="d">{desc}</desc>
<style>{css}</style>
<defs>
  {ty.defs()}
  <path id="zc" pathLength="1" d="{curve.d()}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="{L["rx"]}"/></clipPath>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient>
  <linearGradient id="nameGrad" gradientUnits="userSpaceOnUse" x1="0" y1="700" x2="{felipe_units:.0f}" y2="0">{gradient_stops(stops)}</linearGradient>
  <linearGradient id="accent" x1="0" x2="1">{gradient_stops(stops)}</linearGradient>
  <linearGradient id="line" x1="0" y1="1" x2="0" y2="0">{gradient_stops(stops)}</linearGradient>
  <linearGradient id="band" x1="0" x2="1"><stop offset="0" stop-color="{mid}" stop-opacity="0"/><stop offset=".5" stop-color="{mid}" stop-opacity=".22"/><stop offset="1" stop-color="{mid}" stop-opacity="0"/></linearGradient>
  {aurora_defs}
  <radialGradient id="fade" cx="{ox:.1f}" cy="{oy:.1f}" r="{3.4 * scale:.1f}" gradientUnits="userSpaceOnUse"><stop offset=".35" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <mask id="vignette" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse" x="{ox % 14:.1f}" y="{oy % 14:.1f}"><circle cx="0" cy="0" r=".9" fill="{c["grid"]}"/></pattern>
  <filter id="bloom" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5"/></filter>
  {grain_filter("grain", c["ink"] if theme == "light" else "#ffffff")}
  <mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><use href="#zc" class="reveal" stroke="#fff" stroke-width="16"/></mask>
  <g id="segs" fill="none" stroke-linecap="round" stroke-linejoin="round">{curve.segments(stops)}</g>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  {aurora_svg}
  <g mask="url(#vignette)">
    <rect width="{W}" height="{H}" fill="url(#dots)"/>
    <g fill="none" stroke="{c["grid"]}" stroke-dasharray="1.5 4">{rings}</g>
    <g fill="none" stroke="{c["axis"]}" stroke-width="1">{axes}{ticks}</g>
  </g>
  <g mask="url(#reveal)">
    <use href="#segs" stroke-width="7" opacity="{c["glow"]}" filter="url(#bloom)"/>
    <use href="#segs" stroke-width="1.5"/>
  </g>
  <g fill="none" stroke-linecap="round">{comets}</g>
  <circle class="pulse" cx="{ox:.1f}" cy="{oy:.1f}" r="9" fill="none" stroke="{c["ink"]}" stroke-width="1.2"/>
  <circle cx="{ox:.1f}" cy="{oy:.1f}" r="3.4" fill="{c["bg"]}" stroke="{c["ink"]}" stroke-width="1.3"/>
  <circle cx="{start[0]}" cy="{start[1]}" r="2.6" fill="{stops[0]}"/>
  {labels}
  {strip_svg}
  {eyebrow}
  {name}
  {subtitle}
  {rule}
  {formula}
  {note}
  {"".join(meta)}
  {caption}
  <g fill="none" stroke="{c["axis"]}" stroke-width="1">{marks}</g>
  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="{c["grain"] * 2.4:.2f}"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{L["rx"] - 0.5}" fill="none" stroke="{c["border"]}"/>
</svg>
'''
    return body


def main():
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for kind in LAYOUTS:
            suffix = theme if kind == "desktop" else f"mobile-{theme}"
            svg = render(theme, kind)
            (ASSETS / f"profile-{suffix}.svg").write_text(svg, encoding="utf-8")
            print(f"profile-{suffix}.svg  {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
