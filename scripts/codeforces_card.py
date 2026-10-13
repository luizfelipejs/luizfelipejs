#!/usr/bin/env python3
"""Gera assets/codeforces[-mobile]-{light,dark}.svg com dados da API pública do Codeforces.

Uso: python3 scripts/codeforces_card.py root.svp
Se a API falhar, sai com erro e não mexe nos arquivos existentes.
Usa a mesma base visual dos outros cartões (design.py), então precisa do
fontTools e das fontes EB Garamond, Inter e JetBrains Mono.
"""

import json
import sys
import time
import urllib.request
from collections import Counter

from design import ASSETS, THEMES, Type, mix, svg

API = "https://codeforces.com/api/"

RANK_COLORS = {
    "newbie": ("#808080", "#9198a1"),
    "pupil": ("#008000", "#3fb950"),
    "specialist": ("#03a89e", "#2bc4b8"),
    "expert": ("#0000ff", "#6e8bff"),
    "candidate master": ("#aa00aa", "#d26ad2"),
    "master": ("#ff8c00", "#ffa53d"),
    "international master": ("#ff8c00", "#ffa53d"),
    "grandmaster": ("#ff0000", "#ff6b6b"),
    "international grandmaster": ("#ff0000", "#ff6b6b"),
    "legendary grandmaster": ("#ff0000", "#ff6b6b"),
}

LAYOUTS = {
    # stats: (y da linha dos números, largura da coluna); spark/hist: caixas (x, y, w, h)
    "desktop": dict(W=560, H=80, stats=(52, 66), spark=(292, 30, 128, 30), hist=(452, 30, 106, 30)),
    "mobile": dict(W=330, H=140, stats=(52, 82), spark=(0, 92, 168, 30), hist=(204, 92, 124, 30)),
}


def api(method, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{API}{method}?{query}", headers={"User-Agent": "luizfelipejs-readme"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            if data.get("status") == "OK":
                return data["result"]
            raise RuntimeError(data.get("comment", "resposta inválida"))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def collect(handle):
    user = api("user.info", handles=handle)[0]
    history = api("user.rating", handle=handle)
    submissions = api("user.status", handle=handle)

    solved = {}
    for s in submissions:
        if s.get("verdict") == "OK":
            p = s["problem"]
            solved[(p.get("contestId"), p["index"])] = p

    return {
        "handle": user["handle"],
        "rating": user.get("rating", 0),
        "max_rating": user.get("maxRating", 0),
        "rank": user.get("rank", "unrated"),
        "solved": len(solved),
        "submissions": len(submissions),
        "history": [(c["ratingUpdateTimeSeconds"], c["newRating"]) for c in history],
        "by_rating": sorted(Counter(p["rating"] for p in solved.values() if "rating" in p).items()),
        "tags": Counter(t for p in solved.values() for t in p.get("tags", [])).most_common(5),
    }


def header(d, c, ty, theme):
    rank_color = RANK_COLORS.get(d["rank"], ("#808080", "#9198a1"))[0 if theme == "light" else 1]
    handle_w = ty.width(d["handle"], "italic", 15)
    return (ty.text(0, 16, d["handle"], "italic", 15, c["ink"])
            + f'<circle cx="{handle_w + 10:.1f}" cy="11.5" r="2.4" fill="{rank_color}"/>'
            + ty.text(handle_w + 17, 16, d["rank"], "italic", 13, c["muted"]))


def stats(d, c, ty, y, col):
    items = [("RATING", d["rating"]), ("MÁXIMO", d["max_rating"]),
             ("RESOLVIDOS", d["solved"]), ("CONTESTS", len(d["history"]))]
    out = []
    for i, (label, value) in enumerate(items):
        out.append(ty.text(i * col - 1, y, str(value), "serif", 25, c["ink"], features=("lnum",)))
        out.append(ty.text(i * col, y + 15, label, "mono", 7, c["muted"], tracking=0.12))
    return out


def sparkline(d, c, ty, x, y, w, h):
    """Rating depois de cada contest, numa linha fina com o último ponto marcado."""
    out = [ty.text(x, y + h + 15, "RATING POR CONTEST", "mono", 7, c["muted"], tracking=0.12)]
    pts = d["history"]
    if not pts:
        return out
    ratings = [r for _, r in pts]
    lo, hi = min(ratings), max(ratings)
    t0, t1 = pts[0][0], pts[-1][0]
    xy = [(x + w * ((ts - t0) / (t1 - t0) if t1 > t0 else 1), y + h - h * ((r - lo) / (hi - lo) if hi > lo else 0.5))
          for ts, r in pts]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in xy)
    out.append(f'<path d="M{x},{y + h}H{x + w}" stroke="{c["line"]}"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{c["ink"]}" stroke-width="1" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle cx="{xy[-1][0]:.1f}" cy="{xy[-1][1]:.1f}" r="2.2" fill="{c["ink"]}"/>')
    return out


def histogram(d, c, ty, x, y, w, h):
    """Problemas resolvidos por dificuldade, em barras finas."""
    buckets = d["by_rating"]
    if not buckets:
        return []
    caption = f"DIFICULDADE {buckets[0][0]}–{buckets[-1][0]}"
    out = [ty.text(x, y + h + 15, caption, "mono", 7, c["muted"], tracking=0.12),
           f'<path d="M{x},{y + h}H{x + w}" stroke="{c["line"]}"/>']
    peak = max(n for _, n in buckets)
    slot = w / len(buckets)
    for i, (_, n) in enumerate(buckets):
        bh = max(1.5, (h - 2) * n / peak)
        out.append(f'<rect x="{x + slot * i + slot * 0.3:.1f}" y="{y + h - bh:.1f}" width="{slot * 0.4:.1f}" '
                   f'height="{bh:.1f}" fill="{mix(c["ink"], c["page"], 0.45)}"/>')
    return out


def render(d, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    body = [header(d, c, ty, theme), *stats(d, c, ty, *L["stats"]),
            *sparkline(d, c, ty, *L["spark"]), *histogram(d, c, ty, *L["hist"])]
    desc = (f'{d["handle"]} no Codeforces: rating {d["rating"]} ({d["rank"]}), máximo {d["max_rating"]}, '
            f'{d["solved"]} problemas resolvidos em {len(d["history"])} contests.')
    return svg(L["W"], L["H"], "".join(body), title="Estatísticas no Codeforces", desc=desc, defs=ty.defs())


def main():
    handle = sys.argv[1] if len(sys.argv) > 1 else "root.svp"
    data = collect(handle)
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for kind in LAYOUTS:
            name = f"codeforces-{theme}" if kind == "desktop" else f"codeforces-mobile-{theme}"
            (ASSETS / f"{name}.svg").write_text(render(data, theme, kind), encoding="utf-8")
    print(f'{data["handle"]}: {data["rating"]} ({data["rank"]}), {data["solved"]} resolvidos')


if __name__ == "__main__":
    main()
