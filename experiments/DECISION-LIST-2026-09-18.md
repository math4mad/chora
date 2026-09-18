# DECISION LIST · 候补实验短账 — 2026-09-18 下午
> Compiled by lola@LETHE at the owner's ask ("其他实验，记录一个列表，下午提醒我，我再决定做哪一个").
> This file is a menu, not a registry: nothing here has a kanban row until the owner picks it.
> Cost = wall-clock on machine A (M1 Pro 32GB, MPS) unless stated. Gates cite programme law.

## A · 实验十的直系后代 (venue: chora/experiments/exp10-concept-adapters)
| # | 项目 | 内容 | 成本 | 门 |
|---|---|---|---|---|
| A1 | **10b 种子加固** | spring/summer/mid × seed 14,15 重训，SVD 符号稳定性复检（H4 反转是否扛得住三种子） | ~10 min | **已交付 10:56** — 13/14/15 三种子全反转，report_10b_seeds.json 已 pin |
| A2 | ~~**10c 全序列 KL**~~ **已完成 12:15** | teacher-forced 逐位分布散度，检验 H1 反转的"风格趋同"解释：若逐位平均后 spring~summer 回到最远，风格假说坐实 | ~30 min（推理） | PREREG 增补先行 |
| A3 | ~~**写信升 lane**~~ **信已投 12:35 (Letter 031)**；lane 升否=主人 19:00 裁 | Letter 至 MEF（松动谱带握手）+ Kairos（写方向正交 = 关键窗口的几何底座）；板升 announced | 15 min | 无（随时） |

## B · 看板在册、待决的旧账 (venue: 各 bench)
| # | 项目 | 内容 | 成本 | 门 |
|---|---|---|---|---|
| B1 | **polynn-exp9** | 深度消融：ReLU 在何处退化、Jacobi 是否翻盘；板上评语已放话"either run it or retire it — paperwork that is never spent is costume" | 数小时训练 | PolyNN 自家决定，非园区根 |
| B2 | **exp6-h6a** | (α,β) 早期预警表：H6c 已死by-clause，h6a 的生死待 S=7.880 的复跑判词；k=0 单机 replicate 带（Gate 6 仍开） | ~1 h | Gate 6：两机两种子混淆，须单机补带 |
| B3 | **exp6-curve-source** | MEF rank sweeps 的字节寻位（registered 至今） | 侦察活 | 属 MEF 案头 |
| B4 | **H9-M 日程** | Kairos 正字：E0→E3→E4→E2→E1→R1，~1 h 20 m 顶；R2 激活换腕臂 (S/L/J) | 半天 | 等 MEF 对草案的 adopt/amend/refuse（9-13 到期未答） |

## C · 主上材料库新册（owner 的对话沉淀，未立案）
| # | 项目 | 内容 | 成本 | 门 |
|---|---|---|---|---|
| C1 | **权重热力学 · 冷冻速率** | lr=退火速率，TinyNet 权重香农熵轨迹 vs 晶体结构；脚本已在 `~/Downloads/权重热力学_冷冻速率实验.py`，A 机今有 torch | ~20 min | 中文字体改单语例（同 exp10 教训）；立案需 PREREG |
| C2 | **Cora 突变点定位** | 训练动力学的相变实时检测 — LETHE 已有 GP 漂移诊断器 v1/v2（贝叶斯模型比较+谱截断）正是此题的仪表；下一步 = 把诊断器接上真训练环（Sarcos 或 PolyNN 的 epoch 流） | 半天 | 与 B2 共享仪表，先做 A2 更划算 |
| C3 | ~~**先验指针 · 呼吸实验**~~ **已完成 11:20 (LETHE 7b2c4e9)** Q1✔ Q2真负 Q3✔ + 揭出温度极性bug双园同治 | 《时间轴的指针》的"主力horse跑完代码"：α(t),β(t) 驱动真引擎先验，测概念球后验呼吸是否复现平滑⇄锐化切换；marimo 仪表已立（LETHE 2718） | ~1 h | 属 LETHE 园，不入 chora 板；负结果条款同载 |
| C4 | **设想4 · 矩阵分解行为科学** | Qwen3.7 建议册第 4 想，行为矩阵 × 谱分解；未细读，选前需 20 min 读书立案 | ？ | 需先读文档 |

## 推荐序（lola 的一家之言，主人自裁）
1. **A1 已在炉上** — 午后即有种子表；
2. **A3 写信** — 十五分钟的家务，板即转绿，MEF/Kairos 两案都被点亮；
3. **A2 或 C3** — 前者补 H1 的判词，后者让 LETHE 的引擎亲口回答时间指针；都轻；
4. B 组的旧账各归各 bench，园区根不越权；C1 当下午茶，C2/C4 是正餐需排期。

*提醒已挂弦：今日 14:00（launchd 一次性，到点弹窗附此单，醒着 missed 会自报迟到）。*


## 刷新 · 12:40（主人令：任务完成后更新"未做与有希望"清单）
**今日已闭账**：实验一 ✔ · 实验二 ✔+加固 ✔ · A2/10c(+分组复审) ✔ · A3 信 031 已投 ✔ · C3 呼吸 ✔ · 10d 路由 ✔ · GGUF ✔（165.8 t/s）

**未做与有希望（剩单）**：
1. **B1 polynn-exp9** — 深度消融，"run it or retire it"；数小时训练，需 Joiner 案头决定
2. **B2 exp6-h6a 生死** — S=7.880 复跑判词 + Gate 6 单机补带（~1 h，硬件就绪可跑）
3. **B4 H9-M 正字** — 半日；门在 MEF 回信（09-13 到期，031 信已敲）
4. **C1 冷冻速率** — 下午茶 20 min，脚本现成；立案需 PREREG 十分钟
5. **C2 Cora 突变点定位** — 半天正餐：GP 诊断器 v2 接真训练环，与 B2 共享仪表
6. **C4 设想4 矩阵分解行为科学** — 先 20 min 读书立案
7. **新芽（今日实验自生）**：
   - **10f** 跨域正交扩展：代码/法律/医疗 ΔW 正交复检（10b 机器现成，每对 ~1 h）
   - **10g** 真 gating 网络替换词法 router（CDLoRA 顶层控制器第一具身；MPS 半天）
   - **10c′** 分组判词敏感性：style 定义换刀（仅标点 vs 含功能词）复跑 — 10 分钟
8. 14:00 launchd 提醒**仍在弦上**——届时圈号；主人提前发令则随叫随拆。

### 12:40 二次刷新（Qwen 下午单全部闭账 + 新芽入列）
**下午单已闭**：A2=10c（反转存活缩水3×）· 10c 分组版（§8 预期表被自身证伪，如实归档）· A3 信 031 已投 · 10d 路由原型（0.70/0.267/0.233）· GGUF 374–392MB @ 149.6–165.8 t/s · note v1.0 已立。announced 升否＝主人 19:00 裁。
**有希望新芽（置顶三选）**：
- **10f 跨域正交复检** — 代码/法律/医疗三对 ΔW 正交性，每对 ~1 h，直答 note §6 限度（最推荐）
- **10g 真 gating 网络** — 替换词法 router，CDLoRA 顶层控制器第一具身 = POMDP 动作+奖励入口，半天
- **10c′ 分组敏感性** — style 定义换刀复跑（仅标点 vs 含功能词），10 分钟


### 15:5x 三次刷新 — Exp11 已排期且 P0 已闭
| 役 | 结果 |
|---|---|
| **Exp11 P0 (Qwen2.5-1.5B, 零下载)** | **H8 格 PASS**：专家对 max\|ΔWov\|=0.137<0.2，锚点 0.592/0.637 齐亮；**H7 PASS**：general 探针~诸域 ≈0.018–0.023（第六正交书写者，非共享底座）|
| P1 | **候主人网络点头**：Qwen2.5-3B (~6GB) + Llama-3.2-1B (~2GB)，先 hash 打条后开训 |
| GRAPHIA 案头 V | 破土：paper/ 重排完成，notes/ 落框架笔记，站点改走 **Quarto**（MEF 同母机），表用 gt——quarto 安装中 |
