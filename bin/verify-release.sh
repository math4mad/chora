#!/usr/bin/env bash
# CHORA — verify a restore-point release from the outside: does what GitHub holds match SHA256SUMS,
# and do downloaded assets hash equal to the local ones? Retries missing assets.
#
# macOS ships bash 3.2 — no associative arrays, no ${v@Q}. Names travel in tab-separated temp files
# and JSON is parsed by python. Verified against /bin/bash 3.2.57 before shipping.
#
# Two bugs this file exists to catch, both of them its own first runs:
#   · `while read` drops an unterminated last line — the retry loop silently skipped the one missing
#     file until every temp file here was written line-per-line with a trailing newline;
#   · the asset API returns JSON metadata unless you ask for `Accept: application/octet-stream` — a
#     "round-trip" that hashes metadata is not a round-trip.
# And one platform fact: GitHub rewrites spaces in asset names to dots, so a bundle called
# "Polynomial-Activated NN.bundle" comes back as "Polynomial-Activated.NN.bundle". Matching accepts
# either spelling and proves the file by hash.
set -uo pipefail
ROOT=/Users/mac/Programming/code-2026
DEST="${1:-$ROOT/_rollback/2026-09-13-A}"
TAG="${2:-checkpoint-2026-09-13-A}"
REPO=math4mad/chora; API=https://api.github.com
TOK=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | awk -F= '/^password/{print $2}')
if [ -z "${TOK}" ]; then echo "no github credential — refusing"; exit 1; fi
AUTH="Authorization: token ${TOK}"

curl -s -H "$AUTH" "$API/repos/$REPO/releases/tags/$TAG" > /tmp/rel.json || exit 1

python3 - "$DEST" <<'PYEOF'
import json, sys, pathlib
dest = pathlib.Path(sys.argv[1])
assets = {a["name"]: a for a in json.load(open("/tmp/rel.json")).get("assets", [])}
want = {}
for line in (dest/"SHA256SUMS").read_text().splitlines():
    h, n = line.split(" ", 1)                       # names may contain spaces
    want[n.strip()] = (h, (dest/n.strip()).stat().st_size)

def find(n):
    return assets.get(n) or assets.get(n.replace(" ", "."))

miss = [n for n in want if find(n) is None]
sizebad = [n for n, (h, b) in want.items() if find(n) and find(n)["size"] != b]
print(f"manifest: {len(want)} files · release: {len(assets)} assets · {sum(a['size'] for a in assets.values())/1e6:.0f} MB")
for n in sorted(want):
    a = find(n)
    mark = "✗ MISSING" if n in miss else ("✗ SIZE" if n in sizebad else "✓")
    print(f"   {mark:9s} {n:34s} local {want[n][1]:>10}" + (f"  remote {a['size']:>10}" if a else ""))
print("MISSING:", miss or "none", "| SIZE MISMATCH:", sizebad or "none")
pathlib.Path("/tmp/missing.txt").write_text("".join(n + "\n" for n in miss))
pathlib.Path("/tmp/ids.txt").write_text("".join(f"{n}\t{find(n)['id']}\n" for n in sorted(want) if find(n)))
PYEOF

if [ -s /tmp/missing.txt ] && [ -n "$(tr -d '[:space:]' < /tmp/missing.txt)" ]; then
  echo "── retrying missing assets (URL-encoded names)"
  UP=$(python3 -c 'import json;print(json.load(open("/tmp/rel.json"))["upload_url"].split("{")[0])')
  while IFS= read -r name; do
    [ -z "${name:-}" ] && continue
    enc=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$name")
    resp=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/octet-stream" --data-binary "@$DEST/$name" "$UP?name=$enc")
    id=$(printf '%s' "$resp" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("id",""))
except Exception: print("")')
    printf "   %-34s %s\n" "$name" "${id:+id=$id ✓}${id:-STILL FAILING}"
  done < /tmp/missing.txt
  curl -s -H "$AUTH" "$API/repos/$REPO/releases/tags/$TAG" > /tmp/rel.json
fi

echo "── round-trip: download assets as BYTES and re-hash them"
python3 - <<'PYEOF' > /tmp/dl.sh
import pathlib
ids = {}
for line in pathlib.Path("/tmp/ids.txt").read_text().splitlines():
    if "\t" in line:
        n, i = line.split("\t", 1)
        ids[n] = i
names = [n for n in ("heads.txt", "uncommitted.txt", "SHA256SUMS") if n in ids]
names += [n for n in ids if " " in n]        # everything GitHub renamed is proved by hash
for n in names:
    print(f"{n}\t{ids[n]}")
PYEOF
while IFS=$'	' read -r name id; do
  [ -z "${name:-}" ] && continue
  curl -sL -H "$AUTH" -H "Accept: application/octet-stream" -o "/tmp/rt-asset" "$API/repos/$REPO/releases/assets/$id"
  got=$(shasum -a 256 /tmp/rt-asset | awk '{print $1}')
  want=$(grep -F " $name" "$DEST/SHA256SUMS" | head -1 | awk '{print $1}')
  if [ -n "$want" ] && [ "$got" = "$want" ]; then
    echo "   ✓ $name — bytes from GitHub, hash equals the manifest"
  else
    echo "   ✗ $name — got ${got:0:12}… want ${want:0:12}…"
  fi
done < /tmp/dl.sh
echo "see: https://github.com/$REPO/releases/tag/$TAG"
