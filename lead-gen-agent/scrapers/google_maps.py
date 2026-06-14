"""
Google search scraper — queries Google for businesses in a given niche and city,
extracting business name, website, phone, and snippet from organic results.

Uses a respectful approach: plain HTTP GET with rotating User-Agents and delays.
No headless browser required.
"""

import logging
import re
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup

from config.targets import REGIONS, SEARCH_KEYWORDS
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_GOOGLE_SEARCH_URL = "https://www.google.com/search"
_PHONE_RE = re.compile(r"(\+?[\d\s\-\(\)]{7,20})")
_WEBSITE_RE = re.compile(r"https?://[^\s\"'>]+")


class GoogleMapsScraper(BaseScraper):
    """
    Scrapes Google Search results for businesses matching a niche + city.

    Strategy: issue one search per keyword template, collect result cards
    (title, URL, snippet, visible phone if present).
    """

    source_name = "google_search"

    def __init__(self, region: str, niche: str, max_per_city: int = 10) -> None:
        super().__init__(region, niche)
        self.max_per_city = max_per_city
        self.region_data = REGIONS.get(region, {})

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        country = self.region_data.get("country", "")
        cities = self.region_data.get("cities", [])[:5]  # limit cities per run

        for city in cities:
            city_leads = self._scrape_city(city, country)
            leads.extend(city_leads)
            if len(leads) >= 50:
                break

        return leads

    # ── Private ───────────────────────────────────────────────────────────────

    def _scrape_city(self, city: str, country: str) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        query = f"{self.niche} companies in {city} {country}"
        params = {
            "q": query,
            "num": 20,
            "hl": "en",
            "gl": self.region_data.get("country_code", "US").lower(),
        }

        resp = self._polite_get(_GOOGLE_SEARCH_URL, params=params)
        if resp is None:
            logger.warning("No response for Google query: %s", query)
            return leads

        soup = BeautifulSoup(resp.text, "lxml")

        # Organic result blocks (class "g" in Google's current HTML)
        for block in soup.select("div.g")[:self.max_per_city]:
            try:
                raw = self._parse_lead((block, city, country))
                if raw.get("name"):
                    leads.append(self._normalise(raw))
            except Exception as exc:
                logger.debug("Failed to parse Google result block: %s", exc)

        logger.info(
            "[google_search] %s in %s, %s → %d leads",
            self.niche, city, country, len(leads),
        )
        return leads

    def _parse_lead(self, item: tuple) -> dict[str, Any]:  # type: ignore[override]
        block, city, country = item
        raw: dict[str, Any] = {}

        # Title / name
        title_el = block.select_one("h3")
        raw["name"] = title_el.get_text(strip=True) if title_el else None

        # Website URL
        link_el = block.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        if href.startswith("/url?"):
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            href = parsed.get("q", [""])[0]
        raw["website"] = href if href.startswith("http") else None

        # Snippet / description
        snippet_el = block.select_one("div[data-sncf], div.VwiC3b, span.aCOpRe")
        raw["description"] = snippet_el.get_text(strip=True) if snippet_el else None

        # Phone (sometimes visible in Google snippets)
        text = block.get_text(" ")
        phone_match = _PHONE_RE.search(text)
        raw["phone"] = phone_match.group(0).strip() if phone_match else None

        raw["city"] = city
        raw["country"] = country
        raw["industry"] = self.niche

        return raw
