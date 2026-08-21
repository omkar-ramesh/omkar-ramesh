"""
make_hero_banner.py
-------------------
Renders hero-banner.svg -- the masthead of the profile.

A block-capital ASCII wordmark ("THUNDERX10") drawn in an ANSI-shadow
style font, revealed row by row with a left-to-right wipe, filled with a
single user-space gradient so the color sweeps across the whole wordmark
rather than repeating per glyph. Underneath, a prompt line types itself
out and leaves a blinking cursor.

The letterforms are defined per-character and joined column-wise at
render time -- far easier to keep aligned than hand-writing six 80-char
strings, and it means the wordmark can be changed by editing WORDMARK.

Usage:
    python scripts/make_hero_banner.py
"""

import os

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_DIM, GREEN, CYAN, PURPLE,
    esc, panel, linear_gradient, wipe_reveal, blink, text_w,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "hero-banner.svg")

WORDMARK = "THUNDERX10"
TAGLINE = "AI Engineer & Founder  ::  Oniqutes Digital Solutions"

FONT_SIZE = 15
LINE_H = 15

# Solid block font -- built from U+2588 FULL BLOCK and spaces only.
#
# An ANSI-shadow style font (with ╗ ╔ ╝ ║ ═ outlines) looks sharper in a
# terminal but falls apart here: those box-drawing glyphs aren't
# guaranteed the same advance width as █ in whatever font the viewer's
# browser substitutes, so the letterforms shear apart. █ and space are
# full-width in every monospace font, so the wordmark always lines up.
#
# Each glyph is 5 rows x 6 columns, joined with a one-column gap.
GLYPH_ROWS = 5
GLYPHS = {
    "T": ["██████", "  ██  ", "  ██  ", "  ██  ", "  ██  "],
    "H": ["██  ██", "██  ██", "██████", "██  ██", "██  ██"],
    "U": ["██  ██", "██  ██", "██  ██", "██  ██", "██████"],
    "N": ["██  ██", "███ ██", "██████", "██ ███", "██  ██"],
    "D": ["█████ ", "██  ██", "██  ██", "██  ██", "█████ "],
    "E": ["██████", "██    ", "█████ ", "██    ", "██████"],
    "R": ["█████ ", "██  ██", "█████ ", "██  ██", "██  ██"],
    "X": ["██  ██", " ████ ", "  ██  ", " ████ ", "██  ██"],
    "1": ["  ██  ", " ███  ", "  ██  ", "  ██  ", "██████"],
    "0": ["██████", "██  ██", "██  ██", "██  ██", "██████"],
}

ROW_STAGGER = 0.09
ROW_DUR = 0.75


def build_wordmark_rows(word: str):
    """Join per-glyph rows into full-width text rows, one blank column
    between letters."""
    rows = []
    for r in range(GLYPH_ROWS):
        rows.append(" ".join(GLYPHS[ch][r] for ch in word))
    return rows


def build():
    rows = build_wordmark_rows(WORDMARK)
    mark_w = text_w(rows[0], FONT_SIZE)
    mark_x = (CANVAS_W - mark_w) / 2
    mark_top = 72

    grad_id = "wordmark-grad"
    gradients = linear_gradient(
        grad_id,
        [(0, GREEN), (0.5, CYAN), (1, PURPLE)],
        x1=mark_x, x2=mark_x + mark_w,
    )
    # Soft band used for the repeating shine sweep. Left in
    # objectBoundingBox units (the default) so the gradient travels with
    # the rect instead of staying pinned to the canvas.
    gradients += (
        '<linearGradient id="shine-grad" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0" />'
        '<stop offset="0.5" stop-color="#ffffff" stop-opacity="0.7" />'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0" />'
        '</linearGradient>'
    )

    parts = []
    for i, row_text in enumerate(rows):
        y = mark_top + i * LINE_H
        begin = round(0.15 + i * ROW_STAGGER, 3)
        clip_id = f"hero-row-{i}"
        parts.append(wipe_reveal(clip_id, mark_x, y - FONT_SIZE,
                                 mark_w, LINE_H, begin, ROW_DUR))
        parts.append(f"""
  <g clip-path="url(#{clip_id})">
    <text x="{mark_x}" y="{y}" font-family="{MONO}" font-size="{FONT_SIZE}"
          fill="url(#{grad_id})" xml:space="preserve">{esc(row_text)}</text>
  </g>""")

    # Repeating shine: a bright band swept across a clip cut from the
    # wordmark's own letterforms, so the highlight only ever touches the
    # glyphs and never the panel background. Sweeps in the first third of
    # the cycle then waits, so it reads as an occasional glint rather than
    # a constantly moving distraction.
    shine_rows = "".join(
        f'<text x="{mark_x}" y="{mark_top + i * LINE_H}" font-family="{MONO}" '
        f'font-size="{FONT_SIZE}" xml:space="preserve">{esc(t)}</text>'
        for i, t in enumerate(rows)
    )
    band_w = 110
    shine_begin = round(0.15 + GLYPH_ROWS * ROW_STAGGER + ROW_DUR, 3)
    parts.append(f"""
  <clipPath id="wordmark-clip">{shine_rows}</clipPath>
  <g clip-path="url(#wordmark-clip)">
    <rect x="{mark_x - band_w}" y="{mark_top - FONT_SIZE - 4}"
          width="{band_w}" height="{GLYPH_ROWS * LINE_H + 10}"
          fill="url(#shine-grad)">
      <animate attributeName="x" values="{mark_x - band_w};{mark_x + mark_w};{mark_x + mark_w}"
               keyTimes="0;0.32;1" dur="4.2s" begin="{shine_begin}s"
               repeatCount="indefinite" />
    </rect>
  </g>""")

    # Prompt line under the wordmark
    tag_begin = round(0.15 + GLYPH_ROWS * ROW_STAGGER + 0.35, 3)
    tag_y = mark_top + GLYPH_ROWS * LINE_H + 34
    tag_font = 13
    prompt = "$"
    prompt_x = mark_x
    tag_x = prompt_x + text_w(prompt + " ", tag_font)
    tag_w = text_w(prompt + " " + TAGLINE, tag_font)
    clip_id = "hero-tagline"

    parts.append(wipe_reveal(clip_id, prompt_x, tag_y - tag_font,
                             tag_w + 4, tag_font + 8, tag_begin, 0.9))
    parts.append(f"""
  <g clip-path="url(#{clip_id})">
    <text x="{prompt_x}" y="{tag_y}" font-family="{MONO}" font-size="{tag_font}"
          fill="{GREEN}" font-weight="bold">{esc(prompt)}</text>
    <text x="{tag_x}" y="{tag_y}" font-family="{MONO}" font-size="{tag_font}"
          fill="{TEXT_DIM}" xml:space="preserve">{esc(TAGLINE)}</text>
  </g>""")

    parts.append(blink(prompt_x + tag_w + 8, tag_y - tag_font + 1,
                       7.5, tag_font + 3, CYAN, round(tag_begin + 0.95, 3)))

    height = int(tag_y + 34)
    return panel(CANVAS_W, height, "thunderx10 — ~/profile",
                 "".join(parts), gradients)


def main():
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Saved hero banner -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
