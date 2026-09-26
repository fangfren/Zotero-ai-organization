#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

find_python() {
  local candidate
  for candidate in \
    "${RESEARCH_WORKBENCH_PYTHON:-}" \
    "$ROOT/.venv/bin/python" \
    "python3" \
    "python"; do
    if [[ -n "$candidate" ]] && command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        printf '%s\n' "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON="$(find_python)" || {
  printf '%s\n' "Python 3.10 or newer was not found." >&2
  printf '%s\n' "Install Python and retry, or set RESEARCH_WORKBENCH_PYTHON." >&2
  exit 1
}

export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON" "$ROOT/sync_zotero.py" "$@"
