# diachronic-q-v2 · Kaggle 臂

历时提问测试 v2（真模型版）的 Kaggle 夜航臂。协议与判据同本地
`benches/FSSSS/diachronic_q_v2.py` ＋ `DESIGN_diachronic_q_v2.md`（**判据先冻**）。

- **模型**：Qwen2.5-Instruct 族（0.5b / 1.5b / 3b / 7b；7b 走 4bit）。
- **提问**：Stage A/B 上下文 → 要求 `APPEARS:` / `ICAR:` schema。
- **真值**：`APPEARS ⊇ {iPhone,iPad,iPod}`；`ICAR=no`（iCar 越域不入）。
- **判据**：`H-v2-1` 兄弟召回=1 · `H-v2-2` 守边界(ICAR=no) · `H-v2-3` 无真值外节点。
- **0.5B 本地**：base 不支持 schema（见 `report_diachronic_q_v2.json`）；Instruct 本地已补跑。

## 发射（夜航规矩）
```
/opt/miniconda3/envs/default/bin/kaggle kernels push -p /Users/mac/Programming/code-2026/chora/experiments/diachronic-q-v2
# 席位满 → bin/queue.py add diachronic-q-v2 --cmd '<回收脚本>'
# 回收: kaggle kernels output math4amd/diachronic-q-v2 -p ./out
```
- 即算即落：`report_diachronic_q_v2_kaggle.json` ＋ `REPORT_LINE::`（b64）。
- 疫苗行已带（`pip uninstall torchao`）；`apply_chat_template(..., return_dict=False)`；`from_pretrained(dtype=)`。
