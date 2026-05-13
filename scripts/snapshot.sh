#!/usr/bin/env bash
# Capture fresh rendered HTML for every route from the live Clarion sandbox.
# Requires `agent-browser` on PATH (https://media.zocomputer.com/install/agentbrowser2.sh)
# or any headless Chromium capable of dumping post-hydration DOM.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/snapshots-raw"
BASE="${CLARION_SOURCE_BASE:-https://cis.zo.space}"

mkdir -p "$RAW"

ROUTES=(iren onon ttd deck meta msft googl ffiv ibm sp500)

for r in "${ROUTES[@]}"; do
  echo "→ rendering $BASE/$r"
  agent-browser open "$BASE/$r" >/dev/null
  sleep 4
  agent-browser get html "html" > "$RAW/$r.html"
  echo "  saved $(wc -c < "$RAW/$r.html") bytes"
done

echo "Done. Now run: python3 scripts/build.py"
