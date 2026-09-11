#!/usr/bin/env bash
# ONE SPACE — idempotent workspace setup. Safe to re-run after every clone/pull.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODE="$HOME/Programming/code-2026"

echo "[one-space] root: $ROOT"

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

# ---- manifest stubs -----------------------------------------------------------
for d in models data artifacts/spectra artifacts/atoms artifacts/init-states artifacts/results; do
  [ -f "$ROOT/$d/manifest.json" ] || printf '{ "files": [] }\n' > "$ROOT/$d/manifest.json"
done

# ---- hash helper reminder ------------------------------------------------------
if [ ! -x "$(command -v shasum)" ]; then
  echo "  [warn] shasum not found (needed by the hashing step)"; fi
echo "[one-space] done. Next: verify hashes before consuming anything:"
echo "    cd $ROOT && while read -r p h; do [ \"\$(shasum -a 256 \"\$p\" | cut -d' ' -f1)\" = \"\$h\" ] || echo MISMATCH \$p; done \\"
echo "      < <(python3 -c \"import json;[print(f['path'],f['sha256']) for m in ['models','data'] for f in json.load(open(m+'/manifest.json'))['files']]\")"
