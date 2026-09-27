#!/usr/bin/env python3
# PB23c 十二带 · 读数仪 (归型律承 PB23 半正交案 + 23b「一膝加平线」)
# 只渲染不改冻尺: v4 舱内 verdict (polyfit 斜率 ±0.004) 为正判, 本仪另立三笔直观账——
#   ① 逐档中位 ov(d) 全表  ② 膝之所在: d1 与 d2 之落差 ÷ 后段平均波动 (>3 倍即「独高一日」= 真膝)
#   ③ 三镜一像: 三带(23) → 六带(23b) → 十二带(23c) 同距档并陈, 看曲线随粒度变细是下沉/平移/收敛
# 用法: read_curve.py [report_pb23c.json]
import json, sys, statistics as st

P = sys.argv[1] if len(sys.argv) > 1 else "out/report_pb23c.json"
d = json.load(open(P))
# 算法与舱内冻式同构 (run.py: 每对先取三籽中位, 再跨对中位) —— 免得一页纸上两套小数
by = {}
for r in d["runs"]:
    v = r.get("ov") or r.get("write_ov")
    if v: by.setdefault(r["dist"], []).append(st.median(v))
med = {k: round(st.median(v), 4) for k, v in sorted(by.items())}
print("案:", d.get("case"), "· 带数:", len(d.get("bands", [])), "· 对数:", len(d["runs"]))
print("\n距档  n对  ov中位   逐档差")
prev = None
for k in sorted(med):
    delta = "" if prev is None else f"{med[k]-prev:+.4f}"
    print(f"{k:>4}  {len(by[k]):>4}  {med[k]:.4f}  {delta:>8}")
    prev = med[k]
tops = sorted(((max(v), r["pair"], r["dist"]) for r in d["runs"]
               for v in [r.get("ov") or r.get("write_ov") or [0]]), reverse=True)[:2]
if tops:
    print("最高对 (对级口径, 非档级中位):", "; ".join(f"{p} (d{dd}) {mx:.4f}" for mx, p, dd in tops))
    print("  ⚠ 两口径并陈: 「一膝加平线」之膝住在对级 (b0~b1 单对 0.41-0.47 独高); 档级中位只算薄膝 —— 汇报先说口径。")
ks = sorted(med)
if len(ks) >= 3:
    drop1 = med[ks[0]] - med[ks[1]]
    wig = st.mean([abs(med[b] - med[a]) for a, b in zip(ks[1:], ks[2:])]) if len(ks) > 3 else 1e-9
    ratio = drop1 / max(wig, 1e-9)
    print(f"\n膝检: d1→d2 落差 {drop1:+.4f}; 后段平均波动 {wig:.4f}; 倍数 {ratio:.1f}×"
          f" → {'真膝 (一日之隔独高, 之后入带)' if ratio > 3 else '无独高膝 (渐变或平线)'}")
tail = [med[k] for k in ks[-4:]]
print(f"后段四档极差 {max(tail)-min(tail):.4f} (对首档 {med[ks[0]]:.4f} 之 {(max(tail)-min(tail))/med[ks[0]]*100:.0f}%)"
      f" → {'平线带 (核不动)' if max(tail)-min(tail) < 0.03 else '仍在下沉'}")
if "verdict" in d:
    print("\n舱内正判 (冻式 polyfit ±0.004):", json.dumps(d["verdict"], ensure_ascii=False)[:300])
print("\n三镜一像对照:")
print("  三带 PB23  : 邻带 0.29–0.37 (H-o1 不过·半正交定词) · sha 2e9ed5be")
print("  六带 PB23b : 0.3867/0.3579/0.3444/0.3479/0.3297 → 一膝加平线 · sha 0ef8984a")
print("  十二带     : 见上表 ← 本仪")
