#!/usr/bin/env python3
"""Gera assets/codeforces-{light,dark}.svg com dados da API pública do Codeforces.

Uso: python3 scripts/codeforces_card.py root.svp
Se a API falhar, sai com erro e não mexe nos arquivos existentes.
"""

import json
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

API = "https://codeforces.com/api/"
OUT = Path(__file__).resolve().parent.parent / "assets"

W, H = 840, 360
PAD = 24
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": {
        "surface": "#f6f8fa", "border": "#d1d9e0", "grid": "#e1e6eb",
        "text": "#1f2328", "muted": "#59636e", "accent": "#2a78d6",
    },
    "dark": {
        "surface": "#161b22", "border": "#3d444d", "grid": "#262c35",
        "text": "#f0f6fc", "muted": "#9198a1", "accent": "#3987e5",
    },
}

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


def text(x, y, content, size, fill, weight=400, anchor="start", family=FONT):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(content))}</text>')


def bar(x, y, w, h, r, fill):
    """Barra com só os cantos de cima arredondados, presa na linha de base."""
    r = min(r, w / 2, h)
    return (f'<path d="M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} '
            f'H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z" fill="{fill}"/>')


def stat_tiles(d, t):
    labels = [("Rating atual", d["rating"]), ("Rating máximo", d["max_rating"]),
              ("Problemas resolvidos", d["solved"]), ("Contests", len(d["history"]))]
    col = (W - 2 * PAD) / len(labels)
    out = []
    for i, (label, value) in enumerate(labels):
        x = PAD + i * col
        out.append(text(x, 104, value, 30, t["text"], 600))
        out.append(text(x, 126, label, 13, t["muted"]))
    return out


def rank_chip(d, t, theme):
    color = RANK_COLORS.get(d["rank"], ("#808080", "#9198a1"))[0 if theme == "light" else 1]
    return [f'<circle cx="{PAD + 104}" cy="37" r="4" fill="{color}"/>',
            text(PAD + 114, 42, d["rank"], 13, t["muted"])]


def rating_chart(d, t, x0, y0, w, h):
    out = [text(x0, y0, "Rating por contest", 13, t["muted"], 600)]
    pts = d["history"]
    if not pts:
        return out + [text(x0, y0 + h / 2, "sem contests ainda", 13, t["muted"])]

    left, top, bottom = x0 + 34, y0 + 22, y0 + h - 22
    right = x0 + w - 30
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
        out.append(f'<line x1="{left}" x2="{right}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{t["grid"]}" stroke-width="1"/>')
        out.append(text(left - 8, sy(v) + 4, v, 11, t["muted"], anchor="end"))

    coords = " ".join(f"{sx(ts):.1f},{sy(r):.1f}" for ts, r in pts)
    out.append(f'<polyline points="{coords}" fill="none" stroke="{t["accent"]}" stroke-width="2" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for ts, r in pts:
        out.append(f'<circle cx="{sx(ts):.1f}" cy="{sy(r):.1f}" r="4" fill="{t["accent"]}" '
                   f'stroke="{t["surface"]}" stroke-width="2"/>')
    last_ts, last_r = pts[-1]
    out.append(text(sx(last_ts) + 9, sy(last_r) + 4, last_r, 12, t["text"], 600))

    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%y")
    out.append(text(left, bottom + 18, fmt(t0), 11, t["muted"]))
    if t1 > t0:
        out.append(text(right, bottom + 18, fmt(t1), 11, t["muted"], anchor="end"))
    return out


def difficulty_chart(d, t, x0, y0, w, h):
    out = [text(x0, y0, "Resolvidos por dificuldade", 13, t["muted"], 600)]
    buckets = d["by_rating"]
    if not buckets:
        return out
    top, bottom = y0 + 26, y0 + h - 22
    peak = max(n for _, n in buckets)
    slot = w / len(buckets)
    bw = min(40, slot * 0.6)
    out.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{bottom}" y2="{bottom}" stroke="{t["grid"]}" stroke-width="1"/>')
    for i, (rating, n) in enumerate(buckets):
        cx = x0 + slot * (i + 0.5)
        bh = max(2, (bottom - top - 16) * n / peak)
        out.append(bar(cx - bw / 2, bottom - bh, bw, bh, 4, t["accent"]))
        out.append(text(cx, bottom - bh - 6, n, 12, t["text"], 600, "middle"))
        out.append(text(cx, bottom + 18, rating, 11, t["muted"], anchor="middle"))
    return out


def tags_line(d, t):
    if not d["tags"]:
        return []
    parts = [f'<tspan fill="{t["muted"]}">Tags mais resolvidas:  </tspan>']
    for i, (tag, n) in enumerate(d["tags"]):
        sep = f'<tspan fill="{t["muted"]}">  ·  </tspan>' if i else ""
        parts.append(f'{sep}<tspan fill="{t["text"]}">{escape(tag)}</tspan>'
                     f'<tspan fill="{t["muted"]}"> {n}</tspan>')
    return [f'<text x="{PAD}" y="{H - 24}" font-family="{FONT}" font-size="13">{"".join(parts)}</text>']


def render(d, theme):
    t = THEMES[theme]
    desc = (f'{d["handle"]} no Codeforces: rating {d["rating"]} ({d["rank"]}), máximo {d["max_rating"]}, '
            f'{d["solved"]} problemas resolvidos em {len(d["history"])} contests.')
    body = [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t["surface"]}" stroke="{t["border"]}"/>',
        text(PAD, 42, "Codeforces", 15, t["text"], 600),
        text(W - PAD, 42, d["handle"], 13, t["muted"], anchor="end", family=MONO),
        *rank_chip(d, t, theme),
        *stat_tiles(d, t),
        f'<line x1="{PAD}" x2="{W - PAD}" y1="150" y2="150" stroke="{t["border"]}" stroke-width="1"/>',
        *rating_chart(d, t, PAD, 180, 380, 134),
        *difficulty_chart(d, t, 448, 180, W - 448 - PAD, 134),
        *tags_line(d, t),
    ]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-labelledby="t d"><title id="t">Estatísticas no Codeforces</title>'
            f'<desc id="d">{escape(desc)}</desc>' + "".join(body) + "</svg>\n")


def main():
    handle = sys.argv[1] if len(sys.argv) > 1 else "root.svp"
    data = collect(handle)
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT / f"codeforces-{theme}.svg").write_text(render(data, theme), encoding="utf-8")
    print(f'{data["handle"]}: {data["rating"]} ({data["rank"]}), {data["solved"]} resolvidos')


if __name__ == "__main__":
    main()
