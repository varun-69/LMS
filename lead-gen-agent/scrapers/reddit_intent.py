"""
Reddit intent scraper.

Searches Reddit for posts where business owners / founders explicitly seek
website design, web development, or digital marketing assistance.

Why Reddit works from cloud IPs:
  - Public JSON API requires no authentication
  - Rate-limit is generous (60 req/min for unauthenticated, 1 req/sec is safe)
  - Append .json to any Reddit URL or use /search.json endpoint

Signal quality: someone actively posting "I need a website for my restaurant in London"
is the highest-intent lead possible — they've raised their hand and described the need.
"""

import logging
import re
import time
from typing import Any

import requests

from scrapers.base import BaseScraper, empty_lead

logger = logging.getLogger(__name__)

_REDDIT_SEARCH = "https://www.reddit.com/search.json"
_SUBREDDIT_SEARCH = "https://www.reddit.com/r/{sub}/search.json"

# Subreddits where business owners ask for help
_SUBREDDITS = [
    "smallbusiness",
    "Entrepreneur",
    "startups",
    "marketing",
    "web_design",
    "forhire",
    "hiring",
]

# Intent search phrase templates — {niche} and {location} are filled in at runtime
_INTENT_QUERIES = [
    "need a website {niche} {location}",
    "need website for my {niche}",
    "looking for web designer {location}",
    "looking for web developer {niche}",
    "no website {niche} {location}",
    "need digital marketing {niche} {location}",
    "marketing help {niche} {location}",
    "need SEO {niche}",
    "build website {niche} {location}",
    "website for {niche} business",
    "hire web developer {location}",
    "marketing agency {niche} {location}",
]

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(\+?[0-9][\d\s\-\(\)]{7,16}[0-9])")


class RedditIntentScraper(BaseScraper):
    """
    Scrapes Reddit for high-intent posts from business owners seeking
    web design, web development, or digital marketing services.

    Returns leads shaped around the poster, not a business listing —
    the intent_text field contains the actual post so the outreach agent
    can craft a hyper-personalised message referencing what they wrote.
    """

    source_name = "reddit_intent"

    def __init__(self, location: str, niche: str, max_results: int = 30) -> None:
        super().__init__(location, niche)
        self.max_results = max_results
        self._http = requests.Session()
        self._http.headers.update({
            "User-Agent": "Mozilla/5.0 LeadGenResearch/1.0 (non-commercial)",
            "Accept": "application/json",
        })

    # ── Interface ─────────────────────────────────────────────────────────────

    def scrape(self) -> list[dict[str, Any]]:
        leads: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        # Phase 1 — global Reddit search: intent phrase + niche + location
        for template in _INTENT_QUERIES[:7]:
            query = template.format(niche=self.niche, location=self.location)
            for lead in self._global_search(query):
                url = lead.get("intent_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    leads.append(lead)
            time.sleep(1.5)
            if len(leads) >= self.max_results:
                break

        # Phase 2 — subreddit search for niche-only (broader, more supply)
        if len(leads) < self.max_results:
            for sub in _SUBREDDITS[:3]:
                query = f"need website {self.niche}"
                for lead in self._subreddit_search(sub, query):
                    url = lead.get("intent_url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        leads.append(lead)
                time.sleep(1.5)
                if len(leads) >= self.max_results:
                    break

        logger.info(
            "[reddit] '%s' in '%s' → %d intent posts found",
            self.niche, self.location, len(leads),
        )
        return leads[: self.max_results]

    # ── Private ───────────────────────────────────────────────────────────────

    def _global_search(self, query: str) -> list[dict[str, Any]]:
        params = {"q": query, "sort": "new", "limit": 10, "t": "year", "type": "link"}
        return self._fetch(_REDDIT_SEARCH, params)

    def _subreddit_search(self, subreddit: str, query: str) -> list[dict[str, Any]]:
        url = _SUBREDDIT_SEARCH.format(sub=subreddit)
        params = {"q": query, "restrict_sr": 1, "sort": "new", "limit": 10, "t": "year"}
        return self._fetch(url, params)

    def _fetch(self, url: str, params: dict) -> list[dict[str, Any]]:
        try:
            resp = self._http.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.debug("[reddit] request failed (%s): %s", url, exc)
            return []

        leads = []
        for child in data.get("data", {}).get("children", []):
            lead = self._parse_lead(child.get("data", {}))
            if lead:
                leads.append(lead)
        return leads

    def _parse_lead(self, post: dict) -> dict[str, Any] | None:  # type: ignore[override]
        title = (post.get("title") or "").strip()
        body = (post.get("selftext") or "").strip()
        author = post.get("author") or ""
        permalink = post.get("permalink") or ""
        subreddit = post.get("subreddit") or ""
        upvotes = post.get("score", 0)

        # Skip bots, deleted accounts, removed posts
        if not title or author in ("[deleted]", "AutoModerator", ""):
            return None
        if body in ("[deleted]", "[removed]"):
            body = ""

        full_text = f"{title}\n{body}"

        # Extract contact info from post body (sometimes left by OP)
        emails_found = _EMAIL_RE.findall(full_text)
        phones_found = _PHONE_RE.findall(full_text)
        email = emails_found[0] if emails_found else None
        phone = phones_found[0] if phones_found else None

        # Build readable intent snippet: full title + up to 500 chars of body
        snippet = title
        if body:
            body_preview = body[:500] + ("…" if len(body) > 500 else "")
            snippet = f"{title}\n\n{body_preview}"

        lead = empty_lead()
        lead.update({
            "name": f"u/{author}",
            "niche": self.niche,
            "city": self.location,
            "country": "",
            "email": email,
            "phone": phone,
            "website": None,
            "address": None,
            "has_website": False,
            "lead_type": "intent_post",
            "intent_signal": "reddit_post",
            "intent_text": snippet,
            "intent_url": f"https://www.reddit.com{permalink}",
            "source": f"reddit/r/{subreddit}",
            "industry": self.niche,
            "reddit_upvotes": upvotes,
        })
        return lead
