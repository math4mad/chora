#!/usr/bin/env bash
# CHORA — advisory writer lock for a shared clone.
#
# Why: law 3 ("single writer, many readers") holds per REPOSITORY, not per person. On 2026-09-12 two
# agents worked the same checkout at the same time and it broke a pin without either of them meaning
# to: a manifest entry was taken from the working tree (f0dd985f…, 48,858 B) while the commit carried
# the file's previous version — a pin true of the checkout, false of the repository (chora@f79d588).
# Nothing about that was a merge conflict; git cannot see it, because the collision was between two
# hands' *sequences* of add/commit, not their file bytes.
#
# This is advisory, and it says so: it will not stop a session that ignores it, it will make
# ignoring it VISIBLE (holder, time, ttl, and the fact that it was stolen are all in the lock file and
# in the publisher's log). The publisher beat refuses to commit while a live lock is held — the same
# standing-down rule that ended the six-hour glass freeze (D1).
#
# Usage:
#   bin/writelock.sh status
#   bin/writelock.sh acquire "<bench or session>" [--ttl 3600]
#   bin/writelock.sh renew
#   bin/writelock.sh release
#   bin/writelock.sh take "<bench or session>" --because "<why the holder must step down>"
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
GITDIR="$(git rev-parse --git-dir 2>/dev/null || echo .git)"   # --git-dir, not --gitdir: the first test of this file caught itself
LOCK="$GITDIR/chora-writer.lock"

now=$(date +%s)
live() {  # 0 = held and not stale
  [ -f "$LOCK" ] || return 1
  local exp; exp=$(awk -F= '/^expires=/{print $2}' "$LOCK")
  [ "${exp:-0}" -gt "$now" ]
}
show() { [ -f "$LOCK" ] && { echo "  lock: $LOCK"; sed 's/^/  | /' "$LOCK"; } || echo "  no lock file"; }

case "${1:-status}" in
  status)
    if [ ! -f "$LOCK" ]; then echo "[lock] free"; exit 0; fi
    if live; then echo "[lock] HELD:"; show; exit 0
    else echo "[lock] STALE (ttl elapsed), holder was:"; show; exit 0; fi ;;

  acquire)
    who="${2:?acquire <who>}"; ttl="${4:-3600}"
    if live && ! grep -q "^holder=$who\$" "$LOCK"; then
      echo "[lock] refused — held by another hand:"; show
      echo "[lock] use 'take \"\" --because' only when the holder must step down; stealing is logged"; exit 2; fi
    printf 'holder=%s\nacquired=%s\nexpires=%s\nttl=%s\nsession=%s\npid=%s\n' \
      "$who" "$now" "$((now+ttl))" "$ttl" "${PI_SESSION_ID:-unset}" "$$" > "$LOCK"
    echo "[lock] held by $who for ${ttl}s"; exit 0 ;;

  renew)
    [ -f "$LOCK" ] || { echo "[lock] nothing to renew"; exit 1; }
    who=$(awk -F= '/^holder=/{print $2}' "$LOCK"); ttl=$(awk -F= '/^ttl=/{print $2}' "$LOCK")
    printf 'holder=%s\nacquired=%s\nexpires=%s\nttl=%s\nrenewed=%s\nsession=%s\npid=%s\n' \
      "$who" "$now" "$((now+ttl))" "$ttl" "$now" "${PI_SESSION_ID:-unset}" "$$" > "$LOCK"
    echo "[lock] renewed for $who"; exit 0 ;;

  release)
    [ -f "$LOCK" ] && { who=$(awk -F= '/^holder=/{print $2}' "$LOCK"); rm -f "$LOCK"; echo "[lock] released (was $who)"; } \
      || echo "[lock] nothing held"; exit 0 ;;

  take)
    who="${2:?take <who> --because \"<why>\"}"; why="${4:-unstated}"
    if live; then echo "[lock] STEALING a live lock. Previous holder:"; show
      echo "[lock] reason recorded in this line and in the new lock file:"; echo "        $why"; fi
    ttl=3600
    printf 'holder=%s\nacquired=%s\nexpires=%s\nttl=%s\nstole_from=%s\nbecause=%s\nsession=%s\npid=%s\n' \
      "$who" "$now" "$((now+ttl))" "$ttl" "$(awk -F= '/^holder=/{print $2}' "$LOCK" 2>/dev/null || echo none)" "$why" \
      "${PI_SESSION_ID:-unset}" "$$" > "$LOCK"
    echo "[lock] now held by $who"; exit 0 ;;

  *) echo "usage: writelock.sh {status|acquire <who> [--ttl N]|renew|release|take <who> --because \"…\"}"; exit 64 ;;
esac
