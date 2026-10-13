#!/usr/bin/env python3
"""Gera as artes matemáticas do perfil em assets/:

- zeta-{light,dark}.svg: a curva ζ(1/2 + it) no plano complexo, 0 <= t <= 60
- weierstrass-{light,dark}.svg: a função de Weierstrass, contínua e sem derivada

Precisa do mpmath (pip install mpmath). Só precisa rodar de novo se mudar o desenho.
"""

import math
from pathlib import Path

import mpmath

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
SERIF = "'STIX Two Text', 'Latin Modern Roman', 'CMU Serif', Cambria, Georgia, 'Times New Roman', serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"

THEMES = {
    "light": dict(surface="#f6f8fa", border="#d1d9e0", grid="#e1e6eb", axis="#afb8c1",
                  text="#1f2328", muted="#59636e", stops=("#2a78d6", "#6250d6", "#c4407a"), glow=0.18),
    "dark": dict(surface="#161b22", border="#3d444d", grid="#232a33", axis="#4a525c",
                 text="#f0f6fc", muted="#9198a1", stops=("#3987e5", "#9085e9", "#e06c9f"), glow=0.45),
}

DRAW_CSS = """
.reveal {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw {dur}s cubic-bezier(.33,.0,.2,1) .2s forwards; }}
@keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .reveal {{ animation: none; stroke-dashoffset: 0; }} }}
"""


def lerp_hex(a, b, u):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * u):02x}" for x, y in zip(ca, cb))


def gradient(stops, u):
    if u <= 0.5:
        return lerp_hex(stops[0], stops[1], u * 2)
    return lerp_hex(stops[1], stops[2], (u - 0.5) * 2)


def polyline(points):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)


def zeta_art():
    W, H = 1000, 470
    T, N = 60.0, 2400
    mpmath.mp.dps = 15
    values = [complex(mpmath.zeta(mpmath.mpc(0.5, T * i / N))) for i in range(N + 1)]
    zeros = [float(mpmath.zetazero(k).imag) for k in range(1, 14)]

    # plano complexo: origem em (ox, oy), escala uniforme
    scale, ox, oy = 86, 590, 238
    pts = [(ox + z.real * scale, oy - z.imag * scale) for z in values]
    wrapped = ["  ".join(f"{z:.2f}" for z in zeros[i:i + 5]) for i in range(0, len(zeros), 5)]

    for name, c in THEMES.items():
        seg = 12
        segments = []
        for i in range(0, N, seg):
            chunk = pts[i:i + seg + 1]
            segments.append(f'<path d="{polyline(chunk)}" stroke="{gradient(c["stops"], i / N)}"/>')
        rings = "".join(f'<circle cx="{ox}" cy="{oy}" r="{r * scale}"/>' for r in (1, 2, 3, 4))
        zero_lines = "".join(
            f'<text x="56" y="{318 + 22 * k}" xml:space="preserve" font-family="{MONO}" font-size="13.5" fill="{c["muted"]}">{line}</text>'
            for k, line in enumerate(wrapped))
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">A função zeta de Riemann na reta crítica</title>
<desc id="d">Curva de ζ(1/2 + it) no plano complexo para t entre 0 e 60. A curva passa pela origem a cada zero não trivial: 14.13, 21.02, 25.01, 30.42, 32.94 e assim por diante.</desc>
<style>{DRAW_CSS.format(dur=7)}</style>
<defs>
  <clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="15"/></clipPath>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"/></filter>
  <mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
    <path class="reveal" pathLength="1" d="{polyline(pts)}" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
  </mask>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{c["surface"]}" stroke="{c["border"]}"/>
<g clip-path="url(#frame)">
  <g fill="none" stroke="{c["grid"]}" stroke-width="1">{rings}</g>
  <g stroke="{c["axis"]}" stroke-width="1"><line x1="{ox - 2.2 * scale}" y1="{oy}" x2="{W - 24}" y2="{oy}"/><line x1="{ox}" y1="24" x2="{ox}" y2="{H - 24}"/></g>
  <g mask="url(#reveal)" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <g stroke-width="7" opacity="{c["glow"]}" filter="url(#glow)">{"".join(segments)}</g>
    <g stroke-width="1.8">{"".join(segments)}</g>
  </g>
  <circle cx="{ox}" cy="{oy}" r="4.5" fill="{c["surface"]}" stroke="{c["text"]}" stroke-width="1.5"/>
  <text x="{ox - 10}" y="{oy - 10}" font-family="{MONO}" font-size="12" fill="{c["muted"]}" text-anchor="end">0</text>
  <text x="{W - 32}" y="{oy - 8}" font-family="{MONO}" font-size="12" fill="{c["muted"]}" text-anchor="end">Re</text>
  <text x="{ox + 8}" y="40" font-family="{MONO}" font-size="12" fill="{c["muted"]}">Im</text>
</g>
<text x="54" y="96" font-family="{SERIF}" font-size="46" font-style="italic" fill="{c["text"]}">ζ(½ + it)</text>
<text x="56" y="132" font-family="{MONO}" font-size="14" fill="{c["muted"]}">0 ≤ t ≤ 60</text>
<text x="56" y="186" font-family="{FONT}" font-size="15.5" fill="{c["text"]}">Cada vez que a curva passa pela</text>
<text x="56" y="208" font-family="{FONT}" font-size="15.5" fill="{c["text"]}">origem, t é um zero não trivial.</text>
<text x="56" y="244" font-family="{FONT}" font-size="15.5" fill="{c["muted"]}">A hipótese de Riemann diz que</text>
<text x="56" y="266" font-family="{FONT}" font-size="15.5" fill="{c["muted"]}">todos estão na reta Re(s) = ½.</text>
{zero_lines}
</svg>
'''
        (OUT / f"zeta-{name}.svg").write_text(svg, encoding="utf-8")


def weierstrass_art():
    W, H = 1000, 210
    a, b, terms, n = 0.5, 3, 8, 4000
    x0, x1 = -2.0, 2.0

    def w(x):
        return sum(a ** k * math.cos(b ** k * math.pi * x) for k in range(terms))

    ys = [w(x0 + (x1 - x0) * i / n) for i in range(n + 1)]
    lo, hi = min(ys), max(ys)
    left, right, top, bottom = 360, W - 28, 28, H - 28
    pts = [(left + (right - left) * i / n, bottom - (bottom - top) * (y - lo) / (hi - lo)) for i, y in enumerate(ys)]
    zero_y = bottom - (bottom - top) * (0 - lo) / (hi - lo)

    for name, c in THEMES.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Função de Weierstrass com a = 1/2 e b = 3: contínua em todo ponto e sem derivada em nenhum</title>
<style>{DRAW_CSS.format(dur=4)}</style>
<defs><linearGradient id="g" x1="{left}" x2="{right}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{c["stops"][0]}"/><stop offset=".55" stop-color="{c["stops"][1]}"/><stop offset="1" stop-color="{c["stops"][2]}"/>
</linearGradient></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{c["surface"]}" stroke="{c["border"]}"/>
<line x1="{left}" y1="{zero_y:.1f}" x2="{right}" y2="{zero_y:.1f}" stroke="{c["axis"]}" stroke-width="1"/>
<path class="reveal" pathLength="1" d="{polyline(pts)}" fill="none" stroke="url(#g)" stroke-width="1.2" stroke-linejoin="round"/>
<text x="40" y="78" font-family="{SERIF}" font-size="24" font-style="italic" fill="{c["text"]}">W(x) = Σ<tspan dy="7" font-size="14">n≥0</tspan><tspan dy="-7"> a</tspan><tspan dy="-10" font-size="15">n</tspan><tspan dy="10"> cos(b</tspan><tspan dy="-10" font-size="15">n</tspan><tspan dy="10">πx)</tspan></text>
<text x="42" y="110" font-family="{MONO}" font-size="13.5" fill="{c["muted"]}">a = 1/2,  b = 3</text>
<text x="42" y="146" font-family="{FONT}" font-size="15" fill="{c["text"]}">contínua em todo ponto,</text>
<text x="42" y="168" font-family="{FONT}" font-size="15" fill="{c["text"]}">derivável em nenhum</text>
</svg>
'''
        (OUT / f"weierstrass-{name}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    zeta_art()
    weierstrass_art()
