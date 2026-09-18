#!/usr/bin/env bash
# exp10 · gguf pipeline (afternoon doc §5.2): merge each adapter into the frozen base,
# convert to GGUF f16 via llama.cpp's converter, quantize q4_K_M, measure speed.
# Refuses to run without its tools; honest failures over silent skips.
set -uo pipefail
E=/Users/mac/Programming/code-2026/chora/experiments/exp10-concept-adapters
BASE=/Users/mac/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master
PY=/opt/miniconda3/envs/default/bin/python
LLB=$(brew --prefix llama.cpp 2>/dev/null)/bin
CONV=$(find "$(brew --prefix 2>/dev/null)" ~/tmp/llama.cpp-repo -name convert_hf_to_gguf.py 2>/dev/null | head -1)
[ -x "$LLB/llama-quantize" ] || { echo "llama.cpp 未就位 — 先 brew install llama.cpp"; exit 1; }
if [ -z "$CONV" ]; then
  echo "converter 不在 bottle 里 — 浅克隆 llama.cpp 取一纸脚本"
  git clone --depth 1 https://github.com/ggml-org/llama.cpp ~/tmp/llama.cpp-repo 2>/dev/null \
    && CONV=~/tmp/llama.cpp-repo/convert_hf_to_gguf.py
fi
for arm in spring summer mid; do
  [ -d "$E/gguf/$arm" ] || mkdir -p "$E/gguf/$arm"
  if [ ! -d "$E/gguf/$arm/hf_merged" ]; then
    $PY - "$BASE" "$E/results/adapter_$arm" "$E/gguf/$arm/hf_merged" <<'EOF'
import sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
base, ad, out = sys.argv[1:4]
m = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16)
m = PeftModel.from_pretrained(m, ad).merge_and_unload()
m.save_pretrained(out); AutoTokenizer.from_pretrained(base).save_pretrained(out)
print("merged →", out)
EOF
  fi
  [ -f "$E/gguf/$arm/model-f16.gguf" ] || $PY "$CONV" "$E/gguf/$arm/hf_merged" --outtype f16 --outfile "$E/gguf/$arm/model-f16.gguf" >/dev/null
  [ -f "$E/gguf/$arm/model-q4_K_M.gguf" ] || "$LLB/llama-quantize" "$E/gguf/$arm/model-f16.gguf" "$E/gguf/$arm/model-q4_K_M.gguf" q4_K_M >/dev/null
  # speed test: 64 tokens greedy
  t=$( { /usr/bin/time -p "$LLB/llama-cli" -m "$E/gguf/$arm/model-q4_K_M.gguf" -p "夏天热得受不了怎么办？" -n 64 --temp 0 -no-cnv 2>&1; } | grep -E "tokens per second|Eval time" | tail -1 )
  sz=$(du -m "$E/gguf/$arm/model-q4_K_M.gguf" | cut -f1)
  echo "$arm: q4_K_M ${sz}MB · $t"
done
echo GGUF_PIPELINE_DONE
