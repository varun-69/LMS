"""
Scout Agent — orchestrates intent-based lead scrapers for a given location and niche.

Two complementary strategies:
  1. OverpassNoWebScraper  — OpenStreetMap businesses without a website (works from cloud IPs)
  2. RedditIntentScraper   — Reddit posts where owners ask for websites / marketing help

Both return leads sorted with the most actionable signals first.
"""

import logging
from typing import Any

from scrapers.overpass_noweb import OverpassNoWebScraper
from scrapers.reddit_intent import RedditIntentScraper
from config.settings import settings

logger = logging.getLogger(__name__)


class ScoutAgent:
    """
    Runs all intent scrapers for a location + niche combination and
    returns a deduplicated, merged list of leads.
    """

    def __init__(self, location: str, niche: str) -> None:
        self.location = location
        self.niche = niche
        self._scrapers = [
            OverpassNoWebScraper(location, niche, max_results=settings.MAX_LEADS_PER_SOURCE),
            RedditIntentScraper(location, niche, max_results=settings.MAX_LEADS_PER_SOURCE),
        ]

    def run(self) -> list[dict[str, Any]]:
        """Run all scrapers and return deduplicated leads."""
        all_leads: list[dict[str, Any]] = []

        for scraper in self._scrapers:
            logger.info(
                "[scout] Running %s for '%s' in '%s'",
                scraper.source_name, self.niche, self.location,
            )
            try:
                leads = scraper.scrape()
                logger.info("[scout] %s → %d leads", scraper.source_name, len(leads))
                all_leads.extend(leads)
            except Exception as exc:
                logger.error("[scout] %s failed: %s", scraper.source_name, exc)

        deduped = self._deduplicate(all_leads)
        logger.info(
            "[scout] Total after dedup: %d (raw: %d)", len(deduped), len(all_leads)
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
        # For OSM leads: name + address is the canonical key
        # For Reddit leads: intent_url is unique per post
        intent_url = (lead.get("intent_url") or "").strip()
        if intent_url and lead.get("lead_type") == "intent_post":
            return intent_url
        name = (lead.get("name") or "").lower().strip()
        city = (lead.get("city") or "").lower().strip()
        addr = (lead.get("address") or "").lower().strip()
        return f"{name}|{city}|{addr}"
