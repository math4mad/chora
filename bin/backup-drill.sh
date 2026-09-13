#!/usr/bin/env bash
# CHORA — take a real backup on machine A, then DRILL it.
# Why this file exists: as of 2026-09-13 ~11:20, A had NO _rollback directory at all. Both
# 2026-09-12 parachutes (pause-...-b at 08:24, checkpoint-...-eve at 15:3x) were minted on B and
# live only there, and every byte written since — H6c's fit, the H6a pilot's 36 runs, H9-M's three
# registered grids and their checkpoints — sits on one laptop with no offline copy at all.
# The lesson from B's own drill, applied rather than repeated: a bundle nobody restored is a story,
# and `git clone <bundle>` is NOT a restore (it drops every origin ref that isn't the checked-out
# HEAD, and dropped tips die under reflog expire + gc --prune). So the drill below uses the corrected
# recipe: init → remote add → fetch with three refspecs → then compare HEAD against the tag.
set -uo pipefail
ROOT=/Users/mac/Programming/code-2026
STAMP=2026-09-13-A
DEST="$ROOT/_rollback/$STAMP"
DRILL=/tmp/chora-drill-$STAMP
mkdir -p "$DEST"
rm -rf "$DRILL"; mkdir -p "$DRILL"

repos=(chora " JacobiGP" Middle-Eigen-function Sarcos-NN-Model "Polynomial-Activated NN " Kairos)

echo "══════════ 1 · tags ══════════"
for r in "${repos[@]}"; do
  n=$(echo "$r" | xargs)
  git -C "$ROOT/$r" tag -a "checkpoint-$STAMP" -m "offline restore point, machine A, $(date -u +%FT%TZ): HEAD + the untracked byte stores backed up beside these bundles" 2>/dev/null \
    && echo "  tagged  $n → checkpoint-$STAMP" || echo "  kept    $n → tag exists ($(git -C "$ROOT/$r" rev-parse --short "checkpoint-$STAMP" 2>/dev/null))"
done

echo "══════════ 2 · bundles (--all: every ref, every tag) ══════════"
for r in "${repos[@]}"; do
  n=$(echo "$r" | xargs)
  sn=$(printf '%s' "$n" | tr ' ' '.')      # GitHub rewrites spaces in asset names to dots; match the
                                           # local name to the remote one instead of teaching every
                                           # later tool to normalise (the first PolyNN upload was lost
                                           # exactly that way: a FAILED line and then a renamed asset)
  git -C "$ROOT/$r" bundle create "$DEST/$sn.bundle" --all >/dev/null 2>&1 \
    && printf "  %-26s %s\n" "$sn" "$(du -h "$DEST/$sn.bundle" | cut -f1)" || echo "  FAILED $n"
done

echo "══════════ 3 · the bytes that live in no git anywhere ══════════"
# models/ and data/ are deliberately NOT tarred: law 1 reconstructs them from manifest entries by
# URL+hash, and they are 7.1 GB. Everything here is the opposite case — produced by a run, not
# fetchable, and reproducible only by a claim ("from seed") that today has already been shown false
# for one rank-1 code path.
declare -a stores=(
  "Middle-Eigen-function/outputs|mef-outputs"
  "Sarcos-NN-Model/results|sarcos-results"
  "Polynomial-Activated NN /results|polynn-results"
  " JacobiGP/results|jacobigp-results"
)
for s in "${stores[@]}"; do
  src="${s%%|*}"; name="${s##*|}"
  if [ -d "$ROOT/$src" ]; then
    ( cd "$ROOT" && tar -czf "$DEST/$name.tar.gz" "$src" ) \
      && printf "  %-26s %s\n" "$name" "$(du -h "$DEST/$name.tar.gz" | cut -f1)"
  fi
done
git -C "$ROOT/chora" rev-parse HEAD > "$DEST/heads.txt"
for r in "${repos[@]}"; do n=$(echo "$r" | xargs); printf "%-26s %s %s\n" "$n" "$(git -C "$ROOT/$r" rev-parse HEAD)" "$(git -C "$ROOT/$r" status --porcelain | wc -l | tr -d ' ') dirty-paths" >> "$DEST/heads.txt"; done
# what a bundle does NOT capture: uncommitted work. Named, not hidden.
: > "$DEST/uncommitted.txt"
# BUG FOUND BY READING THE OUTPUT, not by running it: my first version piped `git status --porcelain`
# into `sed` and appended BOTH the upstream redirect and the pipe's output, so the shell opened the
# file, wrote nothing, and the file came out at 172 bytes of nothing — a manifest of gaps listing no
# gaps. A backup tool's honesty file must be the first thing you distrust. Fixed with a plain loop.
: > "$DEST/uncommitted.txt"
for r in "${repos[@]}"; do
  n=$(echo "$r" | xargs)
  while IFS= read -r line; do printf '%-24s %s\n' "$n" "$line" >> "$DEST/uncommitted.txt"; done \
      < <(git -C "$ROOT/$r" status --porcelain 2>/dev/null)
done
( cd "$DEST" && shasum -a 256 *.bundle *.tar.gz heads.txt uncommitted.txt > SHA256SUMS )
echo "  manifest: $(grep -c . "$DEST/SHA256SUMS") files hashed"

echo "══════════ 4 · verify the copies ══════════"
( cd "$DEST" && shasum -a 256 -c SHA256SUMS --status && echo "  SHA256SUMS: all OK" || echo "  SHA256SUMS: MISMATCH" )

echo "══════════ 5 · DRILL: restore each repo with the corrected recipe ══════════"
fail=0
for r in "${repos[@]}"; do
  n=$(echo "$r" | xargs)
  d="$DRILL/$n"; mkdir -p "$d"; 
  ( cd "$d" && git init -q r && cd r \
      && git remote add origin "$DEST/$n.bundle" \
      && git fetch -q origin '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*' '+HEAD:refs/remotes/origin/HEAD' \
      && git checkout -q -B drill "checkpoint-$STAMP" 2>/dev/null )
  got=$(git -C "$DRILL/$n/r" rev-parse HEAD 2>/dev/null)
  want=$(git -C "$ROOT/$r" rev-parse "checkpoint-$STAMP^{commit}" 2>/dev/null)
  if [ -n "$want" ] && [ "$got" = "$want" ]; then
    refs=$(git -C "$DRILL/$n/r" for-each-ref --format='%(refname)' refs/remotes | wc -l | tr -d ' ')
    echo "  ✓ $n restores to $want (tag reached through a ref; $refs origin refs rebuilt)"
  else
    echo "  ✗ $n DRILL FAILED  got=$got want=$want"; fail=1
  fi
done

echo "══════════ 6 · drill a byte store: does a checkpoint hash still hold after untar? ══════════"
( cd "$DRILL" && tar -xzf "$DEST/mef-outputs.tar.gz" ) 
python3 - "$DRILL" <<'PY' || fail=1
import hashlib, json, sys, os, pathlib
drill = pathlib.Path(sys.argv[1])
idx = json.load(open("/Users/mac/Programming/code-2026/chora/artifacts/checkpoints/stage19_h9m_ladders_A.json"))
bad = 0
for c in idx["checkpoints"][:4]:
    p = drill / "Middle-Eigen-function" / pathlib.Path(c["path_on_A"]).relative_to("/Users/mac/Programming/code-2026")
    if not p.exists():
        print(f"   ✗ not in the tarball: {p.name}"); bad += 1; continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"   {'✓' if h == c['sha256'] else '✗'} seed{c['seed']} k={c['rung_k_pct']:>3} restored hash {'matches the pin' if h==c['sha256'] else 'DOES NOT MATCH'}")
    bad += (h != c["sha256"])
sys.exit(1 if bad else 0)
PY

echo "══════════ 7 · what is NOT covered, said out loud ══════════"
echo "  · models/ (6.6 GB) and data/ (476 MB): NOT tarred — law 1 reconstructs them from manifest
    entries by URL+hash; the manifests themselves are in the chora bundle, and their pins are
    re-verified on every beat by chora/bin/validate-manifests.sh."
echo "  · uncommitted work in any repo: NOT in a bundle by definition. Counted here:"
echo "      $(grep -c . "$DEST/uncommitted.txt" 2>/dev/null || echo 0) paths dirty across the six repos (see $DEST/uncommitted.txt)"
echo "  · B's laptop has its own copies of all of this and its own _rollback/2026-09-12*; a bundle on
    one laptop is a one-laptop parachute — the tags are pushed to origin in step 8 so at least the
    labels exist off this machine."
echo "══════════ 8 · push the tags (off-laptop copy of the labels) ══════════"
for r in "${repos[@]}"; do n=$(echo "$r" | xargs)
  git -C "$ROOT/$r" push -q origin "refs/tags/checkpoint-$STAMP" 2>/dev/null \
    && echo "  ✓ tag on origin: $n" || echo "  · tag not pushed (offline or no remote): $n — the bundle is the copy until the network returns"
done

echo
if [ "$fail" = 0 ]; then echo "RESULT: backup taken on A and DRILLED: 6/6 repos restore to their tag, and a restored weight still matches its manifest pin."; else echo "RESULT: backup taken but the DRILL FAILED — treat these files as unverified until it passes."; fi
du -sh "$DEST" | sed 's/^/  size: /'
