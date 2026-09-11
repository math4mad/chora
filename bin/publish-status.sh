#!/usr/bin/env bash
# CHORA — publish the fleet snapshot: regenerate docs/status.json, commit+push
# ONLY that path, and ONLY when a real field moved. The two provenance lines
# ("generated", "chora_head") are ignored by design: chora_head moves because
# the snapshot commits, so honouring it would make the publisher commit
# forever (the ping-pong this script's guard exists to break).
# Invoked by bin/sync.sh and by the launchd agent com.chora.fleet-status.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -L "$ROOT/docs/status.json" ] || [ -d "$ROOT/docs/status.json" ]; then
  echo "[publish] docs/status.json is not a regular file — refusing"; exit 1
fi
bash "$ROOT/bin/status.sh" --publish >/dev/null
cd "$ROOT"
if git diff --quiet -I '.*"generated".*' -I '.*"chora_head".*' -- docs/status.json; then
  echo "[publish] no real drift — snapshot stays committed"
  exit 0
fi
git commit -q -m "status snapshot (auto: publish-status)" -- docs/status.json \
  && { git push -q origin "$(git branch --show-current)" 2>/dev/null \
        && echo "[publish] snapshot pushed" \
        || echo "[publish] committed, push failed (network?) — will retry next beat"; } \
  || { echo "[publish] commit failed (index busy?) — next beat retries"; exit 1; }
