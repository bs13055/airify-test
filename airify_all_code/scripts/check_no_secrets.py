#!/usr/bin/env python3
"""Scan project files for accidentally committed secrets.

This script searches for real-looking secret values (high-entropy tokens,
32-char hex keys, etc.) in the codebase. Placeholders are allowed.

SAFETY: If secrets are found, only the file path and finding type are printed
— the actual secret value is never printed.

Exit codes:
  0 — no secrets found
  1 — secret-like values detected (see output for file paths)
"""

from __future__ import annotations

import sys
from pathlib import Path

# This script lives at airify_all_code/scripts/. CODE_ROOT = airify_all_code;
# PROJECT_ROOT = the Airify repo root (scanned for full coverage: docs + code).
CODE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = CODE_ROOT.parent
# Reuse the security module from the API package.
sys.path.insert(0, str(CODE_ROOT / "apps" / "api"))

from app.core.security import scan_paths_for_secrets  # noqa: E402


SCAN_EXTENSIONS = {".py", ".toml", ".yml", ".yaml", ".json", ".md", ".txt", ".cfg", ".ini", ".sh"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".egg-info"}
SKIP_FILES = {"package-lock.json"}


def collect_files(root: Path) -> list[Path]:
    """Collect project files to scan."""
    files: list[Path] = []
    for path in root.rglob("*"):
        # Skip hidden/generated directories.
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SCAN_EXTENSIONS:
            files.append(path)
    return files


def main() -> int:
    print(f"Scanning for secrets in: {PROJECT_ROOT}")
    files = collect_files(PROJECT_ROOT)
    print(f"  Files to scan: {len(files)}")

    offenders = scan_paths_for_secrets(files, skip_names=SKIP_FILES | {".env.example"})

    if not offenders:
        print("  ✓ No secret-like values found.")
        return 0

    print(f"  ✗ Secret-like values found in {len(offenders)} file(s):")
    for filepath, findings in sorted(offenders.items()):
        # Print file path and count only — NEVER print the actual secret.
        print(f"    {filepath} — {len(findings)} finding(s)")

    return 1


if __name__ == "__main__":
    sys.exit(main())
