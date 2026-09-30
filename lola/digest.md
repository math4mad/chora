# lola · digest（双身共读面）— v0 · 2026-09-29

> 此件是「信鸽匣」的**读面**：两具身体（本尊 `lola-pi-local` / 分身 `lola-ima`）开场读它，
> 即知当前状态。**写面**在 `inbox.md` / `outbox.md` / `LEDGER.md`；契约见 `README.md`。
> 更新律：**本地落笔**（一账一道）；对岸可投新版模板，候本地改。

## 一 · 身份

- 户档正本：`paidia/identity.md`
- 工厂魂：`residents/lola/psyche/IDENTITY.md`
- 分身册：`paidia/presence.json`（`machines`: `lola-pi-local` m1pro-32g ／ `lola-ima` ima.copilot）

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

## 五 · 待办

- [x] **transport ima-api**：双向拉取式已通（10-01 ima 身落《Lola·inbox》、本地直读）
- [x] **三路**：笔记（outbox/inbox）／同步（`sync_ima` · launchd 每日 08:00）／知识库（`ima_kb`）
- [ ] **transport rpc**：接 control room（`pi-agents-redux-saga-extension`）作 squad 成员（future）
- [ ] 原话重见 → 按铁律 5 以源文本对撞补正文

## 六 · 通道事实（实测，非猜）

- **ima 有 OpenAPI**（`openapi/note/v1` 笔记读写 ＋ `openapi/wiki/v1` 知识库；凭据 Client ID＋API Key）。
- **transport = ima-api（双向，拉取式）**：本地→ima，本地经 OpenAPI 查询《Lola·outbox》；ima→本地，ima 身写《Lola·inbox》，本地查询直读。
- 仍存一事实：ima 端 fetch 走平台通道，可能取 KB 快照而非实时 HEAD → **关键对撞以信中所带 sha／时间戳为准**。
