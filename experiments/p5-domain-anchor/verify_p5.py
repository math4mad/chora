#!/usr/bin/env python3
"""verify P5 — 从 report_p5.json 的逐籽原始值重算判词, 与存档 verdict 对账。
退出码即判据: 0=一致, 1=分歧, 2=文件/用法错。
跑法: ../../.venv-g3/bin/python verify_p5.py
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report_p5.json"
FWD = 0.80   # 与 run_p5.py / 冻本一致
CTRL = 0.60

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main() -> int:
    if not REPORT.exists():
        print("FATAL: 无 report_p5.json", file=sys.stderr); return 2
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    v, pc = d["verdict"], d["per_case"]
    lib, ctl = pc["library"], pc["control_spring"]
    gen = v["H-p5-2_generalize"]["acc"]["vals"]

    recompute = {
        "H-p5-0_axis_monotone": all(monotone(p["h0_projs"]) for p in lib),
        "H-p5-1_change_meaning": sum(p["h1_fwd"] > FWD for p in lib) >= 2,
        "H-p5-2_generalize":     sum(g > FWD for g in gen) >= 2,
        "H-p5-3_control_no_v":   sum(p["h1_fwd"] < CTRL for p in ctl) >= 2,
        "instrument_random_v":   sum(p["h1_rand"] < CTRL for p in lib) >= 2,
    }
    fail = 0
    for k, r in recompute.items():
        s = v.get(k, {}).get("pass")
        ok = (s == r)
        print(f"  [{'OK' if ok else 'MISMATCH'}] {k}: stored={s} recomputed={r}")
        fail += 0 if ok else 1
    print(f"\n对账: 分歧 {fail}")
    if fail:
        print("→ 存档 verdict 与逐籽原始值不符 (要么数据动过, 要么判词手改过)")
        return 1
    print("→ 一致。判词可逐籽复现。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
