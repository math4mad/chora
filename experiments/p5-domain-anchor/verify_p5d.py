#!/usr/bin/env python3
"""verify P5d — 从 report_p5d.json 逐籽原始值重算判词。退出码即判据。
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPORT = HERE / "report_p5d.json"
FWD = 0.80

def main() -> int:
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    v, ps = d["verdict"], d["per_seed"]
    mon = lambda p: all(p["projs"][i+1] >= p["projs"][i]-1e-9 for i in range(len(p["projs"])-1)) and p["projs"][-1] > p["projs"][0]
    rc = {
        "H-p5d-0_axis_monotone": all(mon(p) for p in ps),
        "H-p5d-1_change_meaning_train_marker": sum(p["fwd_train_marker"] > FWD for p in ps) >= 2,
        "H-p5d-2_generalize_unseen_marker": sum(p["fwd_unseen_marker"] > FWD for p in ps) >= 2,
        "H-p5d-3_generalize_unseen_marker_food": sum(p["fwd_unseen_marker_food"] > FWD for p in ps) >= 2,
        "instrument_random_v": sum(p["rand"] < 0.50 for p in ps) >= 2,
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
