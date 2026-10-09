#!/usr/bin/env python3
"""verify P5g — 从 report_p5g.json 逐籽原始值重算判词。退出码即判据。
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPORT = HERE / "report_p5g.json"
FWD = 0.80

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main() -> int:
    if not REPORT.exists():
        print("FATAL: 无 report_p5g.json", file=sys.stderr); return 2
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    v, per, gen = d["verdict"], d["per_seed"], d["gen"]
    rc = {
        "H-p5g-0_axis_monotone": all(monotone(p["projs"]) for p in per),
        "H-p5g-1_change_meaning_train_word": sum(p["fwd"] > FWD for p in per) >= 2,
        "H-p5g-2_generalize_museum": sum(g > FWD for g in gen["博物馆"]["vals"]) >= 2,
        "H-p5g-3_generalize_archive": sum(g > FWD for g in gen["档案馆"]["vals"]) >= 2,
        "instrument_random_v": sum(p["rand"] < 0.50 for p in per) >= 2,
    }
    fail = 0
    for k, r in rc.items():
        s = v.get(k, {}).get("pass"); ok = (s == r)
        print(f"  [{'OK' if ok else 'MISMATCH'}] {k}: stored={s} recomputed={r}")
        fail += 0 if ok else 1
    print(f"\n对账: 分歧 {fail}")
    return 1 if fail else 0

if __name__ == "__main__":
    sys.exit(main())
