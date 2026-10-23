"""Logging configuration for Airify.

Safety: this configures standard library logging only. Secrets must NEVER be logged.
Use ``core.security.redact_secret`` before logging anything that could contain a key.
"""

from __future__ import annotations

import logging
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_CONFIGURED = False


def configure_logging(level: int = logging.INFO, fmt: str = _DEFAULT_FORMAT) -> None:
    """Configure root logging once. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(level=level, format=fmt)
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger, ensuring logging is configured.

    Reminder: never pass raw secret values to the logger. Redact first.
    """
    configure_logging()
    return logging.getLogger(name if name else "airify")
