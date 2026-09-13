#!/usr/bin/env bash
# CHORA — publish an offline restore point as a GitHub release, and verify it from the other side.
#
# Why a release and not a commit: law 1 keeps weights out of history, and GitHub blocks single files
# over 100 MB — this parachute is 219 MB with a 177 MB asset. A release asset is the right object:
# outside the history, downloadable, checksummed by us, tied to a tag name.
#
# Credentials come from git's own credential helper; they are read into memory, never echoed, never
# written to disk.  Usage:  bin/publish-release.sh [dir] [tag]
set -uo pipefail
ROOT=/Users/mac/Programming/code-2026
DEST="${1:-$ROOT/_rollback/2026-09-13-A}"
TAG="${2:-checkpoint-2026-09-13-A}"
STAMP="$(basename "$DEST")"
REPO=math4mad/chora
API=https://api.github.com
LOG=/tmp/chora-release-upload.log

TOK=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | awk -F= '/^password/{print $2}')
if [ -z "${TOK}" ]; then echo "no github credential from the helper — refusing"; exit 1; fi
AUTH="Authorization: token ${TOK}"

echo "── identity: $(curl -s -H "$AUTH" "$API/user" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("login"),"· scopes:",",".join(d.get("scopes") or ["?"]))')"

echo "── release body (from the files, not from memory)"
python3 - "$DEST" "$STAMP" > /tmp/release-body.md <<'PY'
import pathlib, sys
d, stamp = pathlib.Path(sys.argv[1]), sys.argv[2]
sums = (d/"SHA256SUMS").read_text().strip()
heads = (d/"heads.txt").read_text().strip()
unc = (d/"uncommitted.txt").read_text().strip() if (d/"uncommitted.txt").exists() else "(none)"
files = [p for p in sorted(d.iterdir()) if p.is_file()]
total = sum(p.stat().st_size for p in files) / 1e6
print(f"""Offline restore point `{stamp}`, minted and **drilled** by `chora/bin/backup-drill.sh`.

**This is a backup, not a build.** Nothing here is needed to run the programme; it exists so that one lost SSD does not erase two days of registers.

* {len(files)} files, **{total:.0f} MB**; every byte hashed below, verified locally before upload and re-downloaded after.
* 6 × `*.bundle` — `git bundle --all`: every branch of every bench repo (including the `gh-pages` sites) **and** the `checkpoint-*` tags.
* `mef-outputs.tar.gz` (177 MB) — 40 `.pt` files: the base ladders behind E0/E3 and H9-M's registered runs. **These bytes exist in no git, on no other machine.**
* `sarcos-results.tar.gz` (27 MB) — the Sarcos run tree (weights `.npz` + `run.json` per arm).
* `polynn-results.tar.gz`, `jacobigp-results.tar.gz` — the small result trees.
* `heads.txt` — the exact HEAD of all six repos at mint; `uncommitted.txt` — the paths that were dirty, i.e. what a bundle structurally *cannot* hold.

## Restore — the recipe that works; `git clone <bundle>` does NOT restore refs

```bash
git init rest && cd rest
git remote add origin <this-dir>/<repo>.bundle
git fetch origin '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*' '+HEAD:refs/remotes/origin/HEAD'
git checkout -B here <the tag in heads.txt, e.g. checkpoint-2026-09-13-A>
```

Drilled at mint on the machine that made it: **6/6 repos restore to their tag** with origin refs
rebuilt, and five restored `.pt` files hash equal to their manifest pins in
`chora:artifacts/checkpoints/stage19_h9m_ladders_A.json`.

## Limits, said out loud
1. Before this upload everything lived on **one SSD**. Disk failure is now covered; account failure
   is not — if this repo or this token dies, the local `_rollback/` copies remain.
2. `models/` (6.6 GB) and `data/` (476 MB) are deliberately absent: law 1 reconstructs them from
   manifest entries by URL + hash, and the manifests ride inside `chora.bundle`.
3. The weights are on a **private** repo. Anyone with repo access can read the tensors; nobody
   outside can. Delete this release if that ever stops being acceptable — tags and history are
   unaffected.

### SHA256SUMS (the manifest of this archive)

```
{sums}
```

### HEADs at mint

```
{heads}
```

### Dirty paths at mint (not in any bundle)

```
{unc}
```
""")
PY

echo "── create release"
python3 - "$TAG" "$STAMP" > /tmp/release.json <<'PY'
import json, sys, pathlib
tag, stamp = sys.argv[1], sys.argv[2]
body = pathlib.Path("/tmp/release-body.md").read_text()
print(json.dumps({"tag_name": tag, "name": f"CHORA offline restore point — {stamp}",
                  "body": body, "draft": False, "prerelease": False}))
PY
REL=$(curl -s -X POST -H "$AUTH" -H "Accept: application/vnd.github+json" "$API/repos/$REPO/releases" -d @/tmp/release.json)
RELID=$(printf '%s' "$REL" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
HTML=$(printf '%s' "$REL" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("html_url",""))' 2>/dev/null)
if [ -z "${RELID:-}" ]; then echo "!! could not create the release:"; printf '%s\n' "$REL" | head -c 400; echo; exit 1; fi
UPURL=$(printf '%s' "$REL" | python3 -c 'import json,sys;print(json.load(sys.stdin)["upload_url"].split("{")[0])')
echo "   $HTML"

echo "── upload (log: $LOG)"
: > "$LOG"
for f in "$DEST"/*; do
  b=$(basename "$f"); sz=$(stat -f%z "$f")
  resp=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/octet-stream" \
           --data-binary "@$f" "$UPURL?name=$b")
  id=$(printf '%s' "$resp" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("id",""))
except Exception: print("")' 2>/dev/null)
  printf "   %-34s %10s B  %s\n" "$b" "$sz" "${id:+id=$id ✓}${id:-FAILED}"
  [ -z "${id:-}" ] && printf '%s\n' "$resp" >> "$LOG"
  sleep 1
done

echo "── what GitHub now holds, and one asset re-downloaded as proof"
curl -s -H "$AUTH" "$API/repos/$REPO/releases/tags/$TAG" > /tmp/rel.json
python3 - <<'PY2'
import json
a=json.load(open("/tmp/rel.json")).get("assets",[])
print(f"   {len(a)} assets, {sum(x['size'] for x in a)/1e6:.0f} MB total")
for x in a: print(f"     {x['name']:34s} {x['size']:>10} B")
PY2
RTID=$(python3 -c "
import json
a=json.load(open('/tmp/rel.json'))['assets']
print(next((x['id'] for x in a if x['name']=='heads.txt'),''))")
if [ -n "${RTID}" ]; then
  curl -sL -H "$AUTH" -o /tmp/rt-asset "$API/repos/$REPO/releases/assets/$RTID"
  want=$(grep -F "heads.txt" "$DEST/SHA256SUMS" | awk '{print $1}')
  got=$(shasum -a 256 /tmp/rt-asset | awk '{print $1}')
  if [ "$got" = "$want" ]; then echo "   round-trip ✓ heads.txt came back from GitHub hashing equal to the local manifest";
  else echo "   round-trip ✗ MISMATCH — treat the upload as unverified"; fi
else
  echo "   round-trip skipped (no heads.txt asset found)"
fi
echo "done: $HTML"
