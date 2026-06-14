"""
Abstract base class for all lead scrapers.
Defines the standard lead schema and shared helpers.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any

import requests
from fake_useragent import UserAgent

from config.settings import settings

logger = logging.getLogger(__name__)

# Canonical lead schema — every scraper must return dicts conforming to this.
LEAD_SCHEMA_KEYS = [
    "name",
    "website",
    "email",
    "phone",
    "address",
    "city",
    "country",
    "industry",
    "source",
    "employees_estimate",
    "description",
    "social_links",
    "rating",
    "review_count",
]

_ua = UserAgent()


def empty_lead() -> dict[str, Any]:
    """Return an empty lead dict with all schema keys set to None / []."""
    lead: dict[str, Any] = {k: None for k in LEAD_SCHEMA_KEYS}
    lead["social_links"] = []
    return lead


class BaseScraper(ABC):
    """
    Abstract scraper.  Subclasses implement `scrape()` and `_parse_lead()`.
    """

    source_name: str = "base"

    def __init__(self, region: str, niche: str) -> None:
        self.region = region
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

    def _normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Merge raw dict onto an empty lead dict so all keys are present."""
        lead = empty_lead()
        lead.update({k: v for k, v in raw.items() if k in LEAD_SCHEMA_KEYS})
        lead["source"] = self.source_name
        return lead

    # ── Interface ─────────────────────────────────────────────────────────────

    @abstractmethod
    def scrape(self) -> list[dict[str, Any]]:
        """
        Run the scraper and return a list of normalised lead dicts.
        Must call self._normalise() on every lead before returning.
        """

    @abstractmethod
    def _parse_lead(self, raw: Any) -> dict[str, Any]:
        """Parse a single raw item (tag, dict, etc.) into a raw lead dict."""
