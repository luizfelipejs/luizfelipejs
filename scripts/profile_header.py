#!/usr/bin/env python3
"""Gera o cabeçalho a partir das curvas já calculadas em zeta-{light,dark}.svg.

Execute python3 scripts/profile_header.py após atualizar a arte da zeta.
Usa apenas a biblioteca padrão do Python.
"""

from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ASSETS = Path(__file__).resolve().parent.parent / "assets"
NS = {"svg": "http://www.w3.org/2000/svg"}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
SERIF = "'STIX Two Text', Cambria, Georgia, 'Times New Roman', serif"
THEMES = {
    "light": dict(surface="#f6f8fa", border="#d1d9e0", grid="#e1e6eb",
                  text="#1f2328", muted="#59636e", accent="#6250d6"),
    "dark": dict(surface="#161b22", border="#3d444d", grid="#29313c",
                 text="#f0f6fc", muted="#9198a1", accent="#9085e9"),
}


def header_art():
    ET.register_namespace("", NS["svg"])
    for theme, colors in THEMES.items():
        source = ET.parse(ASSETS / f"zeta-{theme}.svg")
        # Preserve the original samples and colors, without the reveal mask.
        curve = deepcopy(source.find('.//svg:g[@stroke-width="1.8"]', NS))
        points = [
            tuple(map(float, point))
            for path in curve
            for point in re.findall(r"(-?[0-9.]+),(-?[0-9.]+)", path.attrib["d"])
        ]
        xs, ys = zip(*points)
        left, right, top, bottom = 574, 956, 22, 203
        scale = min((right - left) / (max(xs) - min(xs)),
                    (bottom - top) / (max(ys) - min(ys)))
        tx = (left + right - scale * (min(xs) + max(xs))) / 2
        ty = (top + bottom - scale * (min(ys) + max(ys))) / 2
        ox, oy = tx + 590 * scale, ty + 238 * scale
        curve.set("stroke-width", f"{1.35 / scale:.3f}")
        curve_svg = ET.tostring(curve, encoding="unicode")
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="240" viewBox="0 0 1000 240" role="img" aria-labelledby="title description">
<title id="title">Luiz Felipe · Ciência da Computação · UFPel</title>
<desc id="description">Matemática, arquitetura e sistemas. À direita, a curva de ζ(½ + it) no plano complexo, para 0 ≤ t ≤ 60.</desc>
<rect x=".5" y=".5" width="999" height="239" rx="16" fill="{colors['surface']}" stroke="{colors['border']}"/>
<g fill="none" stroke="{colors['grid']}" stroke-width="1">
  <circle cx="{ox:.2f}" cy="{oy:.2f}" r="{86 * scale:.2f}"/>
  <circle cx="{ox:.2f}" cy="{oy:.2f}" r="{172 * scale:.2f}"/>
  <line x1="{left}" y1="{oy:.2f}" x2="{right}" y2="{oy:.2f}"/>
  <line x1="{ox:.2f}" y1="{top}" x2="{ox:.2f}" y2="{bottom}"/>
</g>
<g transform="translate({tx:.4f} {ty:.4f}) scale({scale:.6f})" fill="none" stroke-linecap="round" stroke-linejoin="round">{curve_svg}</g>
<circle cx="{ox:.2f}" cy="{oy:.2f}" r="2.4" fill="{colors['surface']}" stroke="{colors['accent']}" stroke-width="1.2"/>
<text x="56" y="108" font-family="{FONT}" font-size="52" font-weight="650" letter-spacing="-1.5" fill="{colors['text']}">Luiz Felipe</text>
<text x="58" y="145" font-family="{FONT}" font-size="19" fill="{colors['muted']}">Ciência da Computação · UFPel</text>
<text x="58" y="182" font-family="{FONT}" font-size="15" fill="{colors['muted']}">Matemática · Arquitetura · Sistemas</text>
<text x="765" y="224" text-anchor="middle" font-family="{SERIF}" font-size="14" fill="{colors['muted']}">ζ(½ + it) · 0 ≤ t ≤ 60</text>
</svg>
'''
        (ASSETS / f"header-{theme}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    header_art()
