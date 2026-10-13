#!/usr/bin/env python3
"""Gera o cabeçalho editorial do perfil com uma curva de Hilbert de ordem 4.

Uso: python3 scripts/profile_header.py (somente biblioteca padrão).
Gera versões claras/escuras para desktop e celular em assets/profile-*.svg.
"""

from pathlib import Path


ASSETS = Path(__file__).resolve().parent.parent / "assets"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
THEMES = {
    "light": dict(text="#242b29", muted="#59665f", line="#dce3df", ink="#41705f"),
    "dark": dict(text="#e8ede9", muted="#a2b1a8", line="#2d3c34", ink="#8fb9a1"),
}


def hilbert_points(order):
    """Mapeia a distância percorrida para cada ponto da grade de Hilbert."""
    side = 2 ** order
    points = []
    for distance in range(side * side):
        x = y = 0
        remaining = distance
        size = 1
        while size < side:
            rx = (remaining // 2) & 1
            ry = (remaining ^ rx) & 1
            if ry == 0:
                if rx == 1:
                    x, y = size - 1 - x, size - 1 - y
                x, y = y, x
            x += size * rx
            y += size * ry
            remaining //= 4
            size *= 2
        points.append((x, y))
    return points


def render(theme, mobile=False):
    colors = THEMES[theme]
    width, height = (560, 246) if mobile else (1000, 280)
    margin = 20 if mobile else 32
    art_x, art_y, art_size = (382, 28, 146) if mobile else (722, 28, 196)
    name_y, name_size = (103, 49) if mobile else (132, 76)
    subtitle_y = 144 if mobile else 176
    label_y = 47 if mobile else 61
    points = [(art_x + x * art_size / 15, art_y + y * art_size / 15)
              for x, y in hilbert_points(4)]
    path = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    start, end = points[0], points[-1]
    corners = " ".join(
        f"M{x + dx * 8},{y} H{x} V{y + dy * 8}"
        for x, y, dx, dy in (
            (art_x - 8, art_y - 8, 1, 1),
            (art_x + art_size + 8, art_y - 8, -1, 1),
            (art_x - 8, art_y + art_size + 8, 1, -1),
            (art_x + art_size + 8, art_y + art_size + 8, -1, -1),
        )
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">Luiz Felipe · Ciência da Computação · UFPel</title>
<desc id="description">Cabeçalho com tipografia serifada e uma curva de Hilbert de ordem 4 à direita, desenhada em verde suave.</desc>
<text x="{margin}" y="{label_y}" font-family="{MONO}" font-size="12" fill="{colors['ink']}">matemática &amp; computação</text>
<text x="{margin - 3}" y="{name_y}" font-family="{SERIF}" font-size="{name_size}" letter-spacing="-2" fill="{colors['text']}">Luiz Felipe</text>
<text x="{margin}" y="{subtitle_y}" font-family="{SANS}" font-size="19" fill="{colors['muted']}">Ciência da Computação · UFPel</text>
<text x="{margin}" y="{height - 39}" font-family="{MONO}" font-size="13" fill="{colors['muted']}">análise / arquitetura / sistemas</text>
<path d="{corners}" fill="none" stroke="{colors['line']}" stroke-width="1"/>
<path d="{path}" fill="none" stroke="{colors['ink']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="{start[0]}" cy="{start[1]}" r="3" fill="{colors['ink']}"/>
<circle cx="{end[0]}" cy="{end[1]}" r="3" fill="{colors['ink']}"/>
<text x="{art_x + art_size / 2}" y="{art_y + art_size + 29}" font-family="{MONO}" font-size="10" text-anchor="middle" fill="{colors['muted']}">HILBERT / 04</text>
<line x1="{margin}" y1="{height - 8}" x2="{width - margin}" y2="{height - 8}" stroke="{colors['line']}"/>
</svg>
'''


def header_art():
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for mobile in (False, True):
            suffix = f"mobile-{theme}" if mobile else theme
            (ASSETS / f"profile-{suffix}.svg").write_text(render(theme, mobile), encoding="utf-8")


if __name__ == "__main__":
    header_art()
