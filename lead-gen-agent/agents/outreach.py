"""
Outreach Agent — generates personalised cold-outreach emails for Tier A leads
using the Claude API, and adds them as `outreach_email` on each lead dict.
"""

import logging
from typing import Any

from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class OutreachAgent:
    """
    Generates cold-outreach emails for top-tier (A) leads.

    Only processes Tier A leads to conserve API quota and keep quality high.
    Adds `outreach_email` field to each qualifying lead.
    """

    def __init__(self, tiers: list[str] | None = None) -> None:
        self._claude = ClaudeClient()
        # Generate outreach for these tiers (default A only)
        self.tiers = tiers or ["A"]

    def run(self, leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Iterate over leads, generate outreach for qualifying tiers.
        Returns the full list (non-qualifying leads are unchanged).
        """
        qualifying = [l for l in leads if l.get("tier") in self.tiers]
        logger.info(
            "[outreach] %d qualifying leads (tiers=%s) out of %d total",
            len(qualifying), self.tiers, len(leads),
        )

        for i, lead in enumerate(qualifying):
            service = lead.get("recommended_service", "Digital Marketing")
            logger.info(
                "[outreach] %d/%d generating email for: %s",
                i + 1, len(qualifying), lead.get("name"),
            )
            lead["outreach_email"] = self._claude.generate_outreach(lead, service)

        # Ensure all leads have the key
        for lead in leads:
            lead.setdefault("outreach_email", None)

        return leads
