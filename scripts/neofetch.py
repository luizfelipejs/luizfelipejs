#!/usr/bin/env python3
"""Gera o cartão do perfil no formato do neofetch: assets/neofetch[-mobile]-{light,dark}.svg.

À esquerda, no lugar do logo da distro, a curva ζ(½ + it) desenhada numa malha
de pontos braille; à direita, as informações, com números puxados das APIs
públicas do GitHub e do Codeforces. Roda todo dia pelo workflow.

Uso: python3 scripts/neofetch.py
Se alguma API falhar, sai com erro e não mexe nos arquivos existentes.
Precisa do fontTools e da fonte JetBrains Mono (veja design.py).
"""

import json
import math
import os
import time
import urllib.request
from datetime import date, datetime

from design import ASSETS, Type

GITHUB_USER = "luizfelipejs"
CODEFORCES_USER = "root.svp"

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f",
                 blocks=("#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4")),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#c2cfde",
                  blocks=("#24292f", "#cf222e", "#116329", "#4d2d00", "#0969da", "#8250df", "#1b7c83", "#6e7781")),
}

# size: corpo da fonte; cols: largura do texto em caracteres; art: colunas do desenho (0 = em cima do texto)
LAYOUTS = {
    "desktop": dict(size=11, lead=15, pad=14, art=28, gap=3, cols=52, short=False),
    "mobile": dict(size=11, lead=15, pad=12, art=0, gap=0, cols=46, short=True, art_mobile=26),
}


# ---- dados -----------------------------------------------------------------

def get(url, token=None):
    headers = {"User-Agent": "luizfelipejs-readme", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
                return json.load(resp)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def codeforces(method, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    data = get(f"https://codeforces.com/api/{method}?{query}")
    if data.get("status") != "OK":
        raise RuntimeError(data.get("comment", "resposta inválida do Codeforces"))
    return data["result"]


def collect():
    token = os.environ.get("GITHUB_TOKEN")
    user = get(f"https://api.github.com/users/{GITHUB_USER}", token)
    repos = get(f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100", token)
    commits = get(f"https://api.github.com/search/commits?q=author:{GITHUB_USER}", token)

    cf = codeforces("user.info", handles=CODEFORCES_USER)[0]
    contests = codeforces("user.rating", handle=CODEFORCES_USER)
    solved = {(s["problem"].get("contestId"), s["problem"]["index"])
              for s in codeforces("user.status", handle=CODEFORCES_USER) if s.get("verdict") == "OK"}

    return {
        "since": datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).date(),
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos if not r["fork"]),
        "commits": commits["total_count"],
        "rating": cf.get("rating", 0),
        "max_rating": cf.get("maxRating", 0),
        "rank": cf.get("rank", "unrated"),
        "solved": len(solved),
        "contests": len(contests),
    }


def uptime(since, today):
    """Tempo desde a criação da conta, como o uptime do neofetch."""
    years, months, days = today.year - since.year, today.month - since.month, today.day - since.day
    if days < 0:
        months -= 1
        prev = date(today.year - (today.month == 1), (today.month - 2) % 12 + 1, 1)
        days += (date(today.year, today.month, 1) - prev).days
    if months < 0:
        years, months = years - 1, months + 12
    plural = lambda n, one, many: f"{n} {one if n == 1 else many}"
    return f"{plural(years, 'ano', 'anos')}, {plural(months, 'mês', 'meses')}, {plural(days, 'dia', 'dias')}"


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
    dots = set()
    for z in CURVE:
        i = math.floor((z.real - re0) * scale / dx)
        j = math.floor((im1 - z.imag) * scale / dy)
        dots.add((i, j))
    height = (im1 - im0) * scale
    origin = (x0 + (0 - re0) * scale, y0 + im1 * scale)
    path = "".join(f"M{x0 + (i + .5) * dx:.1f},{y0 + (j + .5) * dy:.1f}h0" for i, j in sorted(dots))
    return path, height, origin


# ---- texto ---------------------------------------------------------------------

def kv(key, value, width):
    """'. Chave: ........ valor', com os pontos completando a largura."""
    fill = max(1, width - len(key) - len(value) - 5)
    return [(". ", "dots"), (key, "key"), (": ", "text"), ("." * fill, "dots"), (" " + value, "value")]


def pair(k1, v1, k2, v2, width):
    left = (width - 3) // 2
    a, b = kv(k1, v1, left + 0), kv(k2, v2, width - left - 3 + 2)
    return a + [(" | ", "text")] + b[1:]


def section(title, width):
    return [("- ", "dots"), (title, "text"), (" " + "─" * (width - len(title) - 3), "dots")]


def lines(d, width, short):
    today = date.today()
    s = lambda full, brief: brief if short else full
    return [
        [("luiz", "value"), ("@", "text"), ("felipe", "value"), (" " + "─" * (width - 12), "dots")],
        kv("OS", s("Linux · Ubuntu 24.04", "Linux · Ubuntu"), width),
        kv("Uptime", uptime(d["since"], today), width),
        kv("Host", s("Universidade Federal de Pelotas", "UFPel"), width),
        kv("Kernel", "Ciência da Computação", width),
        kv("Shell", "zsh · bash", width),
        kv("Languages", "C, C++, Python, LaTeX", width),
        kv("Math", s("análise real, espaços métricos, Lebesgue", "análise real, Lebesgue"), width),
        kv("Systems", s("cache, memória, concorrência", "cache, concorrência"), width),
        section("Projects", width),
        kv("atlas-pdf", s("biblioteca de PDFs para Linux", "biblioteca de PDFs"), width),
        kv("modelagem", s("EDOs, caos e estatística", "EDOs e caos"), width),
        section(f"Codeforces · {CODEFORCES_USER}", width),
        pair("Rating", str(d["rating"]), "Máximo", str(d["max_rating"]), width),
        pair("Resolvidos", str(d["solved"]), "Contests", str(d["contests"]), width),
        section("GitHub", width),
        pair("Repos", str(d["repos"]), "Stars", str(d["stars"]), width),
        pair("Commits", str(d["commits"]), "Followers", str(d["followers"]), width),
    ]


def render(d, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    size, lead, pad = L["size"], L["lead"], L["pad"]
    cw = size * 0.6  # a JetBrains Mono tem avanço de 600/1000 em todos os glifos
    rows = lines(d, L["cols"], L["short"])

    if L["art"]:
        text_x, text_y = pad + (L["art"] + L["gap"]) * cw, pad
    else:
        text_x = pad
    art_cols = L["art"] or L["art_mobile"]
    art_x = pad if L["art"] else pad + (L["cols"] - art_cols) * cw / 2
    path, art_h, origin = braille(art_x, 0, art_cols, cw, lead)
    caption_h = lead * 1.6
    block_h = len(rows) * lead + lead * 1.4  # texto + blocos de cor
    if L["art"]:
        H = math.ceil(pad * 2 + max(block_h, art_h + caption_h))
        art_y = (H - art_h - caption_h) / 2
    else:
        art_y = pad
        text_y = pad + art_h + caption_h + lead * 0.4
        H = math.ceil(text_y + block_h + pad)
    W = math.ceil(pad * 2 + (L["art"] + L["gap"] + L["cols"]) * cw)

    out = []
    for r, row in enumerate(rows):
        col, y = 0, text_y + (r + 1) * lead - lead * 0.28
        for text, role in row:
            out.append(ty.text(text_x + col * cw, y, text, "mono", size, c[role]))
            col += len(text)
    block_y = text_y + len(rows) * lead + lead * 0.55
    for i, color in enumerate(c["blocks"]):
        out.append(f'<rect x="{text_x + i * 3 * cw:.1f}" y="{block_y:.1f}" width="{3 * cw - 2:.1f}" height="{lead * 0.72:.1f}" rx="2" fill="{color}"/>')
    cursor_x = text_x + len(c["blocks"]) * 3 * cw + cw
    out.append(f'<rect class="cursor" x="{cursor_x:.1f}" y="{block_y:.1f}" width="{cw:.1f}" height="{lead * 0.72:.1f}" fill="{c["text"]}"/>')

    caption = "ζ(½ + it), 0 ≤ t ≤ 50"
    art = (f'<g transform="translate(0 {art_y:.1f})">'
           f'<path d="{path}" stroke="{c["text"]}" stroke-width="1.5" stroke-linecap="round"/>'
           f'<circle cx="{origin[0]:.1f}" cy="{origin[1]:.1f}" r="2.8" fill="none" stroke="{c["key"]}" stroke-width="1.1"/>'
           + ty.text(art_x + art_cols * cw / 2, art_h + lead * 1.2, caption, "mono", size * 0.9, c["dots"], anchor="middle")
           + "</g>")

    desc = (f"Cartão no estilo neofetch. À esquerda, a curva da função zeta de Riemann ζ(½ + it) desenhada em pontos "
            f"braille. À direita: Luiz Felipe, Ciência da Computação na UFPel; programa em C, C++ e Python; interesses em "
            f"análise real e sistemas. Codeforces {CODEFORCES_USER}: rating {d['rating']}, {d['solved']} problemas "
            f"resolvidos. GitHub: {d['repos']} repositórios, {d['commits']} commits.")
    css = (".cursor{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
           "@media (prefers-reduced-motion:reduce){.cursor{animation:none}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">luiz@felipe</title>\n<desc id="d">{desc}</desc>\n'
            f"<style>{css}</style>\n<defs>{ty.defs()}</defs>\n"
            f'<rect width="{W}" height="{H}" rx="12" fill="{c["bg"]}"/>\n{art}\n{"".join(out)}\n</svg>\n')


def main():
    data = collect()
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for kind in LAYOUTS:
            name = f"neofetch-{theme}" if kind == "desktop" else f"neofetch-mobile-{theme}"
            (ASSETS / f"{name}.svg").write_text(render(data, theme, kind), encoding="utf-8")
    print(f'{data["repos"]} repos, {data["commits"]} commits; Codeforces {data["rating"]}, {data["solved"]} resolvidos')


if __name__ == "__main__":
    main()
