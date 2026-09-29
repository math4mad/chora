#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title lola: push (本地 → 对岸)
# @raycast.mode compact
# @raycast.icon ✍️
# @raycast.packageName lola
# @raycast.argument1 { "type": "text", "placeholder": "给对岸的话" }
# @raycast.description 写一封信进 outbox 并置剪贴板 (粘进 ima)。
LOLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$LOLA_DIR/lola.py" push "$1"
