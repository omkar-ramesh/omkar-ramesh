"""
make_hardware_panel.py
----------------------
Renders hardware-panel.svg -- the workstation strip.

Replaces the old one-line "Hardware: RTX 5090 + Mac Mini M4" text row
with pixel-art machines that actually move:

  * the GPU's two fans spin continuously (2-frame flipbook, second fan
    offset so the pair doesn't beat in lockstep and read as one part)
  * both machines carry a status LED that breathes

These loop forever while the rest of the profile freezes after its
intro -- that contrast is the point: the still panels are the content,
these are the heartbeat.

Sprites are GENERATED, not hand-drawn. Fan housings need to be circular
and blades need to be clipped to that circle; typing that as 18 rows of
ASCII by hand is unreadable and impossible to tweak. Emitting them from
simple distance math means the radius, blade count and body proportions
are all one-line changes.

Labels only, no specs. I don't know the Mac Mini's config or what either
box is actually used for, and "64GB / training rig" on a public profile
is a claim, not decoration.

Usage:
    python scripts/make_hardware_panel.py
"""

import math
import os

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_FAINT, BG_INSET, BORDER_SOFT,
    GREEN, CYAN,
    esc, panel, fade_up,
)
from sprites import sprite_rects, sprite_w, sprite_h, flipbook, pulse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "hardware-panel.svg")

PX = 4  # size of one sprite pixel, in SVG units (shared by all sprites,
        # so the "resolution" reads as consistent across the panel)

# ---------------------------------------------------------------- palettes

GPU_PALETTE = {
    ".": None,
    "S": "#3d444d",   # shroud edge highlight
    "B": "#22272e",   # card body
    "h": "#0b0f14",   # fan recess
    "r": "#30363d",   # fan housing ring
    "G": "#f2cc60",   # gold PCIe fingers
    "K": "#545d68",   # I/O bracket metal
    "p": "#0b0f14",   # display port cutouts
    "C": "#30363d",   # power connector
    "L": GREEN,       # status LED (drawn separately so it can pulse)
}

FAN_PALETTE = {".": None, "b": "#79c0ff", "@": "#c9d1d9"}

MAC_PALETTE = {
    ".": None,
    "E": "#3d444d",   # outline
    "T": "#b1bac4",   # top surface (silver)
    "a": "#767e87",   # apple mark
    "S": "#6e7681",   # front face, in shadow
    "v": "#4a525b",   # vent slots
}

LED_PALETTE = {".": None, "L": GREEN, "p": "#e6edf3"}

# ---------------------------------------------------------------- GPU art

# Triple-fan card. The silhouette is what makes it read as a GPU rather
# than a generic box: an I/O bracket with display cutouts on one end,
# gold PCIe fingers along the bottom, and a power connector up top. Strip
# those and three circles on a rectangle look like a rack server.
GPU_W, GPU_H = 58, 24
FAN_CENTERS = ((14, 11), (30, 11), (46, 11))
FAN_R = 6.0
FAN_N = 13          # fan sprite is FAN_N x FAN_N
LED_CELLS = ((52, 16), (53, 16))


def _blank(w, h):
    return [["."] * w for _ in range(h)]


def make_gpu_body():
    g = _blank(GPU_W, GPU_H)

    # --- I/O bracket, standing proud of the shroud at the left end
    for y in range(1, 22):
        for x in range(1, 4):
            g[y][x] = "K"
    # display output cutouts
    for sy in (4, 9, 14):
        for y in range(sy, sy + 3):
            g[y][2] = "p"

    # --- shroud slab
    for y in range(2, 20):
        for x in range(5, 57):
            g[y][x] = "B"
    for x in range(5, 57):
        g[2][x] = "S"
        g[19][x] = "S"
    for y in range(2, 20):
        g[y][5] = "S"
        g[y][56] = "S"

    # --- circular fan recesses with a one-pixel housing ring
    for (fcx, fcy) in FAN_CENTERS:
        for y in range(GPU_H):
            for x in range(GPU_W):
                d2 = (x - fcx) ** 2 + (y - fcy) ** 2
                if d2 <= FAN_R ** 2:
                    g[y][x] = "h"
                elif d2 <= (FAN_R + 1) ** 2 and g[y][x] == "B":
                    g[y][x] = "r"

    # --- 12VHPWR power connector on the top edge
    for y in range(0, 2):
        for x in range(44, 54):
            g[y][x] = "C"

    # --- gold PCIe fingers along the bottom, in the usual two blocks
    for x in range(8, 16):
        g[20][x] = "G"
        g[21][x] = "G"
    for x in range(18, 32):
        g[20][x] = "G"
        g[21][x] = "G"

    return ["".join(row) for row in g]


def make_gpu_led():
    g = _blank(GPU_W, GPU_H)
    for (x, y) in LED_CELLS:
        g[y][x] = "L"
    return ["".join(row) for row in g]


def make_fan(angle_deg: float):
    """4-blade fan clipped to a circle, blades rotated `angle_deg`.

    A 4-blade fan is two perpendicular lines through the hub, so the
    pattern repeats every 90 degrees. Rendering the sweep as real
    rotation (rather than just toggling + and X) is what stops it
    reading as a flicker: two frames alternating look broken, four
    frames at 22.5-degree steps look like a spinning fan.
    """
    a = math.radians(angle_deg)
    b = a + math.pi / 2
    c = FAN_N // 2
    g = _blank(FAN_N, FAN_N)
    for y in range(FAN_N):
        for x in range(FAN_N):
            dx, dy = x - c, y - c
            if dx * dx + dy * dy > (FAN_R - 0.2) ** 2:
                continue
            # perpendicular distance to each blade line through the hub
            d1 = abs(dx * math.sin(a) - dy * math.cos(a))
            d2 = abs(dx * math.sin(b) - dy * math.cos(b))
            if min(d1, d2) <= 1.0:
                g[y][x] = "b"
    g[c][c] = "@"
    return ["".join(row) for row in g]


GPU_BODY = make_gpu_body()
GPU_LED = make_gpu_led()
# One 90-degree sweep, which is a full cycle for a 4-blade fan
FAN_FRAMES = [make_fan(a) for a in (0, 22.5, 45, 67.5)]

# ----------------------------------------------------------- Mac Mini art

MAC_W, MAC_H = 38, 26

# Apple mark. The three things that make it readable at this size are the
# leaf leaning right off the top, the notch between the two top lobes,
# and the bite out of the right edge. Drop any one and it just reads as a
# blob.
# Structure follows the classic 1977 Apple pixel mark: a detached
# diagonal leaf off the top right, a notch between the two top lobes, a
# bite stepping into the right edge across three rows, and split feet at
# the bottom. Those four features are the whole silhouette -- lose any
# and it collapses into a blob.
APPLE = [
    ".........##.....",
    "........##......",
    ".......##.......",
    "....###..####...",
    "...##########...",
    "..###########...",
    ".############...",
    ".##########.....",
    ".#########......",
    ".##########.....",
    ".############...",
    ".############...",
    "..##########....",
    "..###....###....",
]


TOP_ROWS = (2, 19)      # inclusive range of the silver top surface
FRONT_ROWS = (20, 23)   # front face, in shadow
BODY_COLS = (2, 35)


def make_mac_body():
    g = _blank(MAC_W, MAC_H)
    x0, x1 = BODY_COLS

    # slab
    for y in range(TOP_ROWS[0], FRONT_ROWS[1] + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = "T" if y <= TOP_ROWS[1] else "S"

    # outline
    for x in range(x0, x1 + 1):
        g[TOP_ROWS[0]][x] = "E"
        g[FRONT_ROWS[1]][x] = "E"
    for y in range(TOP_ROWS[0], FRONT_ROWS[1] + 1):
        g[y][x0] = "E"
        g[y][x1] = "E"
    # seam where the top surface meets the front face
    for x in range(x0 + 1, x1):
        g[FRONT_ROWS[0]][x] = "E"

    # knock the corners off so it reads as a rounded slab
    for (x, y) in ((x0, 2), (x1, 2), (x0, 23), (x1, 23),
                   (x0 + 1, 2), (x1 - 1, 2), (x0 + 1, 23), (x1 - 1, 23),
                   (x0, 3), (x1, 3), (x0, 22), (x1, 22)):
        g[y][x] = "."

    # apple mark, centered on the top surface
    ax = x0 + (x1 - x0 + 1 - len(APPLE[0])) // 2
    ay = 4
    for r, row in enumerate(APPLE):
        for c, ch in enumerate(row):
            if ch == "#":
                g[ay + r][ax + c] = "a"

    # vent slots along the front face
    for x in range(24, 34, 2):
        g[22][x] = "v"

    return ["".join(row) for row in g]


def make_mac_led():
    g = _blank(MAC_W, MAC_H)
    g[22][6] = "p"
    return ["".join(row) for row in g]


MAC_BODY = make_mac_body()
MAC_LED = make_mac_led()

# ------------------------------------------------------------------ panel


def gpu_art(cx, cy):
    parts = [sprite_rects(GPU_BODY, GPU_PALETTE, cx, cy, PX)]
    parts.append(pulse(GPU_LED, LED_PALETTE, cx, cy, PX, dur=1.8, lo=0.25))
    # All three fans share frames, speed AND start time. Offsetting them
    # made the card look faulty rather than mechanical -- fans on one
    # card are driven together, so they should read as one assembly.
    for (fcx, fcy) in FAN_CENTERS:
        ox = cx + (fcx - FAN_N // 2) * PX
        oy = cy + (fcy - FAN_N // 2) * PX
        parts.append(flipbook(FAN_FRAMES, FAN_PALETTE, ox, oy, PX,
                              frame_dur=0.07))
    return "".join(parts)


def mac_art(cx, cy):
    return (sprite_rects(MAC_BODY, MAC_PALETTE, cx, cy, PX)
            + pulse(MAC_LED, LED_PALETTE, cx, cy, PX, dur=2.6, lo=0.15))


MACHINES = [
    {"label": "RTX 5090", "sub": "NVIDIA discrete GPU",
     "accent": GREEN, "sprite": GPU_BODY, "art": gpu_art},
    {"label": "Mac Mini M4", "sub": "Apple silicon desktop",
     "accent": CYAN, "sprite": MAC_BODY, "art": mac_art},
]

CARD_H = 168


def build():
    usable = CANVAS_W - PAD * 2
    gap = 20
    card_w = (usable - gap * (len(MACHINES) - 1)) / len(MACHINES)

    top = 58
    body = []
    art_band_h = sprite_h(GPU_BODY, PX)

    for i, m in enumerate(MACHINES):
        x = PAD + i * (card_w + gap)
        begin = round(0.15 + i * 0.14, 3)

        sw, sh = sprite_w(m["sprite"], PX), sprite_h(m["sprite"], PX)
        sx = x + (card_w - sw) / 2
        # bottom-align the sprites so the two machines sit on one shelf
        sy = top + 20 + (art_band_h - sh)

        label_y = top + CARD_H - 40
        sub_y = top + CARD_H - 21

        body.append(f"""
  <g opacity="0">{fade_up(begin)}
    <rect x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="{CARD_H}" rx="10"
          fill="{BG_INSET}" stroke="{BORDER_SOFT}" stroke-width="1" />
    <rect x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="2.5" rx="1.25"
          fill="{m['accent']}" />
    {m['art'](sx, sy)}
    <text x="{x + card_w / 2:.1f}" y="{label_y}" font-family="{MONO}"
          font-size="13.5" font-weight="bold" fill="{TEXT}"
          text-anchor="middle">{esc(m['label'])}</text>
    <text x="{x + card_w / 2:.1f}" y="{sub_y}" font-family="{MONO}"
          font-size="10.5" fill="{TEXT_FAINT}"
          text-anchor="middle">{esc(m['sub'])}</text>
  </g>""")

    height = int(top + CARD_H + PAD)
    return panel(CANVAS_W, height, "lspci | workstation", "".join(body))


def main():
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Saved hardware panel -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
