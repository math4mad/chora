# PREREG — Experiment 18: 达尔文夫妇案 (C37 双基底层的证伪试验)

**登记**: 2026-09-22 15:3x (+08), 主人准奏"按建议办" (本会话 ③甲锹)
**理论来源**: cora-atlas LEDGER C37 (雷克双基底层: θ=θ₀+ΣᵢBA; 族内可融合, 跨族只能对话)
+ C34 绕行定律 (组合不沿线, 出平面新分量 44–46.5° 跨语料守恒)
**装置**: Kaggle T4 · Qwen2.5-0.5B-Instruct (族一) · Llama-3.2-1B (族二, 挂载失败则 J3 降级为纯描述)
**配方**: exp10 原封 (r=16, α=32, dropout 0.05, 全 attn+mlp 七路, lr=1e-4, ep6, batch2×accum4, seed13)
**语料**: exp10 corpus_spring/corpus_summer 原字节 base64 内嵌 (lora 训练 80/20 定序切分, 后 11 行 held-out)
**探针**: exp10 probes.json 40 题, 答案起点 top-50 分布 (bench.py 语义, 不采样零随机)

## 臂 (四训练 + 一融合 + 一对照)

- Q-spring, Q-summer: Qwen 基座各训一域
- L-spring, L-summer: Llama 基座同配方 (若可挂)
- **M**: ΔW_M = ½(ΔW_spring + ΔW_summer) 直加回 Qwen 基座权重 (merge, 非路由非拼接)
- Base: 无适配器对照

## 判据 (先写后射, 阈值冻结于此)

**J1 · 族内可融合 (C37 正面)**: held-out 域行 NLL: NLL_M(春语料) − NLL_Qspring(春语料) ≤ +0.10 nats
且 同式对夏。两条同过 = J1 成立; 任一塌 = 融合非法, C37 受创。
**J2 · 合非拼接 (C34 的 merge 版)**: 每探针 d = JS(p_M, ½(p_s+p_u)) / JS(p_s, p_u) (弦上偏离比)。
d ≥ 0.15 的探针 ≥ 12/40 → J2 成立 (融合生新分量); d ≤ 0.05 占多数 → 融合=线性平均, C34 不迁移到 merge。
**J3 · 跨族不可通约 (描述性, 无阈值)**: 报告 ①ΔW 形状失配清单 (Qwen 896 维 vs Llama 2048 维, 数值 merge 不可定义);
②probe top-50 分布 Jaccard: 族内 (M vs Q-parents) 对比 跨族 (M vs L-merge 若存在)。预期族内≫跨族 = "只能对话"的量化像。

## 死亡条款 (负结果一等公民)

- J1 塌: θ₀ 共享不保 ΔW 同坐标系 → C37 的"族"定义需重铸 (rank 对齐? 层对齐?), 另案。
- J2 塌 (d≈0): merge 是线性平均, 绕行定律只在混训 (数据耦合) 里活着, 参数耦合无鼓包 → C37 "球=生育器官" 一句降格为修辞。
- 两塌并报, 不挑好的说。

## 收据

- 四臂训练日志 + M 的 NLL 表 + 每探针 d 值 → report_exp18.json (REPORT_LINE base64 回传)
- 计算账: 4×(55 行×6ep) ≈ 15 min T4, 远低于任何网格先例
- 本文件与 run.py 同 commit 冻结; 事后改阈值 = 新行 post-hoc
