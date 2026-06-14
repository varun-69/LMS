"""
Enricher Agent — visits each lead's website to extract contact emails,
social media links, meta description, and page title.
"""

import logging
import re
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config.settings import settings

logger = logging.getLogger(__name__)

_ua = UserAgent()

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)
_SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"linkedin\.com/(?:company|in)/[\w\-]+", re.I),
    "twitter": re.compile(r"(?:twitter|x)\.com/[\w\-]+", re.I),
    "facebook": re.compile(r"facebook\.com/[\w.\-]+", re.I),
    "instagram": re.compile(r"instagram\.com/[\w.\-]+", re.I),
}

_CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/get-in-touch"]


class EnricherAgent:
    """
    Enriches raw leads by visiting their websites and extracting:
    - Email addresses (from mailto links and text)
    - Social media profile URLs
    - Meta description & page title (as description)
    """

    def __init__(self) -> None:
        self._session = requests.Session()

    def run(self, leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enrich a list of leads in place and return them."""
        enriched: list[dict[str, Any]] = []

        for i, lead in enumerate(leads):
            logger.info(
                "[enricher] %d/%d enriching: %s", i + 1, len(leads), lead.get("name")
            )
            enriched.append(self._enrich_lead(lead))

        return enriched

    # ── Private ───────────────────────────────────────────────────────────────

    def _enrich_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        website = lead.get("website")
        if not website or not website.startswith("http"):
            return lead

        try:
            html = self._fetch(website)
            if html:
                lead = self._extract_from_html(lead, html, website)

            # Try a contact page if no email found yet
            if not lead.get("email"):
                for path in _CONTACT_PATHS:
                    contact_url = urljoin(website, path)
                    contact_html = self._fetch(contact_url)
                    if contact_html:
                        emails = _EMAIL_RE.findall(contact_html)
                        emails = [e for e in emails if not e.endswith((".png", ".jpg", ".gif"))]
                        if emails:
                            lead["email"] = emails[0]
                            break

        except Exception as exc:
            logger.debug("[enricher] Failed to enrich %s: %s", website, exc)

        return lead

    def _fetch(self, url: str, timeout: int = 10) -> str | None:
        headers = {
            "User-Agent": _ua.random,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        time.sleep(1.0)  # polite delay
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.ok and "text/html" in resp.headers.get("content-type", ""):
                return resp.text
        except requests.RequestException:
            pass
        return None

    def _extract_from_html(
        self, lead: dict[str, Any], html: str, base_url: str
    ) -> dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")

        # Meta description
        if not lead.get("description"):
            meta = soup.find("meta", attrs={"name": "description"})
            if meta:
                lead["description"] = meta.get("content", "")[:300]

        # Page title as fallback name
        if not lead.get("name"):
            title = soup.find("title")
            if title:
                lead["name"] = title.get_text(strip=True)[:80]

        # Emails from mailto links
        if not lead.get("email"):
            mailto_links = soup.select("a[href^='mailto:']")
            for link in mailto_links:
                email = link["href"].replace("mailto:", "").split("?")[0].strip()
                if _EMAIL_RE.match(email):
                    lead["email"] = email
                    break

        # Emails from page text
        if not lead.get("email"):
            page_text = soup.get_text(" ")
            emails = _EMAIL_RE.findall(page_text)
            emails = [
                e for e in emails
                if not any(e.lower().endswith(ext) for ext in (".png", ".jpg", ".gif", ".svg"))
            ]
            if emails:
                lead["email"] = emails[0]

        # Social links
        page_text = html
        social_links: list[str] = lead.get("social_links") or []
        for platform, pattern in _SOCIAL_PATTERNS.items():
            match = pattern.search(page_text)
            if match:
                full_url = f"https://www.{match.group(0)}"
                if full_url not in social_links:
                    social_links.append(full_url)
        lead["social_links"] = social_links

        return lead
