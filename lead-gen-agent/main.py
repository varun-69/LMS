#!/usr/bin/env python3
"""
AI Lead Generation Agent — finds high-intent leads for digital marketing & web development.

Two complementary signals:
  • Businesses WITHOUT a website (OpenStreetMap data, works from any IP)
  • Founders/owners who POSTED online asking for a website or marketing help (Reddit)

Usage examples:
  python main.py --location "New York" --niche "restaurants"
  python main.py --location "London" --niche "law firms" --output json
  python main.py --location "Mumbai,Delhi" --niche "restaurants,beauty salons" --output both
  python main.py --location "Sydney" --niche "dental clinics" --skip-scoring --output csv
  python main.py --location "Austin" --niche "gyms" --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from agents.crew import LeadGenCrew
from utils.export import ExportManager

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Lead Generation Agent — intent-based lead finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--location",
        default="New York",
        help=(
            "City or area to target. Free-form text, e.g. 'London', 'Mumbai', 'Sydney'. "
            "Comma-separate for multiple: 'New York,Los Angeles'."
        ),
    )
    parser.add_argument(
        "--niche",
        default="restaurants",
        help=(
            "Business niche to target, e.g. 'restaurants', 'law firms', 'dental clinics'. "
            "Comma-separate for multiple: 'restaurants,beauty salons'."
        ),
    )
    parser.add_argument(
        "--output",
        choices=["csv", "json", "both", "table"],
        default="csv",
        help="Output format (default: csv).",
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip website visit / enrichment step.",
    )
    parser.add_argument(
        "--skip-scoring",
        action="store_true",
        help="Skip Claude AI scoring step (no API key needed).",
    )
    parser.add_argument(
        "--skip-outreach",
        action="store_true",
        help="Skip cold email generation step (saves API quota).",
    )
    parser.add_argument(
        "--max-leads",
        type=int,
        default=None,
        help="Truncate final output to this many top leads.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    locations = [l.strip() for l in args.location.split(",") if l.strip()]
    niches = [n.strip() for n in args.niche.split(",") if n.strip()]

    console.print(
        Panel.fit(
            "[bold cyan]AI Lead Generation Agent[/bold cyan]\n"
            f"[white]Locations:[/white] [green]{', '.join(locations)}[/green]  "
            f"[white]Niches:[/white] [yellow]{', '.join(niches)}[/yellow]\n"
            "[white]Signals:[/white] [blue]No-website (OSM)[/blue] + [magenta]Reddit intent posts[/magenta]\n"
            f"[white]Scoring:[/white] {'[red]OFF[/red]' if args.skip_scoring else '[green]ON[/green]'}  "
            f"[white]Outreach:[/white] {'[red]OFF[/red]' if args.skip_outreach else '[green]ON[/green]'}",
            title="[bold]Starting Intent-Based Pipeline[/bold]",
            border_style="cyan",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Hunting high-intent leads...", total=None)
        crew = LeadGenCrew(
            locations=locations,
            niches=niches,
            skip_enrichment=args.skip_enrichment,
            skip_scoring=args.skip_scoring,
            skip_outreach=args.skip_outreach,
        )
        leads = crew.run()
        progress.update(task, description=f"[green]Done! Found {len(leads)} leads.")

    if args.max_leads and len(leads) > args.max_leads:
        leads = leads[: args.max_leads]
        console.print(f"[dim]Truncated to top {args.max_leads} leads.[/dim]")

    if not leads:
        console.print(
            "[red]No leads found. Try a different location or niche. "
            "For OSM data, make sure the city name matches OpenStreetMap "
            "(e.g. 'London' not 'Greater London').[/red]"
        )
        sys.exit(1)

    exporter = ExportManager()
    slug = "_".join(locations[:2]) + "_" + "_".join(n.replace(" ", "_") for n in niches[:2])

    if args.output in ("csv", "both"):
        exporter.to_csv(leads, filename=f"leads_{slug}")

    if args.output in ("json", "both"):
        exporter.to_json(leads, filename=f"leads_{slug}")

    exporter.print_summary_table(leads)

    console.print(
        f"\n[bold green]Done![/bold green] "
        f"[white]{len(leads)} leads. Check [cyan]outputs/[/cyan] for files.[/white]"
    )


if __name__ == "__main__":
    main()
