#!/usr/bin/env python3
"""Gera o cartão do perfil, um terminal rodando neofetch: assets/neofetch[-mobile]-{light,dark}.svg.

Ao abrir a página, o comando `neofetch` é digitado no prompt e a saída é impressa
linha a linha: à esquerda, no lugar do logo da distro, a curva ζ(½ + it) numa
malha de pontos braille; à direita, formação, pesquisa, projetos e o número de
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
PROMPT = "luiz@felipe:~$ "
COMMAND = "neofetch"

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f", prompt="#7ee787"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#c2cfde", prompt="#116329"),
}

# art: colunas do desenho (0 = desenho em cima do texto); cols: largura do texto em caracteres
LAYOUTS = {
    "desktop": dict(size=11, lead=15, pad=16, art=34, gap=5, cols=82, short=False),
    "mobile": dict(size=11, lead=15, pad=12, art=0, gap=0, cols=44, short=True, art_mobile=24),
}

# tempos da animação, em segundos
TYPE_START, TYPE_STEP, PRINT_GAP, LINE_STEP = 0.7, 0.09, 0.35, 0.055


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
    """Rasteriza a curva numa malha de 2 × 4 pontos por caractere, como um terminal com braille.

    Devolve um caminho por linha de texto (para imprimir linha a linha), o número
    de linhas ocupadas e a posição da origem.
    """
    dx, dy = cw / 2, lead / 4
    re0, re1, im1 = -1.55, 3.75, 2.25
    scale = cols * cw / (re1 - re0)
    dots = {(math.floor((z.real - re0) * scale / dx), math.floor((im1 - z.imag) * scale / dy)) for z in CURVE}
    rows = {}
    for i, j in sorted(dots, key=lambda d: (d[1], d[0])):
        rows.setdefault(j // 4, []).append(f"M{x0 + (i + .5) * dx:.1f},{y0 + (j + .5) * dy:.1f}h0")
    return {r: "".join(p) for r, p in rows.items()}, max(rows) + 1, (x0 - re0 * scale, y0 + im1 * scale)


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
        kv("Curso", s("Ciência da Computação · Universidade Federal de Pelotas", "Ciência da Computação · UFPel"), width),
        kv("Pesquisa", s("IC em modelagem matemática: controle populacional e EDPs", "IC em modelagem, EDPs"), width),
        kv("Linguagens", "C, C++, Python, LaTeX", width),
        kv("Matemática", s("análise real, espaços métricos, integração de Lebesgue", "análise real, medida"), width),
        kv("Interesses", s("arquitetura de computadores, memória, concorrência", "arquitetura, concorrência"), width),
        section("Projetos", width),
        kv("atlas-pdf", s("biblioteca de PDFs por conteúdo · Python, Electron, SQLite", "PDFs por conteúdo"), width),
        kv("modelagem", s("mapa logístico e caos, farmacocinética, ajuste de modelos", "caos e ajuste de modelos"), width),
        section("Codeforces", width),
        kv(CODEFORCES_USER, f"{solved} problemas resolvidos", width),
    ]


# ---- o terminal ------------------------------------------------------------------

def at(delay, body):
    """Elemento que aparece de uma vez no instante `delay`, como texto impresso no terminal."""
    return f'<g class="p" style="animation-delay:{delay:.2f}s">{body}</g>'


def render(solved, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    size, lead, pad = L["size"], L["lead"], L["pad"]
    cw = size * 0.6  # a JetBrains Mono tem avanço de 600/1000 em todos os glifos
    bar = 28
    W = math.ceil(pad * 2 + (L["art"] + L["gap"] + L["cols"]) * cw)
    top = bar + pad * 0.6

    def x_of(col):
        return pad + col * cw

    def y_of(row):  # linha de base da linha `row` do terminal
        return top + (row + 1) * lead - lead * 0.28

    def write(col, row, segments):
        out = []
        for text, role in segments:
            out.append(ty.text(x_of(col), y_of(row), text, "mono", size, c[role]))
            col += len(text)
        return "".join(out)

    info = lines(solved, L["cols"], L["short"])
    art_cols = L["art"] or L["art_mobile"]
    art_col = 0 if L["art"] else (L["cols"] - art_cols) / 2
    first = 2  # linha 0: prompt com o comando; linha 1: em branco
    art, art_rows, origin = braille(x_of(art_col), top + first * lead, art_cols, cw, lead)
    caption_row = first + art_rows
    if L["art"]:
        info_row = first + max(0, (art_rows + 1 - len(info)) // 2)
        info_col = L["art"] + L["gap"]
        last = max(caption_row, info_row + len(info) - 1)
    else:
        info_row, info_col = caption_row + 2, 0
        last = info_row + len(info) - 1
    final_row = last + 2
    H = math.ceil(y_of(final_row) + lead * 0.28 + pad)

    # 1) prompt e o comando digitado letra a letra
    out = [write(0, 0, [(PROMPT, "prompt")])]
    for k, ch in enumerate(COMMAND):
        out.append(at(TYPE_START + k * TYPE_STEP, write(len(PROMPT) + k, 0, [(ch, "text")])))
    typed = TYPE_START + len(COMMAND) * TYPE_STEP
    start = typed + PRINT_GAP

    # 2) a saída, linha a linha: desenho e informações saem juntos em cada linha
    delay = lambda row: start + (row - first) * LINE_STEP
    for r in range(art_rows):
        if r in art:
            out.append(at(delay(first + r), f'<path d="{art[r]}" stroke="{c["text"]}" stroke-width="1.5" stroke-linecap="round"/>'))
    out.append(at(delay(first + art_rows // 2),
                  f'<circle cx="{origin[0]:.1f}" cy="{origin[1]:.1f}" r="2.8" fill="none" stroke="{c["key"]}" stroke-width="1.1"/>'))
    caption = "ζ(½ + it), 0 ≤ t ≤ 50"
    out.append(at(delay(caption_row), ty.text(x_of(art_col + art_cols / 2), y_of(caption_row), caption, "mono",
                                              size * 0.9, c["dots"], anchor="middle")))
    for k, segments in enumerate(info):
        out.append(at(delay(info_row + k), write(info_col, info_row + k, segments)))

    # 3) prompt novo, com o cursor piscando
    end = delay(last) + 0.25
    cursor = (f'<rect class="blink" x="{x_of(len(PROMPT)):.1f}" y="{y_of(final_row) - size * 0.8:.1f}" '
              f'width="{cw:.1f}" height="{size:.1f}" fill="{c["text"]}" style="animation-delay:{end:.2f}s"/>')
    out.append(at(end, write(0, final_row, [(PROMPT, "prompt")]) + cursor))
    # cursor do primeiro prompt: anda enquanto o comando é digitado e some no Enter
    out.append(f'<rect class="typing" x="{x_of(len(PROMPT)):.1f}" y="{y_of(0) - size * 0.8:.1f}" '
               f'width="{cw:.1f}" height="{size:.1f}" fill="{c["text"]}"/>')

    span = start
    css = (".p{animation:p .01s steps(1) both}@keyframes p{from{opacity:0}to{opacity:1}}"
           ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
           f".typing{{animation:typing {span:.2f}s linear forwards}}"
           f"@keyframes typing{{0%{{transform:translateX(0)}}"
           f"{TYPE_START / span * 100:.1f}%{{transform:translateX(0);animation-timing-function:steps({len(COMMAND)},jump-start)}}"
           f"{typed / span * 100:.1f}%{{transform:translateX({len(COMMAND) * cw:.1f}px);opacity:1}}"
           f"{(typed + 0.01) / span * 100:.1f}%,100%{{transform:translateX({len(COMMAND) * cw:.1f}px);opacity:0}}}}"
           "@media (prefers-reduced-motion:reduce){.p,.blink{animation:none}.typing{display:none}}")

    dots_bar = "".join(f'<circle cx="{pad + 6 + i * 16}" cy="{bar / 2 + 1}" r="4.5" fill="{c["dots"]}"/>' for i in range(3))
    title = ty.text(W / 2, bar / 2 + 4.5, "luiz@felipe: ~", "mono", size * 0.9, c["dots"], anchor="middle")
    desc = (f"Terminal em que o comando neofetch é digitado e a saída aparece linha a linha. À esquerda, a curva da "
            f"função zeta de Riemann ζ(½ + it) em pontos braille. À direita: Ciência da Computação na UFPel; "
            f"iniciação científica em modelagem matemática (controle populacional e EDPs); C, C++, Python e LaTeX; "
            f"análise real; projetos atlas-pdf e modelagem; {solved} problemas resolvidos no Codeforces como "
            f"{CODEFORCES_USER}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">luiz@felipe</title>\n<desc id="d">{desc}</desc>\n'
            f"<style>{css}</style>\n<defs>{ty.defs()}</defs>\n"
            f'<rect width="{W}" height="{H}" rx="12" fill="{c["bg"]}"/>\n'
            f'{dots_bar}{title}<rect x="0" y="{bar + 4}" width="{W}" height="1" fill="{c["dots"]}" opacity=".35"/>\n'
            f'{"".join(out)}\n</svg>\n')


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
