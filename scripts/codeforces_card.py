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

from design import ASSETS, THEMES, Type, card, gradient_stops, spectrum

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
    "desktop": dict(W=1000, pad=40, stat_cols=4, stat_y=(166, 70), charts_y=256, chart_h=128, side_by_side=True),
    "mobile": dict(W=480, pad=26, stat_cols=2, stat_y=(156, 84), charts_y=344, chart_h=132, side_by_side=False),
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
    rank = d["rank"].upper()
    rank_w = ty.width(rank, "mono", 9.5, 0.16)
    chip_x = right - rank_w - 34
    return (ty.text(x, 50, "CODEFORCES", "mono", 9.5, c["muted"], tracking=0.16)
            + ty.text(x - 1, 84, d["handle"], "italic", 30, c["ink"])
            + f'<rect x="{chip_x:.1f}" y="44.5" width="{rank_w + 34:.1f}" height="26" rx="13" fill="none" stroke="{c["border"]}"/>'
            + f'<circle cx="{chip_x + 14:.1f}" cy="57.5" r="3.5" fill="{rank_color}"/>'
            + ty.text(chip_x + 24, 61, rank, "mono", 9.5, c["text"], tracking=0.16))


def stats(d, c, ty, x0, width, cols, y, row_h):
    items = [("RATING ATUAL", d["rating"]), ("RATING MÁXIMO", d["max_rating"]),
             ("RESOLVIDOS", d["solved"]), ("CONTESTS", len(d["history"]))]
    col = width / cols
    out = []
    for i, (label, value) in enumerate(items):
        x = x0 + (i % cols) * col
        yy = y + (i // cols) * row_h
        out.append(ty.text(x - 2, yy, str(value), "serif", 54, c["ink"], features=("lnum",)))
        out.append(f'<rect x="{x:.1f}" y="{yy + 13}" width="18" height="1.5" fill="{spectrum(c["spectrum"], i / 3)}"/>')
        out.append(ty.text(x, yy + 32, label, "mono", 9, c["muted"], tracking=0.16))
    return out


def rating_chart(d, c, ty, x0, y0, w, h):
    out = [ty.text(x0, y0, "RATING POR CONTEST", "mono", 9, c["muted"], tracking=0.16)]
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
        out.append(f'<path d="M{left},{sy(v):.1f}H{right}" stroke="{c["grid"]}" stroke-dasharray="2 4"/>')
        out.append(ty.text(left - 10, sy(v) + 3.5, str(v), "mono", 9, c["muted"], anchor="end"))

    xy = [(sx(ts), sy(r)) for ts, r in pts]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    area = f"M{xy[0][0]:.1f},{bottom}L{line.replace(' ', 'L')}L{xy[-1][0]:.1f},{bottom}Z"
    out.append(f'<path d="{area}" fill="url(#area)"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="url(#stroke)" stroke-width="2" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for i, (x, y) in enumerate(xy):
        col = spectrum(c["spectrum"], (x - left) / max(right - left, 1))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c["bg"]}" stroke="{col}" stroke-width="2"/>')
    out.append(ty.text(xy[-1][0] + 10, xy[-1][1] + 4, str(pts[-1][1]), "mono", 11, c["ink"]))

    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%y")
    out.append(ty.text(left, bottom + 18, fmt(t0), "mono", 9, c["muted"]))
    if t1 > t0:
        out.append(ty.text(right, bottom + 18, fmt(t1), "mono", 9, c["muted"], anchor="end"))
    return out


def bar(x, y, w, h, r, fill):
    """Barra com só os cantos de cima arredondados, presa na linha de base."""
    r = min(r, w / 2, h)
    return (f'<path d="M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} '
            f'H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z" fill="{fill}"/>')


def difficulty_chart(d, c, ty, x0, y0, w, h):
    out = [ty.text(x0, y0, "RESOLVIDOS POR DIFICULDADE", "mono", 9, c["muted"], tracking=0.16)]
    buckets = d["by_rating"]
    if not buckets:
        return out
    top, bottom = y0 + 30, y0 + h - 22
    peak = max(n for _, n in buckets)
    slot = w / len(buckets)
    bw = min(44, slot * 0.58)
    out.append(f'<rect x="{x0}" y="{bottom}" width="{w}" height="1" fill="{c["axis"]}"/>')
    for i, (rating, n) in enumerate(buckets):
        cx = x0 + slot * (i + 0.5)
        bh = max(2, (bottom - top - 14) * n / peak)
        col = spectrum(c["spectrum"], i / max(len(buckets) - 1, 1))
        out.append(bar(cx - bw / 2, bottom - bh, bw, bh, 5, col))
        out.append(ty.text(cx, bottom - bh - 7, str(n), "mono", 10.5, c["ink"], anchor="middle"))
        out.append(ty.text(cx, bottom + 17, str(rating), "mono", 9, c["muted"], anchor="middle"))
    return out


def tags_block(d, c, ty, x, y, width):
    if not d["tags"]:
        return [], y
    out = [ty.text(x, y, "TAGS MAIS RESOLVIDAS", "mono", 9, c["muted"], tracking=0.16)]
    cx, cy = x, y + 26
    for tag, n in d["tags"]:
        tag_w = ty.width(tag, "sans", 14)
        count_w = ty.width(str(n), "mono", 10)
        if cx + tag_w + count_w + 6 > x + width:
            cx, cy = x, cy + 24
        out.append(ty.text(cx, cy, tag, "sans", 14, c["text"]))
        out.append(ty.text(cx + tag_w + 6, cy, str(n), "mono", 10, c["muted"]))
        cx += tag_w + count_w + 26
    return out, cy


def render(d, theme, kind):
    c, L, ty = THEMES[theme], LAYOUTS[kind], Type()
    W, pad = L["W"], L["pad"]
    stat_y, row_h = L["stat_y"]
    rows = math.ceil(4 / L["stat_cols"])
    body = [header(d, c, ty, theme, pad, W - pad)]
    body += stats(d, c, ty, pad, W - 2 * pad, L["stat_cols"], stat_y, row_h)
    rule_y = stat_y + (rows - 1) * row_h + 56
    body.append(f'<rect x="{pad}" y="{rule_y}" width="{W - 2 * pad}" height="1" fill="{c["grid"]}"/>')

    y, ch = L["charts_y"], L["chart_h"]
    if L["side_by_side"]:
        half = (W - 2 * pad - 60) / 2
        body += rating_chart(d, c, ty, pad, y, half, ch)
        body += difficulty_chart(d, c, ty, pad + half + 60, y, half, ch)
        y += ch + 36
    else:
        body += rating_chart(d, c, ty, pad, y, W - 2 * pad, ch)
        y += ch + 40
        body += difficulty_chart(d, c, ty, pad, y, W - 2 * pad, ch)
        y += ch + 36
    tags, y = tags_block(d, c, ty, pad, y, W - 2 * pad)
    body += tags
    H = math.ceil(y + 34)

    stops = c["spectrum"]
    defs = (ty.defs()
            + f'<linearGradient id="stroke" gradientUnits="userSpaceOnUse" x1="{pad}" x2="{pad + (W - 2 * pad) / (2 if L["side_by_side"] else 1)}">{gradient_stops(stops)}</linearGradient>'
            + f'<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{spectrum(stops, .4)}" stop-opacity=".22"/>'
              f'<stop offset="1" stop-color="{spectrum(stops, .4)}" stop-opacity="0"/></linearGradient>')
    desc = (f'{d["handle"]} no Codeforces: rating {d["rating"]} ({d["rank"]}), máximo {d["max_rating"]}, '
            f'{d["solved"]} problemas resolvidos em {len(d["history"])} contests.')
    return card(W, H, c, "".join(body), title="Estatísticas no Codeforces", desc=desc, defs=defs, theme=theme)


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
