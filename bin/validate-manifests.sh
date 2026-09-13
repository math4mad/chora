#!/usr/bin/env bash
# CHORA — manifest EXISTENCE validator (the check the fleet did not have).
#
# Why: three incidents in two days are one finding wearing three hats —
#   1. artifacts/results/mef/E0_seed14_pretrain.log  pinned, bytes nowhere      (Letter 021 §5)
#   2. the season-1 outline pinned at e3b0c442…/0 B (the hash of nothing),      (PS 1, Letter 021)
#      file written later, the pin never followed
#   3. h6a_pilot_spectra.json pinned from the working tree while HEAD carried    (chora@f79d588)
#      the previous version — a pin true of the checkout, false of the repository
# Every one of them passed "valid JSON + hashes fine + paths conventional". The missing
# clauses are four, and they are cheap:
#
#   (C1) the path is in the manifest            — presence       (already checked by eye)
#   (C2) the path is TRACKED at git HEAD        — the record has it
#   (C3) sha256(bytes AT HEAD) == pin           — the record's bytes ARE the pin's bytes
#   (C4) sha256(bytes ON DISK) == pin          — the checkout agrees too
#   (C5) REVERSE DIRECTION: every tracked file under artifacts/ appears in SOME manifest —
#        added the first time the script was used for anything, which found three tracked
#        files with no pin. A pin without bytes is a permission slip for nothing; bytes
#        without a pin are a fact nobody can cite. Both directions are law 2.
#
# Scope, learned the hard way on the first run (60 "failures", 59 of them by design):
#   artifacts/  -> C1..C4 all required: its bytes live in git, so a pin that HEAD cannot
#                  satisfy is a defect, not a convention.
#   models/ data/ -> C1, C4 required; C2/C3 are WAIVED by law 1 (large binaries are
#                  git-ignored and reconstructed from manifest entries). The waiver is
#                  stated per entry, never inferred from a directory name by a human.
#
# Exit code: 0 by default (report only — the publisher must keep publishing); 1 on a NEW
# failure when --strict is given (use it as a gate).
# Usage:  bin/validate-manifests.sh [--quiet] [--strict]
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
QUIET=0; STRICT=0
[ "${1:-}" = "--quiet" ] && QUIET=1
[ "${1:-}" = "--strict" ] && STRICT=1
EXCEPTIONS="$ROOT/docs/stale-pins.md"

python3 - "$ROOT" "$EXCEPTIONS" "$QUIET" "$STRICT" <<'PY'
import hashlib, json, os, re, subprocess, sys, glob

root, exc_path, quiet, strict = sys.argv[1], sys.argv[2], sys.argv[3] == "1", sys.argv[4] == "1"
os.chdir(root)

# exceptions: any path listed in docs/stale-pins.md inside a ```blocked list``` is exempt,
# with the owner and the ask recorded there. Exemptions are visible or they are not exemptions.
exempt = set()
if os.path.exists(exc_path):
    txt = open(exc_path).read()
    for m in re.finditer(r"^-\s+pin:\s+(\S+)", txt, flags=re.M):
        exempt.add(m.group(1))

def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def at_head(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True)
    return None if r.returncode else r.stdout

tracked_ok = lambda e: e["path"].startswith(("artifacts/",))
rows, fails = 0, []
manifests = sorted(glob.glob("artifacts/*/manifest.json")) + ["data/manifest.json", "models/manifest.json"]
seen_paths = {}
for man in manifests:
    if not os.path.exists(man):
        continue
    for e in json.load(open(man))["files"]:
        rows += 1
        p, pin = e["path"], e["sha256"]
        if p in seen_paths:
            fails.append((man, p, "DUP", f"also pinned in {seen_paths[p]}"))
        seen_paths.setdefault(p, man)
        if not re.fullmatch(r"[0-9a-f]{64}", pin):
            fails.append((man, p, "C1", "pin is not a sha256"))
        hb = at_head(p)
        if hb is None:
            if tracked_ok(e):
                fails.append((man, p, "C2", "not tracked at HEAD, but lives under artifacts/"))
        else:
            if hashlib.sha256(hb).hexdigest() != pin:
                fails.append((man, p, "C3", "bytes at HEAD != pin"))
        if not os.path.exists(p):
            if tracked_ok(e) and hb is None:
                fails.append((man, p, "C4", "no bytes on disk and none in git — a pin for nothing"))
            elif not tracked_ok(e):
                fails.append((man, p, "C4", "no bytes on disk (models/data: reconstructible by URL, but absent)"))
        elif sha(p) != pin:
            fails.append((man, p, "C4", "bytes on disk != pin"))

# C5: the reverse direction — tracked bytes that no manifest names
import fnmatch
nested = sorted(glob.glob("artifacts/**/manifest.json", recursive=True)) + manifests
pins = {}
for m in nested:
    if not os.path.exists(m):
        continue
    for e in json.load(open(m))["files"]:
        pins[e["path"]] = m
lsz = subprocess.run(["git", "ls-files", "-z", "artifacts/"], capture_output=True).stdout
for tp in [x.decode() for x in lsz.split(b"\0") if x.strip()]:
    if tp.endswith("manifest.json"):
        continue
    if os.path.basename(tp) in ("README.md", "NOTICE"):
        continue                       # documentation, not a shared byte — stated, not smuggled
    if tp not in pins:
        fails.append(("(reverse)", tp, "C5", "tracked in git, named by no manifest — uncitable"))

new = [f for f in fails if f[1] not in exempt]
if not quiet:
    print(f"[validate] {rows} pins across {len(manifests)} manifests · "
          f"{len(fails)} failures · {len(new)} NOT exempted")
    for m, p, c, why in fails:
        tag = "EXEMPT" if p in exempt else "NEW"
        print(f"   {tag:6s} {c}  {p}  — {why}")
    if exempt:
        print(f"[validate] registry: {len(exempt)} exemption(s) in docs/stale-pins.md — "
              "each names an owner and an ask; none is a waiver of the rule")
# default: report and exit 0, so a beat that runs this never stops publishing over it;
# --strict: a new failure is an exit 1, which is what a gate before `rebase --continue` should use.
sys.exit(1 if (new and strict) else 0)
PY
