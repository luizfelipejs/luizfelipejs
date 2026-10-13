#!/usr/bin/env python3
"""Gera as peças do perfil abaixo do cabeçalho, no mesmo estilo dele:

- section-{1,2,3}-{tema}.svg: títulos de seção numerados
- link-{nome}-{tema}.svg: botões dos links
- interests[-mobile]-{tema}.svg: matemática e sistemas, cada um com uma figura
- project-{nome}[-mobile]-{tema}.svg: projetos, cada um com uma arte gerada

Uso: python3 scripts/profile_cards.py (precisa do fontTools; veja design.py).
As figuras continuam a numeração do cabeçalho, que é a FIG. 1.
"""

import math
import random
from html import escape

from design import ASSETS, THEMES, Type, card, colored_segments, gradient_stops, path_d, simplify, spectrum

SECTIONS = [("01", "Interesses", " & pesquisa"), ("02", "Projetos", ""), ("03", "Programação", " competitiva")]
LINKS = {"linkedin": "LINKEDIN", "codeforces": "CODEFORCES", "livros": "NOTAS & LIVROS"}

INTERESTS = [
    dict(title="Matemática", kicker="ANÁLISE  ·  EDPs", fig="FIG. 2  ·  WEIERSTRASS, 1872: CONTÍNUA, SEM DERIVADA",
         body="Análise real, espaços métricos e integração de Lebesgue. Na iniciação científica, "
              "trabalhei com modelagem matemática em controle populacional e EDPs."),
    dict(title="Sistemas", kicker="ARQUITETURA  ·  CONCORRÊNCIA", fig="FIG. 3  ·  CACHE ASSOCIATIVA DE 4 VIAS",
         body="Arquitetura de computadores, memória e concorrência: simulações de cache com SimpleScalar, "
              "threads com pthreads e estruturas de dados em C e C++."),
]

PROJECTS = {
    "atlas": dict(number="01", title="Atlas PDF", stack=["PYTHON", "SQLITE", "ELECTRON"],
                  link="github.com/luizfelipejs/atlas-pdf", fig="FIG. 4  ·  ESTANTE POR ASSUNTO",
                  about="estante com lombadas coloridas por assunto e um par de duplicatas ligado por um arco",
                  body="Biblioteca de PDFs para Linux, com indexação por assunto e identificação de duplicatas."),
    "modelagem": dict(number="02", title="modelagem", stack=["PYTHON"], link="github.com/luizfelipejs/modelagem",
                      fig="FIG. 5  ·  ATRATOR DE LORENZ",
                      about="atrator de Lorenz com σ = 10, ρ = 28 e β = 8/3",
                      body="Experimentos com equações diferenciais, caos e modelos estatísticos."),
}


# ---- peças pequenas ------------------------------------------------------

def heading(theme, number, roman, italic):
    c, ty = THEMES[theme], Type()
    size, base, x_title = 24, 31, 60
    title = ty.text(x_title, base, roman, "serif", size, c["ink"], tracking=-0.005)
    end = x_title + ty.width(roman, "serif", size, -0.005)
    if italic:
        title += ty.text(end, base, italic, "italic", size, c["ink"])
        end += ty.width(italic, "italic", size)
    title += ty.text(1, base - 1.5, number, "mono", 10, c["muted"], tracking=0.12)
    W, H = math.ceil(end + 4), 42
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(roman + italic)}">
<defs>{ty.defs()}<linearGradient id="g" x1="0" x2="1">{gradient_stops(c["spectrum"])}</linearGradient></defs>
<rect x="25" y="{base - 5.5}" width="24" height="1.4" fill="url(#g)"/>
{title}
</svg>
'''


def link_pill(theme, label):
    c, ty = THEMES[theme], Type()
    size, track = 9.5, 0.16
    text_w = ty.width(label, "mono", size, track)
    W, H = math.ceil(text_w + ty.width("↗", "mono", 11) + 44), 30
    text = (ty.text(25, H / 2 + 3.4, label, "mono", size, c["text"], tracking=track)
            + ty.text(25 + text_w + 7, H / 2 + 3.8, "↗", "mono", 11, c["muted"]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label.title())}">
<defs>{ty.defs()}<linearGradient id="g" x1="0" x2="1">{gradient_stops(c["spectrum"])}</linearGradient></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{H / 2 - 0.5}" fill="{c["bg"]}" stroke="{c["border"]}"/>
<circle cx="15" cy="{H / 2}" r="2.6" fill="url(#g)"/>
{text}
</svg>
'''


# ---- figuras -------------------------------------------------------------

def plate(c, x, y, w, h, rx=12):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{c["faint"]}" opacity=".55"/>'
            f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{rx - .5}" fill="none" stroke="{c["border"]}"/>')


def glow_defs(fid):
    return f'<filter id="{fid}" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="3.5"/></filter>'


def stroked(segments, c, fid, sid, width=1.4):
    """Traço em degradê com um halo desfocado por baixo; os trechos são desenhados uma vez só."""
    return (f'<defs><g id="{sid}">{segments}</g></defs>'
            f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<use href="#{sid}" stroke-width="{width * 3.5}" opacity="{c["glow"]}" filter="url(#{fid})"/>'
            f'<use href="#{sid}" stroke-width="{width}"/></g>')


def weierstrass(x):
    return sum(0.5 ** k * math.cos(3 ** k * math.pi * x) for k in range(9))


def fig_weierstrass(c, ty, x, y, w, h, uid):
    """W(x) em [−1, 1] e, à direita, uma lente com um trecho ampliado: a mesma aspereza em toda escala."""
    stops = c["spectrum"]
    main_w = w * 0.64
    lens_x, lens_w = x + main_w + 26, w - main_w - 40

    def trace(x0, x1, left, width, top, height, n):
        xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
        ys = [weierstrass(v) for v in xs]
        lo, hi = min(ys), max(ys)
        pts = [(left + width * i / n, top + height - height * (v - lo) / (hi - lo)) for i, v in enumerate(ys)]
        return simplify(pts, 0.2), lo, hi

    pad = 14
    main, lo, hi = trace(-1, 1, x + pad, main_w - pad, y + pad, h - 2 * pad, 1400)
    z0, z1 = 0.30, 0.40
    zoom, zlo, zhi = trace(z0, z1, lens_x + 8, lens_w - 16, y + 22, h - 44, 700)

    def sx(v):
        return x + pad + (main_w - pad) * (v + 1) / 2

    def sy(v):
        return y + pad + (h - 2 * pad) * (hi - v) / (hi - lo)

    bx0, bx1, by0, by1 = sx(z0), sx(z1), sy(zhi) - 3, sy(zlo) + 3
    lens = (
        f'<rect x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" height="{by1 - by0:.1f}" fill="none" stroke="{c["ink"]}" stroke-width=".8" opacity=".6"/>'
        f'<path d="M{bx1:.1f},{by0:.1f}L{lens_x:.1f},{y + 10:.1f}M{bx1:.1f},{by1:.1f}L{lens_x:.1f},{y + h - 10:.1f}" stroke="{c["axis"]}" stroke-width=".8" stroke-dasharray="2 3"/>'
        f'<rect x="{lens_x:.1f}" y="{y + 10:.1f}" width="{lens_w:.1f}" height="{h - 20:.1f}" rx="8" fill="{c["bg"]}" stroke="{c["border"]}"/>'
        + ty.text(lens_x + lens_w - 8, y + h - 16, "×10", "mono", 8.5, c["muted"], anchor="end")
    )
    defs = glow_defs(f"glow{uid}")
    art = (stroked(colored_segments(main, stops, 6), c, f"glow{uid}", f"wa{uid}", 1.2) + lens
           + stroked(colored_segments(zoom, stops[1:], 6), c, f"glow{uid}", f"wb{uid}", 1.1))
    return art, defs


def fig_cache(c, ty, x, y, w, h, uid):
    """Endereço dividido em tag | índice | offset; o índice escolhe o conjunto e a via certa dá hit."""
    stops = c["spectrum"]
    sets, ways, chosen, hit_way = 8, 4, 6, 1
    fields = [("tag", 23, 104, stops[0]), ("índice", 3, 46, stops[len(stops) // 2]), ("offset", 6, 54, stops[-1])]
    bx, by, bh = x + 16, y + h / 2 - 12, 22
    out, centers = [], {}
    for name, bits, fw, col in fields:
        out.append(f'<rect x="{bx:.1f}" y="{by}" width="{fw}" height="{bh}" rx="5" fill="{col}" opacity=".14"/>'
                   f'<rect x="{bx + .5:.1f}" y="{by + .5}" width="{fw - 1}" height="{bh - 1}" rx="4.5" fill="none" stroke="{col}" stroke-opacity=".8"/>')
        out.append(ty.text(bx + fw / 2, by + 14.5, str(bits), "mono", 9, c["text"], anchor="middle"))
        out.append(ty.text(bx + fw / 2, by - 8, name, "italic", 12.5, c["muted"], anchor="middle"))
        centers[name] = bx + fw / 2
        bx += fw + 4
    out.append(ty.text(x + 16, y + h - 10, "ENDEREÇO DE 32 BITS", "mono", 7.5, c["muted"], tracking=0.12))

    gx, gy, gw, gh = x + w - 150, y + 12, 134, h - 24
    cw, gap, row_gap = (gw - 3 * 4) / ways, 4, 2.5
    ch = (gh - (sets - 1) * row_gap) / sets
    rng = random.Random(7)
    cells = []
    for row in range(sets):
        cy = gy + row * (ch + row_gap)
        if row == chosen:
            cells.append(f'<rect x="{gx - 5:.1f}" y="{cy - 2.5:.1f}" width="{gw + 10:.1f}" height="{ch + 5:.1f}" rx="4" fill="{stops[len(stops) // 2]}" opacity=".16"/>')
        for way in range(ways):
            cx = gx + way * (cw + gap)
            if rng.random() < 0.75 or (row == chosen and way == hit_way):
                col = spectrum(stops, rng.random())
                cells.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="2" fill="{col}" opacity="{0.9 if row == chosen else 0.35}"/>')
            else:
                cells.append(f'<rect x="{cx + .5:.1f}" y="{cy + .5:.1f}" width="{cw - 1:.1f}" height="{ch - 1:.1f}" rx="2" fill="none" stroke="{c["grid"]}"/>')
    hx, hy = gx + hit_way * (cw + gap), gy + chosen * (ch + row_gap)
    cells.append(f'<rect class="hit{uid}" x="{hx - 3:.1f}" y="{hy - 3:.1f}" width="{cw + 6:.1f}" height="{ch + 6:.1f}" rx="4" fill="none" stroke="{c["ink"]}" stroke-width="1.2"/>')
    ix, row_y = centers["índice"], hy + ch / 2
    elbow = (f'<path d="M{ix:.1f},{by + bh + 4}V{row_y:.1f}H{gx - 12:.1f}" fill="none" stroke="{c["axis"]}" stroke-dasharray="2 3"/>'
             f'<path d="M{gx - 15:.1f},{row_y - 3.5:.1f}l5,3.5l-5,3.5" fill="none" stroke="{c["axis"]}"/>')
    css = (f".hit{uid}{{animation:hit{uid} 2.4s ease-in-out infinite}}"
           f"@keyframes hit{uid}{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}"
           f"@media (prefers-reduced-motion:reduce){{.hit{uid}{{animation:none}}}}")
    return "".join(out) + elbow + "".join(cells), "", css


def fig_shelf(c, ty, x, y, w, h, uid):
    """Lombadas coloridas por assunto; um par de duplicatas ligado por um arco."""
    stops = c["spectrum"]
    rng = random.Random(4)
    base = y + h - 26
    subjects = [spectrum(stops, u) for u in (0.0, 0.33, 0.66, 1.0)]
    books, bx = [], x + 18
    while bx < x + w - 30:
        group = min(int((bx - x) / (w - 40) * 4), 3)
        bw = rng.choice((8, 9, 10, 12, 14))
        bh = rng.randint(int(h * 0.3), int(h * 0.58))
        books.append([bx, bw, bh, subjects[group], rng.random(), rng.choice((2, 2, 3, 5))])
        bx += bw + books[-1][5]
    a, b = 3, len(books) - 5
    books[b][1:4] = books[a][1:4]  # a duplicata é idêntica: mesma largura, altura e assunto
    bx = x + 18
    for book in books:
        book[0] = bx
        bx += book[1] + book[5]
    out = [f'<rect x="{x + 10}" y="{base:.1f}" width="{w - 20}" height="1.2" fill="{c["axis"]}"/>']
    for i, (bx, bw, bh, col, tone, _gap) in enumerate(books):
        top = base - bh
        lean = ' transform="rotate(-7 {:.1f} {:.1f})"'.format(bx + bw, base) if i == len(books) - 1 else ""
        op = 0.95 if i in (a, b) else 0.42 + 0.35 * tone
        out.append(f'<g{lean}><rect x="{bx:.1f}" y="{top:.1f}" width="{bw}" height="{bh}" rx="1.5" fill="{col}" opacity="{op:.2f}"/>'
                   f'<rect x="{bx + 2:.1f}" y="{top + 7:.1f}" width="{bw - 4}" height="2" fill="{c["bg"]}" opacity=".7"/>'
                   f'<rect x="{bx + 2:.1f}" y="{top + bh - 12:.1f}" width="{bw - 4}" height="1.2" fill="{c["bg"]}" opacity=".5"/></g>')
    (ax, aw, ah, *_), (bxx, bw2, bh2, *_) = books[a], books[b]
    x1, x2 = ax + aw / 2, bxx + bw2 / 2
    top = base - ah - 10
    peak = y + 6
    out.append(f'<path class="dup{uid}" d="M{x1:.1f},{top:.1f}C{x1:.1f},{peak:.1f} {x2:.1f},{peak:.1f} {x2:.1f},{top:.1f}" fill="none" stroke="{c["ink"]}" stroke-width="1" stroke-dasharray="3 3"/>'
               f'<circle cx="{x1:.1f}" cy="{top:.1f}" r="2.4" fill="{c["ink"]}"/><circle cx="{x2:.1f}" cy="{top:.1f}" r="2.4" fill="{c["ink"]}"/>')
    apex = 0.25 * top + 0.75 * peak  # ponto mais alto da curva de Bézier
    out.append(f'<rect x="{(x1 + x2) / 2 - 8:.1f}" y="{apex - 7:.1f}" width="16" height="14" rx="4" fill="{c["bg"]}" stroke="{c["border"]}"/>')
    out.append(ty.text((x1 + x2) / 2, apex + 4, "≡", "mono", 12, c["ink"], anchor="middle"))
    css = (f".dup{uid}{{animation:dup{uid} 1.6s linear infinite}}@keyframes dup{uid}{{to{{stroke-dashoffset:-12}}}}"
           f"@media (prefers-reduced-motion:reduce){{.dup{uid}{{animation:none}}}}")
    return "".join(out), "", css


def lorenz(steps=6500, dt=0.006):
    s, r, b = 10.0, 28.0, 8 / 3

    def f(p):
        x, y, z = p
        return (s * (y - x), x * (r - z) - y, x * y - b * z)

    p, out = (0.1, 0.0, 0.0), []
    for i in range(steps):
        k1 = f(p)
        k2 = f(tuple(p[j] + dt / 2 * k1[j] for j in range(3)))
        k3 = f(tuple(p[j] + dt / 2 * k2[j] for j in range(3)))
        k4 = f(tuple(p[j] + dt * k3[j] for j in range(3)))
        p = tuple(p[j] + dt / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]) for j in range(3))
        if i > 300:
            out.append(p)
    return out


def fig_lorenz(c, ty, x, y, w, h, uid):
    """Projeção x–z do atrator de Lorenz, desenhada aos poucos; a cor segue o tempo."""
    pts3 = lorenz()
    xs, zs = [p[0] for p in pts3], [p[2] for p in pts3]
    pad = 14
    k = min((w - 2 * pad) / (max(xs) - min(xs)), (h - 2 * pad - 14) / (max(zs) - min(zs)))
    cx = x + w / 2 - k * (max(xs) + min(xs)) / 2
    cy = y + (h - 14) / 2 + k * (max(zs) + min(zs)) / 2
    pts = simplify([(cx + k * px, cy - k * pz) for px, pz in zip(xs, zs)], 0.3)
    defs = (glow_defs(f"glow{uid}")
            + f'<mask id="reveal{uid}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
              f'<path class="draw{uid}" pathLength="1" d="{path_d(pts)}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></mask>')
    art = f'<g mask="url(#reveal{uid})">{stroked(colored_segments(pts, c["spectrum"], 10), c, f"glow{uid}", f"lz{uid}", 0.75)}</g>'
    css = (f".draw{uid}{{stroke-dasharray:1 1;stroke-dashoffset:1;animation:draw{uid} 9s cubic-bezier(.4,0,.2,1) .3s forwards}}"
           f"@keyframes draw{uid}{{to{{stroke-dashoffset:0}}}}"
           f"@media (prefers-reduced-motion:reduce){{.draw{uid}{{animation:none;stroke-dashoffset:0}}}}")
    return art, defs, css


# ---- cartões -------------------------------------------------------------

def figure(kind, c, ty, x, y, w, h, uid):
    result = {"weierstrass": fig_weierstrass, "cache": fig_cache, "shelf": fig_shelf, "lorenz": fig_lorenz}[kind](
        c, ty, x, y, w, h, uid)
    art, defs, css = (*result, "") if len(result) == 2 else result
    return plate(c, x, y, w, h) + art, defs, css


def interests(theme, mobile):
    c, ty = THEMES[theme], Type()
    k = 1.15 if mobile else 1.0  # no celular o cartão encolhe mais, então o texto miúdo cresce
    W, gutter = (480, 24) if mobile else (1000, 36)
    col_w = W - 2 * gutter if mobile else (W - 3 * gutter) / 2
    fig_h = 92 if mobile else 84
    body_size, lead = (15.5, 23) if mobile else (13.5, 20.5)
    blocks, defs, css = [], [], []
    y_end = 0
    for i, (item, kind) in enumerate(zip(INTERESTS, ("weierstrass", "cache"))):
        x0 = gutter if mobile else gutter + i * (col_w + gutter)
        y0 = (y_end if mobile and i else 14) + 8
        art, d, s = figure(kind, c, ty, x0, y0, col_w, fig_h, i)
        defs.append(d)
        css.append(s)
        top = y0 + fig_h
        blocks.append(art)
        blocks.append(ty.text(x0, top + 19, item["fig"], "mono", 8 * k, c["muted"], tracking=0.1))
        blocks.append(ty.text(x0, top + 56, item["title"], "serif", 26 * k, c["ink"], tracking=-0.01))
        blocks.append(ty.text(x0 + col_w, top + 54, item["kicker"], "mono", 8.5 * k, c["muted"], tracking=0.14,
                              anchor="end"))
        lines = ty.wrap(item["body"], "sans", body_size, col_w)
        for j, line in enumerate(lines):
            blocks.append(ty.text(x0, top + 80 + j * lead, line, "sans", body_size, c["text"], tracking=-0.005))
        y_end = max(y_end, top + 80 + (len(lines) - 1) * lead + 8)
        if mobile and i == 0:
            blocks.append(f'<rect x="{gutter}" y="{y_end + 16:.1f}" width="{W - 2 * gutter}" height="1" fill="{c["grid"]}"/>')
            y_end += 34
    if not mobile:
        blocks.append(f'<rect x="{W / 2 - .5}" y="30" width="1" height="{y_end - 30:.1f}" fill="{c["grid"]}"/>')
    H = math.ceil(y_end + 24)
    desc = " ".join(f'{item["title"]}: {item["body"]}' for item in INTERESTS)
    return card(W, H, c, "".join(blocks), title="Interesses e pesquisa", desc=desc,
                defs=ty.defs() + "".join(defs), css="".join(css), rx=16, theme=theme)


def project(theme, mobile, key, kind):
    c, ty, p = THEMES[theme], Type(), PROJECTS[key]
    k = 1.15 if mobile else 1.0
    if mobile:
        W, fig = 480, (18, 18, 444, 150)
        tx, tw, top = 24, 432, 18 + 150 + 40
    else:
        W, fig = 1000, (18, 18, 270, 150)
        tx, tw, top = 320, 620, 52
    art, d, s = figure(kind, c, ty, *fig, 0)
    fx, fy, fw, fh = fig
    out = [art, ty.text(fx + 12, fy + fh - 11, p["fig"], "mono", 7.5 * k, c["muted"], tracking=0.08),
           ty.text(tx, top, f"PROJETO {p['number']}", "mono", 8.5 * k, c["muted"], tracking=0.16),
           ty.text(tx - 1.5, top + 40, p["title"], "serif", 34 * k, c["ink"], tracking=-0.012)]
    body_size, lead = (16, 23) if mobile else (14.5, 21)
    lines = ty.wrap(p["body"], "sans", body_size, tw)
    y = top + 68
    for j, line in enumerate(lines):
        out.append(ty.text(tx, y + j * lead, line, "sans", body_size, c["text"], tracking=-0.005))
    y += (len(lines) - 1) * lead + 30 * k

    x, tag_size = tx, 8.5 * k
    for tag in p["stack"]:
        tag_w = ty.width(tag, "mono", tag_size, 0.14)
        out.append(f'<rect x="{x + .5:.1f}" y="{y - 13.5 * k:.1f}" width="{tag_w + 18:.1f}" height="{20 * k:.1f}" '
                   f'rx="{10 * k:.1f}" fill="none" stroke="{c["border"]}"/>')
        out.append(ty.text(x + 9, y + 0.5, tag, "mono", tag_size, c["text"], tracking=0.14))
        x += tag_w + 26
    if p["link"]:
        lx, y = (tx, y + 36) if mobile else (W - 28, y)
        out.append(ty.text(lx, y, p["link"] + "  ↗", "mono", 9.5 * k, c["muted"], tracking=0.02,
                           anchor="start" if mobile else "end"))
    H = math.ceil(y + 26) if mobile else max(fy + fh + 18, math.ceil(y + 26))
    return card(W, H, c, "".join(out), title=p["title"], desc=f'{p["title"]}: {p["body"]} Figura: {p["about"]}.',
                defs=ty.defs() + d, css=s, rx=16, theme=theme)


def main():
    ASSETS.mkdir(exist_ok=True)
    files = {}
    for theme in THEMES:
        for n, (number, roman, italic) in enumerate(SECTIONS, 1):
            files[f"section-{n}-{theme}"] = heading(theme, number, roman, italic)
        for key, label in LINKS.items():
            files[f"link-{key}-{theme}"] = link_pill(theme, label)
        for mobile in (False, True):
            m = "-mobile" if mobile else ""
            files[f"interests{m}-{theme}"] = interests(theme, mobile)
            files[f"project-atlas{m}-{theme}"] = project(theme, mobile, "atlas", "shelf")
            files[f"project-modelagem{m}-{theme}"] = project(theme, mobile, "modelagem", "lorenz")
    for name, svg in files.items():
        (ASSETS / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"{name}.svg  {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
