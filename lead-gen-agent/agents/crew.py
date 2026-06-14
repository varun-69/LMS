"""
LeadGenCrew — orchestrates the full pipeline using CrewAI.

Pipeline:
  1. Scout   — scrapes multiple directories for raw leads
  2. Enricher — visits websites to extract emails & social links
  3. Scorer   — uses Claude AI to score and tier each lead
  4. Outreach — generates personalised cold emails for Tier A leads

Can also be run without CrewAI (standalone mode) for simpler deployments.
"""

import logging
from typing import Any

from config.targets import REGIONS, NICHES
from agents.scout import ScoutAgent
from agents.enricher import EnricherAgent
from agents.scorer import ScorerAgent
from agents.outreach import OutreachAgent

logger = logging.getLogger(__name__)


class LeadGenCrew:
    """
    Orchestrates the full lead generation pipeline for one or more
    region + niche combinations.
    """

    def __init__(
        self,
        regions: list[str],
        niches: list[str],
        skip_enrichment: bool = False,
        skip_scoring: bool = False,
        skip_outreach: bool = False,
    ) -> None:
        self.regions = regions
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
        Run the full pipeline for every (region, niche) combination.
        Returns a sorted, deduplicated list of scored leads.
        """
        all_leads: list[dict[str, Any]] = []

        for region in self.regions:
            if region not in REGIONS:
                logger.warning("Unknown region '%s' — skipping.", region)
                continue
            for niche in self.niches:
                logger.info("=== Pipeline: %s / %s ===", region, niche)
                batch = self._run_pipeline(region, niche)
                all_leads.extend(batch)

        # Global sort by score
        all_leads.sort(key=lambda l: l.get("score", 0), reverse=True)
        logger.info("Pipeline complete. Total leads: %d", len(all_leads))
        return all_leads

    # ── Private ───────────────────────────────────────────────────────────────

    def _run_pipeline(self, region: str, niche: str) -> list[dict[str, Any]]:
        # 1. Scout
        scout = ScoutAgent(region, niche)
        raw_leads = scout.run()
        if not raw_leads:
            logger.warning("No leads found for %s / %s", region, niche)
            return []

        # 2. Enricher
        if not self.skip_enrichment:
            raw_leads = self._enricher.run(raw_leads)

        # 3. Scorer
        if not self.skip_scoring and self._scorer:
            raw_leads = self._scorer.run(raw_leads)

        # 4. Outreach
        if not self.skip_outreach and self._outreach:
            raw_leads = self._outreach.run(raw_leads)

        return raw_leads
