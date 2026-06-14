"""
YellowPages.com scraper — US-focused business directory.
URL pattern: https://www.yellowpages.com/search?search_terms={niche}&geo_location_terms={city}+{state}
"""

import logging
import re
from typing import Any
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from config.targets import REGIONS
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_YP_BASE = "https://www.yellowpages.com/search"


class YellowPagesScraper(BaseScraper):
    """
    Scrapes YellowPages.com for US business leads.
    Extracts: name, address, phone, website, category.
    """

    source_name = "yellowpages"

    def __init__(self, region: str, niche: str, max_pages: int = 2) -> None:
        super().__init__(region, niche)
        self.max_pages = max_pages
        self.region_data = REGIONS.get("US", {})  # YP is US-only
        self.states = self.region_data.get("yellow_pages_states", {})

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        if self.region != "US":
            logger.info("[yellowpages] Only supports US region — skipping.")
            return []

        leads: list[dict[str, Any]] = []
        cities = list(self.states.keys())[:5]

        for city in cities:
            state = self.states.get(city, "")
            city_leads = self._scrape_city(city, state)
            leads.extend(city_leads)
            if len(leads) >= 50:
                break

        return leads

    # ── Private ───────────────────────────────────────────────────────────────

    def _scrape_city(self, city: str, state: str) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        geo = f"{city}+{state}" if state else city

        for page in range(1, self.max_pages + 1):
            params = {
                "search_terms": self.niche,
                "geo_location_terms": geo,
                "page": page,
            }
            resp = self._polite_get(_YP_BASE, params=params)
            if resp is None:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            results = soup.select("div.result, div.v-card")
            if not results:
                break

            for result in results:
                try:
                    raw = self._parse_lead((result, city))
                    if raw.get("name"):
                        leads.append(self._normalise(raw))
                except Exception as exc:
                    logger.debug("[yellowpages] parse error: %s", exc)

        logger.info("[yellowpages] %s in %s, %s → %d leads", self.niche, city, state, len(leads))
        return leads

    def _parse_lead(self, item: tuple) -> dict[str, Any]:  # type: ignore[override]
        result, city = item
        raw: dict[str, Any] = {}

        # Name
        name_el = result.select_one("a.business-name span, h2.n span")
        raw["name"] = name_el.get_text(strip=True) if name_el else None

        # Address
        addr_el = result.select_one("p.adr, .street-address")
        raw["address"] = addr_el.get_text(" ", strip=True) if addr_el else None

        # Phone
        phone_el = result.select_one("p.phone, .phones.phone.primary")
        raw["phone"] = phone_el.get_text(strip=True) if phone_el else None

        # Website
        website_el = result.select_one("a.track-visit-website, a[data-analytics='website']")
        if website_el:
            href = website_el.get("href", "")
            raw["website"] = href if href.startswith("http") else None

        # Category / industry
        cat_el = result.select_one("p.categories a, .categories")
        raw["industry"] = cat_el.get_text(strip=True) if cat_el else self.niche

        raw["city"] = city
        raw["country"] = "United States"

        # Rating
        rating_el = result.select_one(".rating-stars, .ratings")
        try:
            aria = rating_el.get("aria-label", "") if rating_el else ""
            nums = re.findall(r"[\d.]+", aria)
            raw["rating"] = float(nums[0]) if nums else None
        except (ValueError, IndexError):
            raw["rating"] = None

        return raw
