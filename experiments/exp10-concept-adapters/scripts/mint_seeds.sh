#!/usr/bin/env bash
# exp10b hardening: seeds 14,15 for all three arms (no bench needed — SVD reads matrices only)
PY=/opt/miniconda3/envs/default/bin/python
D=/Users/mac/Programming/code-2026/chora/experiments/exp10-concept-adapters
for s in 14 15; do
  $PY $D/scripts/train_lora.py --corpus $D/data/corpus_spring.jsonl --out $D/results/adapter_spring_s$s --tag spring-s$s --seed $s
  $PY $D/scripts/train_lora.py --corpus $D/data/corpus_summer.jsonl --out $D/results/adapter_summer_s$s --tag summer-s$s --seed $s
  $PY $D/scripts/train_lora.py --corpus $D/data/corpus_mid.jsonl    --out $D/results/adapter_mid_s$s    --tag mid-s$s    --seed $s --epochs 3
done
echo MINT_SEEDS_DONE
