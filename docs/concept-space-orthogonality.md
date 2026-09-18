# 概念空间正交性与可组合 Adapter 架构 · 园区注记 (v1.0)
## Concept-space orthogonality & the composable-adapter architecture — consolidated note

> chora/docs/concept-space-orthogonality.md · compiled 2026-09-18 by lola@LETHE
> Fulfils the owner's afternoon doc §7 "16:00–17:00 整理 note + 架构图" slot; v0.1→v1.0
> permitted by the doc's own clause (升 v1.0 待 A2 结果) — A2 landed same day.
> All numbers cite their pinned bytes: artifacts/results/exp10/report_10{a,b,c}*.json ·
> report_10d_router.json · ADAPTER-PINS*.json · GGUF-PINS.json (manifest four-way clean).

## 一句话 (the sentence)

**Concepts live in the WRITE geometry of ΔW — near-orthogonal across domains (seeds 13/14/15
agree) — while the OUTPUT distributions of two domain specialists stay closer to each other
than either is to the base at every position of an answer, content and style alike. The
composability of `W_output = W₀ + Σ pᵢΔWᵢ` is therefore a fact about weights, not about
behavioural distinguishability, and the router demo (10d) shows the gate pᵢ must do the
work the distributions won't.**

## 证据链 (chain of evidence, one row per arm)

| layer | experiment | reading | status |
|---|---|---|---|
| 行为 | 10a H2 | own-lexicon 0.84 / 0.49 ≫ base; cross≈0 | PASS |
| 行为 | 10a H1 | JS ss 0.42 < base~arms 0.55/0.58 — **reversal** | FAILS-as-registered, kept |
| 结构 | 10b U-B | parents 0.55–1.24 ≪ mid–parent 1.8–2.5; ΔWov(ss)≈0 | 三种子复现 |
| 结构 | 10b V-A | 全对 ≈3.8 — 读方向共享 | 三种子复现 |
| 序列 | 10c | 反转存续但缩水 3× (0.165→0.060) | registered |
| 序列 | 10c grouped | **计划 §8 预期图式不成立**: ss 在 content 与 style 上都最小 | honest disconfirmation |
| 工程 | 10d | routed 0.70 vs wrong 0.267 vs base 0.233; router acc 0.8 | demo |
| 工程 | GGUF | q4_K_M 374–392MB; tg 165.8/149.6/154.6 t/s on M1 Pro | 目标 20 t/s 的 7.5× |

## 架构图 (the diagram, byte-honest)

```
                      ┌──────────────────────────────────────────────┐
                      │        Qwen2.5-0.5B  (FROZEN W₀)             │
                      │   GGUF q4_K_M 374MB · 165 t/s · M1 Pro       │
                      └──────────────────┬───────────────────────────┘
                                         │ reads  (V-side: SHARED across adapters, ≈3.8 all pairs)
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
        ┌─────▼─────┐             ┌─────▼─────┐              ┌─────▼─────┐
        │ 🏮 spring  │             │ 🍉 summer │              │ 🎬 更多空间│
        │ ΔW₁ (W₁写) │             │ ΔW₂ (W₂写) │              │ ΔW₃…       │
        └─────┬─────┘             └─────┬─────┘              └─────┬─────┘
              │   writes orthogonal: ⟨ΔW₁,ΔW₂⟩/‖·‖‖·‖ ≈ −0.002 … 0.13   │
              └──────────────┬──────────┴──────────────┬───────────┘
                     p₁▲     │                 p₂▲     │   gating  W = W₀ + Σ pᵢΔWᵢ
                  ┌────▼─────▼─────────────────────▼───▼────┐
                  │   ROUTER (词法/语义/时间指针 α(t),β(t))  │   ← 10d: routed 0.70 vs 0.27
                  │   输出分布不分离 → 分离的责任在门控       │   ← C3(LETHE): 先验指针可作时间门
                  └─────────────────────────────────────────┘
```

推论三条：**① 概念要组合，分开训、运行时合成**（10b: 混数据=插值，非并集）；
**② 门控是必需品不是装饰**（10c: 输出层两专家互相趋近，只有权重几何分立）；
**③ 时间指针是门控的一种形态**（LETHE C3: α(t),β(t) 门控球系数使锚点 折叠桌→煤气罐 迁移——
先验选择容器，在真引擎上有见证）。

## 限度 (limits, carried from v0.1, none smoothed)
0.5B 底座容量封顶；55 对语料、单域对；merge_and_unload 的 bf16 合并精度未做困惑度对照；
router 是词法玩具（0.8 命中），gating 网络未训；"写方向正交"在更大领域间距（代码 vs 法律）
上未验——那正是 §6.2 与短账里 C4 的去处。

## 与园区他案的手握手
- **MEF 中间特征值论**: 三 adapter 全部写进基座晚谱带 (band pct ≈0.71, top-10% 能量 1.5%) — 同题异器，互证
- **Kairos 关键窗口**: 正交写方向 = "换刀不伤布"的几何条件；时间指针门控 (③) 是其廉价前身
- **CDLoRA 候选框架 #1**: 本文是其 ΣpᵢΔWᵢ 公式的第一块实证砖——砖上有三籽印，仍在候选之列，不是唯一
