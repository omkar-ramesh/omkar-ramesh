"""
fetch_contributions.py
-----------------------
Fetches YOUR OWN public GitHub contribution calendar (no auth/token needed
-- this is the same data anyone sees on your public profile page) and
saves it as structured JSON for the heatmap renderer.

Data source: https://github.com/users/<username>/contributions
This is the public HTML fragment GitHub itself uses to render the
contribution graph on your profile page. We parse the `<td>` day cells
with BeautifulSoup rather than calling any private/authenticated API.

Output: data/contributions.json
  {
    "username": "Thunderx10",
    "generated_at": "...",
    "days": [{"date": "2025-01-01", "count": 3, "level": 1}, ...],
    "total_contributions": 1234,
    "current_streak": 5,
    "longest_streak": 42,
    "best_day": {"date": "...", "count": 17}
  }

Usage:
    python scripts/fetch_contributions.py
    python scripts/fetch_contributions.py --username someoneelse
"""

import argparse
import json
import os
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(REPO_ROOT, "data", "contributions.json")

DEFAULT_USERNAME = "Thunderx10"
USER_AGENT = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"


def fetch_contribution_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_contributions(html: str):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as either:
    #   <td class="ContributionCalendar-day" data-date="YYYY-MM-DD" data-level="0-4">
    # or (older markup) <rect class="ContributionCalendar-day" data-date=... data-level=...>
    cells = soup.select("[data-date][data-level]")

    for cell in cells:
        d = cell.get("data-date")
        level = cell.get("data-level")
        if not d:
            continue

        # Try to recover the exact count from the tooltip text if present,
        # otherwise fall back to estimating from level (0-4 buckets).
        count = None
        tooltip_id = cell.get("id")
        if tooltip_id:
            tooltip = soup.find(attrs={"for": tooltip_id})
            if tooltip and tooltip.text:
                text = tooltip.text.strip()
                first_word = text.split(" ")[0].replace(",", "")
                if first_word.isdigit():
                    count = int(first_word)
                elif text.lower().startswith("no contributions"):
                    count = 0

        if count is None:
            # Fallback: approximate count from the level bucket
            level_int = int(level) if level and level.isdigit() else 0
            count = level_int

        days.append({
            "date": d,
            "count": count,
            "level": int(level) if level and level.isdigit() else 0,
        })

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    best_day = max(days, key=lambda d: d["count"], default=None)

    # Longest streak (consecutive days with count > 0)
    longest_streak = 0
    current_run = 0
    for d in days:
        if d["count"] > 0:
            current_run += 1
            longest_streak = max(longest_streak, current_run)
        else:
            current_run = 0

    # Current streak: walk backwards from the most recent day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    return {
        "total_contributions": total,
        "longest_streak": longest_streak,
        "current_streak": current_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]} if best_day else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    args = parser.parse_args()

    html = fetch_contribution_html(args.username)
    days = parse_contributions(html)

    if not days:
        raise RuntimeError(
            "No contribution cells found -- GitHub may have changed its "
            "public HTML markup, or the username has no public activity."
        )

    stats = compute_stats(days)

    payload = {
        "username": args.username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        **stats,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved {len(days)} days of contribution data -> {OUTPUT_PATH}")
    print(f"Total: {stats['total_contributions']} | "
          f"Current streak: {stats['current_streak']} | "
          f"Longest streak: {stats['longest_streak']}")


if __name__ == "__main__":
    main()
