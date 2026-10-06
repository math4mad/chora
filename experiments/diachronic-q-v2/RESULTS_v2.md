# RESULTS · 历时提问测试 v2（真模型）· Qwen2.5-Instruct 族

> 协议/判据：`benches/FSSSS/DESIGN_diachronic_q_v2.md`（先冻）。
> 本地：Qwen2.5-0.5B-Instruct（conda default 环境 torch/transformers）。
> Kaggle 臂：`chora/experiments/diachronic-q-v2/`（kernel `math4amd/diachronic-q-v2`，v3 完赛，`enable_internet:true`）。
> 场景：种子 `i×Mac` ⇒ 阶段 A→B。真值：`APPEARS ⊇ {iPhone,iPad,iPod}`；`ICAR=no`（iCar 越域不入）。

## 一 · 出数（temperature 0）

| 模型 | APPEARS（原答） | ICAR | 结构召回 | 守边界 | 真值外节点 | 判据 |
|---|---|---|---|---|---|---|
| **0.5b-instruct** | iPhone, iPad, iPod, **iPod Touch, iWatch** | no | **1.000** | ✓ | **2** | H1✓ H2✓ **H3✗** |
| **1.5b-instruct** | iPad, iPod | **yes** | 0.667 | **✗** | 0 | **H1✗ H2✗** H3✓ |
| **3b-instruct** | iPhone, **iPads**, iPod | no | 0.667 | ✓ | 1 | **H1✗** H2✓ **H3✗** |
| **7b-instruct** | **Phone, Pad, Pod**（丢 i- 前缀） | no | **0.000** | ✓ | 3 | **H1✗** H2✓ **H3✗** |
| **0.5b base**（本地对照） | iMac, iCar（不守 schema） | yes | 0.000 | ✗ | — | 全败 |

## 二 · 读法（三条）

1. **无一款真模型同时过 H-v2-1/2/3。** 最好者 0.5b：召回满分但**过生成**（iPod Touch/iWatch）；
   3b **复数化**（iPads）；7b **灾难性丢前缀**（只答 `Phone,Pad,Pod`——把组合结构整个丢了）。
2. **边界（iCar）非单调**：0.5b/3b/7b 守住、1.5b 崩（答 `ICAR: yes`）。
   ⇒ **守边界不是「越大越强」**——与园「边界须显式门控」一致：无显式结构，边界在规模上不稳。
3. **7b 的反例最刺眼**：规模上去反而**退回底座概念、抹掉组合**——正是**倒灌律④（去历史化/共时化）**
   的现场：模型给的是**摊平的共时词表**，不是 A→B 的**结构变化**。

## 三 · 与 v0/v1 合读
- v0/v1：**显式 PCS** 能答结构变化且守边界；共时/去历史基线不能。
- v2：**真黑箱 LM**（0.5–7B）**不能稳定**答结构变化、**不能守住边界**。
- 合起来 ⇒ **「竞争性 ≠ 可审计性」的实证态**：模型能流畅说 Apple 产品，却在**结构级历时问题**上不可靠——
  正是园主张「**须显式构建演化序列先验**」的外部证据。

## 四 · 复算
```
# 本地
/opt/miniconda3/envs/default/bin/python3 benches/FSSSS/diachronic_q_v2.py --backend hf \
  --model-path .../GrandFather/models/models/Qwen--Qwen2.5-0.5B-Instruct --instruct
# Kaggle
kaggle kernels push -p chora/experiments/diachronic-q-v2
kaggle kernels output math4amd/diachronic-q-v2 -p chora/experiments/diachronic-q-v2/out
```
- 7b 需 `enable_internet:true`（`pip install bitsandbytes>=0.46.1` 做 4bit）；疫苗行带 torchao 卸载。
