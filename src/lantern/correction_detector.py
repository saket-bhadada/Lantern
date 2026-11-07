"""Lantern – correction detector using structured LLM output (Phase 4)."""

from __future__ import annotations

import json

from lantern.log import get_logger
from lantern.models import CorrectionDetection, Msg
from lantern.router import BrainRouter

log = get_logger("correction_detector")

CORRECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_correction": {
            "type": "boolean",
            "description": "True if the user message is correcting a previous statement or stating a project/team policy rule to follow.",
        },
        "proposed_rule": {
            "type": "string",
            "maxLength": 200,
            "description": "A concise, single-sentence imperative rule summarizing the correction (<=200 chars). Empty if not a correction.",
        },
        "scope": {
            "type": "string",
            "enum": ["global", "channel"],
            "description": "Scope of the rule.",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score between 0.0 and 1.0.",
        },
    },
    "required": ["is_correction", "proposed_rule", "scope", "confidence"],
    "additionalProperties": False,
}

DETECTOR_SYSTEM_PROMPT = """You are a correction detector for an AI teammate named Lantern.
Analyze the user message to determine if the user is giving a direct correction or establishing a team rule/guideline (e.g. "No, our staging server is on port 9000", "Never tag everyone on weekends", "Actually, we use Python 3.11 here").

If it is a correction or rule:
- is_correction: true
- proposed_rule: concise one-line rule stating what to do or avoid (max 200 characters)
- scope: "global" or "channel"
- confidence: 0.0 to 1.0

If it is just a normal question, conversation, or greeting:
- is_correction: false
- proposed_rule: ""
- scope: "global"
- confidence: 0.0

Output valid JSON adhering to the schema."""


class CorrectionDetector:
    """Uses LLM structured output to identify corrections and propose rules."""

    def __init__(self, router: BrainRouter) -> None:
        self._router = router

    async def detect(self, text: str) -> CorrectionDetection:
        messages = [
            Msg(role="system", content=DETECTOR_SYSTEM_PROMPT),
            Msg(role="user", content=text),
        ]
        try:
            comp = await self._router.complete(
                messages,
                schema=CORRECTION_SCHEMA,
                prefer_cloud=False,  # Can run locally or cloud
            )
            raw_text = comp.text.strip()
            # Handle potential markdown wrappers
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            data = json.loads(raw_text)
            return CorrectionDetection.model_validate(data)
        except Exception as exc:
            log.debug("Correction detection failed/skipped: %s", exc)
            return CorrectionDetection(is_correction=False, proposed_rule="", confidence=0.0)
