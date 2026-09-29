#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title lola: log
# @raycast.mode fullOutput
# @raycast.icon 📜
# @raycast.packageName lola
# @raycast.description 信鸽匣台账尾 15 行。
LOLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$LOLA_DIR/lola.py" log 15
