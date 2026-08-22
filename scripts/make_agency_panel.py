"""
make_agency_panel.py
--------------------
Renders agency-panel.svg -- the Oniqutes Digital Solutions section.

Three service cards, each with an animated pixel-art icon:
  * the bot blinks
  * the browser window's tab bar cycles like it's loading
  * the chip's core pulses

NOTE ON CONTENT: the three services below are derived from the Focus line
already on the neofetch card ("Local AI Agents / Client Web Apps / LoRA
Training"). They are a reasonable reading of what the agency does, but
they are an inference, not something confirmed. Anything more specific --
real service names, client counts, founding year, pricing, a website --
has to come from you. Inventing those on a public business page would be
fabricating commercial claims, so the fields simply aren't here.

Edit AGENCY and SERVICES, then re-run.

Usage:
    python scripts/make_agency_panel.py
"""

import os

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_DIM, TEXT_FAINT, BG_INSET, BORDER_SOFT,
    GREEN, CYAN, PURPLE, PINK,
    esc, panel, fade_up, text_w,
)
from sprites import sprite_rects, sprite_w, sprite_h, flipbook, pulse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "agency-panel.svg")

PX = 4

AGENCY_NAME = "Oniqutes Digital Solutions"
AGENCY_ROLE = "Founder"

# ------------------------------------------------------------- pixel icons

ICON_PALETTE = {
    ".": None,
    "#": "#484f58",   # chassis / frame
    "o": GREEN,       # lit elements (recolored per card below)
    "a": GREEN,       # accent detail
}

BOT_OPEN = [
    ".....a.....",
    ".....a.....",
    "..#######..",
    ".#########.",
    ".#.o...o.#.",
    ".#.......#.",
    ".#..ooo..#.",
    ".#########.",
    "..#.....#..",
    "..##...##..",
    "...........",
]

BOT_BLINK = [
    ".....a.....",
    ".....a.....",
    "..#######..",
    ".#########.",
    ".#.......#.",
    ".#.ooo.ooo.",
    ".#..ooo..#.",
    ".#########.",
    "..#.....#..",
    "..##...##..",
    "...........",
]

BROWSER_BASE = [
    "...........",
    ".#########.",
    ".#.......#.",
    ".#########.",
    ".#.......#.",
    ".#..###..#.",
    ".#.#####.#.",
    ".#.......#.",
    ".#########.",
    "...........",
    "...........",
]

# tab-bar dots light up in sequence, like a page loading
BROWSER_FRAMES = []
for _lit in range(3):
    _f = [list(r) for r in BROWSER_BASE]
    for _i in range(3):
        _f[2][2 + _i] = "o" if _i == _lit else "."
    BROWSER_FRAMES.append(["".join(r) for r in _f])

CHIP_BODY = [
    "...#.#.#...",
    "..#######..",
    ".#########.",
    "##.......##",
    "#.........#",
    "#.........#",
    "#.........#",
    "##.......##",
    ".#########.",
    "..#######..",
    "...#.#.#...",
]

CHIP_CORE = [
    "...........",
    "...........",
    "...........",
    "...........",
    "...ooooo...",
    "...o...o...",
    "...ooooo...",
    "...........",
    "...........",
    "...........",
    "...........",
]

# --------------------------------------------------------------- services


def bot_art(x, y, accent):
    pal = dict(ICON_PALETTE, o=accent, a=accent)
    # mostly open-eyed, with a quick blink -- weight the frames by
    # holding BOT_OPEN for several cycles before the single blink frame
    frames = [BOT_OPEN] * 7 + [BOT_BLINK]
    return flipbook(frames, pal, x, y, PX, frame_dur=0.34)


def browser_art(x, y, accent):
    pal = dict(ICON_PALETTE, o=accent, a=accent)
    return flipbook(BROWSER_FRAMES, pal, x, y, PX, frame_dur=0.38)


def chip_art(x, y, accent):
    pal = dict(ICON_PALETTE, o=accent, a=accent)
    return (sprite_rects(CHIP_BODY, pal, x, y, PX)
            + pulse(CHIP_CORE, pal, x, y, PX, dur=1.9, lo=0.22))


# Matches the services actually listed on oniqutes.com (checked
# directly, not inferred) -- Web Development, App Development,
# Conversational Agents & Chatbots, and Workflow Automation, condensed
# to the three that fit an engineering-facing GitHub profile. The site
# also lists Business & Marketing and Business Strategy, which are
# sales-page content rather than build work, so they're left off here.
SERVICES = [
    {
        "title": "AI Agents & Chatbots",
        "desc": "Conversational agents and\ncustom automation",
        "accent": GREEN,
        "art": bot_art,
    },
    {
        "title": "Web & App Development",
        "desc": "Corporate sites, web apps,\nand native applications",
        "accent": CYAN,
        "art": browser_art,
    },
    {
        "title": "Workflow Automation",
        "desc": "n8n pipelines and\nCRM automation",
        "accent": PINK,
        "art": chip_art,
    },
]

CARD_H = 150


def build():
    body = []

    # --- header
    name_y = 62
    body.append(f"""
  <g opacity="0">{fade_up(0.12)}
    <rect x="{PAD}" y="{name_y - 15}" width="3.5" height="20" rx="1.75" fill="{GREEN}" />
    <text x="{PAD + 14}" y="{name_y}" font-family="{MONO}" font-size="16"
          font-weight="bold" fill="{TEXT}">{esc(AGENCY_NAME)}</text>
    <text x="{PAD + 14}" y="{name_y + 20}" font-family="{MONO}" font-size="11.5"
          fill="{TEXT_FAINT}">{esc(AGENCY_ROLE)}</text>
  </g>""")

    # --- service cards
    usable = CANVAS_W - PAD * 2
    gap = 16
    card_w = (usable - gap * (len(SERVICES) - 1)) / len(SERVICES)
    top = name_y + 42

    for i, s in enumerate(SERVICES):
        x = PAD + i * (card_w + gap)
        begin = round(0.3 + i * 0.12, 3)

        icon_w = sprite_w(BOT_OPEN, PX)
        ix = x + 18
        iy = top + 20

        title_y = top + 96
        desc_lines = s["desc"].split("\n")
        desc_svg = "".join(
            f'<text x="{x + 18}" y="{title_y + 20 + j * 15}" font-family="{MONO}" '
            f'font-size="11" fill="{TEXT_DIM}">{esc(line)}</text>'
            for j, line in enumerate(desc_lines)
        )

        body.append(f"""
  <g opacity="0">{fade_up(begin)}
    <rect x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="{CARD_H}" rx="10"
          fill="{BG_INSET}" stroke="{BORDER_SOFT}" stroke-width="1" />
    <rect x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="2.5" rx="1.25"
          fill="{s['accent']}" />
    {s['art'](ix, iy, s['accent'])}
    <text x="{x + 18}" y="{title_y}" font-family="{MONO}" font-size="13"
          font-weight="bold" fill="{TEXT}">{esc(s['title'])}</text>
    {desc_svg}
  </g>""")

    height = int(top + CARD_H + PAD)
    return panel(CANVAS_W, height, "oniqutes --services", "".join(body))


def main():
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Saved agency panel -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
