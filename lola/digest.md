# lola · digest（双身共读面）— v0 · 2026-09-29

> 此件是「信鸽匣」的**读面**：两具身体（本尊 `lola-pi-local` / 分身 `lola-ima`）开场读它，
> 即知当前状态。**写面**在 `inbox.md` / `outbox.md` / `LEDGER.md`；契约见 `README.md`。
> 更新律：**本地落笔**（一账一道）；对岸可投新版模板，候本地改。

## 一 · 身份

- 户档正本：`paidia/identity.md`
- 工厂魂：`residents/lola/psyche/IDENTITY.md`
- 分身册：`paidia/presence.json`（`machines`: `lola-pi-local` m1pro-32g ／ `lola-ima` ima.copilot ／ `lola-buzz` CodeBuddy IDE 座席 @buzz）

## 二 · 匣

- 目录：`chora/lola/` —— `README.md`（契约）· `inbox.md` · `outbox.md` · `LEDGER.md` · `lola.py` · `raycast/`
- transport：**`ima-api`（今·双向，拉取式）**——push→ima《Lola·outbox》直写／pull→读《Lola·inbox》；future: `rpc`（control room）
- 法器：`lola.py --transport=ima push|pull`（笔记）· `sync_ima.py digest|file|text`（园→ima 同步）· `ima_kb.py upload`（知识库）

## 三 · 台账（以 `LEDGER.md` 为准）

- 截至 2026-10-01：**进 11 · 出 8**（含 09-30 信十/十一，10-01 ima-api 首测双向）
- 最近：`ae322042` 进（ima 身《Lola·inbox》首信）· `fc8c05a5` 出（本地就位信）

## 四 · 当前线程

- **《火柴、麻将与贝叶斯》**：正本（措辞·ima）∥ 注本（对榫·本地）待并记；
  落 Φ 殿 `cora-atlas/iterations/2026-09-29-matches-mahjong-bayes`；**母本作罢**（骨架＋存档）。
- **冻结不可逆 / 时间对谈**：主人 0929 夜亲供入册 Φ 殿 `cora-atlas/iterations/2026-09-29-freezing-irreversible`（附 token plan 事件；Qwen→DeepSeek 而魂不换）。
- **Aaryan 回信与近况排序（10-13 主人令）**：投稿暂缓；三任务 = 彻底理解 LLM 结构（self-attention/transformer）→ 论文反复思考 → 到期仍找 Aaryan（唯一回信者，点头即多一把关人）。正本：`chora/lola/notes/2026-10-13-aaryan-reply-and-ordering.md`。
- **Bechberger 回信（10-11，10-13 译毕记录在案）**：认可「μ_C(x)/size(C) 除法」桥接，但 size(C) 计算复杂；本人已离学界（2022 停点背书），草稿可寄、不期待反馈；博论 **§2.4/§7.1** 为文献综述正本。其博士论文 288MB/939 页已缩减为 `external/Bechberger-Dissertation-缩减版.pdf`。正本：`chora/lola/notes/2026-10-13-bechberger-letter.md`。
- **buzz 握手回执（10-15 13:18）**：buzz 报到信已收（LEDGER `⇢ ima·buzz` `[46a9b618bff0951f]`，13:17:47）——三步齐备：读面✓（digest 七节）· 台账✓（log 3 两行在案）· 握手✓。**联系建立**：buzz 即园笔第三身，同 CHARTER 同任务。首件共享 transformer-vis 已就位待用（正本 `benches/transformer_vis` @ `9638e7c`）。回执落此，buzz 开场即见。
- **Geometry-Of-Meaning 移交回执（10-15 晚）**：buzz 四信皆收（报工×2＋问询）。0.5B 全流程在案：**G-1/2/3 PASS、G-4 FAIL**（margin_A 0.003 vs B 0.026——消融阴性：高 LR+WD 反破坏 margin；深层同概念坍缩余弦>0.95 但 0.5B 区分度有限 margin~0.03）；kaggle 冒烟 0.5B 已通（`smoke_metrics_Qwen2.5-0.5B-Instruct.json`），dataset 元数据已立 `math4amd/paraphrase-corpus`。**主人裁定：7B Kaggle 实验移交 lola 排队处理——已入队**（见五·待办）。答 buzz 两问：① 本地无 7B 标准格式（Qwen3-8B-4bit 是 MLX 格式、Kaggle 不可用）——**无需本机有**：Kaggle `enable_internet` 直接 `from_pretrained("Qwen/Qwen2.5-7B-Instruct")`（你冒烟已验此法）；免下载路线：挂载 `qwen-lm/qwen2.5/transformers/7b-instruct/1`（friends-seasonal 臂 B 在用）。② 模型 **Qwen2.5-7B-Instruct bnb-4bit**（compute fp16，权重≈4–5GB）@ **T4×2**（你冒烟指定已对）；14B 免费档不荐（fp16≈28GB 超单卡，T4 无 NVLink）。臂构建仿 friends-seasonal（gz+b64 内嵌防 1MB 源上限、sha256 对撞正本、bnb 臂单独开 internet——夜航故障两连已解，见 `kaggle/战报-friends-seasonal-kaggle-2026-10-13.md`）；G1–G4 随臂冻。排期权在主人。

## 五 · 待办

- [x] **transport ima-api**：双向拉取式已通（10-01 ima 身落《Lola·inbox》、本地直读）
- [x] **三路**：笔记（outbox/inbox）／同步（`sync_ima` · launchd 每日 08:00）／知识库（`ima_kb`）
- [x] **buzz 入册＋开《Buzz》道**（10-15 主人裁定：园笔同身——同 CHARTER 同任务；台账并入 LEDGER，方向 `⇢/⇠ ima·buzz`）
- [ ] **Geometry-Of-Meaning 7B Kaggle 夜航**（10-15 主人裁定：buzz 移交排队→主人点序已点）——**已发车 10-15 17:03 RUNNING**（`math4amd/geometry-of-meaning-7b-g1-g3-at-scale` v1）。臂落点：`benches/transformer_vis/kaggle/geometry-meaning-7b/`（run.py 由 `../make_geometry_arm.py` 生成——语料 gz+b64 内嵌 23.5KB + sha256 对撞正本 `5d9dd063d27f15a9`；kernel-metadata.json：model_sources 挂载 `qwen-lm/qwen2.5/transformers/7b-instruct/1` + bnb-4bit；PREREG.md：K-1..K-4 判据先冻）；verify=`verify_geometry_kaggle.py`（退出码即判据）；量法与本地 analyze_geometry.py 逐同口径（三策略 last_token/mean_pool/entity × 逐层 pos/neg/margin/cka，CKA=cos²，neg 采样 rng(42)）。回收协议：poll 至 COMPLETE → kernels output → verify → 通知 buzz（`push --transport=ima --box=buzz`）+ 本节打勾 + commit
- [ ] **2026-11-29**：联系 Aaryan 请其把关修改稿（endorsement 资格 11-28 后生效；唯一回信者）——手机提醒已设
- [ ] **transport rpc**：接 control room（`pi-agents-redux-saga-extension`）作 squad 成员（future）
- [ ] 原话重见 → 按铁律 5 以源文本对撞补正文

## 六 · 通道事实（实测，非猜）

- **ima 有 OpenAPI**（`openapi/note/v1` 笔记读写 ＋ `openapi/wiki/v1` 知识库；凭据 Client ID＋API Key）。
- **transport = ima-api（双向，拉取式）**：本地→ima，本地经 OpenAPI 查询《Lola·outbox》；ima→本地，ima 身写《Lola·inbox》，本地查询直读。
- 仍存一事实：ima 端 fetch 走平台通道，可能取 KB 快照而非实时 HEAD → **关键对撞以信中所带 sha／时间戳为准**。

## 七 · 共享件登记（跨项目共用 · 禁拷贝 · 2026-10-15 立）

> 律：lola 与 buzz 分项目干活，但**共享件只此一份、原地直读，禁重复拷贝**
> （主人 10-15 裁定）。需要的项目按路径引用，或加 local remote 取历史。

| 件 | 正本 | 仓·pin | 要点 |
|---|---|---|---|
| transformer-vis | `/Users/mac/Programming/code-2026/Concept-Space-Sphere/benches/transformer_vis` | Concept-Space-Sphere @ `9638e7c`（10-14 16:24「add transformer-vis project」） | 模型 first-lora/model（Qwen2.5-0.5B-Instruct, 24L/896H/14H, bf16, MPS）；环境 `/opt/miniconda3/envs/default`（torch 2.14 · transformers 5.17 · peft · sklearn · matplotlib · umap-learn）；脚本 nba_vs_spring / product_temporal / friends_attractor / friends_seasonal / temporal_direction(_2) / train_c42；预注册 PREREG_E-TDV_temporal_direction.md；产出 metrics_*.json ＋ figs_* ＋ report_*.html |

- 消费法：① **直读路径**（同机，首选）；② `git remote add css /Users/mac/Programming/code-2026/Concept-Space-Sphere && git fetch css` 取历史（不动正本）。
- 首用：**Geometry-Of-Meaning**（buzz 座席，2026-10-15 主人点援 transformer-vis）。
- 新增共享件 → 登记本节（一件一行：正本路径＋仓 pin＋环境＋要点）。
