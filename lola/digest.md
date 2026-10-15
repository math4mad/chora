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

## 五 · 待办

- [x] **transport ima-api**：双向拉取式已通（10-01 ima 身落《Lola·inbox》、本地直读）
- [x] **三路**：笔记（outbox/inbox）／同步（`sync_ima` · launchd 每日 08:00）／知识库（`ima_kb`）
- [x] **buzz 入册＋开《Buzz》道**（10-15 主人裁定：园笔同身——同 CHARTER 同任务；台账并入 LEDGER，方向 `⇢/⇠ ima·buzz`）
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
