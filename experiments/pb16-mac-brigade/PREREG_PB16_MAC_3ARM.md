# PREREG_PB16_MAC · 三臂课程对决（S 域序 / R 乱序 / B 旅制）· B 机执行案

> 状态：**判据先冻**（本文提交之时 = 任何一格训练开始之前）
> 上位册：`PREREG_PB16_redblue_exercise.md`（红蓝两军·J1–J4 已冻，本案不重开）、
> `PREREG_PB15_order_tournament.md`（海选·**未获主人另批，本案不射**）、
> `cora-atlas/letters/HANDOFF-MacB-0.5b-brigade.md`（任务书）、
> `cora-atlas/iterations/2026-09-23-brigade-corpus-doctrine.md`（C42/C43 + 四句律）。
> 执行席：MacB（m1-16g）· 仪：`run_pb12_3arm.py`（本案）+ 在册几何仪（exp11 `matrix_run.py` 之 SVD/overlap 管线）。
> 出品路径：`artifacts/results/pb16-mac/report_macb.json`（任务书 §2.7 指定）。

## 0. 三臂（唯一变量 = 课程；语料、剂量、序之外的一切冻死）

| 臂 | 课程 | 出处 |
|---|---|---|
| **S 域序**（= PB16 红方） | 七域按冻结序 general→code→spring→summer→legal→medical→mid 逐块整训，块内洗牌 | PB16 §0 序 |
| **R 乱序**（= PB16 §4 并入之第三者观战，即 P-B12 臂 R） | 295 对全局句级打乱 | P-B12 |
| **B 旅制**（= PB16 蓝方） | 每 batch = 七域各一对的等比混编旅（轮转队列），逐 epoch 轮换 | 中型旅语料律 |

- **底座**：Qwen2.5-0.5B-Instruct（ModelScope 取，**sha256 入 `models/manifest.json` 后方可动第一枚 token**）。
  **降级条款（先冻）**：若 Instruct 下载三次不通 → 改用在册且已验讫的 Qwen2.5-0.5B（`88c14255…`，
  即 PB16 §0 原登记底座），并在报告与回执中记为**偏离**（不静默换底座）。
- **弹药**：`experiments/exp11-kaggle/matrix_corpus_embed.py` 七域内嵌件，解包即验
  （sha256 七/七中，395 条：spring 55 / summer 55 / code 40 / legal 40 / medical 40 / mid 110 / general 55）。
  一字不符即停。
- **配方（exp11 在册原样）**：LoRA r=16 · α=32 · dropout=0.05 · targets 七件套
  （q,k,v,o,gate,up,down_proj）· bias=none · AdamW lr=1e-4 · seed 13/14 双跑 · **4 epoch** ·
  batch=7 · accum=1（三臂同步数等 token；见 §1 之偏离记录）。
- **dtype 偏离（先记）**：MPS/float32（exp11 Kaggle 侧为 CUDA/bfloat16）。三臂同 dtype，臂间可比；跨机对表时此为一格已知差异。
- **并发律**：16 GB → 一次只跑一个训练进程（任务书 §4/园区律）。

## 1. 等预算之构造（"等总 token"的执法方式）

1. **考卷先切**：每域按固定随机种子 `20260923` 抽 ⌈n/4⌉ 条为 **held-out 永不参训**
   （spring 14 / summer 14 / code 10 / legal 10 / medical 10 / mid 28 / general 14 = **100 条考卷**）；
   参训集 = **295 条**，三臂**同一多重集**，故每 epoch 消耗 token 严格相等。
2. **批形**：三臂皆 batch=7 → 43 批/epoch（末批 1 条，三臂同形），4 epoch = **172 步/跑**，6 跑 = 1032 步。
   B 臂的 7 槽恰为七域各一（满编旅 42 批 / 缺编尾批 1 批，缺编数入档）。
3. **同数不同序**：S 与 R 也取 batch=7（而非 exp11 的 batch=2×accum=4）——
   为使三臂**步数与 batch 形完全同构**，序是唯一变量。此选择先冻于此，跑后不改。

## 2. 判据（先冻 · 跑后只记不改）

段（segment）定义（臂间可比）：把每 epoch 的 43 步切成 **7 段**（7,6,6,6,6,6,6），段 k 的更新
ΔW_k = vec(Σ_l (B_lA_l)_after − (B_lA_l)_before)（七 target 模块拼接，float64）。

| 号 | 观测量 | 算法 | 预测（旅制律） |
|---|---|---|---|
| **K1 无缝/横纹**（C42 第一口血） | 段能量谱 E_k=‖ΔW_k‖ | 报告 CV(E)=std/mean 与 E₁/E₇ | S 呈**阶梯**（CV≥0.50 且 E₁/E₇≥1.5）；B 呈**横纹**（CV≤0.25） |
| **K2 干涉热图** | 7×7 段间 cos(ΔW_i,ΔW_j) + k90 子空间重叠（在册仪） | "先入霸权行" = mean cos(段1, 段2..7) | S 该行显著高于 B；B 近对角/均匀 |
| **K3 终局战损**（主判据） | 各域 held-out NLL（100 条考卷，per-domain 均值） | 七域 NLL 均值，逐 epoch 曲线 | 蓝 ≥ 红（PB16 J2 同向）；**须跨 seed 13/14 复现**（差 ≤0.05 nats 视作同向） |
| **K4 后入折扣** | 后入三域 {legal, medical, mid} 终局 NLL | S − B 之差 | B 之后入折扣显著小于 S（PB16 J2 之量化） |

**R 臂角色**：第三者观战——若 R ≤ min(S,B)（乱序反而最好）→ 旅制律与域序律**同降候审**，照登（此即 P-B12 之"若 B ≤ S → 律降级"款的对称面）。

**诚实条款（PB16 J4 之三臂版）**：若 S 总分反胜 B → "先来圈地"红利大于"混编公平"红利，
C42 升格为代价声明、旅制律降级候审——**照登，不改判据**。

**双 seed 失败门（PB15 补丁 A 之借用法）**：先跑功率自测——若任一臂两 seed 的 K3 终局差 > 两臂间差的 1/3，
则序效应低于噪声，全案记 **INCONCLUSIVE**（不得换指标救场）。

**主张范围（补丁 C 先冻）**：本案只声称"该协议·该尺度（0.5B）·该语料（在册七域 395 条）下的课程签名"，
不声称普适定律；跨尺度（1.5B）与跨基质（生物侧）另案。

## 3. 产物与匣账（园律二/三）

- 每 epoch 末存 LoRA checkpoint（safetensors，全 lora_A/B）→ 磁盘 `out/`（**不入 git**，律 3）；
  全部 ckpt 的 **sha256 入 `artifacts/results/manifest.json`**（先 pin 后析），0 字节文件一律作废重跑；
- `report_macb.json`：三臂 × 两 seed × 逐 epoch 的 K1–K4 全表 + 环境（torch/transformers/peft 版本、MPS、
  墙钟、缺编批数）+ 全部输入输出 sha256；
- 崩臂留痕：traceback 与已完成段落的 json 一并入匣，附 `FAILED` 标记，不许静默消失；
- 回执：改 `cora-atlas/letters/HANDOFF-MacB-0.5b-brigade.md` 加"## B 机回执"段 + 本目录 json/log。

## 3.5 仪器试射（dry run · 亦先冻）

依 PB15 补丁 A「仪器未验先射才是真裸体」：正式跑之前，先以 **1 epoch × 1 seed(13) × B 臂**
在 `out_smoke/` 试射一遍，只为验三件事——(a) 段快照/几何管线不出 NaN、(b) checkpoint 非 0 字节、
(c) 墙钟在预算内。**试射产物不入结果表、不入判据、不参与任何比较**，只作为日志留在本目录。
试射完成 → 正式跑（`out/`）；两匣路径分开，永不混列。

## 4. 变更记录

- v1（2026-09-23 · MacB）：依任务书 §2 三臂 + PB16 冻结判据 J1–J4 落地为 K1–K4；
  为三臂步数同构改 batch=2×accum=4 → batch=7（先冻于 §1.3）；PB15 海选未批不射。

## 5. 本案登记的两处账目矛盾（照登，不改任务书）

1. **目录名占号**：任务书指定产物入 `artifacts/results/pb16-mac/`，但 `PREREG_PB16_redblue_exercise.md`
   与 `PREREG_PB16_D_visualization_plan.md` 已占 PB16 号（本案即 PB16 之三臂执行面，非新案）→
   沿用 `pb16-mac` 路径不改（A 机账要收在此），本册自我定名 **PB16-MAC**；若园笔认为应另立 PB17 号，回帖改之。
2. **"170 语料"无对账物**：任务书标题作"0.5B+170 语料"，但 §2.3 指定弹药 = 七域内嵌件（395 条 /
   去 mid 重后 285 条 / 切考卷后参训 295 条），园内在册另有 172 空间（atlas-module1）与 172 题 fresh-probe 卷。
   本案按 §2.3 的**在册七域**执行，"170"之出处待园笔指认（*question*，不入结论）。
