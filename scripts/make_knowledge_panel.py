"""
make_knowledge_panel.py
-----------------------
Renders knowledge-panel.svg -- the "what I work in" map.

Presented as a masonry grid of labelled category cards rather than a flat
chip cloud: with ~40 topics, ungrouped chips turn into an unreadable
wall, while named categories let someone scan for the one area they
actually care about.

Deliberately NO proficiency bars, star ratings or percentages. Those
numbers would be invented -- there's no measurement behind them -- so the
panel names domains and lets the repos themselves be the evidence.

Layout is greedy-masonry: each card drops into whichever column is
currently shortest, so the three columns stay balanced no matter how
CATEGORIES is edited. Footer mimics tree(1)'s "N directories, M files"
summary and is computed from the data, never hardcoded.

Edit CATEGORIES to change content, then re-run.

Usage:
    python scripts/make_knowledge_panel.py
"""

import os

from theme import (
    CANVAS_W, PAD, MONO, TEXT, TEXT_DIM, TEXT_FAINT, BG_INSET, BORDER_SOFT,
    GREEN, CYAN, PURPLE, YELLOW, ORANGE, PINK,
    esc, panel, fade_up, text_w,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "knowledge-panel.svg")

# (category label, accent color, [topics])
#
# Order matters: masonry places cards in sequence into whichever column is
# shortest, so earlier entries land nearer the top. Sequenced by hiring
# signal -- the categories that most differentiate an AI engineer sit
# first, generic tooling last. Labels use the terms that actually appear
# in job postings ("model training & fine-tuning", not "models & stuff")
# since profiles get keyword-scanned before a human ever reads them.
#
# Hardware moved out to hardware-panel.svg.
CATEGORIES = [
    ("agent engineering", GREEN, [
        "agent orchestration",
        "sub-agents",
        "parallel agents",
        "background agents",
        "multi-repo orchestration",
        "headless runs",
    ]),
    ("agent tooling", CYAN, [
        "MCP servers",
        "skills",
        "hooks",
        "harness engineering",
        "model routing",
        "CLI design",
    ]),
    ("context engineering", PURPLE, [
        "context windows",
        "prompt engineering",
        "prompt caching",
        "token optimization",
        "progressive disclosure",
        "extended thinking",
    ]),
    ("model training & fine-tuning", PINK, [
        "LoRA training",
        "RLHF",
        "LLMs",
        "Flux",
        "ComfyUI",
        "Ollama / local inference",
    ]),
    ("evals & feedback loops", YELLOW, [
        "eval-driven loops",
        "self-improving loops",
        "memory consolidation",
    ]),
    ("reliability & security", ORANGE, [
        "self-healing tests",
        "agents in CI/CD",
        "tool-poisoning defense",
        "API key hygiene",
    ]),
    ("automation", GREEN, [
        "n8n",
        "workflow automation",
        "scheduled agents",
    ]),
    ("build stack", CYAN, [
        "Python",
        "Next.js",
        "React",
        "git worktrees",
        "markdown / docs",
    ]),
]

COLS = 3
COL_GAP = 16
CARD_GAP = 14
CARD_PAD = 13

LABEL_FONT = 11.5
ITEM_FONT = 11.5
ITEM_STEP = 19

HEADER_H = 30       # label baseline offset inside card
ITEMS_TOP = 46      # first item baseline offset inside card
GRID_TOP = 60


def card_height(n_items: int) -> int:
    return int(ITEMS_TOP + (n_items - 1) * ITEM_STEP + 18)


def build():
    usable = CANVAS_W - PAD * 2
    col_w = (usable - COL_GAP * (COLS - 1)) / COLS
    col_x = [PAD + i * (col_w + COL_GAP) for i in range(COLS)]
    col_h = [GRID_TOP] * COLS

    body = []
    delay = 0.15

    for label, accent, items in CATEGORIES:
        # greedy masonry: drop into the shortest column
        ci = col_h.index(min(col_h))
        x = col_x[ci]
        y = col_h[ci]
        h = card_height(len(items))

        rows = []
        for i, item in enumerate(items):
            iy = y + ITEMS_TOP + i * ITEM_STEP
            # tree-style connector: last item gets the corner glyph
            connector = "└─" if i == len(items) - 1 else "├─"
            rows.append(f"""
    <text x="{x + CARD_PAD}" y="{iy}" font-family="{MONO}" font-size="{ITEM_FONT}"
          fill="{TEXT_FAINT}">{esc(connector)}</text>
    <text x="{x + CARD_PAD + 20}" y="{iy}" font-family="{MONO}" font-size="{ITEM_FONT}"
          fill="{TEXT}">{esc(item)}</text>""")

        count = str(len(items))
        body.append(f"""
  <g opacity="0">{fade_up(round(delay, 3))}
    <rect x="{x:.1f}" y="{y}" width="{col_w:.1f}" height="{h}" rx="9"
          fill="{BG_INSET}" stroke="{BORDER_SOFT}" stroke-width="1" />
    <rect x="{x:.1f}" y="{y}" width="{col_w:.1f}" height="2.5" rx="1.25" fill="{accent}" />
    <text x="{x + CARD_PAD}" y="{y + HEADER_H}" font-family="{MONO}"
          font-size="{LABEL_FONT}" font-weight="bold" fill="{accent}">{esc(label)}</text>
    <text x="{x + col_w - CARD_PAD:.1f}" y="{y + HEADER_H}" font-family="{MONO}"
          font-size="10" fill="{TEXT_FAINT}" text-anchor="end">{esc(count)}</text>
    <line x1="{x + CARD_PAD}" y1="{y + HEADER_H + 9}" x2="{x + col_w - CARD_PAD:.1f}"
          y2="{y + HEADER_H + 9}" stroke="{BORDER_SOFT}" stroke-width="1" />{''.join(rows)}
  </g>""")

        col_h[ci] = y + h + CARD_GAP
        delay += 0.09

    grid_bottom = max(col_h) - CARD_GAP

    # tree(1)-style summary, computed from the data
    n_dirs = len(CATEGORIES)
    n_files = sum(len(items) for _, _, items in CATEGORIES)
    summary_y = grid_bottom + 26
    body.append(f"""
  <text x="{PAD}" y="{summary_y}" font-family="{MONO}" font-size="10.5"
        fill="{TEXT_FAINT}">{n_dirs} directories, {n_files} files</text>""")

    height = int(summary_y + 22)
    return panel(CANVAS_W, height, "tree ~/knowledge", "".join(body))


def main():
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Saved knowledge panel -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
