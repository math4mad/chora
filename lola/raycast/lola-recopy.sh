#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title lola: recopy 最后一封
# @raycast.mode compact
# @raycast.icon 📤
# @raycast.packageName lola
# @raycast.description 把 outbox 最后一封信重新放回剪贴板 (不重复入账)，供粘进 ima。
LOLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$LOLA_DIR/lola.py" recopy
