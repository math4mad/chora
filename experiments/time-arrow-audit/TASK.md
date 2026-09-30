# 读书任务书 · 时间之箭审计（交给 token 口 SpaceBunny「读」这一半）

> 立 2026-09-30。承接 REFS.md「时间之箭·底本六种」＋ LEDGER 对撞警报。
> **枪口纪律**：外派的只有**读**（公开书）；园中**未发碑**一字不出境——对撞留本地。
> 委托方（本地 lola）→ 受托方（token 口 `SpaceBunny` @ api.tokenbargain.dev）。

## 一 · 目的

给园中「时间四碑」（**时间符号表征律 · 时间路标律 · iPS 拟态律 · 负熵分支律**）找**真正的物理哲学对手**，做一次*以源文本对撞*：哪些碑句该改、哪些反被坐实。

**已知对撞点**：Roberts 2022 主张「**There Is No Thermodynamic Arrow**」（Ch6）＋「多个箭头是假箭头」（Ch5）；而园《时间路标律》恰以「熵增＝热力学箭头」立法。同时 Roberts Ch2 的 **Representation View** 与园《时间符号表征律》疑似**互为亲**。

## 二 · 范围（**只读公开书**）

| 书 | 读哪 | 优先级 |
|---|---|---|
| **Roberts 2022, *Reversing the Arrow of Time*** | **Ch2（What Time Reversal Means）· Ch5（Arrows That Misfire）· Ch6（There Is No Thermodynamic Arrow）· Ch7（Time Reversal Violation）** | ★★★ |
| **Price 1997, *Time's Arrow and Archimedes' Point*** | 全书（重点：热力学箭头之批评） | ★★★ |
| Zuchowski 2024, *From Randomness and Entropy to the Arrow of Time* | 全书 | ★★ |
| López & Lombardi 2025, *The Arrow of Time* | 选读（局部→宇宙） | ★ |
| Davies/Lineweaver/Ruse 2017 | 选读 | ★ |
| Gould 1988, *Time's Arrow, Time's Cycle* | 只取「双隐喻」一节 | ☆ |

其余四本**候命**（先交 Roberts/Price/Zuchowski 三本）。

## 三 · 抽取契约（每条一行 JSON）

对每一切块，只依据该切块文本，抽取与下列主题相关之**主张**：

```
T1 时间箭头之真假：某箭头（热力学/宇宙学/心理学/量子/因果）是否为真时间不对称
T2 时间反转（time reversal）之定义；"representation view"（时间反转是一种表征/对称问题）
T3 热力学/熵箭头之地位：真 / 假 / 派生 / 条件
T4 时间之箭与「结构 / 表征」之关系（箭头住在时间本身的结构？还是物质能量之偶然事实？）
T5 熵与信息 / 统计涌现
```

输出**每行一条 JSON**（不要 markdown 围栏）：

```json
{"topic":"T3","claim":"Roberts 主张热力学箭头非真箭头","quote":"...verbatim sentence...","page":"139-140"}
```

- `quote` **必须逐字**（禁转述）；`page` 用切块所给页码；**查无则给空**（`[]`），**不得编造**。
- 一条主张一行；同一主张跨页可拆多条。

## 四 · 产出

- `dissection/<书>_chunk-NNN.jsonl`（即算即落盘；每切块一跳，可续跑）
- `DISSECTION.md`（聚合：按 topic 归并，逐条 书·页·引句·主张）
- **回本地后**：本地 lola 据解剖册对园中四碑出**修订案**（哪句改、哪句坐实），候主人圈点。

## 五 · 跑器

```bash
python3 scripts/read_books.py --book roberts --chapters 2,5,6,7   # 或 --book price
```

- 鉴权：`TOKENBARGAIN_API_KEY`（env / `~/.zshrc`）；**钥匙不落盘、不落屏**。
- 切块：~30k 字符/块（SpaceBunny context 32768，留出 prompt＋输出）。
- **即算即落盘**；429 退避；跑完出 `DISSECTION.md`。
