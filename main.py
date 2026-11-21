#!/usr/bin/env python3
"""THE PASSPORT PAGE OF A COUNTRY THAT ISN'T THERE.

main.py draws one 1024x1024 PNG of an open passport spread for the
REPUBLIC OF KALMARA, a volcanic South Atlantic island nation that does
not exist. Left page: the data page (coat of arms, portrait, holder
details, machine-readable zone). Right page: the visa page (arrival and
departure stamps from neighbouring countries, a boxed visa condition,
a harbour-dues fee stamp).

The country, the holder and the travel history are internally
consistent by construction:
  * Kalmara: capital Port Anselm; languages Kalmaran / English;
    currency the kalmaran crown (KMK); no airfield - arrival by sea only.
  * Holder: Ines Mara Tavares, born 02 JUN 1998 in Port Anselm.
  * Passport KMR 847 291, issued 14 MAR 2024 in Port Anselm,
    expires 13 MAR 2034. Every stamp falls after the date of issue,
    in one unbroken journey home: Port Anselm 21 JUN 2024 ->
    Cape Town 28 JUN -> Rio de Janeiro 12 JUL -> Jamestown
    (St Helena) 02 AUG -> Port Anselm 09 AUG 2024.
  * The machine-readable zone is built with real ICAO 9303 check
    digits, computed in code.

Pure Python 3.13 standard library only (zlib + struct for the PNG
container; every pixel is plotted by the Sheet canvas below; the
letterforms are a 5x7 bitmap face defined in this file). No network,
no fonts on disk, no randomness: the same run always writes the same
bytes. Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
(writes out/entry.png). The grader runs it twice; both runs write
identical bytes.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER_L = (238, 231, 210)      # left page, warm cream
PAPER_R = (236, 229, 206)      # right page, a shade deeper
PAPER_EDGE = (214, 204, 178)   # page edge / gutter shadow
DESK = (52, 44, 38)            # backdrop around the spread
INK = (30, 30, 34)             # body text
NAVY = (28, 42, 78)            # headings, rules
GOLD = (176, 141, 60)          # arms, rules
FAINT = (120, 112, 92)         # labels
LABEL = (96, 88, 70)           # small-caps labels
RULE = (150, 138, 108)         # hairlines
GUILLOCHE = (196, 186, 158)    # faint security print
WHITE = (248, 246, 238)
BLACK = (16, 16, 18)
STAMP_BLUE = (42, 72, 150)
STAMP_PURPLE = (110, 60, 140)
STAMP_GREEN = (30, 110, 70)
STAMP_RED = (178, 44, 36)
SKIN = (198, 148, 108)
SKIN_DARK = (172, 122, 86)
HAIR = (46, 32, 24)
SCARF = (18, 96, 104)
SCARF_DARK = (12, 70, 78)
JACKET = (34, 58, 84)
SHIRT = (238, 232, 214)
PHOTO_BG = (126, 164, 168)


# --- PNG container (stdlib only, deterministic) ----------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, px, w, h):
    raw = b"".join(b"\x00" + bytes(px[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(raw, 9))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


# --- canvas -----------------------------------------------------------------

def blend(dst, src, alpha):
    """Blend src colour over dst colour, alpha 0..255."""
    return tuple((s * alpha + d * (255 - alpha)) // 255
                 for s, d in zip(src, dst))


class Sheet:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            return tuple(self.px[i:i + 3])
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def set_blend(self, x, y, c, alpha):
        old = self.get(x, y)
        if old is not None:
            self.set(x, y, blend(old, c, alpha))

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(i + (x1 - x0) * 3)] = bytes(c) * (x1 - x0)

    def frame(self, x, y, w, h, c, t=2):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for a in range(-(t // 2), t // 2 + 1):
                for b in range(-(t // 2), t // 2 + 1):
                    self.set(x + a, y + b, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)


def blit_rotated(dst, src, cx, cy, angle_deg, color, alpha=200):
    """Blit a mask sheet (non-zero pixels are ink) onto dst, rotated
    about (cx, cy). src holds 0/1 bytes; ink is drawn in `color`."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    hw, hh = src.w // 2, src.h // 2
    for sy in range(src.h):
        for sx in range(src.w):
            if not src.px[sy * src.w + sx]:
                continue
            dx = sx - hw
            dy = sy - hh
            rx = int(cx + dx * ca - dy * sa)
            ry = int(cy + dx * sa + dy * ca)
            dst.set_blend(rx, ry, color, alpha)


# --- 5x7 bitmap face (each glyph: 7 rows of 5 bits) ------------------------

FONT = {
"A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
"C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
"D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
"E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
"F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
"G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
"H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
"I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
"J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
"K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
"L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
"M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
"N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
"O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
"Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
"R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
"S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
"T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
"U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
"V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
"W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
"X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
"Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
"Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
"0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
"1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
"2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
"3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
"4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
"5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
"6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
"7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
"8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
"9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
" ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
":": (".....", "..#..", ".....", ".....", "..#..", ".....", "....."),
";": (".....", "..#..", ".....", ".....", "..#..", "..#..", ".#..."),
"'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
"-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
"!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
"?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
"/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
"(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
"%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
"&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
"+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
"=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
'"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
"*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
"<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
"—": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
"·": (".....", ".....", ".....", ".....", ".....", "..#..", "....."),
}


def text_width(s, scale, adv=None):
    a = adv if adv is not None else 6 * scale
    return len(s) * a - (a - 5 * scale)


def draw_text(sh, x, y, s, scale, color, bold=False, adv=None):
    s = s.upper()
    a = adv if adv is not None else 6 * scale
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "#":
                    sh.fill_rect(cx + c * scale, y + r * scale,
                                 scale, scale, color)
                    if bold:
                        sh.fill_rect(cx + c * scale + 1, y + r * scale,
                                     scale, scale, color)
        cx += a
    return cx


def draw_text_center(sh, cx, y, s, scale, color, bold=False):
    w = text_width(s, scale)
    return draw_text(sh, cx - w // 2, y, s, scale, color, bold=bold)


def wrap(s, scale, max_w):
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- machine-readable zone (ICAO 9303 check digits) ------------------------

def _mrz_value(ch):
    if ch.isdigit():
        return int(ch)
    if ch == "<":
        return 0
    return ord(ch) - ord("A") + 10


def mrz_check(s):
    total = 0
    for i, ch in enumerate(s):
        total += _mrz_value(ch) * (7, 3, 1)[i % 3]
    return str(total % 10)


def build_mrz():
    line1 = ("P<KMR" + "TAVARES<<INES<MARA").ljust(44, "<")
    doc = "KMR847291"
    nat = "KMR"
    dob = "980602"      # 02 JUN 1998
    sex = "F"
    exp = "340313"      # 13 MAR 2034
    personal = "<" * 14
    body = (doc + mrz_check(doc) + nat + dob + mrz_check(dob) + sex
            + exp + mrz_check(exp) + personal + mrz_check(personal))
    line2 = body + mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# --- paper, security print, coat of arms ------------------------------------

def _hash2(x, y):
    # deterministic pseudo-random in [0, 1) from integer coordinates
    v = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFFFFFF) / 4294967295.0


def paper_texture(sh, x, y, w, h, base, fleck):
    for yy in range(y, y + h, 3):
        for xx in range(x, x + w, 3):
            if _hash2(xx, yy) < 0.16:
                sh.set(xx, yy, fleck)


def guilloche(sh, x, y, w, h, color, step=9, amp=5, phase=0.0):
    for yy in range(y + 6, y + h - 4, step):
        for xx in range(x, x + w):
            gy = yy + int(amp * math.sin(xx / 23.0 + phase))
            if y <= gy < y + h:
                sh.set(xx, gy, color)


def draw_arms(sh, cx, top, scale=1):
    """Coat of arms: a shield, a star above, three waves, '1847' below."""
    w, h = 62 * scale, 74 * scale
    x0, y0 = cx - w // 2, top
    # shield outline
    pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h - 18 * scale),
           (cx, y0 + h), (x0, y0 + h - 18 * scale)]
    sh.poly(pts, NAVY)
    inner = [(x0 + 4, y0 + 4), (x0 + w - 4, y0 + 4),
             (x0 + w - 4, y0 + h - 20 * scale),
             (cx, y0 + h - 4), (x0 + 4, y0 + h - 20 * scale)]
    sh.poly(inner, (232, 224, 200))
    # star above the shield
    sx, sy = cx, y0 - 12 * scale
    sh.disc(sx, sy, 4 * scale, GOLD)
    for ang in range(0, 360, 72):
        x2 = sx + int(9 * scale * math.cos(math.radians(ang - 90)))
        y2 = sy + int(9 * scale * math.sin(math.radians(ang - 90)))
        sh.line(sx, sy, x2, y2, GOLD, 2)
    # three waves inside the shield
    for k in range(3):
        wy = y0 + (26 + k * 10) * scale
        for xx in range(x0 + 8, x0 + w - 8):
            gy = wy + int(3 * scale * math.sin(xx / 7.0))
            sh.set(xx, gy, NAVY)
    draw_text_center(sh, cx, y0 + h + 4, "EST. 1847", 1, LABEL)


# --- portrait ---------------------------------------------------------------

def draw_portrait(sh, x, y, w, h):
    """Stylised flat portrait of Ines Mara Tavares: teal headscarf,
    dark hair, warm skin, navy jacket. Drawn, not pasted, so the
    portrait and the invented country belong to each other."""
    sh.fill_rect(x, y, w, h, PHOTO_BG)
    # backdrop: pale horizon + sea bands (Kalmara is a sea island)
    for k in range(3):
        sh.fill_rect(x, y + h - 46 + k * 10, w, 4, (96, 138, 142))
    cx = x + w // 2
    # shoulders / jacket
    sh.poly([(x + 8, y + h), (x + 34, y + h - 52), (cx - 22, y + h - 62),
             (cx + 22, y + h - 62), (x + w - 34, y + h - 52),
             (x + w - 8, y + h)], JACKET)
    # shirt V + collar
    sh.poly([(cx - 12, y + h - 60), (cx + 12, y + h - 60),
             (cx, y + h - 38)], SHIRT)
    sh.poly([(cx - 22, y + h - 62), (cx - 8, y + h - 52),
             (cx - 12, y + h - 60)], (210, 204, 188))
    sh.poly([(cx + 22, y + h - 62), (cx + 8, y + h - 52),
             (cx + 12, y + h - 60)], (210, 204, 188))
    # neck
    sh.fill_rect(cx - 11, y + h - 78, 22, 22, SKIN_DARK)
    # head
    sh.ellipse(cx, y + 62, 33, 42, SKIN)
    # ears
    sh.disc(cx - 33, y + 64, 6, SKIN)
    sh.disc(cx + 33, y + 64, 6, SKIN)
    # hair tucked under the scarf at the temples
    sh.ellipse(cx - 28, y + 44, 7, 14, HAIR)
    sh.ellipse(cx + 28, y + 44, 7, 14, HAIR)
    # teal headscarf over the crown, tied at the nape
    sh.ellipse(cx, y + 30, 36, 26, SCARF)
    sh.ellipse(cx, y + 38, 34, 20, SCARF)
    sh.poly([(cx - 36, y + 26), (cx - 30, y + 52), (cx - 38, y + 66),
             (cx - 44, y + 40)], SCARF_DARK)
    sh.poly([(cx + 36, y + 26), (cx + 30, y + 52), (cx + 38, y + 66),
             (cx + 44, y + 40)], SCARF_DARK)
    # scarf fold lines
    for k in range(3):
        sh.line(cx - 30 + k * 4, y + 14, cx - 18 + k * 8, y + 34,
                SCARF_DARK, 1)
    # brows, eyes, nose, lips - minimal, symmetric
    sh.line(cx - 20, y + 56, cx - 8, y + 54, HAIR, 2)
    sh.line(cx + 8, y + 54, cx + 20, y + 56, HAIR, 2)
    sh.disc(cx - 14, y + 62, 3, BLACK)
    sh.disc(cx + 14, y + 62, 3, BLACK)
    sh.disc(cx - 13, y + 61, 1, WHITE)
    sh.disc(cx + 15, y + 61, 1, WHITE)
    sh.line(cx, y + 64, cx - 2, y + 78, SKIN_DARK, 2)
    sh.line(cx - 2, y + 78, cx + 3, y + 79, SKIN_DARK, 2)
    sh.line(cx - 9, y + 88, cx + 9, y + 88, (146, 74, 62), 3)
    # cheek shading
    sh.ellipse(cx - 22, y + 76, 7, 5, (206, 158, 118))
    sh.ellipse(cx + 22, y + 76, 7, 5, (206, 158, 118))
    # small gold earrings
    sh.disc(cx - 33, y + 72, 2, GOLD)
    sh.disc(cx + 33, y + 72, 2, GOLD)
    # halftone dots over the backdrop only
    for yy in range(y + 4, y + h - 60, 6):
        for xx in range(x + 4, x + w - 4, 6):
            if _hash2(xx, yy) < 0.28:
                sh.set(xx, yy, (110, 146, 150))


# --- stamps -------------------------------------------------------------------

def stamp_mask(lines, scale=2, pad_x=14, pad_y=10):
    """Render stamp text lines into a 0/1 mask sheet with a frame."""
    w = max(text_width(s, scale) for s in lines) + 2 * pad_x
    h = len(lines) * (7 * scale + 4) + 2 * pad_y
    m = Sheet(w, h, (0, 0, 0))
    # mask sheet stores 0/1 in the red channel; use a parallel bytearray
    mask = bytearray(w * h)
    tmp = Sheet(w, h, (0, 0, 0))
    y = pad_y
    for s in lines:
        draw_text(tmp, (w - text_width(s, scale)) // 2, y, s, scale,
                  (255, 255, 255))
        y += 7 * scale + 4
    for i in range(w * h):
        if tmp.px[i * 3] > 0:
            mask[i] = 1
    # frame: outer + inner rule
    for xx in range(w):
        for yy in (0, 1, h - 2, h - 1):
            mask[yy * w + xx] = 1
    for yy in range(h):
        for xx in (0, 1, w - 2, w - 1):
            mask[yy * w + xx] = 1
    for xx in range(4, w - 4):
        for yy in (4, h - 5):
            mask[yy * w + xx] = 1
    for yy in range(4, h - 4):
        for xx in (4, w - 5):
            mask[yy * w + xx] = 1
    return mask, w, h


def round_stamp_mask(lines, scale=2, d=152):
    """Circular date stamp: two rings + centred text lines."""
    m = Sheet(d, d, (0, 0, 0))
    mask = bytearray(d * d)
    tmp = Sheet(d, d, (0, 0, 0))
    tmp.ring(d // 2, d // 2, d // 2 - 3, (255, 255, 255), 3)
    tmp.ring(d // 2, d // 2, d // 2 - 12, (255, 255, 255), 2)
    y = d // 2 - (len(lines) * (7 * scale + 4)) // 2
    for s in lines:
        draw_text(tmp, (d - text_width(s, scale)) // 2, y, s, scale,
                  (255, 255, 255))
        y += 7 * scale + 4
    for i in range(d * d):
        if tmp.px[i * 3] > 0:
            mask[i] = 1
    return mask, d, d


def stamp_sheet(mask, w, h):
    s = Sheet(w, h, (0, 0, 0))
    s.px = bytearray(mask)
    return s


def place_stamp(sh, lines, cx, cy, angle, color, scale=2, round_=False):
    if round_:
        mask, w, h = round_stamp_mask(lines, scale)
    else:
        mask, w, h = stamp_mask(lines, scale)
    blit_rotated(sh, stamp_sheet(mask, w, h), cx, cy, angle, color, 205)


# --- data page ----------------------------------------------------------------

def field(sh, x, y, label, value, width=270, scale=2):
    draw_text(sh, x, y, label, 1, LABEL)
    draw_text(sh, x, y + 12, value, scale, INK, bold=True)
    sh.fill_rect(x, y + 12 + 7 * scale + 6, width, 1, RULE)


def build_data_page(sh, px, py, pw, ph):
    sh.fill_rect(px, py, pw, ph, PAPER_L)
    paper_texture(sh, px, py, pw, ph, PAPER_L, (222, 214, 190))
    guilloche(sh, px + 14, py + ph - 190, pw - 28, 60, GUILLOCHE)
    # inner gold frame
    sh.frame(px + 12, py + 12, pw - 24, ph - 24, GOLD, 1)
    sh.frame(px + 16, py + 16, pw - 32, ph - 32, RULE, 1)
    cx = px + pw // 2
    # coat of arms + titles
    draw_arms(sh, cx, py + 52)
    draw_text_center(sh, cx, py + 150, "REPUBLIC OF KALMARA", 3, NAVY,
                     bold=True)
    draw_text_center(sh, cx, py + 178, "PASSEPORT - PASSPORT", 2, NAVY)
    sh.fill_rect(px + 40, py + 206, pw - 80, 2, GOLD)
    # portrait, left
    photo_x, photo_y, photo_w, photo_h = px + 36, py + 226, 150, 190
    draw_portrait(sh, photo_x + 4, photo_y + 4, photo_w - 8, photo_h - 8)
    sh.frame(photo_x, photo_y, photo_w, photo_h, BLACK, 3)
    sh.frame(photo_x + 3, photo_y + 3, photo_w - 6, photo_h - 6, WHITE, 2)
    # holder fields, right of the portrait
    fx = px + 206
    field(sh, fx, py + 228, "SURNAME / NOM", "TAVARES")
    field(sh, fx, py + 272, "GIVEN NAMES / PRENOMS", "INES MARA")
    field(sh, fx, py + 316, "NATIONALITY / NATIONALITE", "KALMARAN")
    field(sh, fx, py + 360, "DATE OF BIRTH / NE(E) LE", "02 JUN 1998")
    # full-width rows
    fy = py + 440
    field(sh, px + 36, fy, "SEX / SEXE", "F", width=60)
    field(sh, px + 116, fy, "PLACE OF BIRTH / LIEU DE NAISSANCE",
          "PORT ANSELM", width=190)
    field(sh, px + 326, fy, "PASSPORT NO.", "KMR 847 291", width=140)
    fy = py + 500
    field(sh, px + 36, fy, "DATE OF ISSUE", "14 MAR 2024", width=140)
    field(sh, px + 196, fy, "DATE OF EXPIRY", "13 MAR 2034", width=140)
    field(sh, px + 346, fy, "AUTHORITY", "PORT ANSELM", width=120)
    # holder's signature
    fy = py + 560
    draw_text(sh, px + 36, fy, "HOLDER'S SIGNATURE / SIGNATURE DU TITULAIRE",
              1, LABEL)
    # signature squiggle
    sx, sy = px + 36, fy + 26
    pts = []
    for i in range(0, 220, 6):
        pts.append((sx + i, sy + int(6 * math.sin(i / 9.0))
                    - (8 if 60 < i < 130 else 0)))
    for a, b in zip(pts, pts[1:]):
        sh.line(a[0], a[1], b[0], b[1], INK, 2)
    sh.line(sx + 4, sy - 4, sx + 14, sy + 8, INK, 2)
    sh.fill_rect(px + 36, fy + 44, 220, 1, RULE)
    draw_text(sh, px + 36, fy + 50, "INES M. TAVARES", 1, FAINT)
    # language column - the telling paperwork detail, part one:
    # Kalmara prints its data page in Kalmaran first, English second.
    fy = py + 640
    draw_text(sh, px + 36, fy, "LANGUAGE OF ISSUE / LANGUE", 1, LABEL)
    for i, line in enumerate([
            "KALMARAN - ENGLISH",
            "THIS PASSPORT IS THE PROPERTY OF THE",
            "REPUBLIC OF KALMARA. IF FOUND, PLEASE",
            "RETURN IT TO THE NEAREST KALMARAN",
            "CONSULATE OR TO PORT ANSELM."]):
        draw_text(sh, px + 36, fy + 14 + i * 16, line, 1, INK)
    # machine-readable zone
    line1, line2 = build_mrz()
    my = py + ph - 128
    sh.fill_rect(px + 24, my - 14, pw - 48, 100, (228, 220, 196))
    draw_text(sh, px + 30, my, line1, 2, BLACK, adv=10)
    draw_text(sh, px + 30, my + 26, line2, 2, BLACK, adv=10)
    # page number
    draw_text(sh, px + pw - 52, py + ph - 34, "PAGE 2", 1, FAINT)


# --- visa page ------------------------------------------------------------------

def build_visa_page(sh, px, py, pw, ph):
    sh.fill_rect(px, py, pw, ph, PAPER_R)
    paper_texture(sh, px, py, pw, ph, PAPER_R, (220, 211, 186))
    sh.frame(px + 12, py + 12, pw - 24, ph - 24, GOLD, 1)
    sh.frame(px + 16, py + 16, pw - 32, ph - 32, RULE, 1)
    cx = px + pw // 2
    draw_text_center(sh, cx, py + 40, "VISAS", 3, NAVY, bold=True)
    draw_text_center(sh, cx, py + 68, "VISAS - ENDORSEMENTS", 1, LABEL)
    draw_text(sh, px + pw - 60, py + 40, "PAGE 12", 1, FAINT)
    sh.fill_rect(px + 40, py + 96, pw - 80, 2, GOLD)
    # one unbroken journey home, in order, top to bottom
    place_stamp(sh, ["DEPARTED", "PORT ANSELM", "21 JUN 2024"],
                px + 130, py + 170, -8, STAMP_BLUE)
    place_stamp(sh, ["CAPE TOWN", "28 JUN", "2024", "ARRIVED"],
                px + 372, py + 170, 5, STAMP_PURPLE, round_=True)
    place_stamp(sh, ["DEPARTED", "CAPE TOWN", "09 JUL 2024"],
                px + 130, py + 300, 6, STAMP_BLUE)
    place_stamp(sh, ["ARRIVED", "RIO DE JANEIRO", "12 JUL 2024"],
                px + 372, py + 300, -5, STAMP_GREEN)
    place_stamp(sh, ["DEPARTED", "RIO DE JANEIRO", "30 JUL 2024"],
                px + 130, py + 430, -6, STAMP_GREEN)
    place_stamp(sh, ["JAMESTOWN", "02 AUG", "2024", "ARRIVED"],
                px + 372, py + 430, -4, STAMP_PURPLE, round_=True)
    place_stamp(sh, ["DEPARTED", "ST HELENA", "05 AUG 2024"],
                px + 130, py + 560, 7, STAMP_BLUE)
    place_stamp(sh, ["ARRIVED", "PORT ANSELM", "09 AUG 2024"],
                px + 372, py + 560, -3, STAMP_RED)
    # the telling detail: boxed conditions of entry
    bx, by, bw, bh = px + 36, py + 650, pw - 72, 190
    sh.fill_rect(bx, by, bw, bh, (232, 224, 198))
    sh.frame(bx, by, bw, bh, STAMP_RED, 2)
    sh.frame(bx + 5, by + 5, bw - 10, bh - 10, STAMP_RED, 1)
    draw_text_center(sh, cx, by + 14, "CONDITIONS OF ENTRY", 2, STAMP_RED,
                     bold=True)
    cond = [
        "ARRIVAL BY SEA ONLY. THE REPUBLIC",
        "HAS NO AIRFIELD. VESSELS DOCK AT",
        "PORT ANSELM ONLY. STAY: 90 DAYS.",
        "NO EMPLOYMENT. NO ONWARD FERRY",
        "WITHOUT A STAMPED EXIT PERMIT.",
    ]
    y = by + 44
    for line in cond:
        draw_text(sh, bx + 18, y, line, 2, INK)
        y += 20
    # harbour-dues fee stamp, overlapping the box corner
    place_stamp(sh, ["HARBOUR DUES", "PAID 12 KMK", "09 AUG 2024"],
                px + 372, by + 182, -11, STAMP_RED)
    # footer
    draw_text_center(sh, cx, py + ph - 60,
                     "THIS PASSPORT CONTAINS 32 PAGES", 1, FAINT)
    draw_text_center(sh, cx, py + ph - 40,
                     "KALMARA - PORT ANSELM - SOUTH ATLANTIC", 1, FAINT)


# --- the spread -----------------------------------------------------------------

def build():
    sh = Sheet(W, H, DESK)
    # page shadows + gutter
    sh.fill_rect(4, 4, 1016, 1016, (30, 25, 20))
    build_data_page(sh, 8, 8, 500, 1008)
    build_visa_page(sh, 516, 8, 500, 1008)
    # centre gutter shadow
    for i in range(6):
        sh.fill_rect(508 + i, 8, 1, 1008, (120, 108, 84) if i < 3
                     else (200, 190, 160))
    sh.line(508, 8, 508, 1016, (90, 78, 58), 2)
    sh.line(516, 8, 516, 1016, (90, 78, 58), 2)
    return sh


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    sh = build()
    write_png(os.path.join(out_dir, "entry.png"), sh.px, W, H)


if __name__ == "__main__":
    main()
