"""
Export manager — saves lead lists to CSV / JSON and prints rich summary tables.
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich import box

from config.settings import settings

logger = logging.getLogger(__name__)
console = Console()


class ExportManager:
    """Handles all output serialisation for the lead generation pipeline."""

    def __init__(self, output_dir: str | None = None) -> None:
        self.output_dir = Path(output_dir or settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Private ───────────────────────────────────────────────────────────────

    def _timestamped(self, base: str, ext: str) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{base}_{ts}.{ext}"

    # ── Public ────────────────────────────────────────────────────────────────

    def to_csv(self, leads: list[dict[str, Any]], filename: str = "leads") -> Path:
        """Write leads to a CSV file. Returns the path to the created file."""
        if not leads:
            logger.warning("No leads to export to CSV.")
            return self.output_dir / f"{filename}_empty.csv"

        path = self._timestamped(filename, "csv")
        fieldnames = list(leads[0].keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lead in leads:
                # Flatten lists/dicts so CSV stays clean
                flat = {}
                for k, v in lead.items():
                    if isinstance(v, (list, dict)):
                        flat[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        flat[k] = v
                writer.writerow(flat)

        logger.info("Exported %d leads to %s", len(leads), path)
        console.print(f"[green]CSV saved:[/green] {path}")
        return path

    def to_json(self, leads: list[dict[str, Any]], filename: str = "leads") -> Path:
        """Write leads to a pretty-printed JSON file. Returns the path."""
        if not leads:
            logger.warning("No leads to export to JSON.")
            return self.output_dir / f"{filename}_empty.json"

        path = self._timestamped(filename, "json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False, default=str)

        logger.info("Exported %d leads to %s", len(leads), path)
        console.print(f"[green]JSON saved:[/green] {path}")
        return path

    def print_summary_table(self, leads: list[dict[str, Any]]) -> None:
        """Print a rich summary table to stdout."""
        if not leads:
            console.print("[yellow]No leads to display.[/yellow]")
            return

        table = Table(
            title=f"Lead Generation Results — {len(leads)} leads",
            box=box.ROUNDED,
            show_lines=True,
        )

        cols = [
            ("Tier", "cyan", 5),
            ("Score", "magenta", 6),
            ("Name", "white", 30),
            ("City", "green", 16),
            ("Country", "green", 12),
            ("Industry", "yellow", 20),
            ("Service", "blue", 22),
            ("Budget/mo (USD)", "red", 16),
            ("Source", "dim", 12),
            ("Website", "dim", 30),
        ]

        for name, style, width in cols:
            table.add_column(name, style=style, max_width=width, no_wrap=False)

        for lead in leads:
            table.add_row(
                str(lead.get("tier", "-")),
                str(lead.get("score", "-")),
                str(lead.get("name", "-"))[:30],
                str(lead.get("city", "-"))[:16],
                str(lead.get("country", "-"))[:12],
                str(lead.get("industry", "-"))[:20],
                str(lead.get("recommended_service", "-"))[:22],
                str(lead.get("estimated_budget_usd_monthly") or "-"),
                str(lead.get("source", "-"))[:12],
                str(lead.get("website", "-"))[:30],
            )

        console.print(table)

        # Tier breakdown
        tier_a = sum(1 for l in leads if l.get("tier") == "A")
        tier_b = sum(1 for l in leads if l.get("tier") == "B")
        tier_c = sum(1 for l in leads if l.get("tier") == "C")
        console.print(
            f"\n[bold]Tier breakdown:[/bold] "
            f"[cyan]A: {tier_a}[/cyan] | "
            f"[yellow]B: {tier_b}[/yellow] | "
            f"[dim]C: {tier_c}[/dim]"
        )
