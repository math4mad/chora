# PREREG_PB21 · CHILDES 湿臂：真幼儿语料上的序效应外检

> 状态：**判据先冻**（本文 commit 早于任何一格 pb21 训练）。
> 立梁门必答：本问若答『是』——序效应在**真实儿童语料**（CHILDES 纵向, 非合成/非成人袋）上复现，梁三得**外检销**（从"实验室内律"升"发育事实"）；
> 若答『否』而 2b/16c 仍过——序效应**附袋条件**（低熵重复的真 CDS 不产波），梁三措辞降级"高结构差异袋之律"候审，**不豁免不遮掩**。

## 0. 弹药（sha 立户）
- 原料: CHILDES Brown(214)+Bernstein(50) 会话 .cha, 264/264, 月龄 13–62（主人 0926 会话内自 TalkBank 取得, 依 Letter 033 三承诺: 只发衍生测量, 不回传原文）;
- 铣程: CHAT 清洗（CHI/MOT 等语者行, 错话头取词干, 附行/时戳剥离）→ 全量 91,641 行留仓（from-scratch 大案 PB22 备用）;
- **本弹小袋**（与 LADDER-2b 剂量同尺可比）: 三档定籽抽样各 1200 参训 + 300 held-out
  - B1_13-24 sha ee68a37b3f97 / B2_25-40 sha 0758506cb86a / B3_41-62 sha e22260ca67c8（curriculum_small/manifest.json）
  - 抽样籽 20260926, 清洗与切分全程确定性, 复铣可复现。

## 1. 弹道（LADDER-2b 原舱改制, 一弹两仓 env 已通）
- 两臂: **ladder**（B1→B2→B3 月龄序贯）vs **mixed**（同袋全局乱序）;
- seeds {13,14,15} × 双臂 = 6 舱次; LoRA r16/α32 七靶 lr1e-4, 2 epochs, batch=8, seq=256——**与 2b 逐项同方, 读数跨案可比**;
- 底座 Qwen2.5-0.5B-Instruct（Kaggle 挂载 /kaggle/input/models 或 AutoDL LADDER_MODEL）;
- checkpoint: 每 epoch 3 拍, 每拍三段 held-out CE 轨迹（ce_traj）。

## 2. 判据（先冻, 逐 seed, 2/3 多数——与 2b 同门同阈, 不许改尺）
- **H-w1 波浪不对称**: A = Σ₊(三段 held-out CE 正增量), 要求 **A_ladder ≥ 2·A_mixed** 于 ≥2/3 种子;
- **H-w2 节省法**: ladder 臂各段 末 epoch 低点 − 首 epoch 低点 ≤ **−0.10 nats** 于 ≥2/3 种子;
- 旁观不判（如实报）: 各段终值 NLL 的月龄梯度 / B1 高重复袋是否天然低波（真 CDS 熵低, 波幅基线预期低于 2b——**若不对称比仍过闸, 说明序效应扛得住低熵袋, 外检更硬**）。

## 3. 生死与账
- 双过 = 梁三外检销钉 + 序效应三袋系会师（合成幼儿袋/成人七域袋/真 CDS 袋）;
- 任一败 = 按 §0 裂法入册, 2b/16c 账不追改;
- 原始 json 先 sha 入册再判读; 衍生测量可发表（MacW 亲批 "Publishing derived measures is fine", 0925 函在匣）; **原文一字不发**。
- 排场: Kaggle 双席位夜航（AutoDL 待主人开机可迁）; 回收四验哨入队。
