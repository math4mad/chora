#!/usr/bin/env bash
# CHORA — read-only fleet dashboard: where every bench stands, right now.
# Usage: bin/status.sh [-v | --publish]
#   -v        list dirty files per bench
#   --publish write docs/status.json (for the home page) and echo its path
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="${1:-}"
BENCHES=(JacobiGP MEF Sarcos PolyNN Kairos)

if [ "${V:-}" = "--publish" ]; then
  python3 - "$ROOT" <<'PY'
import subprocess, sys, os, json, datetime
root = sys.argv[1]
benches = ["JacobiGP", "MEF", "Sarcos", "PolyNN", "Kairos"]
repo_for = {"JacobiGP": "JacobiGP", "MEF": "Middle-Eigen-function",
            "Sarcos": "Sarcos-NN-Model", "PolyNN": "Polynomial-Activated-NN", "Kairos": None}
def g(d, *args):
    r = subprocess.run(["git", "-C", d, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None
cb = g(root, "rev-parse", "--short", "HEAD")
out = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "chora_head": cb, "benches": []}
for b in benches:
    d = os.path.join(root, "benches", b)
    head = g(d, "log", "-1", "--format=%h")
    if head is None:
        out["benches"].append({"name": b, "missing": True}); continue
    dirty = [l for l in g(d, "status", "--porcelain").splitlines() if ".DS_Store" not in l]
    br = g(d, "branch", "--show-current") or "main"
    remote = g(d, "remote", "get-url", "origin")
    state = "no-remote"
    if remote:
        o = g(d, "rev-parse", "--verify", "-q", f"origin/{br}")
        if not o: state = "never-pushed"
        else:
            ahead = g(d, "rev-list", "--count", f"origin/{br}..HEAD") or "?"
            state = "synced" if ahead == "0" else f"local +{ahead} unpushed"
    out["benches"].append({"name": b, "head": head, "commit_at": g(d, "log", "-1", "--format=%cI"),
        "subject": g(d, "log", "-1", "--format=%s")[:110], "dirty": len(dirty),
        "state": state, "repo": repo_for[b], "branch": br})
p = os.path.join(root, "docs", "status.json")
json.dump(out, open(p, "w"), indent=1, ensure_ascii=False)
print(os.path.relpath(p, root))
PY
  exit 0
fi

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
for b in "${BENCHES[@]}"; do
  [ -d "$ROOT/benches/$b" ] && ! git -C "$ROOT/benches/$b" remote -v 2>/dev/null | grep -q . \
    && echo "  note: $b has no remote (local-only bench)"
done; true
