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
if git diff --quiet -I '.*"generated".*' -I '.*"chora_head".*' -- docs/status.json; then
  echo "[publish] no real drift — snapshot stays committed"
  exit 0
fi
git commit -q -m "status snapshot (auto: publish-status)" -- docs/status.json \
  && { git push -q origin "refs/heads/$BR" 2>/dev/null \
        && echo "[publish] snapshot pushed ($BR)" \
        || echo "[publish] committed, push of refs/heads/$BR failed (offline, or $BR is not ahead of origin/$BR) — will retry next beat"; } \
  || { echo "[publish] commit failed (index busy?) — next beat retries"; exit 1; }
