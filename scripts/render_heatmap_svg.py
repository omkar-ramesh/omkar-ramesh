"""
render_heatmap_svg.py
---------------------
Reads data/contributions.json (from fetch_contributions.py) and renders
contrib-heatmap.svg -- the only panel the daily GitHub Action rebuilds.

Layout: a row of stat cards across the top, then the 53x7 contribution
grid with month labels, then the Less->More legend. Everything shares
theme.py's palette so it stacks cleanly under the other panels.

Animation: stat cards fade-and-rise first, then the grid reveals as a
diagonal wave (cells are staggered by column+row, so the sweep runs
top-left to bottom-right). Plays once and freezes.

Usage:
    python scripts/render_heatmap_svg.py
"""

import json
import os
from datetime import datetime, timedelta

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_DIM, TEXT_FAINT, BG_INSET, BORDER_SOFT,
    HEAT, GREEN, CYAN, PURPLE, ORANGE,
    esc, panel, fade_up,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(REPO_ROOT, "data", "contributions.json")
OUTPUT_PATH = os.path.join(REPO_ROOT, "contrib-heatmap.svg")

WEEKS = 53
DAYS = 7

CELL = 11
GAP = 3
STEP = CELL + GAP

STAT_H = 58
GRID_LEFT = PAD + 26          # room for the Mon/Wed/Fri day labels


def level_for_count(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    if count <= 15:
        return 4
    return 5


def build_grid(days_data):
    """Arrange the trailing 53 weeks into [week][weekday], GitHub-style
    (columns = weeks, rows = Sun..Sat)."""
    by_date = {d["date"]: d for d in days_data}

    if days_data:
        last_date = datetime.strptime(days_data[-1]["date"], "%Y-%m-%d").date()
    else:
        last_date = datetime.utcnow().date()

    end = last_date
    while end.weekday() != 5:      # advance to Saturday
        end += timedelta(days=1)

    start = end - timedelta(weeks=WEEKS - 1, days=6)
    while start.weekday() != 6:    # back up to Sunday
        start -= timedelta(days=1)

    grid = []
    cursor = start
    for _ in range(WEEKS):
        col = []
        for _ in range(DAYS):
            key = cursor.strftime("%Y-%m-%d")
            entry = by_date.get(key)
            col.append({"date": key, "count": entry["count"] if entry else 0})
            cursor += timedelta(days=1)
        grid.append(col)
    return grid


def month_labels(grid):
    labels = []
    last_month = None
    for i, week in enumerate(grid):
        first = week[0]["date"]
        month = first[:7]
        if month != last_month:
            labels.append((i, datetime.strptime(first, "%Y-%m-%d").strftime("%b")))
            last_month = month
    return labels


def stat_cards(payload, y):
    best = payload.get("best_day") or {}
    cards = [
        ("total", f"{payload.get('total_contributions', 0)}", "past year", GREEN),
        ("current streak", f"{payload.get('current_streak', 0)}", "days", CYAN),
        ("longest streak", f"{payload.get('longest_streak', 0)}", "days", PURPLE),
        ("best day", f"{best.get('count', 0)}", best.get("date", "—"), ORANGE),
    ]

    usable = CANVAS_W - PAD * 2
    gap = 12
    w = (usable - gap * (len(cards) - 1)) / len(cards)

    out = []
    for i, (label, value, sub, accent) in enumerate(cards):
        x = PAD + i * (w + gap)
        begin = round(0.15 + i * 0.09, 3)
        out.append(f"""
  <g opacity="0">{fade_up(begin)}
    <rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{STAT_H}" rx="8"
          fill="{BG_INSET}" stroke="{BORDER_SOFT}" stroke-width="1" />
    <rect x="{x:.1f}" y="{y + 10}" width="2.5" height="{STAT_H - 20}" rx="1.25" fill="{accent}" />
    <text x="{x + 16:.1f}" y="{y + 21}" font-family="{MONO}" font-size="10.5"
          fill="{TEXT_FAINT}">{esc(label)}</text>
    <text x="{x + 16:.1f}" y="{y + 42}" font-family="{MONO}" font-size="19"
          font-weight="bold" fill="{TEXT}">{esc(value)}</text>
    <text x="{x + w - 14:.1f}" y="{y + 42}" font-family="{MONO}" font-size="10"
          fill="{TEXT_FAINT}" text-anchor="end">{esc(str(sub))}</text>
  </g>""")
    return "".join(out), y + STAT_H


def build(payload):
    grid = build_grid(payload.get("days", []))
    body = []

    cards_svg, after_cards = stat_cards(payload, 56)
    body.append(cards_svg)

    months_y = after_cards + 32
    grid_top = months_y + 12

    # month labels
    for week_idx, name in month_labels(grid):
        x = GRID_LEFT + week_idx * STEP
        body.append(f"""
  <text x="{x}" y="{months_y}" font-family="{MONO}" font-size="10"
        fill="{TEXT_FAINT}">{esc(name)}</text>""")

    # weekday labels (GitHub shows only Mon/Wed/Fri)
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = grid_top + row * STEP + CELL - 1.5
        body.append(f"""
  <text x="{PAD}" y="{y}" font-family="{MONO}" font-size="9.5"
        fill="{TEXT_FAINT}">{esc(name)}</text>""")

    # cells -- diagonal reveal wave
    base = 0.5
    for w_i, week in enumerate(grid):
        for d_i, day in enumerate(week):
            level = level_for_count(day["count"])
            x = GRID_LEFT + w_i * STEP
            y = grid_top + d_i * STEP
            begin = round(base + (w_i + d_i) * 0.011, 3)
            title = esc(f"{day['count']} contributions on {day['date']}")
            body.append(f"""
  <rect x="{x}" y="{y - 3}" width="{CELL}" height="{CELL}" rx="2.5"
        fill="{HEAT[level]}" opacity="0">
    <title>{title}</title>
    <animate attributeName="opacity" from="0" to="1" begin="{begin}s"
             dur="0.3s" fill="freeze" />
    <animate attributeName="y" from="{y - 3}" to="{y}" begin="{begin}s"
             dur="0.3s" fill="freeze" calcMode="spline"
             keySplines="0.22 0.61 0.36 1" />
  </rect>""")

    grid_bottom = grid_top + DAYS * STEP
    legend_y = grid_bottom + 26

    # footer: generated stamp (left) + Less..More legend (right)
    stamp = payload.get("generated_at", "")[:10]
    body.append(f"""
  <text x="{PAD}" y="{legend_y}" font-family="{MONO}" font-size="10"
        fill="{TEXT_FAINT}">updated {esc(stamp)} · auto-refreshed daily</text>""")

    lw, lgap = 11, 4
    legend_total = len(HEAT) * (lw + lgap)
    lx = CANVAS_W - PAD - legend_total - 74
    body.append(f"""
  <text x="{lx}" y="{legend_y}" font-family="{MONO}" font-size="10"
        fill="{TEXT_FAINT}">Less</text>""")
    for i, color in enumerate(HEAT):
        bx = lx + 32 + i * (lw + lgap)
        body.append(f"""
  <rect x="{bx}" y="{legend_y - 9}" width="{lw}" height="{lw}" rx="2.5" fill="{color}" />""")
    body.append(f"""
  <text x="{lx + 32 + legend_total + 2}" y="{legend_y}" font-family="{MONO}"
        font-size="10" fill="{TEXT_FAINT}">More</text>""")

    height = int(legend_y + 24)
    username = payload.get("username", "")
    return panel(CANVAS_W, height, f"git log --author={username}", "".join(body))


def main():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Could not find '{INPUT_PATH}'.\n"
            "Run scripts/fetch_contributions.py first."
        )

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build(payload))

    print(f"Saved contribution heatmap -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
