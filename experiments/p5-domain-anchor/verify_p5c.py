#!/usr/bin/env python3
"""verify P5c — 从 report_p5c.json 逐籽原始值重算判词, 与存档 verdict 对账。
退出码即判据: 0=一致, 1=分歧, 2=文件错。
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report_p5c.json"
FWD = 0.80

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main() -> int:
    if not REPORT.exists():
        print("FATAL: 无 report_p5c.json", file=sys.stderr); return 2
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    v = d["verdict"]; bp = d["by_position"]
    wlib = bp["word"]["per_case"]["library"]
    plib = bp["prov"]["per_case"]["library"]
    recompute = {
        "H-p5c-0_axis_monotone_word": all(monotone(p["projs"]) for p in wlib),
        "H-p5c-1_change_meaning_word": sum(p["fwd"] > FWD for p in wlib) >= 2,
        "H-p5c-2_generalize_word": sum(g > FWD for g in bp["word"]["gen_lib_to_food"]["vals"]) >= 2,
        "H-p5c-3_change_meaning_prov": sum(p["fwd"] > FWD for p in plib) >= 2,
        "H-p5c-4_generalize_prov": sum(g > FWD for g in bp["prov"]["gen_lib_to_food"]["vals"]) >= 2,
        "instrument_random_v": sum(p["rand"] < 0.50 for p in wlib) >= 2,
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
