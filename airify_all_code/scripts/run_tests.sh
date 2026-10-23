#!/usr/bin/env bash
# Airify test runner.
# Runs compile check, pytest, and secret scan.
# No external API calls. No live providers. No AWS.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Airify Test Runner ==="
echo ""

echo "1. Compile check..."
python3 -m compileall apps/api scripts
echo "   ✓ Compile OK"
echo ""

echo "2. Running pytest..."
python3 -m pytest -q
echo "   ✓ Tests passed"
echo ""

echo "3. Secret scan..."
python3 scripts/check_no_secrets.py
echo ""

echo "=== All checks passed ==="
