"""Safety tests: no real secrets in the repo; .env.example present; .env absent."""

from __future__ import annotations

from pathlib import Path

from app.core.security import (
    REDACTED,
    find_secret_like_strings,
    is_placeholder,
    looks_like_secret,
    redact_secret,
    scan_paths_for_secrets,
)


# Build a fake, real-LOOKING 32-char hex key at runtime so the literal never appears in
# any source file (keeps the repo-wide secret scan clean while still exercising detection).
_FAKE_HEX_KEY = ("abcdef0123" * 3) + "ab"  # 32 chars, clearly fake


def test_redact_secret_always_returns_placeholder():
    assert redact_secret(_FAKE_HEX_KEY) == REDACTED
    assert redact_secret(None) == REDACTED


def test_placeholder_allowed_but_real_looking_key_rejected():
    # The shipped placeholder is allowed.
    assert is_placeholder("REPLACE_WITH_REAL_KEY_OUTSIDE_REPO") is True
    assert looks_like_secret("REPLACE_WITH_REAL_KEY_OUTSIDE_REPO") is False
    # A real-looking 32-char hex OWM key is rejected (flagged as secret-like).
    assert looks_like_secret(_FAKE_HEX_KEY) is True
    assert find_secret_like_strings("key=" + _FAKE_HEX_KEY)


def test_env_example_exists_and_has_placeholders_only(repo_root: Path):
    env_example = repo_root / ".env.example"
    assert env_example.is_file(), ".env.example must exist"
    text = env_example.read_text(encoding="utf-8")
    assert "REPLACE_WITH_REAL_KEY_OUTSIDE_REPO" in text
    # The example itself must not contain real secret-like values.
    assert find_secret_like_strings(text) == []


def test_dotenv_does_not_exist(repo_root: Path):
    assert not (repo_root / ".env").exists(), ".env must NOT be committed"


def test_no_real_secret_like_value_in_created_files(repo_root: Path):
    """Scan created source/config files for real-looking secrets (placeholders excluded)."""
    candidates = []
    backend = repo_root / "apps" / "api"
    candidates.extend(backend.rglob("*.py"))
    for name in (".env.example", ".gitignore", "pyproject.toml", "README.md"):
        p = repo_root / name
        if p.is_file():
            candidates.append(p)

    offenders = scan_paths_for_secrets(candidates)
    assert offenders == {}, f"Secret-like strings found in: {list(offenders)}"
