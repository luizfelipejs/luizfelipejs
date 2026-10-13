"""Tipografia em contornos para os SVGs do perfil.

Os textos viram contornos (<path>) tirados da própria fonte com o fontTools,
então os SVGs ficam idênticos em qualquer navegador, sem depender de fontes
instaladas. Cada glifo é desenhado uma vez em <defs> e reaproveitado com <use>.

Precisa do fontTools e da JetBrains Mono (licença OFL); no Ubuntu,
`apt install python3-fonttools fonts-jetbrains-mono`.
"""

from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

FONT_FILES = {"mono": "JetBrainsMono-Regular.ttf"}
FONT_DIRS = ("/usr/share/fonts", "/usr/local/share/fonts", "~/.local/share/fonts", "~/.fonts")


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

    def _ref(self, f, name):
        key = (f.key, name)
        if key not in self.used:
            d = f.outline(name)
            self.used[key] = (f"{f.key[0]}{len(self.used)}", d) if d else (None, "")
        return self.used[key][0]

    def defs(self):
        return "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in self.used.values() if gid)
