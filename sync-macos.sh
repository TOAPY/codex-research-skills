#!/usr/bin/env bash
set -euo pipefail
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${RESEARCH_SKILLS_PYTHON:-python3}"
exec "$PYTHON_BIN" "$SCRIPT_ROOT/scripts/manage.py" sync --repo "$SCRIPT_ROOT" "$@"
