#!/usr/bin/env bash
# PB23c v5 回收四验 —— 完赛/败舱皆收（v5 流式后每一对算完即落盘, 半舱亦是净收）。
# 判: 配对满额 198 (66×3籽) → 收哨; 半舱 (≥66 但 <198) → 出降格草稿并续巡补射之议。
# 律: 数字先 sha 入册再判读; 缺籽如实注, 不许拿两籽冒充三籽。
set -u
export PATH=/opt/miniconda3/envs/default/bin:$PATH
ROOT=/Users/mac/Programming/code-2026/Concept-Space-Sphere
CASE=$ROOT/chora/experiments/pb23c-fine12
DEST=$CASE/out_v5
SLUG=math4amd/pb23c-fine12
REP=$DEST/report_pb23c.json

ST=$(kaggle kernels status "$SLUG" 2>/dev/null | grep -o 'KernelWorkerStatus\.[A-Z]*')
case "$ST" in
  *COMPLETE*|*ERROR*|*CANCEL*) ;;
  *) echo "在途 $SLUG ($ST)"; exit 1;;
esac
mkdir -p "$DEST"
kaggle kernels output "$SLUG" -p "$DEST" >/dev/null 2>&1
[ -s "$REP" ] || { echo "✘ 残报亦无 ($REP) — 全灭, 另册验尸"; exit 1; }
n=$(python3 -c "import json;print(len(json.load(open('$REP'))['runs']))" 2>/dev/null || echo 0)
sd=$(python3 -c "import json;d=json.load(open('$REP'));print(len(sorted({r['seed'] for r in d['runs'] if r.get('seed')})))" 2>/dev/null || echo 0)
echo "收讫 $SLUG ($ST) · 配对落盘 $n / 198 (66×3籽) · 完籽 $sd/3"
[ "$n" -ge 66 ] || { echo "✘ 不足一籽之 66 对, 本哨续巡"; exit 1; }
cd "$CASE" || exit 1
shasum -a 256 "$REP" > VERDICT_PB23c_draft.txt
python3 read_curve.py "$REP" >> VERDICT_PB23c_draft.txt
if [ "$ST" != "KernelWorkerStatus.COMPLETE" ] || [ "$n" -lt 198 ]; then
  { echo ""; echo "⚠ 降格读数 (舱态 $ST · 配对 $n/198 · 完籽 $sd/3): 缺籽如实注, 不追改冻条;";
    echo "   半舱亦是净收 —— 此即 v5「配对即算即落盘」之效 (v4 同死法时配对数为 0)。";
    echo "   补射之议候主人 (可 PB_SEEDS 单籽分弹只补缺籽)。"; } >> VERDICT_PB23c_draft.txt
  echo "判形草稿已出 (降格), 见 VERDICT_PB23c_draft.txt"; exit 0
fi
echo "判形草稿已出 (满舱), 见 VERDICT_PB23c_draft.txt"; grep -q '"verdict"' "$REP"
