#!/usr/bin/env python3
"""
AI Lead Generation Agent — CLI entry point.

Usage examples:
  python main.py --region US --niche "restaurants" --output csv
  python main.py --region UK --niche "law firms" --output json
  python main.py --region ALL --niche ALL --output both
  python main.py --region US,AU --niche "e-commerce stores,dental clinics" --output csv
  python main.py --region IN --niche "SaaS startups" --skip-enrichment --skip-outreach
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Allow imports from repo root
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import print as rprint

from config.targets import REGIONS, NICHES
from agents.crew import LeadGenCrew
from utils.export import ExportManager

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Lead Generation Agent for Digital Marketing & Web Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--region",
        default="US",
        help="Region(s) to target. Options: US, UK, AU, IN, ALL. Comma-separated for multiple.",
    )
    parser.add_argument(
        "--niche",
        default="restaurants",
        help="Business niche(s) to target. Use 'ALL' for all niches. Comma-separated.",
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
        help="Skip website visit / enrichment step (faster, less data).",
    )
    parser.add_argument(
        "--skip-outreach",
        action="store_true",
        help="Skip outreach email generation step (saves API quota).",
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


def resolve_regions(region_arg: str) -> list[str]:
    if region_arg.upper() == "ALL":
        return list(REGIONS.keys())
    return [r.strip().upper() for r in region_arg.split(",")]


def resolve_niches(niche_arg: str) -> list[str]:
    if niche_arg.upper() == "ALL":
        return NICHES
    return [n.strip() for n in niche_arg.split(",")]


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

    regions = resolve_regions(args.region)
    niches = resolve_niches(args.niche)

    # Header
    console.print(
        Panel.fit(
            "[bold cyan]AI Lead Generation Agent[/bold cyan]\n"
            f"[white]Regions:[/white] [green]{', '.join(regions)}[/green]  "
            f"[white]Niches:[/white] [yellow]{', '.join(niches)}[/yellow]\n"
            f"[white]Enrichment:[/white] {'[red]OFF[/red]' if args.skip_enrichment else '[green]ON[/green]'}  "
            f"[white]Outreach:[/white] {'[red]OFF[/red]' if args.skip_outreach else '[green]ON[/green]'}",
            title="[bold]Starting Pipeline[/bold]",
            border_style="cyan",
        )
    )

    # Run pipeline
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Running lead generation pipeline...", total=None)
        crew = LeadGenCrew(
            regions=regions,
            niches=niches,
            skip_enrichment=args.skip_enrichment,
            skip_outreach=args.skip_outreach,
        )
        leads = crew.run()
        progress.update(task, description=f"[green]Done! Found {len(leads)} leads.")

    # Truncate if requested
    if args.max_leads and len(leads) > args.max_leads:
        leads = leads[: args.max_leads]
        console.print(f"[dim]Truncated to top {args.max_leads} leads.[/dim]")

    if not leads:
        console.print("[red]No leads found. Try different region/niche or check your connection.[/red]")
        sys.exit(1)

    # Export
    exporter = ExportManager()

    if args.output in ("csv", "both"):
        filename = f"leads_{'_'.join(regions)}_{'_'.join(n.replace(' ', '_') for n in niches[:2])}"
        exporter.to_csv(leads, filename=filename)

    if args.output in ("json", "both"):
        filename = f"leads_{'_'.join(regions)}_{'_'.join(n.replace(' ', '_') for n in niches[:2])}"
        exporter.to_json(leads, filename=filename)

    if args.output == "table":
        exporter.print_summary_table(leads)
    else:
        exporter.print_summary_table(leads)

    console.print(
        f"\n[bold green]Pipeline complete![/bold green] "
        f"[white]{len(leads)} leads processed. Check the [cyan]outputs/[/cyan] directory.[/white]"
    )


if __name__ == "__main__":
    main()
