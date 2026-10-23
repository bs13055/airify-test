"""Consent text for Airify V1 demo.

Generic consent for local demonstration use. NOT a legal document.
Future production use requires proper legal review.

V1: consent is informational only. No binding agreement is formed.
"""

from __future__ import annotations


DEMO_CONSENT_TEXT = """
Airify Platform V1 — Demo Consent Notice

By using this demo platform, you acknowledge that:

1. This is a DEMONSTRATION platform using mock data only.
2. No real PM2.5 measurements are provided.
3. This is NOT medical advice, diagnosis, or treatment.
4. Action suggestions are general environmental guidance only.
5. This demo does not ask for your name, email, or phone number; PII-like
   payload keys are stripped before local storage.
6. An anonymous session ID is stored locally in your browser.
7. Approximate location (rounded to ~100m) may be stored locally for analytics.
8. Feedback you provide is stored locally for product improvement only. Please
   do not enter personal, address, or medical information — free-text feedback
   may still contain whatever you choose to type.
9. You may clear all local data by clearing your browser storage.

This platform does not:
- Diagnose any condition
- Provide personalized medical recommendations
- Guarantee accuracy of any air quality information
- Ask you for personally identifiable information (free-text feedback may still
  contain what you choose to type)
- Share data with third parties

This is not a privacy compliance claim.

For actual health concerns related to air quality, consult a qualified
healthcare professional.

This consent notice is for demonstration purposes only and does not
constitute a legally binding agreement. Future production deployment
requires proper legal and privacy review.
""".strip()


def get_demo_consent_text() -> str:
    """Return the demo consent text."""
    return DEMO_CONSENT_TEXT


def consent_includes_key_points(text: str) -> bool:
    """Verify consent text includes required key points."""
    required = [
        "not medical advice",
        "mock data",
        "demonstration",
        "does not ask for your name, email, or phone",
        "anonymous",
    ]
    text_lower = text.lower()
    return all(point in text_lower for point in required)
