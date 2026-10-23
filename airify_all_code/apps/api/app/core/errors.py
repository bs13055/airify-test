"""Application error types.

Centralized error hierarchy for Airify. These are used by services and API
handlers for consistent error reporting.
"""

from __future__ import annotations


class AirifyError(Exception):
    """Base exception for all Airify application errors."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigurationError(AirifyError):
    """Raised when application configuration is invalid or incomplete."""


class ProviderError(AirifyError):
    """Raised when a provider operation fails (e.g., cache miss in live mode)."""


class ValidationError(AirifyError):
    """Raised when input validation fails at the service layer."""


class NotFoundError(AirifyError):
    """Raised when a requested resource is not found."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is not available (offline/disabled)."""
