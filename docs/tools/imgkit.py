"""Tiny drawing kit: draws at 2x and downsamples for smooth edges."""
import re
from PIL import Image, ImageDraw, ImageFont

FD = "/usr/share/fonts/truetype/dejavu/"
S = 2  # supersampling factor

PAL = dict(bg0="#0b1220", bg1="#1b1f3b", card="#162033", card2="#1e293b", line="#334155",
           text="#e2e8f0", dim="#94a3b8", teal="#2dd4bf", amber="#fbbf24", red="#f87171",
           green="#4ade80", blue="#60a5fa", purple="#a78bfa", white="#ffffff")


def font(size, bold=False, mono=False):
    name = ("DejaVuSansMono" if mono else "DejaVuSans") + ("-Bold" if bold else "")
    return ImageFont.truetype(FD + name + ".ttf", int(size * S))


class Canvas:
    def __init__(self, w, h, bg=("#0b1220", "#1b1f3b")):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S), bg[0])
        if bg[0] != bg[1]:
            d = ImageDraw.Draw(self.img)
            c0, c1 = self._rgb(bg[0]), self._rgb(bg[1])
            for y in range(h * S):
                t = y / (h * S - 1)
                d.line([(0, y), (w * S, y)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))
        self.d = ImageDraw.Draw(self.img)

    @staticmethod
    def _rgb(hexs):
        hexs = hexs.lstrip("#")
        return tuple(int(hexs[i:i + 2], 16) for i in (0, 2, 4))

    def _s(self, v):
        return [int(x * S) for x in v] if isinstance(v, (list, tuple)) else int(v * S)

    def rect(self, box, r=12, fill=None, outline=None, width=1, dash=False):
        if dash and outline:
            self.dashed_rect(box, outline, width)
            if fill:
                self.d.rounded_rectangle(self._s(box), radius=self._s(r), fill=fill)
                self.dashed_rect(box, outline, width)
            return
        self.d.rounded_rectangle(self._s(box), radius=self._s(r), fill=fill, outline=outline,
                                 width=int(width * S))

    def dashed_rect(self, box, color, width=2, dash=10, gap=7):
        x0, y0, x1, y1 = box
        for (a, b) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
            self.line([a, b], color, width, dash=(dash, gap))

    def line(self, pts, fill, width=2, dash=None):
        if not dash:
            self.d.line(self._s([c for p in pts for c in p]), fill=fill, width=int(width * S))
            return
        import math
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if L == 0:
                continue
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            pos, on = 0, True
            while pos < L:
                seg = min(dash[0] if on else dash[1], L - pos)
                if on:
                    self.d.line(self._s([x0 + ux * pos, y0 + uy * pos, x0 + ux * (pos + seg), y0 + uy * (pos + seg)]),
                                fill=fill, width=int(width * S))
                pos += seg
                on = not on

    def arrow(self, p0, p1, fill, width=3, head=12, dash=None):
        import math
        self.line([p0, p1], fill, width, dash)
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        pts = [p1, (p1[0] - head * math.cos(a - 0.4), p1[1] - head * math.sin(a - 0.4)),
               (p1[0] - head * math.cos(a + 0.4), p1[1] - head * math.sin(a + 0.4))]
        self.d.polygon(self._s([c for p in pts for c in p]), fill=fill)

    def circle(self, c, r, fill=None, outline=None, width=2):
        x, y = c
        self.d.ellipse(self._s([x - r, y - r, x + r, y + r]), fill=fill, outline=outline, width=int(width * S))

    def text(self, xy, s, size=20, fill="#e2e8f0", bold=False, mono=False, anchor="la"):
        self.d.text(self._s(xy), s, font=font(size, bold, mono), fill=fill, anchor=anchor)

    def measure(self, s, size, bold=False, mono=False):
        return font(size, bold, mono).getlength(s) / S

    def multiline(self, xy, lines, size=20, fill="#e2e8f0", gap=1.45, **kw):
        x, y = xy
        for ln in lines:
            self.text((x, y), ln, size, fill, **kw)
            y += size * gap

    def save(self, path):
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        out.save(path, optimize=True)
        return path


# ------------------------------------------------------------------ terminal screenshots
TC = dict(g="#3fb950", r="#ff7b72", y="#e3b341", b="#79c0ff", c="#56d4dd", d="#8b949e",
          w="#e6edf3", m="#d2a8ff")


def _parse(line):
    """'{g}text{/}more' -> [(text, color)]"""
    out, color, pos = [], TC["w"], 0
    for m in re.finditer(r"\{(\w|/)\}", line):
        if m.start() > pos:
            out.append((line[pos:m.start()], color))
        color = TC["w"] if m.group(1) == "/" else TC[m.group(1)]
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], color))
    return out


def terminal(lines, path, title="llm-rollout-lab — zsh", width=1600, margin=44, pad=30, max_size=23):
    plain = [re.sub(r"\{(\w|/)\}", "", l) for l in lines]
    maxlen = max(len(p) for p in plain)
    avail = width - 2 * margin - 2 * pad
    size = min(max_size, avail / (0.602 * maxlen))
    lh = size * 1.6
    bar = 46
    height = int(2 * margin + bar + 2 * pad + lh * len(lines))
    c = Canvas(width, height, bg=("#0f172a", "#1e1b4b"))
    x0, y0, x1, y1 = margin, margin, width - margin, height - margin
    c.rect((x0 + 6, y0 + 10, x1 + 6, y1 + 12), 16, fill="#070b14")          # shadow
    c.rect((x0, y0, x1, y1), 16, fill="#0d1117", outline="#30363d", width=2)
    c.rect((x0, y0, x1, y0 + bar), 16, fill="#161b22")
    c.rect((x0, y0 + 24, x1, y0 + bar), 0, fill="#161b22")
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        c.circle((x0 + 28 + i * 26, y0 + bar / 2), 8, fill=col)
    c.text(((x0 + x1) / 2, y0 + bar / 2), title, 17, "#8b949e", anchor="mm")
    y = y0 + bar + pad
    for l in lines:
        x = x0 + pad
        for seg, col in _parse(l):
            c.text((x, y), seg, size, col, mono=True)
            x += c.measure(seg, size, mono=True)
        y += lh
    return c.save(path)
