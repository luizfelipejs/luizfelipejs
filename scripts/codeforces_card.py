#!/usr/bin/env python3
"""Gera assets/codeforces[-mobile]-{light,dark}.svg com dados da API pública do Codeforces.

Uso: python3 scripts/codeforces_card.py root.svp
Se a API falhar, sai com erro e não mexe nos arquivos existentes.
Usa a mesma base visual dos outros cartões (design.py), então precisa do
fontTools e das fontes EB Garamond, Inter e JetBrains Mono.
"""

import json
import math
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone

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
    "desktop": dict(W=1000, pad=2, stat_cols=4, stat_y=(104, 62), charts_y=178, chart_h=112, side_by_side=True),
    "mobile": dict(W=480, pad=2, stat_cols=2, stat_y=(100, 66), charts_y=240, chart_h=120, side_by_side=False),
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


def header(d, c, ty, theme, x, right):
    rank_color = RANK_COLORS.get(d["rank"], ("#808080", "#9198a1"))[0 if theme == "light" else 1]
    rank_w = ty.width(d["rank"], "italic", 16)
    return (ty.text(x - 1, 40, d["handle"], "italic", 22, c["ink"])
            + f'<circle cx="{right - rank_w - 10:.1f}" cy="34.5" r="3" fill="{rank_color}"/>'
            + ty.text(right, 40, d["rank"], "italic", 16, c["muted"], anchor="end"))


def stats(d, c, ty, x0, width, cols, y, row_h):
    items = [("RATING ATUAL", d["rating"]), ("RATING MÁXIMO", d["max_rating"]),
             ("RESOLVIDOS", d["solved"]), ("CONTESTS", len(d["history"]))]
    col = width / cols
    out = []
    for i, (label, value) in enumerate(items):
        x = x0 + (i % cols) * col
        yy = y + (i // cols) * row_h
        out.append(ty.text(x - 1.5, yy, str(value), "serif", 38, c["ink"], features=("lnum",)))
        out.append(ty.text(x, yy + 22, label, "mono", 8.5, c["muted"], tracking=0.14))
    return out


def rating_chart(d, c, ty, x0, y0, w, h):
    out = [ty.text(x0, y0, "RATING POR CONTEST", "mono", 8.5, c["muted"], tracking=0.14)]
    pts = d["history"]
    if not pts:
        return out + [ty.text(x0, y0 + h / 2, "sem contests ainda", "italic", 15, c["muted"])]

    left, top, bottom, right = x0 + 34, y0 + 22, y0 + h - 22, x0 + w - 34
    ratings = [r for _, r in pts]
    lo = max(0, (min(ratings) // 100) * 100)
    step = max(100, -(-(max(ratings) - lo) // 200) * 100)
    hi = lo + 2 * step
    t0, t1 = pts[0][0], pts[-1][0]

    def sx(ts):
        return left + (right - left) * ((ts - t0) / (t1 - t0) if t1 > t0 else 0.5)

    def sy(r):
        return bottom - (bottom - top) * (r - lo) / (hi - lo)

    for v in (lo, lo + step, hi):
        out.append(f'<path d="M{left},{sy(v):.1f}H{right}" stroke="{c["line"]}" stroke-dasharray="1 4"/>')
        out.append(ty.text(left - 10, sy(v) + 3.5, str(v), "mono", 8.5, c["muted"], anchor="end"))

    xy = [(sx(ts), sy(r)) for ts, r in pts]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    out.append(f'<polyline points="{line}" fill="none" stroke="{c["ink"]}" stroke-width="1.3" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for x, y in xy:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{c["page"]}" stroke="{c["ink"]}" stroke-width="1.2"/>')
    out.append(ty.text(xy[-1][0] + 9, xy[-1][1] + 4, str(pts[-1][1]), "mono", 10, c["ink"]))

    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%y")
    out.append(ty.text(left, bottom + 18, fmt(t0), "mono", 8.5, c["muted"]))
    if t1 > t0:
        out.append(ty.text(right, bottom + 18, fmt(t1), "mono", 8.5, c["muted"], anchor="end"))
    return out


def difficulty_chart(d, c, ty, x0, y0, w, h):
    out = [ty.text(x0, y0, "RESOLVIDOS POR DIFICULDADE", "mono", 8.5, c["muted"], tracking=0.14)]
    buckets = d["by_rating"]
    if not buckets:
        return out
    top, bottom = y0 + 30, y0 + h - 22
    peak = max(n for _, n in buckets)
    slot = w / len(buckets)
    bw = min(34, slot * 0.46)
    out.append(f'<rect x="{x0}" y="{bottom}" width="{w}" height="1" fill="{c["line"]}"/>')
    for i, (rating, n) in enumerate(buckets):
        cx = x0 + slot * (i + 0.5)
        bh = max(2, (bottom - top - 14) * n / peak)
        out.append(f'<rect x="{cx - bw / 2:.1f}" y="{bottom - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                   f'fill="{mix(c["ink"], c["page"], 0.62)}"/>')
        out.append(ty.text(cx, bottom - bh - 7, str(n), "mono", 10, c["ink"], anchor="middle"))
        out.append(ty.text(cx, bottom + 17, str(rating), "mono", 8.5, c["muted"], anchor="middle"))
    return out


def tags_block(d, c, ty, x, y, width):
    if not d["tags"]:
        return [], y
    out = [ty.text(x, y, "TAGS MAIS RESOLVIDAS", "mono", 8.5, c["muted"], tracking=0.14)]
    cx, cy = x, y + 24
    for tag, n in d["tags"]:
        tag_w = ty.width(tag, "italic", 15)
        count_w = ty.width(str(n), "mono", 9.5)
        if cx + tag_w + count_w + 6 > x + width:
            cx, cy = x, cy + 22
        out.append(ty.text(cx, cy, tag, "italic", 15, c["ink"]))
        out.append(ty.text(cx + tag_w + 5, cy, str(n), "mono", 9.5, c["muted"]))
        cx += tag_w + count_w + 24
    return out, cy


def render(d, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    W, pad = L["W"], L["pad"]
    stat_y, row_h = L["stat_y"]
    rows = math.ceil(4 / L["stat_cols"])
    body = [header(d, c, ty, theme, pad, W - pad)]
    body += stats(d, c, ty, pad, W - 2 * pad, L["stat_cols"], stat_y, row_h)
    rule_y = stat_y + (rows - 1) * row_h + 44
    body.append(f'<rect x="{pad}" y="{rule_y}" width="{W - 2 * pad}" height="1" fill="{c["line"]}"/>')

    y, ch = L["charts_y"], L["chart_h"]
    if L["side_by_side"]:
        half = (W - 2 * pad - 60) / 2
        body += rating_chart(d, c, ty, pad, y, half, ch)
        body += difficulty_chart(d, c, ty, pad + half + 60, y, half, ch)
        y += ch + 30
    else:
        body += rating_chart(d, c, ty, pad, y, W - 2 * pad, ch)
        y += ch + 34
        body += difficulty_chart(d, c, ty, pad, y, W - 2 * pad, ch)
        y += ch + 30
    tags, y = tags_block(d, c, ty, pad, y, W - 2 * pad)
    body += tags
    H = math.ceil(y + 16)
    desc = (f'{d["handle"]} no Codeforces: rating {d["rating"]} ({d["rank"]}), máximo {d["max_rating"]}, '
            f'{d["solved"]} problemas resolvidos em {len(d["history"])} contests.')
    return svg(W, H, "".join(body), title="Estatísticas no Codeforces", desc=desc, defs=ty.defs())


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
