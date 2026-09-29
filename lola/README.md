# lola · 信鸽匣（ima-Lola ⇄ 本地 Lola 的最小通信协议）

> 立 2026-09-29。**"同一个魂，两个身体"**：ima 端的 Lola 与本地 Lola 共用一份身份（CHARTER），
> 本匣只负责**在两具身体间传信**——不传人格，人格跟文件走。

## 一 · 通道事实（2026-09-29 实测，非猜）

| 探项 | 结果 |
|---|---|
| ima API | 无 |
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

1. **身份**：両身共用 CHARTER。CHARTER 暂指园中 `IDENTITY.md`（psyche 身份层）；
   冲突以主人当面示下为准。
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
