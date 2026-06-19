"""
LeadGenCrew — orchestrates the intent-based lead generation pipeline.

Pipeline:
  1. Scout    — finds businesses without websites (OSM) + Reddit intent posts
  2. Enricher — visits any found websites, extracts emails & social links
  3. Scorer   — uses Claude AI to score and tier each lead
  4. Outreach — generates personalised cold emails for Tier A leads
"""

import logging
from typing import Any

from agents.scout import ScoutAgent
from agents.enricher import EnricherAgent
from agents.scorer import ScorerAgent
from agents.outreach import OutreachAgent

logger = logging.getLogger(__name__)


class LeadGenCrew:
    """
    Orchestrates the full lead generation pipeline for one or more
    location + niche combinations.
    """

    def __init__(
        self,
        locations: list[str],
        niches: list[str],
        skip_enrichment: bool = False,
        skip_scoring: bool = False,
        skip_outreach: bool = False,
    ) -> None:
        self.locations = locations
        self.niches = niches
        self.skip_enrichment = skip_enrichment
        self.skip_scoring = skip_scoring
        self.skip_outreach = skip_outreach

        self._enricher = EnricherAgent()
        self._scorer = ScorerAgent() if not skip_scoring else None
        self._outreach = OutreachAgent() if not skip_outreach else None

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self) -> list[dict[str, Any]]:
        """
        Run the full pipeline for every (location, niche) combination.
        Returns a sorted, deduplicated list of scored leads.
        """
        all_leads: list[dict[str, Any]] = []

        for location in self.locations:
            for niche in self.niches:
                logger.info("=== Pipeline: %s / %s ===", location, niche)
                batch = self._run_pipeline(location, niche)
                all_leads.extend(batch)

        all_leads.sort(key=lambda l: l.get("score", 0), reverse=True)
        logger.info("Pipeline complete. Total leads: %d", len(all_leads))
        return all_leads

    # ── Private ───────────────────────────────────────────────────────────────

    def _run_pipeline(self, location: str, niche: str) -> list[dict[str, Any]]:
        # 1. Scout
        scout = ScoutAgent(location, niche)
        leads = scout.run()
        if not leads:
            logger.warning("No leads found for '%s' in '%s'", niche, location)
            return []

        # 2. Enricher — only for leads that already have a website URL
        if not self.skip_enrichment:
            enrichable = [l for l in leads if l.get("website")]
            if enrichable:
                enriched = self._enricher.run(enrichable)
                enriched_names = {l.get("name") for l in enriched}
                unenriched = [l for l in leads if l.get("name") not in enriched_names]
                leads = enriched + unenriched

        # 3. Scorer
        if not self.skip_scoring and self._scorer:
            leads = self._scorer.run(leads)

        # 4. Outreach
        if not self.skip_outreach and self._outreach:
            leads = self._outreach.run(leads)

        return leads
