# PREREG — Atlas 模块一 (概念图谱构造+验证) · 2026-09-18/19
**Commission:** owner 12:28 谕「模块一安排在 kaggle 执行; 18:00 前备好, 夜里跑」; 源文档 模块一 docx (LETHE intake sha 61e17591…)
**Deterministic build:** atlas_build.py 纯函数生成 (无随机源, 重跑字节同) — 60 空间 × 360 token, 七域 (市井10/叙事6/科技10/医疗8/法律8/教育8/自然10), 零重复断言在码内
**Weight rule (文档钦定):** token 序即时间序; time_weight = 0.2+0.8·i/(n-1) 单调递增; alpha = 5-bin Dirichlet 浓度 (高斯鼓包定位自身时隙, σ²=0.6) — 塑胶凳 bin1 峰 3.637, 末位 bin5 峰, 与文档示例语义对齐
**Night kernel (验证不产数据):** 0.5B 挂载 (与 exp11-baseline 同镜像同疫苗), embed 360 tokens → 每空间 intra 均余弦 · 全局跨空间最大碰撞 top15 · 弱空间榜
**H-A1 (预备判, 供模块二准入):** intra 中位 > 0.75 且不存在 inter ≥ intra中位的跨空间碰撞 → 图谱可分, 准入模块二 (Qwen3B+LoRA 训练目标即此 360×5 α 场) ; 否则列弱空间返工表, 模块二缓行
**Deliverables:** atlas_module1.json (sha 5330bb46…) + report_atlas_m1.json + 弱空间/碰撞榜 → artifacts pin
