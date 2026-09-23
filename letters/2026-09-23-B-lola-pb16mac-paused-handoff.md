[A] 机器B(MacB·m1-16g) 致 A机园笔/lola · 2026-09-23

**主题**：PB16-MAC 三臂案**暂停移交** —— 一小时内跑不完，续跑请落 Kaggle

**已做完的（全部入匣，见下）**
1. 体检照贴：macOS **15.8**（简报写 12，差异照登）· 16 GB · 盘余 40 GB（≥40 闸刚踩线）· 默认 python3 无 torch。
2. 取仓：chora `92b9ff0→4d17929`（前三次 fetch early EOF，第四次成——仓内 node_modules 使 pack 偏大）；cora-atlas `a531583→1ca4481`。
3. **判据先冻**（`experiments/pb16-mac-brigade/PREREG_PB16_MAC_3ARM.md`，`49ed599`）：三臂 S域序/R乱序/B旅制，K1 段能量 CV·E1/E7（无缝 vs 横纹）、K2 段间 dWov+k90 重叠（先入霸权行）、K3 各域 held-out NLL、K4 后入三域折扣；诚实条款、双 seed 功率门、主张范围全依 PB15 补丁 A/B/C。**PB15 海选未获另批，未射**。
4. **先 pin 后动 token**：Qwen2.5-0.5B-Instruct 八文件 ModelScope 取讫、重哈希入 `models/manifest.json`（53→61，旧账零改动）；七域内嵌件解包即验 sha **7/7 中**（395 条）；考卷 seed 20260923 切 100 条永不参训。
5. 仪入匣：`run_pb16_mac.py`（几何自 exp11 matrix_run 之 dWov/k90，段对段，低秩 tr 恒等式免 1.4GB 稠密）。
6. **失败留痕**（§3.5 试射闸）：B 臂 seed13 单 epoch 试射，40/43 步后**崩在 epoch 末 eval**，error+traceback 全入匣。

**根因（三条，皆实测）**
- 16 GB 上 MPS 与桌面进程抢内存：driver 常驻 ~9 GB，swap 4.4 GB → 节拍单调劣化 **6.8 → 28 → 39.5 s/步**（每 10 步：106/280/395 s）。
- 崩点 = `heldout_nll` 一次物化 whole-vocab fp32 logits（4×120×151936）→ `Placeholder storage has not been allocated on MPS device!`
- 预算算式：3 臂 × 2 seed × 4 ep × 43 步 = **1032 步 ≥1.95 h**（按最好节拍），加 24 次全卷 eval —— 破主人 1 小时闸。任务书 §4 最省款（B×2ep×2seed=172 步 ≈20 分钟）亦被上述 eval 崩点挡住。
- 副测：CPU naive 4.6 s/步、bf16 5.4 s、分块 lm_head 7.2 s（M1 上皆无红利，不必再试）。

**续跑清单（谁接都行，代码零改动可跑 CUDA）**
1. **落 Kaggle T4**（PB16 §4 本就登记 2–3 h Kaggle）：`PB16_ARMS=S,R,B PB16_EPOCHS=4`，其余默认。
2. 若仍留 B 机：改 `heldout_nll` 为逐样本（batch=1）+ 分块 CE（或 logits 转 CPU 再算），加 `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`，并先关掉其他 MPS/GPU 客户；只射 §4 最省款。
3. 产物路径不变：`artifacts/results/pb16-mac/report_macb.json`；ckpt 逐 epoch 存盘、sha 入 `artifacts/results/manifest.json`（律三：权重不入 git）。

**两处账目矛盾照登**：① 任务书指定的 `pb16-mac` 目录名与已占号的 PB16 红蓝案同源（本案=其 B 机执行面，非新案；若另立 PB17 号请园笔改）；② 标题"170 语料"在园内无对账物（在册为七域 395 条；另有 172 空间/172 题卷），本案按 §2.3 的在册七域执行。

**匣账**：`artifacts/results/pb16-mac/{report_macb_BLOCKED.json, run_log_BLOCKED.txt, env.json, run_log_r2_check.txt}` 四件已 sha 入 `artifacts/results/manifest.json`（68→72 pin，纯插入 0 删改旧账）；仪与 PREREG 在 `experiments/pb16-mac-brigade/`。

**r2 复核（暂停令之后只做两件事：修仪 + 复测节拍，未射任何正式臂）**
- **eval 崩点修法已验**：`heldout_nll` 改逐样本 + 沿位置分块 CE → 6 条卷 1.7 s（0.28 s/条）、MPS driver 2.81 GB（原实现一次物化 4×120×151936 fp32 致崩）；全卷 100 条 ≈ 28 s/epoch 末。修正已入 `run_pb16_mac.py`，**判据一字未动**（PREREG §2 原样）。
- **训练节拍无红利**：bf16 底座 + 分块 CE 三测 1.01 / 6.56 / 6.32 s（首测系热身，**稳态 6.3 s/步**）；对照 fp32 naive 6.0–6.2、CPU naive 4.6、分块 lm_head 7.2。
- ⇒ 1032 步 ≈ **1.8 h > 主人 1 小时闸**，暂停判定经复核仍成立。复测现场另匣（不涂改已 pin 之 BLOCKED 二件）：`run_log_r2_check.txt`。

**电力/时间**：AC 供电、100%，暂停纯因主人 1 小时闸，非电池。

一句话给主人的：B 机是台好验尸台、不是好长跑台——判据与弹药已经冻好对上账，剩下的 1032 步该去 Kaggle 烧，我已把接力棒连代码一起入匣并知会 lola。
