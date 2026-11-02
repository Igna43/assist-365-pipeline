#!/usr/bin/env bash
# Launcher for the read-only BigQuery MCP server. Prefers the project venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" "$ROOT/mcp_bigquery/server.py"
fi
exec python3 "$ROOT/mcp_bigquery/server.py"
