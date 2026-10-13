#!/usr/bin/env python3
"""Gera o cartão do perfil, no formato do neofetch: assets/neofetch[-mobile]-{light,dark}.svg.

À esquerda, no lugar do logo da distro, a curva ζ(½ + it) desenhada numa malha
de pontos braille; à direita, formação, pesquisa, projetos e o número de
problemas resolvidos no Codeforces, puxado da API pública. Roda todo dia pelo workflow.

Uso: python3 scripts/neofetch.py
Se a API falhar, sai com erro e não mexe nos arquivos existentes.
Precisa do fontTools e da fonte JetBrains Mono (veja design.py).
"""

import json
import math
import time
import urllib.request

from design import ASSETS, Type

CODEFORCES_USER = "root.svp"

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#c2cfde"),
}

# size: corpo da fonte; cols: largura do texto em caracteres; art: colunas do desenho (0 = em cima do texto)
LAYOUTS = {
    "desktop": dict(size=11, lead=15, pad=14, art=26, gap=3, cols=52, short=False),
    "mobile": dict(size=11, lead=15, pad=12, art=0, gap=0, cols=44, short=True, art_mobile=24),
}


# ---- dados -----------------------------------------------------------------

def codeforces(method, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"https://codeforces.com/api/{method}?{query}",
                                 headers={"User-Agent": "luizfelipejs-readme"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            if data.get("status") == "OK":
                return data["result"]
            raise RuntimeError(data.get("comment", "resposta inválida do Codeforces"))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def solved_count():
    submissions = codeforces("user.status", handle=CODEFORCES_USER)
    return len({(s["problem"].get("contestId"), s["problem"]["index"])
                for s in submissions if s.get("verdict") == "OK"})


# ---- a curva -----------------------------------------------------------------

BERNOULLI = (1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6)  # B₂ … B₁₄


def zeta(s, n=30):
    """ζ(s) por Euler–Maclaurin: soma direta até n − 1 e correção pela cauda."""
    total = sum(k ** -s for k in range(1, n)) + n ** (1 - s) / (s - 1) + 0.5 * n ** -s
    term, fact = s * n ** (-s - 1), 2
    for j, b in enumerate(BERNOULLI, 1):
        total += b / fact * term
        term *= (s + 2 * j - 1) * (s + 2 * j) / n ** 2
        fact *= (2 * j + 1) * (2 * j + 2)
    return total


CURVE = [zeta(complex(0.5, 50 * i / 12000)) for i in range(12001)]  # 0 ≤ t ≤ 50


def braille(x0, y0, cols, cw, lead):
    """Rasteriza a curva numa malha de 2 × 4 pontos por caractere, como um terminal com braille."""
    dx, dy = cw / 2, lead / 4
    re0, re1, im0, im1 = -1.55, 3.75, -2.4, 2.25
    scale = cols * cw / (re1 - re0)
    dots = {(math.floor((z.real - re0) * scale / dx), math.floor((im1 - z.imag) * scale / dy)) for z in CURVE}
    origin = (x0 + (0 - re0) * scale, y0 + im1 * scale)
    path = "".join(f"M{x0 + (i + .5) * dx:.1f},{y0 + (j + .5) * dy:.1f}h0" for i, j in sorted(dots))
    return path, (im1 - im0) * scale, origin


# ---- texto ---------------------------------------------------------------------

def kv(key, value, width):
    """'. Chave: ........ valor', com os pontos completando a largura."""
    fill = max(1, width - len(key) - len(value) - 5)
    return [(". ", "dots"), (key, "key"), (": ", "text"), ("." * fill, "dots"), (" " + value, "value")]


def section(title, width):
    return [("- ", "dots"), (title, "text"), (" " + "─" * (width - len(title) - 3), "dots")]


def lines(solved, width, short):
    s = lambda full, brief: brief if short else full
    return [
        [("luiz", "value"), ("@", "text"), ("felipe", "value"), (" " + "─" * (width - 12), "dots")],
        kv("Curso", "Ciência da Computação · UFPel", width),
        kv("Pesquisa", s("IC em controle populacional e EDPs", "IC em modelagem, EDPs"), width),
        kv("Linguagens", "C, C++, Python, LaTeX", width),
        kv("Matemática", s("análise real, espaços métricos", "análise real, medida"), width),
        kv("Interesses", s("arquitetura, memória, concorrência", "arquitetura, concorrência"), width),
        section("Projetos", width),
        kv("atlas-pdf", s("PDFs por conteúdo · Python, Electron", "PDFs por conteúdo"), width),
        kv("modelagem", s("caos, farmacocinética, ajustes", "caos e ajuste de modelos"), width),
        section("Codeforces", width),
        kv(CODEFORCES_USER, f"{solved} problemas resolvidos", width),
    ]


def render(solved, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    size, lead, pad = L["size"], L["lead"], L["pad"]
    cw = size * 0.6  # a JetBrains Mono tem avanço de 600/1000 em todos os glifos
    rows = lines(solved, L["cols"], L["short"])

    art_cols = L["art"] or L["art_mobile"]
    art_x = pad if L["art"] else pad + (L["cols"] - art_cols) * cw / 2
    path, art_h, origin = braille(art_x, 0, art_cols, cw, lead)
    caption_h = lead * 1.6
    text_h = len(rows) * lead
    if L["art"]:
        text_x = pad + (L["art"] + L["gap"]) * cw
        H = math.ceil(pad * 2 + max(text_h, art_h + caption_h))
        art_y, text_y = (H - art_h - caption_h) / 2, (H - text_h) / 2
    else:
        text_x, art_y = pad, pad
        text_y = pad + art_h + caption_h + lead * 0.4
        H = math.ceil(text_y + text_h + pad)
    W = math.ceil(pad * 2 + (L["art"] + L["gap"] + L["cols"]) * cw)

    out = []
    for r, row in enumerate(rows):
        col, y = 0, text_y + (r + 1) * lead - lead * 0.28
        for text, role in row:
            out.append(ty.text(text_x + col * cw, y, text, "mono", size, c[role]))
            col += len(text)

    caption = "ζ(½ + it), 0 ≤ t ≤ 50"
    art = (f'<g transform="translate(0 {art_y:.1f})">'
           f'<path d="{path}" stroke="{c["text"]}" stroke-width="1.5" stroke-linecap="round"/>'
           f'<circle cx="{origin[0]:.1f}" cy="{origin[1]:.1f}" r="2.8" fill="none" stroke="{c["key"]}" stroke-width="1.1"/>'
           + ty.text(art_x + art_cols * cw / 2, art_h + lead * 1.2, caption, "mono", size * 0.9, c["dots"], anchor="middle")
           + "</g>")

    desc = (f"Cartão no estilo neofetch. À esquerda, a curva da função zeta de Riemann ζ(½ + it) em pontos braille. "
            f"À direita: Ciência da Computação na UFPel; iniciação científica em modelagem matemática (controle "
            f"populacional e EDPs); C, C++, Python e LaTeX; análise real; projetos atlas-pdf e modelagem; "
            f"{solved} problemas resolvidos no Codeforces como {CODEFORCES_USER}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">luiz@felipe</title>\n<desc id="d">{desc}</desc>\n'
            f"<defs>{ty.defs()}</defs>\n"
            f'<rect width="{W}" height="{H}" rx="12" fill="{c["bg"]}"/>\n{art}\n{"".join(out)}\n</svg>\n')


def main():
    solved = solved_count()
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for kind in LAYOUTS:
            name = f"neofetch-{theme}" if kind == "desktop" else f"neofetch-mobile-{theme}"
            (ASSETS / f"{name}.svg").write_text(render(solved, theme, kind), encoding="utf-8")
    print(f"Codeforces: {solved} resolvidos")


if __name__ == "__main__":
    main()
