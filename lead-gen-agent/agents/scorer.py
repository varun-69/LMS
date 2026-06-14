"""
Scorer Agent — uses Claude API to score each enriched lead and add
scoring metadata (score, tier, reasoning, recommended_service, outreach_hook).
"""

import logging
from typing import Any

from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class ScorerAgent:
    """
    Scores each lead using the ClaudeClient and sorts results by score descending.
    Adds the following keys to each lead:
      - score (int 0-100)
      - tier  (str A/B/C)
      - reasoning (str)
      - estimated_budget_usd_monthly (int|None)
      - recommended_service (str)
      - pain_points_identified (list[str])
      - outreach_hook (str)
    """

    def __init__(self) -> None:
        self._claude = ClaudeClient()

    def run(self, leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score all leads and return them sorted by score (highest first)."""
        scored: list[dict[str, Any]] = []

        for i, lead in enumerate(leads):
            logger.info(
                "[scorer] %d/%d scoring: %s", i + 1, len(leads), lead.get("name")
            )
            scoring = self._claude.score_lead(lead)
            lead.update(scoring)
            scored.append(lead)

        scored.sort(key=lambda l: l.get("score", 0), reverse=True)
        logger.info("[scorer] Scoring complete. Top lead: %s (score=%s)",
                    scored[0].get("name") if scored else "none",
                    scored[0].get("score") if scored else 0)
        return scored
