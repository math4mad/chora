#!/usr/bin/env bash
# PB24 spurt-nodes 回收四验 (CPU 舱; 完赛/败舱皆收 — 日志即幸存者)
# 判: 27 格 run 行齐 + 3 verdict + 哨兵词 PB24-NODES-DONE → 收哨出草稿。
set -u
export PATH=/opt/miniconda3/envs/default/bin:$PATH
ROOT=/Users/mac/Programming/code-2026/Concept-Space-Sphere
CASE=$ROOT/chora/experiments/pb24-spurt-nodes
DEST=$CASE/out_v1
SLUG=math4amd/pb24-spurt-nodes
RPT=$DEST/report_pb24.jsonl

ST=$(kaggle kernels status "$SLUG" 2>/dev/null | grep -o 'KernelWorkerStatus\.[A-Z]*')
case "$ST" in
  *COMPLETE*|*ERROR*|*CANCEL*) ;;
  *) echo "在途 $SLUG ($ST)"; exit 1;;
esac
mkdir -p "$DEST"
kaggle kernels output "$SLUG" -p "$DEST" >/dev/null 2>&1
[ -s "$RPT" ] || { echo "✘ 无报 ($RPT) — 另册验尸"; exit 1; }
N=$(grep -c '"seed"' "$RPT"); NV=$(grep -c '"verdict"' "$RPT")
LOG=$(ls "$DEST"/*.log 2>/dev/null | head -1)
if [ "$N" -eq 27 ] && [ "$NV" -eq 3 ] && grep -q 'PB24-NODES-DONE' "$LOG" 2>/dev/null; then
  echo "☑ PB24 满舱回收 ($N run + $NV verdict)"; exit 0
else
  echo "◐ PB24 半舱 ($N/27 run, $NV/3 verdict) — 降格草稿, 续巡"; exit 1
fi
