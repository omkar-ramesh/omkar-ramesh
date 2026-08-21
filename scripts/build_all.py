"""
build_all.py
------------
Regenerates every panel in one go.

    python scripts/build_all.py            # everything
    python scripts/build_all.py --static   # skip the network fetch

--static rebuilds only the panels whose content lives in the scripts
(hero, neofetch card, stack) and leaves the heatmap alone -- handy while
iterating on design without re-scraping contribution data each time.
"""

import argparse
import sys

import make_hero_banner
import make_neofetch_card
import make_agency_panel
import make_knowledge_panel
import make_hardware_panel
import fetch_contributions
import render_heatmap_svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true",
                        help="skip fetching contributions / rendering heatmap")
    parser.add_argument("--username", default=fetch_contributions.DEFAULT_USERNAME)
    args = parser.parse_args()

    make_hero_banner.main()
    make_neofetch_card.main()
    make_agency_panel.main()
    make_knowledge_panel.main()
    make_hardware_panel.main()

    if args.static:
        print("(skipped heatmap -- --static)")
        return

    sys.argv = ["fetch_contributions.py", "--username", args.username]
    fetch_contributions.main()
    render_heatmap_svg.main()


if __name__ == "__main__":
    main()
