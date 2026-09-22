#!/usr/bin/env bash
# 补位射手: GPU 席位空出即推下一臂。顺序 qwen7 → llama1(候网页许可)。全推完退 0。
set -u
K=/opt/miniconda3/envs/default/bin/kaggle
D="$(cd "$(dirname "$0")/.." && pwd)"; cd "$D"
busy=0
for r in math4amd/exp11-qwen2-5-1-5b-matrix math4amd/exp11-qwen2-5-3b-matrix math4amd/exp11-qwen25-7b-matrix math4amd/exp11-llama32-1b-matrix; do
  s=$($K kernels status $r 2>/dev/null)
  echo "$s" | grep -q "RUNNING\|QUEUED" && busy=$((busy+1))
done
[ "$busy" -ge 2 ] && { echo "席位满 ($busy/2), 本轮不射"; exit 1; }
if [ ! -f qwen7/.pushed-ok ]; then
  out=$(cd qwen7 && $K kernels push -p . 2>&1)
  if echo "$out" | grep -q "successfully pushed"; then touch "$D/qwen7/.pushed-ok"; echo "qwen7 已射 (v+1)"; exit 0; fi
  echo "qwen7 射败: $(echo "$out" | tail -1)"; exit 1
fi
if [ ! -f llama1/.pushed-ok ]; then
  out=$(cd llama1 && $K kernels push -p . 2>&1)
  if echo "$out" | grep -q "successfully pushed"; then touch "$D/llama1/.pushed-ok"; echo "llama1 已射"; exit 0; fi
  echo "llama1 射败 (候网页许可?): $(echo "$out" | tail -1)"; exit 1
fi
echo "四臂俱已射毕"; exit 0
