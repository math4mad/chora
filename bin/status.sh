#!/usr/bin/env bash
# CHORA — read-only fleet dashboard: where every bench stands, right now.
# Usage: bin/status.sh   (add -v to list dirty files per bench)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="${1:-}"
BENCHES=(JacobiGP MEF Sarcos PolyNN Kairos)

printf '%-9s %-8s %-7s %-22s %s\n' "BENCH" "HEAD" "AGE" "BRANCH/DIRTY" "LAST WORD"
printf '%s\n' "---------------------------------------------------------------------------------"
for b in "${BENCHES[@]}"; do
  d="$ROOT/benches/$b"
  if ! git -C "$d" rev-parse -q --git-dir >/dev/null 2>&1; then
    printf '%-9s %s\n' "$b" "MISSING — run bin/sync.sh"; continue
  fi
  sha=$(git -C "$d" log -1 --format=%h)
  age=$(git -C "$d" log -1 --format=%cr)
  n=$( { git -C "$d" status --porcelain | grep -v '\.DS_Store' || true; } | wc -l | tr -d ' ')
  dirty=$([ "$n" = "0" ] && echo clean || echo "⚠ $n uncommitted")
  last=$(git -C "$d" log -1 --format=%s | cut -c1-60)
  printf '%-9s %-8s %-7s %-22s %s\n' "$b" "$sha" "$age" "$dirty" "$last"
  [ "$V" = "-v" ] && [ "$n" != "0" ] && git -C "$d" status --porcelain | grep -v '\.DS_Store' | sed 's/^/            /'
done

echo
echo "registered predictions awaiting verdict:"
[ -d "$ROOT/meetings" ] && grep -rl "candidate\|H6c\|H9" "$ROOT"/meetings/*.md 2>/dev/null | tail -3 | sed 's/^/  meeting: /'
echo "letters newest-first:"
ls -t "$ROOT"/letters/*.md 2>/dev/null | grep -v INDEX | head -3 | xargs -n1 basename | sed 's/^/  /'
echo "artifacts manifests:"
for m in "$ROOT"/artifacts/*/manifest.json "$ROOT"/artifacts/*/*/manifest.json; do
  [ -f "$m" ] && printf '  %-46s %s files\n' "${m#$ROOT/}" "$(python3 -c "import json;print(len(json.load(open('$m'))['files']))" 2>/dev/null || echo ?)"
done
[ -L "$ROOT/benches/Kairos" ] && ! git -C "$ROOT/benches/Kairos" remote -v | grep -q . && echo "  note: Kairos has no remote (local-only bench)"
