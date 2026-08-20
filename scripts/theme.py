"""
theme.py
--------
Shared design tokens + SVG helpers for every panel in the profile.

Everything renders on one 860px-wide grid so the panels stack into a
single coherent column on the GitHub profile. Keeping the palette and
geometry in one place is what makes the separate SVGs read as one
designed page rather than four unrelated images.

All animation is SMIL (<animate> / <animateTransform>) because GitHub
strips <script> and sanitizes inline CSS from README-embedded SVGs, but
does run SMIL inside images loaded via <img>.
"""

# ---------------------------------------------------------------- layout

CANVAS_W = 860          # every panel is this wide -> clean vertical stack
PAD = 30                # standard inner padding
RADIUS = 12             # panel corner radius

# ---------------------------------------------------------------- colors
# GitHub-dark derived palette. Kept deliberately tight: one background,
# one border, three text weights, and a small accent ramp used for the
# gradient sweeps and the contribution greens.

BG = "#0d1117"
BG_INSET = "#010409"    # darker wells (chips, stat cards)
BORDER = "#30363d"
BORDER_SOFT = "#21262d"

TEXT = "#e6edf3"        # primary
TEXT_DIM = "#8b949e"    # secondary / labels
TEXT_FAINT = "#484f58"  # tertiary / decoration

GREEN = "#39d353"
CYAN = "#79c0ff"
PURPLE = "#bc8cff"
YELLOW = "#f2cc60"
ORANGE = "#ffa657"
PINK = "#ff7b9c"

# Contribution heatmap ramp (levels 0..5)
HEAT = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# Traffic-light dots used on every panel's title bar
DOT_RED = "#ff5f56"
DOT_AMBER = "#ffbd2e"
DOT_GREEN = "#27c93f"

# ---------------------------------------------------------------- type

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace"

# Monospace advance-width ratio. Used to size clip rects and chips from
# character counts, since we can't measure text at generation time.
CHAR_RATIO = 0.6


def char_w(font_size: float) -> float:
    """Approximate advance width of one monospace glyph."""
    return font_size * CHAR_RATIO


def text_w(s: str, font_size: float) -> float:
    return len(s) * char_w(font_size)


# ---------------------------------------------------------------- helpers

def esc(s: str) -> str:
    """XML-escape text content."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def panel(width: int, height: int, title: str, body: str,
          gradients: str = "") -> str:
    """Wrap panel content in the shared window chrome.

    Every panel gets the same frame -- rounded dark card, hairline
    border, three traffic-light dots, and a dim title label -- so the
    stacked panels read as windows on one desktop.
    """
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <defs>{gradients}</defs>
  <rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="{RADIUS}"
        fill="{BG}" stroke="{BORDER}" stroke-width="1.5" />
  <line x1="0" y1="38" x2="{width}" y2="38" stroke="{BORDER_SOFT}" stroke-width="1" />
  <circle cx="{PAD}" cy="19.5" r="5.5" fill="{DOT_RED}" />
  <circle cx="{PAD + 19}" cy="19.5" r="5.5" fill="{DOT_AMBER}" />
  <circle cx="{PAD + 38}" cy="19.5" r="5.5" fill="{DOT_GREEN}" />
  <text x="{width / 2}" y="24" font-family="{MONO}" font-size="11.5"
        fill="{TEXT_FAINT}" text-anchor="middle">{esc(title)}</text>
{body}
</svg>
"""


def linear_gradient(gid: str, stops, x1: float, x2: float,
                    y1: float = 0, y2: float = 0) -> str:
    """Horizontal (or diagonal) gradient in user-space coordinates, so it
    spans a known pixel range rather than each glyph individually."""
    stop_tags = "".join(
        f'<stop offset="{off}" stop-color="{color}" />' for off, color in stops
    )
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
        f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{stop_tags}</linearGradient>'
    )


def wipe_reveal(clip_id: str, x: float, y: float, w: float, h: float,
                begin: float, dur: float = 0.5) -> str:
    """A clipPath whose rect widens 0 -> w, revealing content left to
    right like it's being typed/printed."""
    return f"""
  <clipPath id="{clip_id}">
    <rect x="{x}" y="{y}" width="0" height="{h}">
      <animate attributeName="width" from="0" to="{w}" begin="{begin}s"
               dur="{dur}s" fill="freeze" calcMode="spline"
               keySplines="0.22 0.61 0.36 1" />
    </rect>
  </clipPath>"""


def fade_up(begin: float, dur: float = 0.45, dy: float = 8) -> str:
    """Animation pair for a group: fade in while settling upward."""
    return f"""
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s"
             dur="{dur}s" fill="freeze" />
    <animateTransform attributeName="transform" type="translate"
                      from="0,{dy}" to="0,0" begin="{begin}s" dur="{dur}s"
                      fill="freeze" calcMode="spline"
                      keySplines="0.22 0.61 0.36 1" />"""


def blink(x: float, y: float, w: float, h: float, color: str,
          begin: float) -> str:
    """Looping block cursor -- the one animation that never freezes, so
    the profile reads as 'live' after everything else settles."""
    return f"""
  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="0">
    <animate attributeName="opacity" values="0;1;1;0;0"
             keyTimes="0;0.01;0.5;0.51;1" begin="{begin}s" dur="1.05s"
             repeatCount="indefinite" />
  </rect>"""
