"""Security helpers for Airify.

Provides secret redaction and a lightweight heuristic to detect obvious secret-like
strings in project files. These helpers exist to enforce the Airify rule that real API
keys must never be committed, logged, printed, copied, stored in docs, or inserted in
tests.

NOTE: detection here is a best-effort guardrail, not a cryptographic guarantee.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

REDACTED = "SECRET_REDACTED"

# Known-safe placeholder tokens that are allowed to appear in the repo.
ALLOWED_PLACEHOLDERS = {
    "REPLACE_WITH_REAL_KEY_OUTSIDE_REPO",
    "your-api-key",
    "changeme",
    "xxx",
}

# Heuristics for "real-looking" secrets.
# - OpenWeatherMap keys are 32-char lowercase hex strings.
_OWM_HEX_KEY = re.compile(r"\b[0-9a-f]{32}\b")
# - Generic long high-entropy-ish token (letters+digits, length >= 32).
#   Underscores/hyphens are NOT allowed so ordinary snake_case identifiers and dotted
#   import paths are not misflagged; a real key is a single contiguous alphanumeric run.
_GENERIC_LONG_TOKEN = re.compile(r"\b(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{32,}\b")


def redact_secret(value: object) -> str:
    """Return a redacted placeholder regardless of input.

    Always returns ``SECRET_REDACTED`` so the real value can never be printed/logged.
    """
    return REDACTED


def is_placeholder(value: str) -> bool:
    """True if the value is a recognized safe placeholder (not a real secret)."""
    v = (value or "").strip()
    if not v:
        return True
    return v in ALLOWED_PLACEHOLDERS


def looks_like_secret(value: str) -> bool:
    """Heuristic: does this string look like a real secret/API key?

    Placeholders and empty values are NOT considered secrets.
    """
    v = (value or "").strip()
    if not v or is_placeholder(v):
        return False
    if _OWM_HEX_KEY.search(v):
        return True
    if _GENERIC_LONG_TOKEN.search(v):
        return True
    return False


def find_secret_like_strings(text: str) -> List[str]:
    """Return distinct secret-like substrings found in ``text`` (placeholders excluded)."""
    found: List[str] = []
    for match in set(_OWM_HEX_KEY.findall(text)) | set(_GENERIC_LONG_TOKEN.findall(text)):
        if not is_placeholder(match):
            found.append(match)
    return sorted(found)


def scan_paths_for_secrets(
    paths: Iterable[Path],
    *,
    skip_names: Iterable[str] = (".env.example",),
) -> dict[str, List[str]]:
    """Scan files for secret-like strings.

    Returns a mapping of ``{file_path: [secret_like, ...]}`` for any offending files.
    ``.env.example`` is skipped by default because it intentionally holds placeholders.
    The real values themselves are never returned to logs by callers; treat the keys
    (file paths) as the actionable signal.
    """
    skip = set(skip_names)
    offenders: dict[str, List[str]] = {}
    for path in paths:
        if path.name in skip or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = find_secret_like_strings(text)
        if hits:
            offenders[str(path)] = hits
    return offenders
