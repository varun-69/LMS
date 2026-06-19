"""
Claude API client for lead scoring and outreach email generation.

Two main capabilities:
  - score_lead(lead_data)      → structured scoring dict (0-100, tier, reasoning …)
  - generate_outreach(lead)    → personalised cold email string
"""

import json
import logging
from typing import Any

import anthropic

from config.settings import settings

logger = logging.getLogger(__name__)


# ── System prompts ────────────────────────────────────────────────────────────

_SCORER_SYSTEM_PROMPT = """You are a senior business development analyst at a boutique digital marketing
and web development agency that serves English-speaking markets (US, UK, Australia) and India.

Your leads come from two high-intent sources:
  1. "no_website" leads — real businesses found on OpenStreetMap with NO website. They are active
     (they appear in OSM map data, often have a phone number) but have zero digital presence.
  2. "intent_post" leads — Reddit posts where a founder/owner explicitly asked for a website,
     web developer, or marketing help. The 'intent_text' field contains the actual post.

Score each lead on likelihood of conversion, estimated budget, and best service fit.

When given a lead record, respond with a valid JSON object containing exactly these fields:

{
  "score": <integer 0-100>,
  "tier": "<A|B|C>",
  "reasoning": "<2-3 sentences explaining the score, referencing the specific intent signal>",
  "estimated_budget_usd_monthly": <integer or null>,
  "recommended_service": "<one of: Web Design, Web Development, SEO, PPC, Social Media Marketing, E-commerce Development, Content Marketing, Email Marketing, Full Digital Marketing, Brand Strategy>",
  "pain_points_identified": ["<pain point 1>", "<pain point 2>"],
  "outreach_hook": "<exactly 3 sentences: 1 empathy/observation referencing their specific situation, 1 value proposition, 1 low-friction CTA>"
}

Scoring rubric:
  80–100 (Tier A): Strong intent signal (active Reddit post OR OSM business with phone number),
                   contactable, clear service need, reasonable budget range.
  50–79  (Tier B): Good fit but limited contact info, smaller niche, or weaker signal.
  0–49   (Tier C): Vague signal, very small budget, spam post, or disqualifying factor.

IMPORTANT: For "intent_post" leads, read the intent_text carefully — the person described their exact
need. Reference it in the outreach_hook. For "no_website" leads, the hook should open with the fact
that you noticed they don't have a website while researching businesses in their area.

Respond ONLY with the JSON object. No markdown fences, no extra text.
"""

_OUTREACH_SYSTEM_PROMPT = """You are an expert cold-email copywriter working for a digital marketing and
web development agency. Your emails have a 40%+ open rate and generate genuine replies.

Write concise, personalised, non-spammy cold outreach emails that:
  - Have a punchy subject line (max 8 words)
  - Open with a specific observation about the prospect's business (not generic praise)
  - Clearly state ONE relevant problem you can solve for them
  - Offer concrete social proof (invent plausible but realistic case study numbers)
  - Include a simple, low-friction CTA (15-min call, not "book a demo")
  - Are under 200 words total (excluding subject line)
  - Sound like a human, not a template blast

Format your response as:
Subject: <subject line>

<email body>

Signature placeholder: [Your Name] | [Agency Name] | [Phone]
"""


class ClaudeClient:
    """
    Thin wrapper around the Anthropic SDK, providing higher-level methods
    for the lead generation pipeline.
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MODEL

    # ── Internal helper ───────────────────────────────────────────────────────

    def _chat(self, system: str, user_message: str, max_tokens: int = 1024) -> str:
        """Send a single-turn message and return the text response."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()

    # ── Public API ────────────────────────────────────────────────────────────

    def score_lead(self, lead_data: dict) -> dict:
        """
        Score a lead using Claude.

        Args:
            lead_data: A normalised lead dictionary from the scraper/enricher.

        Returns:
            A dict with keys: score, tier, reasoning, estimated_budget_usd_monthly,
            recommended_service, pain_points_identified, outreach_hook.
            On error, returns a safe fallback dict with score=0.
        """
        user_message = (
            "Please score the following business lead for our digital marketing / web dev agency.\n\n"
            f"Lead Data:\n{json.dumps(lead_data, indent=2, ensure_ascii=False)}"
        )

        try:
            raw = self._chat(
                system=_SCORER_SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=800,
            )
            # Strip accidental markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            result: dict[str, Any] = json.loads(raw)
            logger.info(
                "Scored lead '%s': %s (tier %s)",
                lead_data.get("name", "unknown"),
                result.get("score"),
                result.get("tier"),
            )
            return result

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Claude scoring response: %s", exc)
            return {
                "score": 0,
                "tier": "C",
                "reasoning": "Scoring failed due to parse error.",
                "estimated_budget_usd_monthly": None,
                "recommended_service": "Unknown",
                "pain_points_identified": [],
                "outreach_hook": "",
            }
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during scoring: %s", exc)
            return {
                "score": 0,
                "tier": "C",
                "reasoning": f"API error: {exc}",
                "estimated_budget_usd_monthly": None,
                "recommended_service": "Unknown",
                "pain_points_identified": [],
                "outreach_hook": "",
            }

    def generate_outreach(self, lead: dict, service: str) -> str:
        """
        Generate a personalised cold outreach email for a lead.

        Args:
            lead:    Enriched + scored lead dictionary.
            service: The recommended service string (e.g. "SEO", "Web Design").

        Returns:
            Full email text including subject line, body, and signature placeholder.
        """
        business_context = {
            "business_name": lead.get("name", "the business"),
            "industry": lead.get("industry", "unknown"),
            "city": lead.get("city", ""),
            "country": lead.get("country", ""),
            "website": lead.get("website", ""),
            "description": lead.get("description", ""),
            "pain_points": lead.get("pain_points_identified", []),
            "outreach_hook_seed": lead.get("outreach_hook", ""),
            "recommended_service": service,
            "employees_estimate": lead.get("employees_estimate", ""),
        }

        user_message = (
            f"Write a cold outreach email for the following prospect.\n"
            f"We are pitching: {service}\n\n"
            f"Business context:\n{json.dumps(business_context, indent=2, ensure_ascii=False)}"
        )

        try:
            email_text = self._chat(
                system=_OUTREACH_SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=600,
            )
            logger.info(
                "Generated outreach email for '%s'", lead.get("name", "unknown")
            )
            return email_text
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during outreach generation: %s", exc)
            return f"[Outreach generation failed: {exc}]"
