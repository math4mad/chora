# PREREG_LADDER-2b · 波浪与节省（AutoDL 4090, 3 种子）

冻结时刻: 2026-09-24 夜, 先于任何 2b 舱次点火 (本文件 commit 即弹上膛前的封条)。
前身: LADDER-2 v3 单种子探量级 (RESULTS_LADDER-2_v3.md, 记录臂不判死) —— 本臂升格为**判死臂**。

## 弹道
- 基座 Qwen2.5-0.5B-Instruct (AutoDL 离线挂载, sha 户 = autodl/qwen05-sha256.txt)
- 袋: s1_naming(240) / s2_rhyme(280) / s3_dialogue(540), 与 v3 逐字同袋 (builder 复用, sha 对账)
- 两喂法 × seeds {13,14,15} = 6 舱次连射; epochs=2, batch=8, lr=1e-4, seq=256 (v3 原方)
- checkpoint 网格修正: 每 epoch 恰 3 拍 (v1-v3 之 0.498/0.500 双发伪影已除, step % ck 且 step≠last_ckpt_step)

## 判据 (主判二条, 逐种子判, 多数决)
**H-w1 波浪不对称度**: 对每段 g 计正CE增量和 P_g = Σ max(0, CE_g(t+1)−CE_g(t)) (跨 checkpoint),
  不对称度 A = Σ_g P_g(ladder) / max(Σ_g P_g(mixed), 1e-6)。
  **过 = A ≥ 2.0 于 ≥2/3 种子。**
**H-w2 节省法幅度**: 对 ladder 臂每段 g, 找第二次喂后首个 CE 低点 L2_g 与首次喂低点 L1_g,
  S_g = L2_g − L1_g。**过 = min_g S_g ≤ −0.10 nats 于 ≥2/3 种子。**
旁观不判: Bfro 增速差 / selfcos 序列 / mixed 臂末程效率优势 (specialization vs efficiency 账面留后续案)。

## 生死与诚实条款
- 双过 → **序效应第一张湿判据成立**, 入 LEDGER, 论文素材节生;
- 一过一败 → 如实分报, 胜者保留、败者立 2c 修订案 (新冻, 不挪旧靶);
- 双败 → 波浪与节省都是 v3 单种子噪声, 全部读数挂 exploratory, 2b 判死记录在案;
- 任何情况下 2b 原始 json 先 sha 入册再判读 (数字入 LEDGER 先对 sha256, 园律)。

## 预算
6 舱次 ≈ 4090 上一小时级, ¥2–3 封顶; 射完回收即 shutdown 止血 (AutoDL 关机停计)。
