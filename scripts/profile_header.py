#!/usr/bin/env python3
"""Gera o cabeçalho do perfil, os títulos de seção e os pequenos ornamentos.

Uso: python3 scripts/profile_header.py (precisa do fontTools; veja design.py).
Gera em assets/ as versões claras/escuras de profile[-mobile]-*.svg, section-*.svg
(cada título com um ornamento matemático), icon-*.svg (ícones dos projetos) e
rule-*.svg (o fio do rodapé, uma função de Weierstrass).

O cabeçalho é o nome e, ao lado, a curva de ζ(½ + it) no plano complexo para
0 ≤ t ≤ 50. O eixo real nasce na linha de base do nome; a curva passa pela
origem a cada zero não trivial e vai clareando conforme t cresce.
"""

import math

import ornaments
from design import ASSETS, THEMES, Type, mix, path_d, svg

T_MAX = 50.0
BERNOULLI = (1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6)  # B₂ … B₁₄
SECTIONS = [("Interesses", " & pesquisa", "cantor"), ("Projetos", "", "hilbert"),
            ("Programação", " competitiva", "tree")]


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
    """Amostra adaptativa de t ↦ ζ(½ + it), passando exatamente pelos zeros."""
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

    prev = (knots[0], critical(knots[0]))
    out.append(prev)
    for t in knots[1:]:
        cur = (t, critical(t))
        split(*prev, *cur)
        prev = cur
    return out, zeros


def curve_svg(c, ox, oy, scale):
    """A curva em trechos curtos de tinta sólida, cada vez mais clara conforme t cresce."""
    samples, zeros = sample(0.12 / scale)
    pts = [(ox + z.real * scale, oy - z.imag * scale) for _, z in samples]
    ts = [t for t, _ in samples]
    segs, start, run = [], 0, 0.0
    for i in range(1, len(pts)):
        run += math.dist(pts[i - 1], pts[i])
        if run >= 8 or i == len(pts) - 1:
            u = (ts[start] + ts[i]) / 2 / T_MAX
            segs.append(f'<path d="{path_d(pts[start:i + 1])}" stroke="{mix(c["ink"], c["page"], 0.08 + 0.6 * u)}"/>')
            start, run = i, 0.0
    return path_d(pts), "".join(segs), zeros


LAYOUTS = {
    # nome: (x, tamanho); a linha de base do nome é o eixo real da curva
    "desktop": dict(scale=35, name=(-1.5, 50), subtitle=13, gap=40, top=6),
    "mobile": dict(scale=27, name=(-1, 38), subtitle=12, gap=28, top=5),
}


def hero(theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    scale, (nx, ns) = L["scale"], L["name"]
    oy = L["top"] + 2.25 * scale  # topo da curva (Im ≈ 2,19) com uma pequena folga

    gap = ns * 0.24
    luiz = ty.width("Luiz", "serif", ns, -0.01)
    name = (ty.text(nx, oy, "Luiz", "serif", ns, c["ink"], tracking=-0.01)
            + ty.text(nx + luiz + gap, oy, "Felipe", "italic", ns, c["ink"], tracking=-0.01))
    name_end = nx + luiz + gap + ty.width("Felipe", "italic", ns, -0.01)

    ox = name_end + L["gap"] + 1.46 * scale  # ζ(½) ≈ −1,46 é o ponto mais à esquerda
    full, segs, zeros = curve_svg(c, ox, oy, scale)
    right = ox + 3.7 * scale
    W = math.ceil(right + 2)
    sub_y = oy + L["subtitle"] * 2.5
    subtitle = ty.text(1, sub_y, "Ciência da Computação  ·  UFPel", "sans", L["subtitle"], c["muted"])
    caption = ty.text(right, oy + 2.33 * scale + 2, "ζ(½ + it)", "italic", L["subtitle"] - 1, c["muted"], anchor="end")
    H = math.ceil(max(oy + 2.33 * scale + 8, sub_y + 10))

    css = (".draw{stroke-dasharray:1 1;stroke-dashoffset:1;animation:draw 4.5s cubic-bezier(.55,0,.2,1) .3s forwards}"
           "@keyframes draw{to{stroke-dashoffset:0}}"
           "@media (prefers-reduced-motion:reduce){.draw{animation:none;stroke-dashoffset:0}}")
    defs = (ty.defs()
            + f'<mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
              f'<path class="draw" pathLength="1" d="{full}" fill="none" stroke="#fff" stroke-width="12" '
              f'stroke-linecap="round" stroke-linejoin="round"/></mask>')
    body = f'''{name}
{subtitle}
<path d="M{name_end + 18:.1f},{oy:.1f}H{right:.1f}" stroke="{c["line"]}" stroke-width="1"/>
<g mask="url(#reveal)" fill="none" stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round">{segs}</g>
<circle cx="{ox:.1f}" cy="{oy:.1f}" r="2.6" fill="{c["page"]}" stroke="{c["ink"]}" stroke-width="1.1"/>
{caption}'''
    desc = (f"O nome Luiz Felipe e, ao lado, a curva da função zeta de Riemann ζ(½ + it) para 0 ≤ t ≤ {T_MAX:g}, "
            f"que passa pela origem a cada zero não trivial ({', '.join(f'{z:.2f}' for z in zeros[:4])}…).")
    return svg(W, H, body, title="Luiz Felipe · Ciência da Computação · UFPel", desc=desc, defs=defs, css=css)


def emblem(kind, c, x, y):
    """Ornamento de 28 × 20 px à esquerda de cada título."""
    color = c["muted"]
    if kind == "cantor":
        return ornaments.cantor(color, x, y + 2, 27, 16, levels=4)
    if kind == "hilbert":
        return ornaments.hilbert(color, x + 4, y, 20)
    return ornaments.tree(color, c["page"], x + 2, y + 2, 24, 16, depth=3)


def heading(theme, roman, italic, kind):
    c, ty = THEMES[theme], Type()
    size, base, x_title = 19, 38, 40
    title = ty.text(x_title, base, roman, "serif", size, c["ink"], tracking=-0.005)
    end = x_title + ty.width(roman, "serif", size, -0.005)
    if italic:
        title += ty.text(end, base, italic, "italic", size, c["ink"])
        end += ty.width(italic, "italic", size)
    body = emblem(kind, c, 1, base - 17) + title
    return svg(math.ceil(end + 4), 46, body, title=f"{roman}{italic}", defs=ty.defs())


def icon(theme, kind):
    """Ícones dos projetos, do tamanho de uma letra maiúscula do texto do GitHub."""
    c = THEMES[theme]
    if kind == "atlas":
        body, W, title = ornaments.shelf(c["ink"], 1.5, 2, 20, 14), 30, "Estante"
    else:
        body, W, title = ornaments.lorenz(c["ink"], 1, 1, 26, 16, 0.32, steps=4600), 28, "Atrator de Lorenz"
    return svg(W, 18, body, title=title)


def rule(theme):
    c = THEMES[theme]
    body = ornaments.weierstrass(c["muted"], 1, 2, 430, 14)
    return svg(432, 18, body, title="Função de Weierstrass: contínua em todo ponto, derivável em nenhum")


def main():
    ASSETS.mkdir(exist_ok=True)
    files = {}
    for theme in THEMES:
        files[f"profile-{theme}"] = hero(theme, "desktop")
        files[f"profile-mobile-{theme}"] = hero(theme, "mobile")
        for n, section in enumerate(SECTIONS, 1):
            files[f"section-{n}-{theme}"] = heading(theme, *section)
        for kind in ("atlas", "modelagem"):
            files[f"icon-{kind}-{theme}"] = icon(theme, kind)
        files[f"rule-{theme}"] = rule(theme)
    for name, doc in files.items():
        (ASSETS / f"{name}.svg").write_text(doc, encoding="utf-8")
        print(f"{name}.svg  {len(doc) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
