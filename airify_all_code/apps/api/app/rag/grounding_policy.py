"""Grounding policy for RAG outputs.

Defines rules for what can and cannot be claimed without source evidence.
Prevents hallucination in future LLM-grounded outputs.

V1 rules:
- No claim without source attribution
- All mock/ungrounded outputs must be labeled
- Medical claims are NEVER allowed regardless of grounding
- PM2.5 predictions must be labeled as mock unless from validated model
"""

from __future__ import annotations

from typing import Optional


class GroundingPolicy:
    """Policy enforcement for grounded claims."""

    # Claims that require verified source evidence.
    REQUIRES_SOURCE = [
        "pm25_measurement",
        "health_effect",
        "regulatory_standard",
        "statistical_claim",
    ]

    # Claims that are NEVER allowed regardless of grounding.
    NEVER_ALLOWED = [
        "medical_diagnosis",
        "disease_prediction",
        "treatment_recommendation",
        "clinical_advice",
        "safety_guarantee",
    ]

    def can_claim(self, claim_type: str, has_source: bool = False) -> bool:
        """Check if a claim type is allowed.

        Returns False for never-allowed claims.
        Returns True for sourced claims.
        Returns False for unsourced claims that require a source.
        """
        if claim_type in self.NEVER_ALLOWED:
            return False
        if claim_type in self.REQUIRES_SOURCE:
            return has_source
        return True

    def label_output(
        self, content: str, is_grounded: bool = False, source: Optional[str] = None
    ) -> dict:
        """Label an output with grounding status."""
        return {
            "content": content,
            "is_grounded": is_grounded,
            "source": source or "none",
            "label": "grounded" if is_grounded else "ungrounded_mock",
            "disclaimer": (
                "This information is grounded in cited sources."
                if is_grounded
                else "This is ungrounded/mock information. Not verified."
            ),
        }
