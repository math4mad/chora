#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title lola: status
# @raycast.mode compact
# @raycast.icon 🧭
# @raycast.packageName lola
# @raycast.description 信鸽匣概览：进/出计数 + 末条。
LOLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$LOLA_DIR/lola.py" status
