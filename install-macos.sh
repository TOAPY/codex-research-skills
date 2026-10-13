#!/usr/bin/env bash
set -euo pipefail
# Also works on Linux for repository-level Cloud preparation.
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${RESEARCH_SKILLS_PYTHON:-python3}"
command -v "$PYTHON_BIN" >/dev/null || { echo 'Python 3.9+ is required.' >&2; exit 1; }
# Standalone bootstrap: ./install-macos.sh --bootstrap URL [CLONE_DIR]
if [ "${1:-}" = '--bootstrap' ]; then
  [ "$#" -ge 2 ] || { echo 'Usage: --bootstrap URL [CLONE_DIR]' >&2; exit 1; }
  REPO_URL="$2"
  CLONE_DIR="${3:-$HOME/Documents/Codex/codex-research-skills}"
  if [ ! -e "$CLONE_DIR" ]; then
    git clone -- "$REPO_URL" "$CLONE_DIR"
  fi
  exec "$PYTHON_BIN" "$CLONE_DIR/scripts/manage.py" sync --repo "$CLONE_DIR" --remote-url "$REPO_URL"
fi
exec "$PYTHON_BIN" "$SCRIPT_ROOT/scripts/manage.py" sync --repo "$SCRIPT_ROOT" "$@"
