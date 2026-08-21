"""
sprites.py
----------
Tiny pixel-art engine: character-grid sprites -> SVG rects.

Sprites are authored as lists of equal-length strings, one character per
pixel, plus a palette mapping characters to colors. A character missing
from the palette (or mapped to None) is transparent.

Horizontal runs of the same color collapse into a single <rect>, which
matters here: a 32x14 sprite is 448 pixels but usually emits well under
80 rects, keeping the committed SVGs small.

Frame animation is done the authentic 8-bit way -- draw every frame
stacked in place, then flip their opacity on a loop so exactly one is
visible at a time. No transforms, no interpolation, just cels swapping.
"""


def sprite_rects(grid, palette, ox, oy, px, opacity=None, extra=""):
    """Render one sprite. `grid` is a list of strings, `palette` maps
    characters to colors, `px` is the size of one pixel in SVG units."""
    out = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            ch = row[c]
            color = palette.get(ch)
            if color is None:
                c += 1
                continue
            run = 1
            while c + run < len(row) and row[c + run] == ch:
                run += 1
            x = ox + c * px
            y = oy + r * px
            out.append(
                f'<rect x="{x:g}" y="{y:g}" width="{run * px:g}" height="{px:g}" '
                f'fill="{color}"{extra} />'
            )
            c += run
    body = "".join(out)
    if opacity is not None:
        return f'<g opacity="{opacity}">{body}</g>'
    return body


def sprite_w(grid, px):
    return len(grid[0]) * px


def sprite_h(grid, px):
    return len(grid) * px


def flipbook(frames, palette, ox, oy, px, frame_dur=0.12, begin=0.0):
    """Stack N frames at the same spot and cycle their visibility.

    Each frame is visible for exactly 1/N of the loop. Built with
    discrete keyTimes so frames snap rather than cross-fade -- cross-fading
    would read as motion blur and lose the pixel-art crispness.
    """
    n = len(frames)
    total = round(frame_dur * n, 4)
    out = []
    for i, grid in enumerate(frames):
        # visible only during slice i
        start = i / n
        end = (i + 1) / n
        if i == 0:
            values = "1;1;0;0"
            key_times = f"0;{end:.4f};{end:.4f};1"
        elif i == n - 1:
            values = "0;0;1;1"
            key_times = f"0;{start:.4f};{start:.4f};1"
        else:
            values = "0;0;1;1;0;0"
            key_times = f"0;{start:.4f};{start:.4f};{end:.4f};{end:.4f};1"

        rects = sprite_rects(grid, palette, ox, oy, px)
        out.append(f"""
    <g opacity="{1 if i == 0 else 0}">
      <animate attributeName="opacity" values="{values}" keyTimes="{key_times}"
               dur="{total}s" begin="{begin}s" repeatCount="indefinite"
               calcMode="discrete" />
      {rects}
    </g>""")
    return "".join(out)


def pulse(grid, palette, ox, oy, px, dur=2.0, begin=0.0,
          lo=0.2, hi=1.0):
    """A sprite layer that breathes between two opacities -- used for
    power LEDs so the machines read as switched on."""
    rects = sprite_rects(grid, palette, ox, oy, px)
    return f"""
    <g>
      <animate attributeName="opacity" values="{hi};{lo};{hi}" dur="{dur}s"
               begin="{begin}s" repeatCount="indefinite" />
      {rects}
    </g>"""
