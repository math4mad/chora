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

---

# ORCHESTRA 框架志（v0.2 骨架已立, 18:11 两幕剧 v2 全绿）

## 解剖图 —— Redux 扩展只有三种物种, 别混
| 物种 | 挂在哪 | 本园成员 |
|---|---|---|
| **middleware** | dispatch 流水线 | guard(00) · saga(10) · persist 写端(90) |
| **store enhancer** | store 本体 | **time-travel**（正解在此, 非中间件）· persist 读端(rehydrate) · DevTools |
| **selector** | 订阅侧 | per-agent 上下文切片 = 渐进披露的唯一读出口 |

「持久层」是一对鸳鸯腿：写端 middleware（链底收票）+ 读端 rehydrate（回放造种子）——单挂一半只能记账不能复活。

## 插座表（00→99, 越靠前越早见票; 每件自带过肩测试+保险丝）
```
00 guard      身份写篱: meta.origin ∉ 名单 → 拒账留审计 (今日实测拒 hacker ✔)
10 saga       P/D/K 工人宿舍
20 throttle   (候) 限流闸
30 bridge     (候) 进程间总线 —— 多机园区
90 persist    链底账本 NDJSON
```

## 上下文铁律（主人方案的定案）
**state.world/plans/clarif = 唯一真身; agents[id].scratch = 私事带篱; 各 agent 的“那一份上下文”由 selector 现切, 不存副本。**
存副本=多本真相=迟早对账打架；切视图=一份真相 N 张车窗。（POMDP 语：belief 共享，观测各自投影。）

## 加件规矩
新中间件三件套：`tests/` 过肩测试、本表登记、可拔保险丝。一次一件, 砸完一颗核桃再上座。
