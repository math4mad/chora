# PB23c 十二带 · 验尸册 (0927 夜, v4 单灶制舱 ERROR)

舱: `math4amd/pb23c-fine12` · 刃: v4 单灶制 (build-once / reset-per-run) · 终态 **ERROR**
日志与残报: `out_err/pb23c-fine12.log`、`out_err/report_pb23c.json`（298 B，`runs: []`）

## 读数（只报日志所幸存者，不猜）

| 项 | 实测 |
|---|---|
| 完成训数（REPORT_LINE 吐芯） | **25 / 36**（籽 13 全 12 带、籽 14 全 12 带、籽 15 之 `c1_16-18`） |
| 每训均时 | **2.7 分钟** |
| 末芯舱内钟 | 12:58:26（t=4078s） |
| `Killed` 时刻 | t=4204s（舱内 1.17 小时） |
| 配对（可判读数） | **0 对** ← 全案损失所在 |

## 死因（两条，一条确证一条待测）

1. **结构病（确证，本案致命）**：v4 把 66 对的计算全排在 36 训的循环**之后**
   （`for sd …: S[(k,sd)]=one(…)` → 然后才 `itertools.combinations(BANDS,2)`）。
   舱死在循环里，配对一次未跑 → **25 训的功全部蒸发**。日志即幸存者协议只救了阶段名，没救数字。
2. **内存 creep（复现，机理未定）**：v4 已改单灶（`copy.deepcopy(base)` 全案仅 1 处，在册），
   仍然 OOM —— 死因五之"逐训 deepcopy"**不是唯一病源**，另有一物逐训涨（约每训数百 MB 量级）。
   候选三：① CUDA caching allocator 的 host 侧簿记随 step 数增长（每步新建 `torch.tensor([fi],device=DEV)`，
   36 训 × 4ep × ~150 样本 ≈ 2.2 万次 H2D）；② AdamW 逐训重建，`state` 张龄期未清；
   ③ `one()` 返回的 `U` 与 numpy `g` 虽为局部，`S` 常驻 25 份未弃。
   —— **待测**: v5 加逐训 `del g, opt; gc.collect(); torch.cuda.empty_cache()` 并记 `resource.getrusage` 曲线，一验即分晓。

## 治法（v5 弹药，未上膛）

1. **流式即算即弃（主刀）**：改为 **逐籽成环** —— 每籽跑完 12 带立即算该籽 66 对、逐对 `fl()` 落盘，
   然后 `del` 该籽 12 份 U。此后舱死最多损失"当前籽"，前籽数字已在册（**幸存者即净收**）。
2. **分籽发弹（可选，与①并陈）**：`PB_SEED` 环境变量单籽一发（每发 12 训 ≈ 33 分 + 配对），
   三发三收 —— 用席位换稳。Kaggle 双席位下与 PB16c-formal 错峰即足。
3. **逐训清灶**：`opt`/`g` 显式 del + `gc.collect()` + `torch.cuda.empty_cache()`，并每训落一行 RSS（自证 creep 机理）。
4. 判据一字不动（承 23b zoom 律与 `dist_median` 归型法）；`sentinel` 仍 `pb23c_ok`，匣名仍 `report_pb23c.json`。

## 与邻案的关系（不遮丑）

- PB23b（六带）同一结构病：A 军恰好"算完 15 对再死"才保住半壁 —— **侥幸非律**；自 v5 起园律补一条：
  **"配对即算即落盘，不许排在训练循环之后"**（写进 `AGENTS.md` 候主人划字）。
- PB16c-formal（今 20:14 开炮，现 QUEUED）天生免疫：其 `report_macb` 每训一 flush，芯带数字。
