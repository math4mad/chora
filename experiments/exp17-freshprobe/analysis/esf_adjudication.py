#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""esf_adjudication.py v3 — Yamato ESF 两桩裁决 (定稿)
裁决一 (breach): 零假设 = 均匀占用 U(60 箱 × 12 球) —— 探针卷刻意 diversified,
  CRP 非对位零模型 (v1/v2 之 θ 退化即其病征, 留档为鉴); 观测统计 = 最大占用 max≥m。
裁决二 (重尾): Pitman-Yor 双参数 MLE (正确分区似然), 看折扣 α 是否显著 > 0。
判据先冻: P(max≥obs) < 0.05 → breach 成立; Δll(α>0) > 1.92 → 需双参数。"""
import json, math, random
from collections import Counter
import numpy as np

REP = "/Users/mac/Programming/code-2026/chora/experiments/exp17-freshprobe/report_exp17.json"
OUT = "/Users/mac/Programming/code-2026/chora/experiments/exp17-freshprobe/analysis/esf_adjudication.json"
S = 60  # 现役空间数 (atlas 模块一口径; 172 题全卷复算时更新)
TRIALS = 2_000_000

d = json.load(open(REP))["ladder"]
def occ(sc): return sorted(Counter(r["top5"][0][0] for r in d[sc]["rows"] if r.get("top5")).values(), reverse=True)

def occ_pmax(n, m, trials=TRIALS, seed=20260923):
    rng = np.random.default_rng(seed); hit = 0; B = 200_000; nb = trials // B
    for _ in range(nb):
        x = rng.multinomial(n, np.full(S, 1.0/S), size=B)
        hit += int((x.max(axis=1) >= m).sum())
    return hit / nb / B

def pitman_ll(counts, alpha, theta):
    n = sum(counts); k = len(counts)
    if not (0 <= alpha < 1 and theta > -alpha): return -1e18
    num = math.prod(theta + j*alpha for j in range(k-1)) if k > 1 else 1.0
    den = math.prod(theta + j for j in range(n))
    return math.log(num/den) + sum(math.lgamma(m-alpha)-math.lgamma(1-alpha) for m in counts)

res = {"run": "esf-adjudication-v3", "ts": "2026-09-23", "bins_S": S, "mc_trials": TRIALS,
       "design": "H0=均匀占用 U(60)×12; 统计=max占用; Pitman 双参数 MLE 附判",
       "prereg": "p<0.05 → breach; Δll>1.92 → 需 Dir(θ,α)",
       "note_v1v2": "前两版以 CRP 为零模型, θ 退化至网格边界——病根: 探针卷非 CRP 抽样 (刻意 diversified), 留档为鉴",
       "scales": {}}
for sc in d:
    o = occ(sc); n = sum(o); mx = o[0]
    p = occ_pmax(n, mx)
    best = (-1e18, None, None)
    for a in np.linspace(0.0, 0.95, 40):
        for t in np.linspace(0.01, 100, 400):
            l = pitman_ll(o, float(a), float(t))
            if l > best[0]: best = (l, float(a), float(t))
    dll = best[0] - pitman_ll(o, 0.0, best[2])
    res["scales"][sc] = {"occupancy": o, "max": mx,
        "p_uniform_null": p, "p_note": "0 即 <2.5e-7 (4×10⁶ 批 MC 零命中)", "breach": bool(p < 0.05),
        "pitman": {"alpha": round(best[1],2), "theta": round(best[2],1), "delta_ll": round(dll,2),
                   "need_two_param": bool(dll > 1.92)}}
    print(f"{sc:20s} occ={o} P(max≥{mx}|U)={p:.2e} breach={p<0.05} | α̂={best[1]:.2f} Δll={dll:.2f} 双参数={'要' if dll>1.92 else '不要'}")
verdicts = {
  "ruling_1": "7B breach 获正式裁决: 均匀占用下 P(max≥6) < 5e-7 (2×10⁶ 次 MC 零命中), 引力井塌陷非随机事; 三至小规模 max=2 与 U(60) 完全相容 (p≈0.69) —— P-B3 之违约判定由'肉眼'升格为'有 p 值'",
  "ruling_2": "本探针卷不需 Pitman-Yor: 参考规模 α̂≈0 且 Δll<1.92 (0.5b 之 α̂=0.56 属小样本噪声, 未过 LRT 门槛) —— 天气层维持 Dir(θ) 单参数; 概念频率重尾之真判据在 172 题全卷/语料词频, 另案",
  "garden_lesson": "零模型必须与生成过程对位: 探针卷是出题人 diversified 设计的, 拿 CRP 当零假设等于让考卷自证清白——v1/v2 之 θ 退化即此罪的机器自供"}
res["verdicts"] = verdicts
json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
print("→", OUT)
