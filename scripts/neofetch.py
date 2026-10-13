#!/usr/bin/env python3
"""Gera o cartão do perfil, um terminal rodando neofetch: assets/neofetch[-mobile]-{light,dark}.svg.

Ao abrir a página, o comando `neofetch` é digitado no prompt e a saída é impressa
linha a linha: formação, pesquisa, projetos e o número de problemas resolvidos no
Codeforces, puxado da API pública. Roda todo dia pelo workflow.

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

# columns: larguras das colunas de informação, em caracteres; no desktop ficam lado a lado, para o cartão ser baixo
LAYOUTS = {
    "desktop": dict(size=11, lead=15, pad=14, columns=(56, 56), col_gap=8),
    "mobile": dict(size=11, lead=15, pad=12, columns=(44,), col_gap=0),
}

# tempos da animação, em segundos
TYPE_START, TYPE_STEP, PRINT_GAP, LINE_STEP = 0.7, 0.09, 0.35, 0.07


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


# ---- texto ---------------------------------------------------------------------

def kv(key, value, width):
    """'. Chave: ........ valor', com os pontos completando a largura."""
    fill = max(1, width - len(key) - len(value) - 5)
    return [(". ", "dots"), (key, "key"), (": ", "text"), ("." * fill, "dots"), (" " + value, "value")]


def section(title, width):
    return [("- ", "dots"), (title, "text"), (" " + "─" * (width - len(title) - 3), "dots")]


def columns(solved, widths):
    """As informações, em uma coluna (celular) ou duas lado a lado (desktop)."""
    header = [("luiz", "value"), ("@", "text"), ("felipe", "value")]
    if len(widths) == 1:
        (w,) = widths
        return [[
            header + [(" " + "─" * (w - 12), "dots")],
            kv("Curso", "Ciência da Computação · UFPel", w),
            kv("Pesquisa", "IC em modelagem, EDPs", w),
            kv("Linguagens", "C, C++, Python, LaTeX", w),
            kv("Matemática", "análise real, medida", w),
            section("Projetos", w),
            kv("atlas-pdf", "PDFs por conteúdo", w),
            kv("modelagem", "caos e ajuste de modelos", w),
            section("Codeforces", w),
            kv(CODEFORCES_USER, f"{solved} problemas resolvidos", w),
        ]]
    left, right = widths
    return [
        [
            header + [(" " + "─" * (left - 12), "dots")],
            kv("Curso", "Ciência da Computação · UFPel", left),
            kv("Pesquisa", "IC: controle populacional e EDPs", left),
            kv("Linguagens", "C, C++, Python, LaTeX", left),
            kv("Matemática", "análise real, espaços métricos, Lebesgue", left),
        ],
        [
            section("Projetos", right),
            kv("atlas-pdf", "biblioteca de PDFs por conteúdo · Electron", right),
            kv("modelagem", "mapa logístico, farmacocinética, ajustes", right),
            section("Codeforces", right),
            kv(CODEFORCES_USER, f"{solved} problemas resolvidos", right),
        ],
    ]


# ---- o terminal ------------------------------------------------------------------

def at(delay, body):
    """Elemento que aparece de uma vez no instante `delay`, como texto impresso no terminal."""
    return f'<g class="p" style="animation-delay:{delay:.2f}s">{body}</g>'


def render(solved, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    size, lead, pad = L["size"], L["lead"], L["pad"]
    cw = size * 0.6  # a JetBrains Mono tem avanço de 600/1000 em todos os glifos
    width = sum(L["columns"]) + L["col_gap"] * (len(L["columns"]) - 1)
    W = math.ceil(pad * 2 + width * cw)
    top = pad * 0.55

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

    info = columns(solved, L["columns"])
    final_row = 1 + max(len(col) for col in info)
    H = math.ceil(y_of(final_row) + lead * 0.28 + pad * 0.55)

    # 1) prompt e o comando digitado letra a letra
    out = [write(0, 0, [(PROMPT, "prompt")])]
    for k, ch in enumerate(COMMAND):
        out.append(at(TYPE_START + k * TYPE_STEP, write(len(PROMPT) + k, 0, [(ch, "text")])))
    typed = TYPE_START + len(COMMAND) * TYPE_STEP
    start = typed + PRINT_GAP

    # 2) a saída, linha a linha
    col = 0
    for col_width, rows in zip(L["columns"], info):
        for k, segments in enumerate(rows):
            out.append(at(start + k * LINE_STEP, write(col, 1 + k, segments)))
        col += col_width + L["col_gap"]

    # 3) prompt novo, com o cursor piscando
    end = start + (final_row - 1) * LINE_STEP + 0.25
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

    desc = (f"Terminal em que o comando neofetch é digitado e a saída aparece linha a linha: Ciência da Computação "
            f"na UFPel; iniciação científica em modelagem matemática (controle populacional e EDPs); C, C++, Python e "
            f"LaTeX; análise real; projetos atlas-pdf e modelagem; {solved} problemas resolvidos no Codeforces como "
            f"{CODEFORCES_USER}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">luiz@felipe</title>\n<desc id="d">{desc}</desc>\n'
            f"<style>{css}</style>\n<defs>{ty.defs()}</defs>\n"
            f'<rect width="{W}" height="{H}" rx="10" fill="{c["bg"]}"/>\n{"".join(out)}\n</svg>\n')


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
