#!/usr/bin/env python3
"""verify P5b — 从 report_p5b.json 逐籽原始值重算判词, 与存档 verdict 对账。
退出码即判据: 0=一致, 1=分歧, 2=文件错。
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report_p5b.json"
FWD = 0.80
CTRL = 0.50

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main() -> int:
    if not REPORT.exists():
        print("FATAL: 无 report_p5b.json", file=sys.stderr); return 2
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    v = d["verdict"]; bp = d["by_position"]
    libP = bp["prov"]["per_case"]["library"]
    prov_gen = bp["prov"]["gen_lib_to_food"]["vals"]
    end_gen = bp["end"]["gen_lib_to_food"]["vals"]

    recompute = {
        "H-p5b-0_axis_monotone": all(monotone(p["projs"]) for p in libP),
        "H-p5b-1_change_meaning": sum(p["fwd"] > FWD for p in libP) >= 2,
        "H-p5b-2_generalize_at_marker": sum(g > FWD for g in prov_gen) >= 2,
        "H-p5b-3_position_specificity_end": sum(g < CTRL for g in end_gen) >= 2,
        "instrument_random_v": sum(p["rand"] < CTRL for p in libP) >= 2,
    }
    fail = 0
    for k, r in recompute.items():
        s = v.get(k, {}).get("pass")
        ok = (s == r)
        print(f"  [{'OK' if ok else 'MISMATCH'}] {k}: stored={s} recomputed={r}")
        fail += 0 if ok else 1
    print(f"\n对账: 分歧 {fail}")
    if fail:
        print("→ 存档 verdict 与逐籽原始值不符"); return 1
    print("→ 一致。判词可逐籽复现。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
