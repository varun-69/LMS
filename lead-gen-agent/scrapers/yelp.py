"""
Yelp.com scraper — business directory covering US, UK, Australia, and Canada.
URL: https://www.yelp.com/search?find_desc={niche}&find_loc={city}+{state}
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from config.targets import REGIONS
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_YELP_SEARCH = "https://www.yelp.com/search"
_YELP_BIZ = "https://www.yelp.com"

# Yelp is available in US, UK, AU (not directly in India)
_SUPPORTED_REGIONS = {"US", "UK", "AU"}


class YelpScraper(BaseScraper):
    """
    Scrapes Yelp search results for business leads.
    Extracts: name, address, phone, website, rating, review_count, categories.
    """

    source_name = "yelp"

    def __init__(self, region: str, niche: str, max_per_city: int = 15) -> None:
        super().__init__(region, niche)
        self.max_per_city = max_per_city
        self.region_data = REGIONS.get(region, {})

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        if self.region not in _SUPPORTED_REGIONS:
            logger.info("[yelp] Region %s not supported — skipping.", self.region)
            return []

        leads: list[dict[str, Any]] = []
        cities = self.region_data.get("cities", [])[:5]
        country = self.region_data.get("country", "")

        for city in cities:
            city_leads = self._scrape_city(city, country)
            leads.extend(city_leads)
            if len(leads) >= 50:
                break

        return leads

    # ── Private ───────────────────────────────────────────────────────────────

    def _scrape_city(self, city: str, country: str) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        params = {
            "find_desc": self.niche,
            "find_loc": f"{city}, {country}",
            "ns": 1,
        }

        resp = self._polite_get(_YELP_SEARCH, params=params)
        if resp is None:
            logger.warning("[yelp] No response for %s in %s", self.niche, city)
            return leads

        soup = BeautifulSoup(resp.text, "lxml")

        # Yelp renders differently — try multiple selectors
        cards = (
            soup.select("div[data-testid='serp-ia-card']")
            or soup.select("li.regular-search-result")
            or soup.select("div.businessName")
        )

        for card in cards[: self.max_per_city]:
            try:
                raw = self._parse_lead((card, city, country))
                if raw.get("name"):
                    leads.append(self._normalise(raw))
            except Exception as exc:
                logger.debug("[yelp] parse error: %s", exc)

        logger.info("[yelp] %s in %s → %d leads", self.niche, city, len(leads))
        return leads

    def _parse_lead(self, item: tuple) -> dict[str, Any]:  # type: ignore[override]
        card, city, country = item
        raw: dict[str, Any] = {}

        # Name
        name_el = (
            card.select_one("a.css-19v1rkv, span.css-1egxyvc")
            or card.select_one("h3 a, h4 a")
            or card.select_one("[class*='businessName'] a")
        )
        raw["name"] = name_el.get_text(strip=True) if name_el else None

        # Rating
        rating_el = card.select_one("div[aria-label*='star rating'], span[aria-label*='star']")
        if rating_el:
            aria = rating_el.get("aria-label", "")
            nums = re.findall(r"[\d.]+", aria)
            try:
                raw["rating"] = float(nums[0]) if nums else None
            except ValueError:
                raw["rating"] = None

        # Review count
        review_el = card.select_one("span[class*='reviewCount'], a[href*='reviews']")
        if review_el:
            text = review_el.get_text()
            nums = re.findall(r"\d+", text)
            raw["review_count"] = int(nums[0]) if nums else None

        # Address
        addr_el = card.select_one("address, p[class*='secondaryAttributes']")
        raw["address"] = addr_el.get_text(" ", strip=True) if addr_el else None

        # Phone
        phone_el = card.select_one("p[class*='phone'], span[class*='phone']")
        raw["phone"] = phone_el.get_text(strip=True) if phone_el else None

        # Category / industry
        cat_els = card.select("span.css-1fdy0l5 a, a[class*='tag']")
        cats = [el.get_text(strip=True) for el in cat_els]
        raw["industry"] = ", ".join(cats) if cats else self.niche

        # Website link (from profile, not always shown in listing)
        link_el = card.select_one("a.css-19v1rkv, h3 a, h4 a")
        if link_el:
            href = link_el.get("href", "")
            raw["website"] = f"{_YELP_BIZ}{href}" if href.startswith("/biz") else None

        raw["city"] = city
        raw["country"] = country

        return raw
