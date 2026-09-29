#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title lola: pull (对岸 → 本地)
# @raycast.mode compact
# @raycast.icon 🕊️
# @raycast.packageName lola
# @raycast.description 把剪贴板里的 ima 回信折入信鸽匣 (inbox + LEDGER)。先在 ima 里 Cmd+C。
LOLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$LOLA_DIR/lola.py" pull
