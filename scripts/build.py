"""Generates the profile README artwork as self-contained SVGs.

Text is converted to outlines so the SVGs render the same everywhere
(GitHub serves README images without access to web fonts).

Usage: python scripts/build.py <Unbounded.ttf> <Figtree.ttf>
"""
import os
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

BLUE, YELLOW, PINK, GREEN = "#2F5FE3", "#FFD400", "#FF8FB1", "#5DB877"
INK, WHITE, RED = "#111111", "#FFFFFF", "#E8382E"
DYELLOW, DBLUE, DPINK, DGREEN = "#E0B400", "#1F44B8", "#E86A93", "#3F9A5B"
SW = 5
O = f'stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round" stroke-linecap="round"'


class Face:
    def __init__(self, path, wght):
        self.f = instantiateVariableFont(TTFont(path), {"wght": wght})
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.hmtx = self.f["hmtx"]

    def width(self, t, size, ls=0):
        w = sum(self.hmtx[self.cmap[ord(c)]][0] for c in t) * size / self.upm
        return w + ls * max(len(t) - 1, 0)

    def fit(self, t, maxw, maxsize, ls=0):
        return min(maxsize, maxsize * maxw / self.width(t, maxsize, ls))

    def text(self, t, x, y, size, fill=INK, anchor="start", ls=0, extra=""):
        w = self.width(t, size, ls)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        sc = size / self.upm
        pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.1f}")
        for c in t:
            g = self.cmap[ord(c)]
            self.gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, x, y)))
            x += self.hmtx[g][0] * sc + ls
        return f'<path d="{pen.getCommands()}" fill="{fill}" {extra}/>'

    def wrap(self, t, size, maxw):
        lines, cur = [], ""
        for word in t.split():
            trial = (cur + " " + word).strip()
            if self.width(trial, size) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
        return lines


D = Face(sys.argv[1], 900)   # display
B = Face(sys.argv[2], 700)   # body
BX = Face(sys.argv[2], 800)  # labels

MOTION_OFF = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(name, w, h, body, css="", title=""):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
         f"<title>{title}</title><style>{css}{MOTION_OFF}</style>{body}</svg>")
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(s)
    print(f"{name:22s} {len(s)/1024:6.1f} KB")


def st(stroke, extra):
    if not stroke:
        return extra
    o = O.replace(f'stroke-width="{SW}" ', "") if "stroke-width" in extra else O
    return f"{o} {extra}"


def rect(x, y, w, h, fill, rx=0, stroke=True, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {st(stroke, extra)}/>'


def circ(x, y, r, fill, stroke=True, extra=""):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {st(stroke, extra)}/>'


def path(d, fill="none", extra="", stroke=True):
    return f'<path d="{d}" fill="{fill}" {st(stroke, extra)}/>'


def tri(x, y, s, fill=INK, left=False):
    k = -1 if left else 1
    return f'<path d="M{x} {y - s}L{x + k * s * 1.5} {y}L{x} {y + s}Z" fill="{fill}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def cloud(cs):
    return ("".join(f'<circle cx="{x}" cy="{y}" r="{r + SW}" fill="{INK}"/>' for x, y, r in cs)
            + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{WHITE}"/>' for x, y, r in cs))


def pipe(d, fill, w=18):
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w + 2 * SW}" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>')


def gear(cx, cy, r, fill, cls=""):
    teeth = "".join(
        f'<rect x="{-r * 0.2:.1f}" y="{-r * 1.3:.1f}" width="{r * 0.4:.1f}" height="{r * 2.6:.1f}" rx="3" fill="{fill}" {O} transform="rotate({a})"/>'
        for a in (0, 45, 90, 135))
    return (f'<g transform="translate({cx} {cy})"><g class="{cls}">{teeth}'
            f'<circle r="{r}" fill="{fill}" {O}/><circle r="{r * 0.35:.1f}" fill="{INK}"/></g></g>')


def spark(x, y, s, fill):
    return path(f"M{x} {y - s}Q{x} {y} {x + s} {y}Q{x} {y} {x} {y + s}Q{x} {y} {x - s} {y}Q{x} {y} {x} {y - s}Z", fill,
                extra='stroke-width="3"')


def pill(cx, cy, label, fill, face=BX, size=16, padx=18, h=36, ls=0.6, ink=INK):
    w = face.width(label, size, ls) + padx * 2
    return (rect(cx - w / 2, cy - h / 2, w, h, fill, rx=h / 2, extra='stroke-width="4"')
            + face.text(label, cx, cy + size * 0.36, size, ink, "middle", ls)), w


# ---------------------------------------------------------------- hero
def hero():
    W, H = 1200, 520
    b = [rect(0, 0, W, H, BLUE, stroke=False)]

    # name sign
    b += [rect(96, 0, 14, 62, INK, stroke=False), rect(486, 0, 14, 62, INK, stroke=False),
          rect(58, 68, 500, 150, INK, rx=12, stroke=False),
          rect(48, 58, 500, 150, YELLOW, rx=12),
          rect(66, 76, 464, 114, BLUE, rx=4)]
    for x, y in ((57, 67), (539, 67), (57, 199), (539, 199)):
        b.append(circ(x, y, 3.5, INK, stroke=False))
    size = D.fit("SAMARTH", 420, 80)
    b.append(D.text("SAMARTH", 298, 133 + size * 0.02, min(size, 60), WHITE, "middle"))
    b.append(D.text("VERMA", 298, 177, 34, YELLOW, "middle", ls=10))

    b.append(D.text("Ideas in.", 48, 282, 38, WHITE))
    b.append(D.text("Working software out.", 48, 330, 38, WHITE))

    x = 48
    for i, lab in enumerate(["HACKATHON BUILDER", "AI + DESIGN ENGINEER", "FULL-STACK DEVELOPER"]):
        if i == 2:
            x, y = 48, 438
        else:
            y = 388
        w = BX.width(lab, 15, 0.6) + 36
        p, _ = pill(x + w / 2, y, lab, YELLOW if i != 1 else PINK, size=15)
        b.append(p)
        x += w + 12

    b.append(cloud([(60, 540, 62), (150, 556, 52), (-10, 500, 40), (236, 566, 40), (330, 580, 34)]))
    # ---- machine
    # tower
    b += [rect(634, 330, 82, 24, DBLUE, rx=6), rect(640, 96, 70, 240, GREEN, rx=35),
          rect(634, 122, 82, 18, YELLOW, rx=6), rect(634, 296, 82, 18, YELLOW, rx=6)]
    for i, col in enumerate((WHITE, PINK, YELLOW)):
        b.append(circ(675, 172 + i * 48, 17, col, extra=f'class="lamp l{i}"'))
    b.append(pipe("M712 218H768V300H830", PINK))
    # chimney + smoke
    for i, (dx, r) in enumerate(((0, 17), (10, 22), (-6, 26))):
        b.append(f'<g class="puff p{i}">{circ(1120 + dx, 96, r, WHITE)}</g>')
    b += [rect(1100, 128, 40, 92, GREEN), rect(1091, 116, 58, 20, GREEN, rx=5)]
    # conveyor
    b += [rect(626, 466, 12, 40, INK, stroke=False), rect(790, 466, 12, 40, INK, stroke=False),
          rect(604, 440, 240, 28, WHITE, rx=14)]
    for x in range(622, 830, 34):
        b.append(circ(x, 454, 6, INK, stroke=False))
    for i, col in enumerate((WHITE, PINK, GREEN)):
        b.append(f'<g class="box b{i}">{rect(805, 400, 40, 40, col, rx=5)}'
                 f'<path d="M817 412l-6 8 6 8M833 412l6 8-6 8" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></g>')
    b.append(rect(578, 388, 56, 100, PINK, rx=8))
    b.append(rect(588, 400, 36, 10, INK, rx=5, stroke=False))
    # body
    b += [path("M1120 250L1160 214V424L1120 462Z", DYELLOW),
          path("M820 250L860 214H1160L1120 250Z", "#FFE566"),
          rect(820, 250, 300, 212, YELLOW, rx=4),
          rect(798, 384, 36, 64, INK, rx=7, stroke=False)]
    # dome
    b += [path("M900 214A90 90 0 0 1 1080 214Z", PINK),
          gear(990, 176, 22, BLUE, "spin"),
          path("M926 190A66 66 0 0 1 962 146", extra=f'stroke="{WHITE}" stroke-width="7"', stroke=False).replace('fill="none"', f'fill="none" stroke-linecap="round"'),
          rect(888, 208, 204, 14, DBLUE, rx=7)]
    # gauge
    b += [circ(904, 336, 50, WHITE), circ(904, 336, 50, "none")]
    for a in range(-60, 61, 30):
        b.append(f'<path d="M904 298V306" stroke="{INK}" stroke-width="4" stroke-linecap="round" transform="rotate({a} 904 336)"/>')
    b.append(f'<g transform="translate(904 336)"><path class="needle" d="M0 4V-34" stroke="{RED}" stroke-width="6" stroke-linecap="round"/></g>')
    b.append(circ(904, 336, 7, INK, stroke=False))
    # lights, vents, plate
    for i, col in enumerate((RED, GREEN, BLUE)):
        b.append(circ(1000 + i * 40, 290, 12, col, extra=f'class="lamp l{i}"'))
    for i in range(3):
        b.append(f'<path d="M984 {332 + i * 16}H1096" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    b.append(rect(984, 394, 112, 40, WHITE, rx=6))
    b.append(D.text("SV-01", 1040, 422, 20, INK, "middle"))
    b += [spark(770, 96, 16, YELLOW), spark(1178, 300, 12, WHITE), spark(604, 250, 11, WHITE), spark(850, 150, 9, YELLOW)]

    css = (".puff{transform-box:fill-box;transform-origin:center;animation:rise 4.5s linear infinite}"
           ".p1{animation-delay:-1.5s}.p2{animation-delay:-3s}"
           "@keyframes rise{0%{transform:translateY(24px) scale(.5);opacity:0}20%{opacity:1}100%{transform:translateY(-78px) scale(1.15);opacity:0}}"
           ".box{animation:belt 6s linear infinite}.b1{animation-delay:-2s}.b2{animation-delay:-4s}"
           "@keyframes belt{to{transform:translateX(-216px)}}"
           ".spin{animation:spin 8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
           ".needle{animation:swing 3.2s cubic-bezier(.45,0,.2,1) infinite alternate}"
           "@keyframes swing{from{transform:rotate(-52deg)}to{transform:rotate(48deg)}}"
           ".lamp{animation:blink 2.4s steps(1) infinite}.l1{animation-delay:-.8s}.l2{animation-delay:-1.6s}"
           "@keyframes blink{0%,70%{opacity:1}71%,100%{opacity:.35}}")
    svg("hero.svg", W, H, "".join(b), css, "Samarth Verma. Ideas in, working software out.")


# ---------------------------------------------------------------- strips
def ticker_units(labels, size, y, fill, tri_fill, span):
    unit, x = [], 0
    for lab in labels:
        unit.append(D.text(lab, x, y, size, fill))
        x += D.width(lab, size) + 22
        unit.append(tri(x, y - size * 0.36, size * 0.42, tri_fill))
        x += size * 0.63 + 22
    n = int(span / x) + 2
    g = "".join(f'<g transform="translate({i * x:.1f} 0)">{"".join(unit)}</g>' for i in range(n))
    return g, x


def strip():
    W, H = 1200, 50
    g, uw = ticker_units(["SAMARTH VERMA", "IDEAS IN", "WORKING SOFTWARE OUT"], 17, 31, INK, BLUE, W)
    body = (rect(0, 0, W, H, YELLOW, stroke=False) + f'<g class="t">{g}</g>'
            + rect(0, 0, W, 5, INK, stroke=False) + rect(0, H - 5, W, 5, INK, stroke=False))
    css = f".t{{animation:t 16s linear infinite}}@keyframes t{{to{{transform:translateX(-{uw:.1f}px)}}}}"
    svg("strip.svg", W, H, body, css, "Samarth Verma: ideas in, working software out")


def header(name, title):
    W, H = 1200, 84
    g, uw = ticker_units(["SAMARTH VERMA"], 14, 47, WHITE, YELLOW, 360)
    body = (rect(0, 0, W, H, BLUE, stroke=False)
            + '<clipPath id="l"><rect x="0" y="0" width="330" height="84"/></clipPath>'
            + '<clipPath id="r"><rect x="870" y="0" width="330" height="84"/></clipPath>'
            + f'<g clip-path="url(#l)"><g class="t">{g}</g></g>'
            + f'<g clip-path="url(#r)"><g transform="translate(870 0)"><g class="t">{g}</g></g></g>'
            + tri(338, 42, 9, YELLOW) + tri(862, 42, 9, YELLOW, left=True)
            + rect(374, 16, 460, 56, INK, rx=28, stroke=False)
            + rect(370, 12, 460, 56, YELLOW, rx=28)
            + D.text(title, 600, 50, 25, INK, "middle", ls=2)
            + rect(0, 0, W, 5, INK, stroke=False) + rect(0, H - 5, W, 5, INK, stroke=False))
    css = f".t{{animation:t 12s linear infinite}}@keyframes t{{to{{transform:translateX(-{uw:.1f}px)}}}}"
    svg(name, W, H, body, css, title.title())


# ---------------------------------------------------------------- about
def about():
    W, H = 1200, 530
    lines = ["Builds AI products end to end, from model to interface.",
             "Most begin at hackathons: SIH 2026, IIT Mandi Multimodal AI, Build Arena.",
             "Cyclone forecasts, voice bridges, coronary risk maps, skill passports.",
             "TypeScript, Python, Flutter, Swift. Whichever the job needs."]
    b = [rect(0, 0, W, H, YELLOW, stroke=False),
         cloud([(40, 500, 60), (120, 520, 50), (-10, 430, 44), (190, 540, 36)]),
         cloud([(1160, 500, 60), (1080, 520, 50), (1210, 430, 44), (1010, 540, 36)]),
         path("M220 438V86A46 46 0 0 1 266 40H934A46 46 0 0 1 980 86V438Z", BLUE),
         rect(246, 70, 708, 350, "#FFE566", rx=6)]
    y = 122
    for l in lines:
        for w in B.wrap(l, 25, 676):
            b.append(B.text(w, 600, y, 25, INK, "middle"))
            y += 34
        y += 16
    b += [rect(196, 446, 808, 56, DPINK, rx=10), rect(196, 436, 808, 56, PINK, rx=10)]
    for i, x in enumerate((226, 276)):
        b.append(rect(x, 448, 34, 32, BLUE, rx=5))
        b.append(tri(x + (22 if i == 0 else 12), 464, 7, WHITE, left=(i == 0)))
    b += [circ(952, 466, 21, INK, stroke=False), circ(952, 462, 21, RED),
          D.text("GO", 952, 468, 13, WHITE, "middle"),
          gear(1090, 110, 26, WHITE, "spin"), gear(1136, 160, 16, PINK, "spin2"),
          spark(110, 120, 20, WHITE), spark(160, 200, 11, BLUE)]
    css = (".spin{animation:s 9s linear infinite}.spin2{animation:s 5.6s linear infinite reverse}"
           "@keyframes s{to{transform:rotate(360deg)}}")
    svg("about.svg", W, H, "".join(b), css, "About: " + " ".join(lines))


# ---------------------------------------------------------------- project cards
def ic(body):
    return f'<g transform="translate(130 112)" {O}>{body}</g>'


ICONS = {
    "vaayu": ic(f'<path d="M0 -12C22 -44 46 -12 32 10M0 12C-22 44 -46 12 -32 -10" fill="none" stroke-width="7"/>'
                f'<circle r="13" fill="{BLUE}"/>'),
    "yogyata": ic(f'<rect x="-24" y="-32" width="48" height="64" rx="7" fill="{WHITE}"/>'
                  f'<circle cy="-11" r="10" fill="{BLUE}"/><path d="M-11 13l7 7 14-14" fill="none" stroke-width="6"/>'),
    "vaani": ic(f'<path d="M-38 -30H4A7 7 0 0 1 11 -23V-3A7 7 0 0 1 4 4H-20L-32 15V4H-38A7 7 0 0 1 -45 -3V-23A7 7 0 0 1 -38 -30Z" fill="{WHITE}"/>'
                f'<path d="M-4 -6H38A7 7 0 0 1 45 1V21A7 7 0 0 1 38 28H32V39L20 28H-4A7 7 0 0 1 -11 21V1A7 7 0 0 1 -4 -6Z" fill="{PINK}"/>'),
    "cardio": ic(f'<path d="M0 30C-46 0 -24 -36 0 -14C24 -36 46 0 0 30Z" fill="{RED}"/>'
                 f'<path d="M-22 2H-8L-2 -9L5 12L10 2H22" fill="none" stroke="{WHITE}" stroke-width="4"/>'),
    "noeffort": ic(f'<rect x="-32" y="-34" width="38" height="68" rx="8" fill="{BLUE}"/>'
                   f'<rect x="-25" y="-24" width="24" height="40" rx="3" fill="{WHITE}" stroke-width="3"/>'
                   f'<path d="M18 -12A16 16 0 0 1 18 12M28 -22A30 30 0 0 1 28 22" fill="none" stroke-width="6"/>'),
    "overear": ic(f'<rect x="-2" y="-8" width="16" height="44" rx="8" fill="{WHITE}"/><circle cx="-6" cy="-12" r="20" fill="{WHITE}"/>'
                  f'<circle cx="-10" cy="-14" r="6" fill="{INK}" stroke="none"/>'
                  f'<path d="M26 -30A26 26 0 0 1 34 -6" fill="none" stroke-width="6"/>'),
}

PROJECTS = [
    ("vaayu", "VaayuDrishti", "Cyclone tracks, uncertainty and district exposure from ECMWF ensemble forecasts.", "PYTHON"),
    ("yogyata", "Yogyata", "Skill passports where Verified is granted only by a human who reviewed real work.", "TYPESCRIPT"),
    ("vaani", "VaaniSetu", "Offline, on-device voice bridge from Hindi to Santali for primary classrooms.", "FLUTTER"),
    ("cardio", "CardioMap", "Coronary risk from bedside data, painted per vessel on a 3D heart.", "PYTHON"),
    ("noeffort", "noEffortLabs", "Describe a voice assistant in plain words, talk to it, put it on a phone line.", "TYPESCRIPT"),
    ("overear", "over-ear", "Answer Claude Code permission prompts with a tap on Bluetooth earbuds.", "SWIFT"),
]


def card(key, name, desc, lang):
    W, H = 600, 290
    b = [rect(0, 0, W, H, PINK, stroke=False),
         f'<ellipse cx="130" cy="246" rx="74" ry="10" fill="{DPINK}"/>',
         path("M58 168H202V196A44 44 0 0 1 158 240H102A44 44 0 0 1 58 196Z", BLUE),
         path("M58 168V112A72 72 0 0 1 202 112V168Z", YELLOW),
         f'<path d="M76 118A54 54 0 0 1 104 66" fill="none" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>',
         ICONS[key],
         rect(46, 160, 168, 18, DBLUE, rx=9)]
    b.append(D.text(name, 244, 92, D.fit(name, 320, 31), INK))
    y = 128
    for l in B.wrap(desc, 18.5, 322):
        b.append(B.text(l, 244, y, 18.5, INK))
        y += 26
    p, w = pill(244 + (BX.width(lang, 13, 0.8) + 30) / 2, 232, lang, YELLOW, size=13, padx=15, h=30, ls=0.8)
    b.append(p)
    b += [circ(548, 232, 19, INK, stroke=False),
          f'<path d="M539 232H556M549 224l8 8-8 8" fill="none" stroke="{WHITE}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>']
    svg(f"card-{key}.svg", W, H, "".join(b), "", f"{name}: {desc}")


# ---------------------------------------------------------------- stack
def stack():
    W, H = 1200, 370
    cols = [("LANGUAGES", ["TypeScript", "Python", "Dart", "Swift"]),
            ("FRAMEWORKS", ["React", "Flutter", "Tailwind CSS", "Node.js"]),
            ("DOMAINS", ["Voice AI", "Forecast data", "Clinical ML", "On-device apps"])]
    b = [rect(0, 0, W, H, GREEN, stroke=False), pipe("M-20 196H1220", PINK, 22)]
    for i, (title, items) in enumerate(cols):
        x = 90 + i * 360
        b += [rect(x + 10, 60, 300, 268, INK, rx=10, stroke=False), rect(x, 50, 300, 268, PINK, rx=10)]
        p, _ = pill(x + 150, 50, title, GREEN, face=D, size=15, padx=22, h=40, ls=1.5)
        b.append(p)
        for j, it in enumerate(items):
            y = 92 + j * 52
            b.append(rect(x + 26, y, 248, 38, YELLOW if j % 2 == 0 else WHITE, rx=19, extra='stroke-width="4"'))
            b.append(BX.text(it, x + 150, y + 25.5, 17, INK, "middle"))
        if i < 2:
            b += [rect(x + 318, 178, 24, 36, YELLOW, rx=5)]
    svg("stack.svg", W, H, "".join(b), "", "Stack: " + "; ".join(f"{t.title()}: {', '.join(i)}" for t, i in cols))


# ---------------------------------------------------------------- contact buttons
def button(name, label, fill):
    W, H = 300, 92
    body = (rect(14, 16, 276, 64, INK, rx=32, stroke=False) + rect(6, 8, 276, 64, fill, rx=32)
            + D.text(label, 130, 48, D.fit(label, 170, 19), INK, "middle", ls=1)
            + circ(246, 40, 17, INK, stroke=False)
            + f'<path d="M238 40H253M247 33l7 7-7 7" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
    svg(name, W, H, body, "", label.title())


os.makedirs(OUT, exist_ok=True)
hero()
strip()
header("head-about.svg", "ABOUT")
header("head-projects.svg", "SHIPPED PROJECTS")
header("head-stack.svg", "STACK")
header("head-contact.svg", "SAY HELLO")
about()
for p in PROJECTS:
    card(*p)
stack()
button("btn-linkedin.svg", "LINKEDIN", PINK)
button("btn-email.svg", "EMAIL", GREEN)
