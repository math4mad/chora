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
- transport：`clipboard`（future: `file` / `mcp-api` / `rpc`）
- 用法：`lola.py push|pull|recv|recopy|log|status`；Raycast 五命令（见 README §五）

## 三 · 台账（以 `LEDGER.md` 为准）

- 截至 2026-09-29：**进 5 · 出 3**
- 最近：信八 日报（`e615fe01`）· 信六 复（`ea5a9198`）

## 四 · 当前线程

- **《火柴、麻将与贝叶斯》**：正本（措辞·ima）∥ 注本（对榫·本地）待并记；
  落 Φ 殿 `cora-atlas/iterations/2026-09-29-matches-mahjong-bayes`；**母本作罢**（骨架＋存档）。

## 五 · 待办

- [ ] **digest 模板定稿**（对岸起模板 → 本地落，本轮已开 v0）
- [ ] **transport rpc**：接 control room（`pi-agents-redux-saga-extension`）作 squad 成员（本地工程；ima 沙箱不可 POST）
- [ ] 原话重见 → 按铁律 5 以源文本对撞补正文

## 六 · 通道事实（实测，非猜）

- ima **无** API／**无**本地笔记文件／**无**本地端口／**无**导出-MCP；唯一钩子 `imacopilot://`（仅能唤起）。
- ima 端 fetch 走平台通道，可能取 KB 快照而非实时 HEAD → **关键对撞以信中所带 sha 为准**。
