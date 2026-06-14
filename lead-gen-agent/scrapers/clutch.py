"""
Clutch.co scraper — finds digital marketing and web development agencies
listed on Clutch for the target regions.

Scrapes the agencies/digital-marketing and web-designers listing pages.
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from config.targets import REGIONS
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_CLUTCH_BASE = "https://clutch.co"
_HOURLY_RE = re.compile(r"\$[\d,]+\s*[–\-/]\s*\$[\d,]+\s*/\s*hr", re.IGNORECASE)

_CATEGORY_PATHS = {
    "digital_marketing": "/agencies/digital-marketing",
    "web_design": "/web-designers",
    "seo": "/agencies/seo",
    "social_media": "/agencies/social-media-marketing",
    "web_development": "/developers",
}

_COUNTRY_FILTER = {
    "US": "united-states",
    "UK": "united-kingdom",
    "AU": "australia",
    "IN": "india",
}


class ClutchScraper(BaseScraper):
    """
    Scrapes Clutch.co for agency listings in the target region.
    Extracts: name, website, rating, review count, hourly rate, location, services.
    """

    source_name = "clutch"

    def __init__(self, region: str, niche: str, max_pages: int = 3) -> None:
        super().__init__(region, niche)
        self.max_pages = max_pages
        self.country_slug = _COUNTRY_FILTER.get(region, "united-states")
        self.region_data = REGIONS.get(region, {})

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        category_path = _CATEGORY_PATHS.get("digital_marketing")

        for page in range(1, self.max_pages + 1):
            url = f"{_CLUTCH_BASE}{category_path}"
            params = {
                "page": page,
                "client_focus[]": "small-business",
                "sort_by": "verified_reviews",
            }
            resp = self._polite_get(url, params=params)
            if resp is None:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("li.provider-row, article.directory-list-item")
            if not cards:
                logger.info("[clutch] No more cards on page %d", page)
                break

            for card in cards:
                try:
                    raw = self._parse_lead(card)
                    if raw.get("name"):
                        lead = self._normalise(raw)
                        # Filter by region if location data present
                        location = raw.get("address", "")
                        country = self.region_data.get("country", "")
                        if not location or country.lower() in location.lower() or not country:
                            leads.append(lead)
                except Exception as exc:
                    logger.debug("[clutch] parse error: %s", exc)

            logger.info("[clutch] page %d → %d leads so far", page, len(leads))
            if len(leads) >= 50:
                break

        return leads

    def _parse_lead(self, card: Any) -> dict[str, Any]:  # type: ignore[override]
        raw: dict[str, Any] = {}

        # Company name
        name_el = card.select_one("h3.company-name, .company_info h3, a.company-name")
        raw["name"] = name_el.get_text(strip=True) if name_el else None

        # Website (Clutch wraps it; take the profile link as fallback)
        website_el = card.select_one("a.website-link, a[data-link_type='website']")
        if website_el:
            raw["website"] = website_el.get("href", None)
        else:
            profile_el = card.select_one("a.directory-list-item__profile-link, h3 a")
            href = profile_el.get("href", "") if profile_el else ""
            raw["website"] = f"{_CLUTCH_BASE}{href}" if href.startswith("/") else href or None

        # Rating
        rating_el = card.select_one(".sg-rating__number, span.rating")
        try:
            raw["rating"] = float(rating_el.get_text(strip=True)) if rating_el else None
        except ValueError:
            raw["rating"] = None

        # Review count
        review_el = card.select_one(".sg-rating__reviews, .reviews-count")
        if review_el:
            nums = re.findall(r"\d+", review_el.get_text())
            raw["review_count"] = int(nums[0]) if nums else None

        # Hourly rate
        rate_el = card.select_one(".hourly-rate, .profile-summary__item--hourly")
        raw["description"] = rate_el.get_text(strip=True) if rate_el else None

        # Location
        loc_el = card.select_one(".location-city, .locality")
        raw["address"] = loc_el.get_text(strip=True) if loc_el else None

        # Country / city
        raw["country"] = self.region_data.get("country", "")
        raw["city"] = (raw["address"] or "").split(",")[0].strip()
        raw["industry"] = self.niche or "Digital Marketing Agency"

        return raw
