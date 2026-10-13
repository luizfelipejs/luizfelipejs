"""Pequenas artes de traço fino para o perfil, cada uma desenhada dentro de uma caixa (x, y, w, h).

Todas são monocromáticas: recebem só a cor do traço. Só biblioteca padrão.
"""

import math

from design import path_d


def cantor(color, x, y, w, h, levels=5):
    """Conjunto de Cantor: a cada nível, tira-se o terço do meio de cada segmento."""
    rows, segments = [], [(0.0, 1.0)]
    step = h / (levels - 1)
    for level in range(levels):
        rows += [f"M{x + a * w:.2f},{y + level * step:.2f}H{x + b * w:.2f}" for a, b in segments]
        segments = [part for a, b in segments for part in ((a, a + (b - a) / 3), (b - (b - a) / 3, b))]
    return f'<path d="{"".join(rows)}" stroke="{color}" stroke-width="1.6" stroke-linecap="butt"/>'


def hilbert(color, x, y, size, order=3):
    """Curva de Hilbert: percorre toda a grade 2ⁿ × 2ⁿ sem passar duas vezes pelo mesmo ponto."""
    side = 2 ** order
    pts = []
    for d in range(side * side):
        hx = hy = 0
        rest, s = d, 1
        while s < side:
            rx = (rest // 2) & 1
            ry = (rest ^ rx) & 1
            if ry == 0:
                if rx == 1:
                    hx, hy = s - 1 - hx, s - 1 - hy
                hx, hy = hy, hx
            hx, hy = hx + s * rx, hy + s * ry
            rest //= 4
            s *= 2
        pts.append((x + hx * size / (side - 1), y + size - hy * size / (side - 1)))
    return (f'<path d="{path_d(pts)}" fill="none" stroke="{color}" stroke-width="1" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def tree(color, bg, x, y, w, h, depth=4):
    """Árvore binária completa, como uma árvore de segmentos."""
    edges, nodes = [], []
    for level in range(depth):
        count = 2 ** level
        ny = y + h * level / (depth - 1)
        for i in range(count):
            nx = x + w * (i + 0.5) / count
            nodes.append((nx, ny))
            if level + 1 < depth:
                cy = y + h * (level + 1) / (depth - 1)
                for j in (2 * i, 2 * i + 1):
                    edges.append(f"M{nx:.2f},{ny:.2f}L{x + w * (j + 0.5) / (2 * count):.2f},{cy:.2f}")
    dots = "".join(f'<circle cx="{nx:.2f}" cy="{ny:.2f}" r="1.5"/>' for nx, ny in nodes)
    return (f'<path d="{"".join(edges)}" stroke="{color}" stroke-width=".8"/>'
            f'<g fill="{bg}" stroke="{color}" stroke-width=".9">{dots}</g>')


def lorenz_points(steps=5000, dt=0.006):
    s, r, b = 10.0, 28.0, 8 / 3

    def f(p):
        px, py, pz = p
        return (s * (py - px), px * (r - pz) - py, px * py - b * pz)

    p, out = (0.1, 0.0, 0.0), []
    for i in range(steps):
        k1 = f(p)
        k2 = f(tuple(p[j] + dt / 2 * k1[j] for j in range(3)))
        k3 = f(tuple(p[j] + dt / 2 * k2[j] for j in range(3)))
        k4 = f(tuple(p[j] + dt * k3[j] for j in range(3)))
        p = tuple(p[j] + dt / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]) for j in range(3))
        if i > 1200:  # descarta o transiente que espirala a partir da origem
            out.append((p[0], p[2]))
    return out


def lorenz(color, x, y, w, h, width=0.6, steps=5000):
    """Atrator de Lorenz (σ = 10, ρ = 28, β = 8/3), projeção x–z."""
    pts = lorenz_points(steps)
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    k = min(w / (max(xs) - min(xs)), h / (max(zs) - min(zs)))
    cx, cy = x + w / 2 - k * (max(xs) + min(xs)) / 2, y + h / 2 + k * (max(zs) + min(zs)) / 2
    screen = [(cx + k * px, cy - k * pz) for px, pz in pts]
    thinned = [screen[0]]
    for p in screen[1:]:
        if math.dist(p, thinned[-1]) > 0.6:
            thinned.append(p)
    return (f'<path d="{path_d(thinned)}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linejoin="round"/>')


def shelf(color, x, y, w, h):
    """Estante: lombadas de alturas diferentes, a última inclinada."""
    widths = (2.6, 3.4, 2.2, 3.0, 2.6, 3.4)
    heights = (0.78, 1.0, 0.7, 0.88, 0.62, 0.92)
    out, bx = [], x
    for i, (bw, bh) in enumerate(zip(widths, heights)):
        top = y + h * (1 - bh)
        tilt = f' transform="rotate(-14 {bx + bw:.2f} {y + h:.2f})"' if i == len(widths) - 1 else ""
        out.append(f'<rect x="{bx:.2f}" y="{top:.2f}" width="{bw}" height="{h * bh:.2f}" rx=".4"{tilt}/>')
        bx += bw + 1.1
    return (f'<g fill="none" stroke="{color}" stroke-width=".8">{"".join(out)}</g>'
            f'<path d="M{x - 1:.2f},{y + h + 1:.2f}H{bx + 2:.2f}" stroke="{color}" stroke-width=".8"/>')


def weierstrass(color, x, y, w, h, samples=1600):
    """Função de Weierstrass (a = 1/2, b = 3): contínua em todo ponto, derivável em nenhum."""
    def f(t):
        return sum(0.5 ** k * math.cos(3 ** k * math.pi * t) for k in range(9))

    ys = [f(-1 + 2 * i / samples) for i in range(samples + 1)]
    lo, hi = min(ys), max(ys)
    pts = [(x + w * i / samples, y + h - h * (v - lo) / (hi - lo)) for i, v in enumerate(ys)]
    return (f'<path d="{path_d(pts)}" fill="none" stroke="{color}" stroke-width=".7" '
            f'stroke-linejoin="round"/>')
