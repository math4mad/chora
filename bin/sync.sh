#!/usr/bin/env bash
# CHORA (formerly ONE SPACE) — idempotent workspace setup. Safe to re-run after every clone/pull.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODE="$HOME/Programming/code-2026"

echo "[chora] root: $ROOT"

mkdir -p "$ROOT/benches"
mkdir -p "$ROOT"/{models,data,artifacts/spectra,artifacts/atoms,artifacts/init-states,artifacts/results,letters,schemas,bin}

# ---- benches: symlink the existing working checkouts (no competing clones) --
link_bench() { # name, source-dir
  local name="$1" src="$2"
  if [ ! -d "$src/.git" ] && [ ! -f "$src/.git" ]; then
    echo "  [skip] $name: no checkout at $src"; return
  fi
  local head; head="$(git -C "$src" rev-parse --short HEAD)"
  local branch; branch="$(git -C "$src" branch --show-current)"
  ln -sfn "$src" "$ROOT/benches/$name"
  echo "  [bench] $name -> $src ($branch @ $head)"
}
mkdir -p "$ROOT/benches"
link_bench JacobiGP "$CODE/ JacobiGP"
link_bench MEF      "$CODE/Middle-Eigen-function"
link_bench Sarcos   "$CODE/Sarcos-NN-Model"
link_bench PolyNN   "$CODE/Polynomial-Activated NN "  # trailing space is real; five benches now
link_bench Kairos   "$CODE/Kairos"

# ---- shared bytes: each bench's expected paths link INTO the shared store ----
# MEF: modelscope cache at ./models (layout models/models/...), data at ./data (RTE.zip)
# Sarcos: data/ holds the GPML .mat files (git-ignored)
# JacobiGP: no model bytes; results stay in-repo, mirrored to artifacts/results
share() { # bench-name, bench-relative-path, shared-target
  local name="$1" bp="$2" target="$3"
  local benchdir
  benchdir="$(cd "$ROOT/benches/$name" 2>/dev/null && pwd -P)" \
    || { echo "  [skip] $1 missing"; return; }
  local full="$benchdir/$bp"
  if [ -e "$full" ] && [ ! -L "$full" ]; then
    echo "  [exists] $1/$bp — real dir, NOT touching; merge by hand once (see README)"
    return
  fi
  mkdir -p "$(dirname "$full")" "$ROOT/$target"
  ln -sfn "$ROOT/$target" "$full"
  echo "  [share] $1/$bp -> $target"
}
share MEF    models models
share MEF    data   data
share Sarcos data   data
share PolyNN  data   data   # Fashion-MNIST lands in the shared store when fetched

# ---- manifest stubs -----------------------------------------------------------
for d in models data artifacts/spectra artifacts/atoms artifacts/init-states artifacts/results; do
  [ -f "$ROOT/$d/manifest.json" ] || printf '{ "files": [] }\n' > "$ROOT/$d/manifest.json"
done

# ---- hash helper reminder ------------------------------------------------------
if [ ! -x "$(command -v shasum)" ]; then
  echo "  [warn] shasum not found (needed by the hashing step)"; fi
# ---- fleet dashboard snapshot ------------------------------------------------
# Refresh docs/status.json; commit+push ONLY that path, and only when a real
# field moved (the "generated" timestamp alone never triggers a commit).
if bash "$ROOT/bin/status.sh" --publish >/dev/null 2>&1; then
  # NB: 'generated' and 'chora_head' are provenance, not state — chora_head
  # changes *because* the snapshot commits, so ignoring it breaks the
  # self-sustaining ping-pong (first publish after each real move commits;
  # every later publish sees only these two lines and stays silent).
  if ! git -C "$ROOT" diff --quiet -I '.*"generated".*' -I '.*"chora_head".*' -- docs/status.json 2>/dev/null; then
    echo "[chora] fleet status moved — publishing snapshot"
    git -C "$ROOT" commit -q -m "status snapshot (auto: bin/sync.sh)" -- docs/status.json \
      && { git -C "$ROOT" remote get-url origin >/dev/null 2>&1 \
           && git -C "$ROOT" push -q origin "$(git -C "$ROOT" branch --show-current)" 2>/dev/null \
           && echo "[chora] dashboard pushed to origin" \
           || echo "[chora] snapshot committed (not pushed — no origin or network; push at leisure)"; }
  else
    echo "[chora] fleet status current (snapshot unchanged — a one-line 'provenance' drift of docs/status.json vs HEAD is expected: timestamp + chora_head refresh locally, never commit-worthy)"
  fi
fi
echo "[chora] done. Next: verify hashes before consuming anything:"
echo "    cd $ROOT && while read -r p h; do [ \"\$(shasum -a 256 \"\$p\" | cut -d' ' -f1)\" = \"\$h\" ] || echo MISMATCH \$p; done \\"
echo "      < <(python3 -c \"import json;[print(f['path'],f['sha256']) for m in ['models','data'] for f in json.load(open(m+'/manifest.json'))['files']]\")"
