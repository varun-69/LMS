"""
Scout Agent — orchestrates all scrapers for a given region and niche,
deduplicates results, and returns a clean list of raw leads.
"""

import logging
from typing import Any

from scrapers.google_maps import GoogleMapsScraper
from scrapers.clutch import ClutchScraper
from scrapers.yellow_pages import YellowPagesScraper
from scrapers.yelp import YelpScraper
from config.settings import settings

logger = logging.getLogger(__name__)


class ScoutAgent:
    """
    Runs multiple scrapers in sequence and deduplicates results by website + name.
    """

    def __init__(self, region: str, niche: str) -> None:
        self.region = region
        self.niche = niche
        self._scrapers = [
            GoogleMapsScraper(region, niche),
            ClutchScraper(region, niche),
            YellowPagesScraper(region, niche),
            YelpScraper(region, niche),
        ]

    def run(self) -> list[dict[str, Any]]:
        """
        Run all scrapers and return deduplicated leads.
        Returns at most MAX_LEADS_PER_SOURCE × number_of_scrapers leads.
        """
        all_leads: list[dict[str, Any]] = []

        for scraper in self._scrapers:
            logger.info(
                "[scout] Running %s scraper for '%s' in %s",
                scraper.source_name, self.niche, self.region,
            )
            try:
                leads = scraper.scrape()
                logger.info(
                    "[scout] %s returned %d leads", scraper.source_name, len(leads)
                )
                all_leads.extend(leads)
            except Exception as exc:
                logger.error(
                    "[scout] Scraper %s failed: %s", scraper.source_name, exc
                )

        deduped = self._deduplicate(all_leads)
        logger.info(
            "[scout] Total after dedup: %d (from %d raw)", len(deduped), len(all_leads)
        )
        return deduped

    # ── Private ───────────────────────────────────────────────────────────────

    def _deduplicate(self, leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []

        for lead in leads:
            key = self._dedup_key(lead)
            if key not in seen:
                seen.add(key)
                unique.append(lead)

        return unique

    def _dedup_key(self, lead: dict[str, Any]) -> str:
        website = (lead.get("website") or "").lower().rstrip("/")
        name = (lead.get("name") or "").lower().strip()
        # Prefer website as the dedup key; fall back to name + city
        if website:
            return website
        city = (lead.get("city") or "").lower()
        return f"{name}|{city}"
