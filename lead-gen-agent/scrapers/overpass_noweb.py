"""
OpenStreetMap Overpass API scraper.

Finds local businesses in a given location that have NO website in their OSM record.
These are the highest-value leads: real, active businesses with zero digital presence.

Why this works from cloud IPs: the Overpass API is a free public service with no
IP-based restrictions — unlike Yelp, Google, or YellowPages.

API docs: https://wiki.openstreetmap.org/wiki/Overpass_API
"""

import logging
import time
from typing import Any

import requests

from scrapers.base import BaseScraper, empty_lead

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Maps niche keywords → OSM key=value pairs to query
# Each niche may map to multiple OSM tags (tried in order until results found)
OSM_NICHE_TAGS: dict[str, list[tuple[str, str]]] = {
    "restaurants": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "cafes": [("amenity", "cafe"), ("amenity", "coffee_shop")],
    "bars": [("amenity", "bar"), ("amenity", "pub"), ("amenity", "nightclub")],
    "hotels": [("tourism", "hotel"), ("tourism", "motel"), ("tourism", "guest_house")],
    "hotels and hospitality": [("tourism", "hotel"), ("tourism", "hostel"), ("tourism", "guest_house")],
    "beauty salons": [("shop", "hairdresser"), ("shop", "beauty"), ("shop", "nail_salon")],
    "dentists": [("amenity", "dentist")],
    "dental clinics": [("amenity", "dentist")],
    "gyms": [("leisure", "fitness_centre"), ("leisure", "sports_centre")],
    "fitness gyms": [("leisure", "fitness_centre"), ("leisure", "sports_centre")],
    "law firms": [("office", "lawyer"), ("office", "attorney")],
    "medical clinics": [("amenity", "clinic"), ("amenity", "doctors")],
    "healthcare clinics": [("amenity", "clinic"), ("amenity", "doctors"), ("amenity", "hospital")],
    "real estate agencies": [("office", "estate_agent"), ("office", "real_estate")],
    "accountants": [("office", "accountant")],
    "accounting firms": [("office", "accountant")],
    "pharmacies": [("amenity", "pharmacy")],
    "veterinarians": [("amenity", "veterinary")],
    "florists": [("shop", "florist")],
    "bakeries": [("shop", "bakery")],
    "auto dealerships": [("shop", "car"), ("amenity", "car_rental")],
    "auto repair": [("shop", "car_repair"), ("shop", "tyres")],
    "retail": [("shop", "clothes"), ("shop", "shoes"), ("shop", "gift"), ("shop", "department_store")],
    "construction companies": [("craft", "builder"), ("craft", "construction")],
    "electricians": [("craft", "electrician")],
    "plumbers": [("craft", "plumber")],
    "home services": [("craft", "builder"), ("craft", "electrician"), ("craft", "plumber")],
    "photographers": [("craft", "photographer"), ("shop", "photo")],
    "educational institutes": [("amenity", "school"), ("amenity", "college"), ("amenity", "university")],
    "gyms": [("leisure", "fitness_centre")],
    "opticians": [("shop", "optician")],
    "insurance agencies": [("office", "insurance")],
    "financial advisors": [("office", "financial_advisor"), ("office", "financial")],
    "wedding planners": [("shop", "wedding")],
    "travel agencies": [("shop", "travel_agency")],
    "printing": [("shop", "copyshop"), ("craft", "printer")],
    "tattoo shops": [("shop", "tattoo")],
    "spas": [("leisure", "spa"), ("shop", "massage")],
    "grocery": [("shop", "supermarket"), ("shop", "grocery"), ("shop", "convenience")],
    "pet shops": [("shop", "pet")],
    "bookshops": [("shop", "books")],
    "electronics": [("shop", "electronics"), ("shop", "mobile_phone")],
}


class OverpassNoWebScraper(BaseScraper):
    """
    Queries OpenStreetMap via Overpass API for businesses in a location
    that have a name but no website tag — prime targets for web services.
    """

    source_name = "osm_no_website"

    def __init__(self, location: str, niche: str, max_results: int = 50) -> None:
        super().__init__(location, niche)
        self.max_results = max_results

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        tags = self._resolve_tags()
        if not tags:
            logger.info("[overpass] No OSM tags mapped for niche '%s' — skipping.", self.niche)
            return []

        leads: list[dict[str, Any]] = []
        seen: set[str] = set()

        for osm_key, osm_val in tags:
            batch = self._query(osm_key, osm_val)
            for lead in batch:
                dedup_key = f"{(lead.get('name') or '').lower()}|{(lead.get('address') or '').lower()}"
                if dedup_key not in seen and lead.get("name"):
                    seen.add(dedup_key)
                    leads.append(lead)
            if len(leads) >= self.max_results:
                break
            time.sleep(2.0)  # Be polite to the free public API

        logger.info(
            "[overpass] '%s' in '%s' → %d businesses without website",
            self.niche, self.location, len(leads),
        )
        return leads[: self.max_results]

    # ── Private ───────────────────────────────────────────────────────────────

    def _resolve_tags(self) -> list[tuple[str, str]]:
        """Match niche string to OSM tag pairs (case-insensitive substring match)."""
        niche_lower = self.niche.lower()
        # Exact or substring match
        for key, tags in OSM_NICHE_TAGS.items():
            if niche_lower in key or key in niche_lower:
                return tags
        # Partial word match fallback
        niche_words = set(niche_lower.split())
        for key, tags in OSM_NICHE_TAGS.items():
            key_words = set(key.split())
            if niche_words & key_words:
                return tags
        return []

    def _query(self, osm_key: str, osm_val: str) -> list[dict[str, Any]]:
        """
        Run an Overpass QL query for businesses with the given tag in the location,
        filtering to only those WITHOUT a 'website' tag.
        """
        # Use the geocodeArea shortcut — Overpass resolves the city name automatically
        query = f"""
[out:json][timeout:60];
area[name="{self.location}"]->.a;
(
  node["{osm_key}"="{osm_val}"]["name"][!"website"](area.a);
  way["{osm_key}"="{osm_val}"]["name"][!"website"](area.a);
);
out body center {self.max_results};
"""
        try:
            resp = requests.post(
                OVERPASS_URL,
                data={"data": query.strip()},
                timeout=75,
                headers={"User-Agent": "LeadGenBot/1.0 (non-commercial research)"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning(
                "[overpass] Query failed (%s=%s in %s): %s",
                osm_key, osm_val, self.location, exc,
            )
            return []

        results = []
        for element in data.get("elements", []):
            lead = self._parse_lead(element)
            if lead:
                results.append(lead)

        return results

    def _parse_lead(self, element: dict) -> dict[str, Any] | None:  # type: ignore[override]
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            return None

        # Reconstruct address from OSM addr:* fields
        addr_parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
        ]
        address_line = " ".join(p for p in addr_parts if p).strip() or None
        city = tags.get("addr:city") or self.location
        postcode = tags.get("addr:postcode", "")

        osm_type = element.get("type", "node")
        osm_id = element.get("id", "")
        osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

        intent_text = (
            f"'{name}' is an active {self.niche} business in {self.location} "
            f"with no website on record. "
        )
        if tags.get("phone") or tags.get("contact:phone"):
            intent_text += "Has a phone number — directly reachable."
        if tags.get("opening_hours"):
            intent_text += f" Operating hours: {tags['opening_hours']}."

        lead = empty_lead()
        lead.update({
            "name": name,
            "niche": self.niche,
            "city": city,
            "country": "",
            "phone": tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile"),
            "email": tags.get("email") or tags.get("contact:email"),
            "website": None,
            "address": f"{address_line}, {postcode}".strip(", ") if address_line else postcode or None,
            "has_website": False,
            "lead_type": "no_website",
            "intent_signal": "osm_no_website",
            "intent_text": intent_text,
            "intent_url": osm_url,
            "source": self.source_name,
            "industry": self.niche,
            "description": tags.get("description") or tags.get("note"),
        })
        return lead
