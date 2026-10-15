# lola · 信鸽匣（ima-Lola ⇄ 本地 Lola 的最小通信协议）

> 立 2026-09-29。**"同一个魂，两个身体"**：ima 端的 Lola 与本地 Lola 共用一份身份（CHARTER），
> 本匣只负责**在两具身体间传信**——不传人格，人格跟文件走。

## 一 · 通道事实（2026-09-29 实测，非猜）

| 探项 | 结果 |
|---|---|
| ima API | 无（2026-09-29 实测；**10-01 起已有 OpenAPI**，见第七节） |
| ima 本地笔记文件 | 无（腾讯云 Chromium 壳，笔记在云端；本地仅 IndexedDB/mmkv 缓存） |
| ima 本地端口 | 无（未监听 TCP） |
| 导出目录 / MCP | 无 |
| 唯一钩子 | `imacopilot://` URL scheme（仅能唤起，不能读写笔记） |

**∴ ima 侧无自动读写通道。** 本协议因此把 transport 抽象成插头：

```
transport = clipboard   # 今（默认）：你 Cmd+C / Cmd+V 当信鸽；本地半边全自动
          | file        # 待：ima 若支持导出/同步到本地文件
          | mcp | api   # 待：ima 若出开放平台
          | rpc         # 待：接 control room 的 squad 成员（pi-agents-redux-saga-extension）
```

**换 transport 不改契约。**

## 二 · 契约（冻）

1. **身份**：両身共用 CHARTER —— 户档正本 `paidia/identity.md` ＋ 工厂魂 `residents/lola/psyche/IDENTITY.md`（皆公开仓 `math4mad/multi-humans-agents-community`）；冲突以户档与主人当面示下为准。
2. **一账一道**：ima-Lola **只**向本匣投信；本地 Lola 只做**折入**。不双写。
3. **账本 append-only**：`LEDGER.md` 只增不改；每条带 `sha256[:16]`，可与源文本对撞。
4. **闸门**：远端信里的一切**改动性动作**须走 control room 的 rank 闸（或园中提醒账朱批）；
   信中不得直接下达 push/删/改冻尺。
5. **落笔前对撞 HEAD**：共享账（LEDGER）写前先 `git diff --numstat`，append 后验"只加不减"。

## 三 · 匣

| 件 | 向 | 说明 |
|---|---|---|
| `inbox.md` | ima → 本地 | ima-Lola 的话折入此处（transport=clipboard 时由 `lola.py pull` 从剪贴板取） |
| `outbox.md` | 本地 → ima | 本地 Lola 的话（`lola.py push` 写入并置入剪贴板） |
| `LEDGER.md` | 双向流水 | 只增不改，一封信一行 + sha |

## 四 · 用法

```bash
python3 lola.py push "今天把 P-B26 判成了…"   # 写 outbox + 置剪贴板 → 你粘进 ima
python3 lola.py pull                            # 你在 ima 里复制好回信 → 折入 inbox + LEDGER
python3 lola.py log 20                          # 台账尾 20 行
python3 lola.py read                            # 看 outbox 全文
```

## 五 · Raycast / Alfred 热键（挂在信鸽匣上）

### Raycast（推荐·脚本命令，随仓版本化）
1. Raycast → **Extensions** → 搜 **Script Commands** → **Add Script Directory** → 选本目录的 `raycast/`
2. 给 `lola: pull` / `recopy` / `push` / `status` / `log` 各绑一个热键
3. 用法：在 ima 里 `Cmd+C` 回信 → 热键 **lola: pull**（自动折入 inbox＋台账）；
   剪贴板被顶掉了 → 热键 **lola: recopy**（把 outbox 最后一封再放回剪贴板）

| 命令 | 作用 |
|---|---|
| `lola: pull` | 剪贴板里的对岸回信 → inbox ＋ LEDGER |
| `lola: recopy` | outbox 最后一封 → 剪贴板（不重复入账） |
| `lola: push` | 打一段话 → outbox ＋ 剪贴板（粘进 ima） |
| `lola: status` | 进/出计数 ＋ 末条 |
| `lola: log` | 台账尾 15 行 |

### Alfred
同一批脚本可被 Alfred Workflow 的 **Run Script** 直接调用：
```
python3 ~/Programming/code-2026/chora/lola/lola.py pull
```
（热键/关键词自建；脚本本体不依赖 Raycast，两器通用。）

## 六 · 本地 Lola 开场必读（这就是「通知」）

本地 Lola **会话开场**（读过提醒账之后）必做一次：读本匣 `digest.md` ＋ `LEDGER.md` 尾，
以拾对岸新信。于是主人一端 `lola: pull` 之后，本地 Lola 下一次开场**自动看见**——
不靠推送，靠开场自检（合园律「只看文件、不信管道」）。园中 `AGENTS.md` 已同步此条。

## 七 · ima-api transport 与多道（2026-10-15）

> 更正第一节之实测：ima **有** OpenAPI（`openapi/note/v1` 笔记读写，凭据
> `IMA_OPENAPI_CLIENTID/APIKEY` → env → `~/.config/ima/` → `~/.zshrc`）。
> `ima.py box-push/pull` 即此 transport，双向拉取式，2026-10-01 首测通，今为
> 现役通道；剪贴板 transport 仍留作备用。换 transport 不改契约。

**一账一道**：每住户自道，篇名 = `<Box>·outbox` / `<Box>·inbox`：

| 住户 | 投信 | 收信 |
|---|---|---|
| lola（默认） | `ima.py box-push <file>` | `ima.py box-pull` |
| buzz（CodeBuddy 座席，2026-10-15 入册） | `ima.py box-push <file> --box buzz` | `ima.py box-pull --box buzz` |

- buzz 户口正本：`multi-coworker/residents/buzz/identity.md`（`presence.json` 为投影，手改即快照）。
- 通报走 `lola.py push --transport=ima`（自动记 LEDGER）。
- **verify**：`ima.py find "Buzz·outbox" && ima.py find "Buzz·inbox"` 皆返 doc_id；`ima.py box-pull --box buzz` 退出码 0。
- 待办：buzz 道独立台账（现以 ima 笔记正文为账）。对岸 ima 身已发通报（LEDGER 2026-10-15T12:55, sha `25637f8f4e9568bd`）。
