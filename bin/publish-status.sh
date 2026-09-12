#!/usr/bin/env bash
# CHORA — publish the fleet snapshot AND the exp/dev board: regenerate docs/status.json and
# docs/kanban.{md,json}, commit+push ONLY those paths, and ONLY when a real field moved. The two
# provenance lines ("generated", "chora_head") are ignored by design: chora_head moves because
# the snapshot commits, so honouring it would make the publisher commit
# forever (the ping-pong this script's guard exists to break). The board's own
# "Generated " stamp line is ignored on the same reasoning: it moves because the beat
# commits, and everything else in kanban.md/json is derived, so a real lane change
# always lands on a non-ignored line.
# Invoked by bin/sync.sh and by the launchd agent com.chora.fleet-status.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -L "$ROOT/docs/status.json" ] || [ -d "$ROOT/docs/status.json" ]; then
  echo "[publish] docs/status.json is not a regular file — refusing"; exit 1
fi
cd "$ROOT"

# --- D1 (docs/glass-freeze-mechanism-2026-09-12.md): refuse to run while a ---
# --- sequencer (rebase/merge/cherry-pick) owns the branch, or while HEAD is ---
# --- detached. On 2026-09-12 a human rebase with a conflicted manifest froze ---
# --- the glass for six hours: each beat committed its snapshot onto the ---
# --- detached rebase HEAD, pushed `origin ""` (empty branch name), blamed the ---
# --- network, and then truthfully printed "no real drift" forever because the ---
# --- drift guard was reading its own orphan. ~49 commits contained by no ---
# --- branch, and the unstaged churn blocked `git rebase --continue` — i.e. the ---
# --- publisher was not a bystander to the stuck rebase, it was what kept it ---
# --- stuck. The publisher is a servant of the record, never a co-writer of the ---
# --- index. Standing down is not an error: exit 0, say why, next beat retries.
for st in rebase-merge rebase-apply CHERRY_PICK_HEAD REVERT_HEAD MERGE_HEAD; do
  if [ -e ".git/$st" ]; then
    echo "[publish] sequencer state present (.git/$st) — standing down, index is not mine"
    exit 0
  fi
done
if ! BR="$(git symbolic-ref --quiet --short HEAD)" || [ -z "${BR:-}" ]; then
  echo "[publish] HEAD is detached — standing down (a snapshot into no branch is an orphan)"
  exit 0
fi
bash "$ROOT/bin/status.sh" --publish >/dev/null
# --- the exp/dev board rides the same beat: lanes are derived from the record, so a board
# --- that is not regenerated is a board that is silently wrong (the glass proved that today).
# --- stdlib-only python; a render failure must never take the glass down with it.
if [ -f "$ROOT/bin/kanban.py" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/bin/kanban.py" --write >/dev/null 2>&1 \
    || echo "[publish] kanban render failed (registry unreadable?) — glass continues, board is stale"
fi
for f in docs/kanban.md docs/kanban.json docs/status.json; do
  if [ -L "$ROOT/$f" ] || [ -d "$ROOT/$f" ]; then
    echo "[publish] $f is not a regular file — refusing"; exit 1
  fi
done
if git diff --quiet -I '.*"generated".*' -I '.*"chora_head".*' -I '^Generated ' -- docs/status.json docs/kanban.json docs/kanban.md; then
  echo "[publish] no real drift — snapshot stays committed"
  exit 0
fi
git commit -q -m "status snapshot (auto: publish-status)" -- docs/status.json docs/kanban.json docs/kanban.md \
  && { git push -q origin "refs/heads/$BR" 2>/dev/null \
        && echo "[publish] snapshot pushed ($BR)" \
        || echo "[publish] committed, push of refs/heads/$BR failed (offline, or $BR is not ahead of origin/$BR) — will retry next beat"; } \
  || { echo "[publish] commit failed (index busy?) — next beat retries"; exit 1; }
