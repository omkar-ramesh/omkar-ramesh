"""
make_neofetch_card.py
---------------------
Renders neofetch-card.svg -- the identity panel, laid out the way real
neofetch output looks: a chunky ASCII logo on the left, key/value system
info on the right, and the classic color-palette strip along the bottom.

Both columns live inside ONE svg rather than two images in a markdown
table. GitHub's table rendering can't be trusted to hold two images in
exact vertical alignment across themes and viewport widths, but an SVG's
internal coordinates always will.

Animation: the bolt wipes in row by row, then the info rows fade-and-rise
in sequence (like neofetch printing its output), then the palette blocks
pop in left to right.

Edit ROWS to change the card's content, then re-run.

Usage:
    python scripts/make_neofetch_card.py
"""

import os

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_DIM, TEXT_FAINT, BG_INSET, BORDER_SOFT,
    GREEN, CYAN, PURPLE, YELLOW, ORANGE, PINK,
    esc, panel, linear_gradient, wipe_reveal, fade_up, text_w,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "neofetch-card.svg")

HEADER_USER = "omkar"
HEADER_HOST = "thunderx10"

# Exact card content -- edit here, then re-run the script.
ROWS = [
    ("User", "Omkar Ramesh"),
    ("Role", "AI Engineer & Founder"),
    ("Company", "Oniqutes Digital Solutions"),
    ("Stack", "Python • Next.js • ComfyUI • Ollama • Flux"),
    # Hardware intentionally omitted -- it has its own panel now
    # (hardware-panel.svg), with pixel art instead of a text row.
    ("Focus", "Local AI Agents • Client Web Apps • LoRA Training"),
    ("Location", "India"),
]

# Lightning bolt -- the "distro logo" slot. Block glyphs only (█ ▀ ▄),
# which render reliably in monospace across platforms.
BOLT = [
    "        ▄▄████",
    "      ▄██████▀",
    "    ▄██████▀  ",
    "  ▄██████▀    ",
    " ▄██████▀     ",
    "▄███████████▄ ",
    "▀▀▀▀▀▄█████▀  ",
    "    ▄█████▀   ",
    "   ▄████▀     ",
    "  ▄███▀       ",
    " ▄██▀         ",
    " ▀            ",
]

PALETTE = [GREEN, CYAN, PURPLE, YELLOW, ORANGE, PINK,
           "#56d364", "#a5d6ff"]

BOLT_FONT = 13
BOLT_LINE_H = 15.5
ROW_FONT = 13
ROW_H = 27


def build():
    body = []

    content_top = 62
    bolt_x = PAD + 14
    bolt_w = text_w(BOLT[0], BOLT_FONT)

    grad_id = "bolt-grad"
    gradients = linear_gradient(
        grad_id,
        [(0, YELLOW), (0.55, ORANGE), (1, GREEN)],
        x1=bolt_x, y1=content_top,
        x2=bolt_x + bolt_w, y2=content_top + len(BOLT) * BOLT_LINE_H,
    )

    # --- left column: bolt logo, row-by-row wipe
    for i, line in enumerate(BOLT):
        y = content_top + i * BOLT_LINE_H
        begin = round(0.1 + i * 0.06, 3)
        clip_id = f"bolt-{i}"
        body.append(wipe_reveal(clip_id, bolt_x, y - BOLT_FONT,
                                bolt_w, BOLT_LINE_H, begin, 0.5))
        body.append(f"""
  <g clip-path="url(#{clip_id})">
    <text x="{bolt_x}" y="{y}" font-family="{MONO}" font-size="{BOLT_FONT}"
          fill="url(#{grad_id})" xml:space="preserve">{esc(line)}</text>
  </g>""")

    # --- right column: header + rows
    info_x = PAD + bolt_w + 60
    key_w = max(text_w(k, ROW_FONT) for k, _ in ROWS) + 26

    header = f"{HEADER_USER}@{HEADER_HOST}"
    header_y = content_top + 4
    body.append(f"""
  <g opacity="0">{fade_up(0.35)}
    <text x="{info_x}" y="{header_y}" font-family="{MONO}" font-size="14.5"
          font-weight="bold" fill="{GREEN}">{esc(HEADER_USER)}<tspan fill="{TEXT_FAINT}">@</tspan><tspan fill="{CYAN}">{esc(HEADER_HOST)}</tspan></text>
    <line x1="{info_x}" y1="{header_y + 11}" x2="{CANVAS_W - PAD}" y2="{header_y + 11}"
          stroke="{BORDER_SOFT}" stroke-width="1" />
  </g>""")

    rows_top = header_y + 38
    for i, (key, value) in enumerate(ROWS):
        y = rows_top + i * ROW_H
        begin = round(0.55 + i * 0.11, 3)
        body.append(f"""
  <g opacity="0">{fade_up(begin)}
    <text x="{info_x}" y="{y}" font-family="{MONO}" font-size="{ROW_FONT}"
          font-weight="bold" fill="{CYAN}">{esc(key)}</text>
    <text x="{info_x + key_w}" y="{y}" font-family="{MONO}" font-size="{ROW_FONT}"
          fill="{TEXT}">{esc(value)}</text>
  </g>""")

    # --- palette strip (neofetch's signature color blocks)
    bolt_bottom = content_top + len(BOLT) * BOLT_LINE_H
    rows_bottom = rows_top + len(ROWS) * ROW_H
    strip_y = max(bolt_bottom, rows_bottom) + 14

    block_w, block_h, gap = 26, 11, 6
    strip_begin = 0.55 + len(ROWS) * 0.11 + 0.15
    for i, color in enumerate(PALETTE):
        x = info_x + i * (block_w + gap)
        begin = round(strip_begin + i * 0.05, 3)
        body.append(f"""
  <rect x="{x}" y="{strip_y}" width="{block_w}" height="{block_h}" rx="2.5"
        fill="{color}" opacity="0">
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s"
             dur="0.3s" fill="freeze" />
  </rect>""")

    height = int(strip_y + block_h + PAD)
    return panel(CANVAS_W, height, "neofetch", "".join(body), gradients)


def main():
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Saved neofetch card -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
