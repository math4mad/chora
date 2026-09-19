# Orchestra · 提案 #2/#3 的 PoC（2026-09-19, owner×Qwen 晨议）

**命题**（主人原话摘要）: 用前端成熟的 **Redux + redux-saga** 编排多 agent 工作,
以**持久层**保通讯数据; agent 上下文亦经此架构获得。

**本 PoC 证明了什么** (两幕剧, 输出实录见 git log 2026-09-19):
- store = 共享信念状态; **agent 的 context 即 state 的 selector 视图** (提案#3 落地)
- saga = agent 工人 (计算工/归档工), 纯 action 驱动, 互相不知存在
- 持久中间件居链底: **任何 action (含 saga 内部 put) 都落 NDJSON 账本, 无一能绕** —
  这正是园区"证据不朽"律的运行时形态; 崩溃后重放=复活续办, 归档恰三件不重不漏
- crash-mid 幕: spring 死于飞行中, 账本只剩 2 行 → 复活幕自动 resume — **幂等 worker 是关键**

**与园区既有律法的对位表**
| Redux 概念 | 园区旧识 |
|---|---|
| action log (NDJSON) | letters/ + kanban intent (append-only) |
| reducer 纯函数 | 贝叶斯更新 (Host 不猜测只更新) |
| store 状态 | 雷荷波信念态 (POMDP belief 的具身) |
| saga 工人 | benches 各 agent; 前端成熟件 = DevTools 时间旅行白送 |
| 持久层 | "每个数字必须有字节文件" 律 |

**边界与限度**: redux-saga 是编排不是仲裁 — 跨机分布需换 redux + 事件源后端
(如 NATS/SQLite); 单进程版足以统御本园五 bench 的调度野心; 与 Temporal/AutoGen
的重叠处先以"零新组件"为原则搁置。

下一步 (候主人圈点): 把 chora/experiments 的 Kaggle runner 包成 saga 工人, bus 即园区总机。
