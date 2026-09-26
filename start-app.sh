#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5187}"
URL="http://${HOST}:${PORT}"

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

server_is_ready() {
  "$PYTHON" -c 'import socket, sys; s = socket.create_connection((sys.argv[1], int(sys.argv[2])), 0.5); s.close()' \
    "$HOST" "$PORT" >/dev/null 2>&1
}

open_browser() {
  if command -v open >/dev/null 2>&1; then
    open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1
  elif command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "$URL"
  else
    printf 'Open %s in a browser.\n' "$URL"
  fi
}

PYTHON="$(find_python)" || {
  printf '%s\n' "Python 3.10 or newer was not found." >&2
  printf '%s\n' "Install Python and retry, or set RESEARCH_WORKBENCH_PYTHON." >&2
  exit 1
}

export PYTHONDONTWRITEBYTECODE=1

if server_is_ready; then
  printf 'Research Workbench is already running at %s\n' "$URL"
  open_browser
  exit 0
fi

"$PYTHON" "$ROOT/app_server.py" --host "$HOST" --port "$PORT" &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup INT TERM

for ((attempt = 0; attempt < 80; attempt++)); do
  if server_is_ready; then
    open_browser
    wait "$SERVER_PID"
    exit $?
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    wait "$SERVER_PID"
    exit $?
  fi
  sleep 0.25
done

printf 'The workbench server did not start on %s:%s within 20 seconds.\n' "$HOST" "$PORT" >&2
cleanup
wait "$SERVER_PID" >/dev/null 2>&1 || true
exit 1
