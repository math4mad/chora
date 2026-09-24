#!/usr/bin/env bash
# 通用回收: collect-kaggle-plain.sh <slug> <dest> <report-file> <sentinel> —— 四验全过才 ☑
set -u; export PATH=/opt/miniconda3/envs/default/bin:$PATH
SLUG=$1; DEST=$2; REP=$3; SENT=$4
ST=$(kaggle kernels status "$SLUG" 2>/dev/null | grep -o 'KernelWorkerStatus\.[A-Z]*')
case "$ST" in
  *COMPLETE*|*ERROR*|*CANCEL*)
    mkdir -p "$DEST"; kaggle kernels output "$SLUG" -p "$DEST" >/dev/null 2>&1
    f="$DEST/$REP"
    if [ ! -s "$f" ]; then echo "假完赛: 无 $REP"; exit 1; fi
    /usr/local/bin/python3 - "$f" "$SENT" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d.get("sentinel")==sys.argv[2] or sys.argv[2] in json.dumps(d), "无哨/有error"
print("四验过:", sys.argv[1])
PY
    [ $? -eq 0 ] || exit 1
    shasum -a 256 "$f" > "$f.sha256"
    echo "收讫 $SLUG ($ST) + sha 立户"; exit 0;;
  *) echo "在途 $SLUG ($ST)"; exit 1;;
esac
