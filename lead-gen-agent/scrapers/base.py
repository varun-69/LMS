"""
Abstract base class for all lead scrapers.
Defines the standard lead schema and shared helpers.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import requests
from fake_useragent import UserAgent

from config.settings import settings

logger = logging.getLogger(__name__)

# Canonical lead schema — every scraper must return dicts conforming to this.
LEAD_SCHEMA_KEYS = [
    # ── Identity ──────────────────────────────────────────────────────────
    "name",
    "niche",
    "city",
    "country",
    # ── Contact ───────────────────────────────────────────────────────────
    "phone",
    "email",
    "website",
    "address",
    # ── Web presence status ───────────────────────────────────────────────
    "has_website",       # bool — False = primary target
    "lead_type",         # "no_website" | "intent_post" | "directory"
    # ── Intent signals ────────────────────────────────────────────────────
    "intent_signal",     # "osm_no_website" | "reddit_post" | "yelp_no_website"
    "intent_text",       # Evidence: post body, listing description, etc.
    "intent_url",        # URL to the evidence source
    # ── Metadata ──────────────────────────────────────────────────────────
    "source",
    "scraped_at",
    "rating",
    "review_count",
    "industry",
    "description",
    "social_links",
    # ── AI scored (added by ScorerAgent) ─────────────────────────────────
    "score",
    "tier",
    "reasoning",
    "estimated_budget_usd_monthly",
    "recommended_service",
    "pain_points_identified",
    "outreach_hook",
    # ── Outreach (added by OutreachAgent) ─────────────────────────────────
    "outreach_email",
]

_ua = UserAgent()


def empty_lead() -> dict[str, Any]:
    """Return an empty lead dict with all schema keys set to None / []."""
    lead: dict[str, Any] = {k: None for k in LEAD_SCHEMA_KEYS}
    lead["social_links"] = []
    lead["pain_points_identified"] = []
    lead["scraped_at"] = datetime.now(timezone.utc).isoformat()
    return lead


class BaseScraper(ABC):
    """Abstract scraper. Subclasses implement `scrape()` and `_parse_lead()`."""

    source_name: str = "base"

    def __init__(self, location: str, niche: str) -> None:
        self.location = location
        self.niche = niche
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": _ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
        }

    def _refresh_headers(self) -> None:
        self.session.headers.update({"User-Agent": _ua.random})

    def _polite_get(
        self,
        url: str,
        params: dict | None = None,
        timeout: int = 15,
        retries: int = 3,
    ) -> requests.Response | None:
        """GET with random delay, rotating UA, and retry logic."""
        for attempt in range(1, retries + 1):
            self._refresh_headers()
            delay = random.uniform(settings.REQUEST_DELAY_MIN, settings.REQUEST_DELAY_MAX)
            time.sleep(delay)
            try:
                resp = self.session.get(url, params=params, timeout=timeout)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                logger.warning(
                    "[%s] attempt %d/%d failed for %s: %s",
                    self.source_name, attempt, retries, url, exc,
                )
                if attempt < retries:
                    time.sleep(2 ** attempt)
        return None

    # ── Interface ─────────────────────────────────────────────────────────────

    @abstractmethod
    def scrape(self) -> list[dict[str, Any]]:
        """Run the scraper and return a list of normalised lead dicts."""

    @abstractmethod
    def _parse_lead(self, raw: Any) -> dict[str, Any] | None:
        """Parse a single raw item into a lead dict (return None to skip)."""
