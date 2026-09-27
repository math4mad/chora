#!/usr/bin/env bash
# PB16c-FORMAL 回收四验 —— 在途退 1 (队列自鸣重试), 收讫且验讫退 0。
# 律: 完赛 + 九格齐 (S/B/R × 16/17/18) + 哨兵专属 + 无 0 字节壳 (律二: 0 字节 safetensors = 截断空壳一律作废重收)。
set -u
export PATH=/opt/miniconda3/envs/default/bin:$PATH
ROOT=/Users/mac/Programming/code-2026/Concept-Space-Sphere
CASE=$ROOT/chora/experiments/pb16c-formal
DEST=$CASE/out_formal
SLUG=math4amd/pb16c-formal
REP=$DEST/pb16c-formal-out/report_pb16c_formal.json

ST=$(kaggle kernels status "$SLUG" 2>/dev/null | grep -o 'KernelWorkerStatus\.[A-Z]*')
case "$ST" in
  *COMPLETE*|*ERROR*|*CANCEL*) ;;
  *) echo "在途 $SLUG ($ST)"; exit 1;;
esac
mkdir -p "$DEST"
kaggle kernels output "$SLUG" -p "$DEST" >/dev/null 2>&1
[ -s "$REP" ] || { echo "✘ 报告缺席/空壳: $REP"; exit 1; }
grep -q pb16c_formal_ok "$REP" || { echo "✘ 哨缺 (未终局, 只算不判)"; }
if find "$DEST" -name "*.safetensors" -size -1k | grep -q .; then
  echo "✘ 0 字节壳现身, 一律作废重收"; find "$DEST" -name "*.safetensors" -size -1k; exit 1
fi
n=$(python3 -c "import json;print(len(json.load(open('$REP'))['results']))" 2>/dev/null || echo 0)
echo "收讫 $SLUG ($ST) · results=$n/9"
[ "$n" -eq 9 ] || exit 1
cd "$CASE" && python3 analyze_pb16c_formal.py "$DEST/pb16c-formal-out/report_pb16c_formal.json" \
  | tee VERDICT_PB16c_formal_draft.txt
echo "判读仪已跑, 草稿见 VERDICT_PB16c_formal_draft.txt (正式判词候主人)"
grep -q pb16c_formal_ok "$REP"
