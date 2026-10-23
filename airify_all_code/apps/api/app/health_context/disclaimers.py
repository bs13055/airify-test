"""Health disclaimers for Airify.

All health-related outputs MUST include appropriate disclaimers.
This module provides standard disclaimer text for the platform.

NOT medical advice. NOT clinical decision support.
"""

from __future__ import annotations


# Standard disclaimers for different contexts.
GENERAL_DISCLAIMER = (
    "This is general environmental guidance, not medical advice. "
    "Airify does not diagnose, treat, or prevent any disease. "
    "Consult a qualified healthcare professional for medical concerns."
)

ESTIMATE_DISCLAIMER = (
    "This PM2.5 estimate uses mock data for demonstration purposes only. "
    "It does not reflect actual air quality measurements. "
    "Do not make health decisions based on this information."
)

RECOMMENDATION_DISCLAIMER = (
    "Action suggestions are general environmental guidance only. "
    "They are not personalized medical recommendations. "
    "Individual health responses to air quality vary. "
    "Consult a healthcare professional for personal health advice."
)

FEEDBACK_DISCLAIMER = (
    "Feedback is collected for product improvement only. "
    "No personal health information is stored. "
    "This platform does not provide medical consultations."
)

PWA_DISCLAIMER = (
    "Installing this app does not make it a validated medical device. "
    "This is a demonstration platform for environmental awareness only."
)


def get_disclaimer(context: str = "general") -> str:
    """Get the appropriate disclaimer for a given context.

    Args:
        context: One of 'general', 'estimate', 'recommendation', 'feedback', 'pwa'.

    Returns:
        Disclaimer text string.
    """
    disclaimers = {
        "general": GENERAL_DISCLAIMER,
        "estimate": ESTIMATE_DISCLAIMER,
        "recommendation": RECOMMENDATION_DISCLAIMER,
        "feedback": FEEDBACK_DISCLAIMER,
        "pwa": PWA_DISCLAIMER,
    }
    return disclaimers.get(context, GENERAL_DISCLAIMER)


def must_include_disclaimer(output: dict) -> dict:
    """Ensure any health-context output includes a disclaimer field."""
    if "disclaimer" not in output:
        output["disclaimer"] = GENERAL_DISCLAIMER
    return output
