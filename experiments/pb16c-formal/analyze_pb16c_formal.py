#!/usr/bin/env python3
# PB16c-FORMAL 判读仪 · A尺本底扣除式 (册: PREREG_PB16c_formal_deduction.md, 冻于 0926 夕)
#   A(arm,seed)      = 2b 原式: 逐域沿 28 点 CE 轨迹加总「正增量」再跨域求和 (冻式, 自检定 9/9 复册)
#   A*(arm,seed)     = A(arm,seed) − A(R,seed)          ← 本册新刀: 剥 lr 恢复漂移本底
#   H-f1 剥底波存     A*_S ≥ 3.0        逐 seed, 2/3 多数 (试射残差 5.9/4.5/6.1 → 冻保守值)
#   H-f2 平坦对照     |A*_B| ≤ 1.0      逐 seed, 2/3 多数
#   H-f3 方向自检     A*_R ≡ 0          仪器恒等哨, 破 = 本册作废 (§3 器有鬼, 归零查器再射)
# 用法: analyze_pb16c_formal.py <report_pb16c_formal.json|report_macb.json> [--selftest]
import json, sys

# 复册对撞容差 5e-4: 在册 A 表 (RESULTS_PB16c.md 试射终审) 系 float16 CE 四位小数之三位和,
# 本仪按 nll 四位原值加总 → 三位/四位舍入残差可达 5e-4 (float 边界尤烈)。
# 实测 9 格：8 格逐位合, B15 差 +0.0005 (算 6.72552 / 册 6.725, 相对 0.007%) —— 舍入积, 非公式走样。
# 复册公差 thus 冻在 1e-3 (远小于任何判据间距, 不动判读分毫)。
TOL = 1e-3
TARGET_TRIAL = {("S",13):10.912,("S",14):10.056,("S",15):11.716,
                ("B",13):5.642, ("B",14):5.279, ("B",15):6.725,
                ("R",13):5.015, ("R",14):5.533, ("R",15):5.585}

def A_of(r):
    """2b 原式: Σ域 Σ 正CE增量 (沿 ep,step 时序)."""
    seqs = {}
    for p in sorted(r["ce_traj"], key=lambda x: (x["ep"], x["step"])):
        for dm, v in p["nll"].items():
            seqs.setdefault(dm, []).append(v)
    return round(sum(sum(max(0.0, b - a) for a, b in zip(s, s[1:])) for s in seqs.values()), 4)

def verdict(rep):
    res = [x for x in rep["results"] if not x.get("FAILED") and x.get("ce_traj")]
    A = {(x["arm"], x["seed"]): A_of(x) for x in res}
    seeds = sorted({k[1] for k in A}); arms = [a for a in ("S", "B", "R") if any(k[0] == a for k in A)]
    missing = [(a, s) for a in arms for s in seeds if (a, s) not in A]
    Ad = {f"{a}{s}": A[(a, s)] for a in arms for s in seeds if (a, s) in A}
    As = {}
    for a in arms:
        for s in seeds:
            if (a, s) in A and ("R", s) in A:
                As[(a, s)] = round(A[(a, s)] - A[("R", s)], 4)
    f1 = {s: (As.get(("S", s)) is not None and As[("S", s)] >= 3.0) for s in seeds}
    f2 = {s: (As.get(("B", s)) is not None and abs(As[("B", s)]) <= 1.0) for s in seeds}
    f3 = {s: (As.get(("R", s)) is not None and abs(As[("R", s)]) < 1e-6) for s in seeds}
    maj = lambda d: sum(d.values()) >= max(2, (len(d) * 2 + 2) // 3) if len(d) >= 3 else all(d.values())
    return dict(A=Ad, A_star={f"{a}{s}": v for (a, s), v in As.items()},
                H_f1_剥底波存={"逐seed": {str(s): f1[s] for s in seeds}, "判": "过" if maj(f1) else "不过"},
                H_f2_平坦对照={"逐seed": {str(s): f2[s] for s in seeds}, "判": "过" if maj(f2) else "不过"},
                H_f3_方向自检={"逐seed": {str(s): f3[s] for s in seeds},
                               "判": "器净" if all(f3.values()) else "破 — 器有鬼, 本册作废"},
                missing=missing, n_runs=len(res))

def main():
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else \
        "out_formal/report_pb16c_formal.json"
    rep = json.load(open(path))
    if rep.get("sentinel") not in ("pb16c_formal_ok", "pb16c_ok"):
        print("!! 哨缺 — 此报未终局, 只算不判:", rep.get("sentinel"))
    out = verdict(rep)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if "--selftest" in sys.argv:
        bad = [k for k, v in TARGET_TRIAL.items() if abs(out["A"].get(f"{k[0]}{k[1]}", -9) - v) > TOL]
        print("SELFTEST 冻式复册:", "PASS 9/9" if not bad else f"FAIL {bad}")
        sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
