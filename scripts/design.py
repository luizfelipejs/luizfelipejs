"""Base visual do perfil: paleta, tipografia em contornos e texturas.

Os textos viram contornos (<path>) tirados das próprias fontes com o fontTools,
então os SVGs ficam idênticos em qualquer navegador, sem depender de fontes
instaladas. Cada glifo é desenhado uma vez em <defs> e reaproveitado com <use>.

A paleta (THEMES) não depende de nada além da biblioteca padrão; a tipografia
precisa do fontTools (pip install fonttools) e das fontes EB Garamond, Inter e
JetBrains Mono, todas sob a licença OFL.
"""

from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": dict(
        bg="#fbf9f4", bg2="#f2eee5", border="#e3ddd0",
        ink="#18161f", text="#2d2a33", muted="#6b665d",
        faint="#ece7dc", grid="#ddd6c7", axis="#bdb3a1",
        spectrum=("#2f50d8", "#7440e0", "#cf3a7b", "#e8691d"),
        comet="#fffaf2", aurora=0.13, glow=0.20, grain=0.075,
    ),
    "dark": dict(
        bg="#0b0d12", bg2="#11141c", border="#222836",
        ink="#f4f1ea", text="#d7d4cd", muted="#8f96a3",
        faint="#151923", grid="#1d2330", axis="#343c4e",
        spectrum=("#4cc9f0", "#7b8cff", "#c77dff", "#ff6b9d", "#ffb86b"),
        comet="#ffffff", aurora=0.24, glow=0.55, grain=0.05,
    ),
}

FONT_FILES = {
    "serif": "EBGaramond12-Regular.ttf",
    "italic": "EBGaramond12-Italic.ttf",
    "sans": "Inter-Regular.otf",
    "mono": "JetBrainsMono-Regular.ttf",
}
FONT_DIRS = ("/usr/share/fonts", "/usr/local/share/fonts", "~/.local/share/fonts", "~/.fonts")


def mix(a, b, u):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * u):02x}" for x, y in zip(ca, cb))


def spectrum(stops, u):
    """Cor na posição u ∈ [0, 1] de um degradê com paradas igualmente espaçadas."""
    u = min(max(u, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(u), len(stops) - 2)
    return mix(stops[i], stops[i + 1], u - i)


def gradient_stops(stops):
    n = len(stops) - 1
    return "".join(f'<stop offset="{i / n:.3f}" stop-color="{c}"/>' for i, c in enumerate(stops))


def grain_filter(fid, color, strength=1.0):
    """Ruído fino de papel: turbulência fractal transformada em pontos de tinta."""
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return (f'<filter id="{fid}" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="11" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 {r:.3f}  0 0 0 0 {g:.3f}  0 0 0 0 {b:.3f}  {1.8 * strength:.2f} 0 0 0 -.62"/>'
            f'</filter>')


def keyframes(name, frames):
    body = "".join(f"{p:.3f}%{{{rule}}}" for p, rule in frames)
    return f"@keyframes {name}{{{body}}}"


def path_d(pts):
    """Polilinha em coordenadas relativas, arredondada a 0,1 px sem acumular erro."""
    pts = [(round(x, 1), round(y, 1)) for x, y in pts]
    steps = (f"{round(x1 - x0, 1):g},{round(y1 - y0, 1):g}" for (x0, y0), (x1, y1) in zip(pts, pts[1:]))
    return f"M{pts[0][0]:g},{pts[0][1]:g}l" + " ".join(steps)


def simplify(pts, tol):
    """Douglas–Peucker: descarta pontos que desviam menos de tol da reta entre vizinhos."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        norm = (dx * dx + dy * dy) ** 0.5 or 1
        far, idx = 0.0, None
        for i in range(a + 1, b):
            dist = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / norm
            if dist > far:
                far, idx = dist, i
        if idx is not None and far > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def colored_segments(pts, stops, step=8.0):
    """Fatia uma polilinha em trechos curtos, cada um com a cor da sua posição no percurso."""
    out, start, run = [], 0, 0.0
    for i in range(1, len(pts)):
        run += ((pts[i][0] - pts[i - 1][0]) ** 2 + (pts[i][1] - pts[i - 1][1]) ** 2) ** 0.5
        if run >= step or i == len(pts) - 1:
            color = spectrum(stops, (start + i) / 2 / (len(pts) - 1))
            out.append(f'<path d="{path_d(pts[start:i + 1])}" stroke="{color}"/>')
            start, run = i, 0.0
    return "".join(out)


def card(W, H, c, body, *, title, desc, defs="", css="", rx=18, theme="light"):
    """Moldura comum dos cartões: fundo em degradê, grão de papel e borda fina."""
    grain = c["ink"] if theme == "light" else "#ffffff"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title>
<desc id="d">{escape(desc)}</desc>
<style>{css}</style>
<defs>
  {defs}
  <clipPath id="card"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient>
  {grain_filter("grain", grain)}
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  {body}
  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="{c["grain"] * 2.4:.2f}"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{rx - 0.5}" fill="none" stroke="{c["border"]}"/>
</svg>
'''


def find_font(name):
    for root in FONT_DIRS:
        hits = sorted(Path(root).expanduser().rglob(name)) if Path(root).expanduser().is_dir() else []
        if hits:
            return hits[0]
    raise SystemExit(f"fonte {name} não encontrada em {', '.join(FONT_DIRS)}")


class Face:
    """Uma fonte: métricas, kerning (GPOS) e contornos dos glifos."""

    def __init__(self, key):
        from fontTools.ttLib import TTFont

        self.key = key
        self.font = TTFont(find_font(FONT_FILES[key]))
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.hmtx = self.font["hmtx"]
        self._kern = {}
        self._pairs = self._kern_subtables()
        self._subs = {}

    def _kern_subtables(self):
        if "GPOS" not in self.font:
            return []
        gpos = self.font["GPOS"].table
        indices = sorted({i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern"
                          for i in fr.Feature.LookupListIndex})
        tables = []
        for i in indices:
            lookup = gpos.LookupList.Lookup[i]
            for st in lookup.SubTable:
                st = st.ExtSubTable if lookup.LookupType == 9 else st
                if getattr(st, "LookupType", lookup.LookupType) == 2:
                    tables.append(st)
        return tables

    def glyph(self, char, features=()):
        name = self.cmap.get(ord(char))
        if name is None:
            raise SystemExit(f"{FONT_FILES[self.key]} não tem o caractere {char!r}")
        for tag in features:
            name = self.substitutions(tag).get(name, name)
        return name

    def substitutions(self, tag):
        """Substituições simples (GSUB tipo 1) de uma feature, como lnum ou smcp."""
        if tag not in self._subs:
            table, gsub = {}, self.font["GSUB"].table if "GSUB" in self.font else None
            indices = sorted({i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == tag
                              for i in fr.Feature.LookupListIndex}) if gsub else []
            for i in indices:
                lookup = gsub.LookupList.Lookup[i]
                for st in lookup.SubTable:
                    st = st.ExtSubTable if lookup.LookupType == 7 else st
                    for src, dst in getattr(st, "mapping", {}).items():
                        table.setdefault(src, dst)
            self._subs[tag] = table
        return self._subs[tag]

    def advance(self, name):
        return self.hmtx[name][0]

    def kern(self, left, right):
        key = (left, right)
        if key not in self._kern:
            self._kern[key] = self._lookup_kern(left, right)
        return self._kern[key]

    def _lookup_kern(self, left, right):
        for st in self._pairs:
            cov = st.Coverage.glyphs
            if left not in cov:
                continue
            if st.Format == 1:
                for rec in st.PairSet[cov.index(left)].PairValueRecord:
                    if rec.SecondGlyph == right:
                        return getattr(rec.Value1, "XAdvance", 0) or 0
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs.get(left, 0)
                c2 = st.ClassDef2.classDefs.get(right, 0)
                value = st.Class1Record[c1].Class2Record[c2].Value1
                adv = getattr(value, "XAdvance", 0) or 0
                if adv:
                    return adv
        return 0

    def outline(self, name):
        from fontTools.pens.svgPathPen import SVGPathPen

        pen = SVGPathPen(self.glyphs, ntos=lambda n: str(round(n)))
        self.glyphs[name].draw(pen)
        return pen.getCommands()


class Type:
    """Compõe texto como contornos reutilizáveis.

    Uso: t = Type(); t.text(...) devolve SVG e t.defs() devolve os glifos usados,
    que vão uma vez só no <defs> do documento.
    """

    _faces = {}

    def __init__(self):
        self.used = {}

    @classmethod
    def face(cls, key):
        if key not in cls._faces:
            cls._faces[key] = Face(key)
        return cls._faces[key]

    def _layout(self, text, face, tracking, features=()):
        """Posições horizontais (em unidades da fonte) de cada glifo, com kerning."""
        f = self.face(face)
        names = [f.glyph(c, features) for c in text]
        xs, x = [], 0
        for i, name in enumerate(names):
            xs.append(x)
            x += f.advance(name)
            if i + 1 < len(names):
                x += f.kern(name, names[i + 1]) + tracking * f.upm
        return f, names, xs, x

    def width(self, text, face, size, tracking=0.0, features=()):
        f, _, _, w = self._layout(text, face, tracking, features)
        return w * size / f.upm

    def text(self, x, y, text, face, size, fill="currentColor", tracking=0.0, anchor="start", attrs="",
             features=()):
        f, names, xs, w = self._layout(text, face, tracking, features)
        k = size / f.upm
        if anchor == "middle":
            x -= w * k / 2
        elif anchor == "end":
            x -= w * k
        uses = []
        for name, gx in zip(names, xs):
            gid = self._ref(f, name)
            if gid:
                uses.append(f'<use href="#{gid}" x="{gx}"/>')
        return (f'<g fill="{fill}" transform="translate({x:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})"{attrs}>'
                + "".join(uses) + "</g>")

    def runs(self, x, y, parts, size, fill="currentColor"):
        """Texto misto (fórmulas): partes (texto, fonte, escala, deslocamento vertical em em)."""
        out = []
        for text, face, scale, dy in parts:
            s = size * scale
            out.append(self.text(x, y + dy * size, text, face, s, fill, features=("lnum",)))
            x += self.width(text, face, s, features=("lnum",))
        return "".join(out), x

    def wrap(self, text, face, size, width):
        lines, line = [], ""
        for word in text.split():
            trial = f"{line} {word}".strip()
            if line and self.width(trial, face, size) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        return lines + [line] if line else lines

    def _ref(self, f, name):
        key = (f.key, name)
        if key not in self.used:
            d = f.outline(name)
            self.used[key] = (f"{f.key[0]}{len(self.used)}", d) if d else (None, "")
        return self.used[key][0]

    def defs(self):
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self.used.values() if gid)
