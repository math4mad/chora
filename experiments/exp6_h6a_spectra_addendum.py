#!/usr/bin/env python3
"""
exp6 H6a pilot — the spectra addendum.

A2 §3 promised law 4's retained-energy analogue ("say which of the two it is"), so the pilot computed
realized per-layer spectra for all 36 deciding arms — and then its own writer dropped them: the row
list is built with `{k: v for k, v in x.items() if k != "spectrum"}`, so the field was stripped on
the way to disk. The computation happened, the bytes were discarded, and the artifact that shipped
is silent on the one column Sarcos's rules demand. This file recomputes them from the same run
records (weights.npz at the trained endpoint), writes them next to the verdict, and changes nothing
about the check: no fit, no statistic, no threshold is touched here.

Usage: /path/to/.venv/bin/python chora/experiments/exp6_h6a_spectra_addendum.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent
BENCH_S = Path(os.environ.get("SARCOS", CHORA / "benches" / "Sarcos")).resolve()
RUNS = BENCH_S / "results" / "runs"
OUT = CHORA / "artifacts" / "results" / "sarcos" / "exp6_h6a_pilot" / "h6a_pilot_spectra.json"
WIDTHS = {"primary": [64, 64], "sensitivity": [256, 256]}
RUNGS, SEEDS = (1, 2, 4, 8, 16, 21), (13, 14, 15)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def spectrum(npz: Path) -> dict:
    import numpy as np
    z = np.load(npz)
    out = {}
    for k in sorted(z.files):
        if "weight" not in k:
            continue
        W = z[k].astype(np.float64)
        s = np.linalg.svd(W, compute_uv=False)
        e2 = s ** 2
        tot = float(e2.sum())
        out[k] = {"shape": list(W.shape),
                  "energy_top1_share": float(e2[0] / tot) if tot else None,
                  "energy_top4_share": float(e2[:4].sum() / tot) if tot else None,
                  "eff_rank_1e-6": int((s > 1e-6 * s[0]).sum()) if len(s) else 0,
                  "frobenius": math.sqrt(tot)}
    return out


def main() -> int:
    vp = OUT.parent / "h6a_pilot_verdict.json"
    if not vp.exists():
        sys.exit("the pilot's verdict must exist first")
    rows = []
    for wkey in WIDTHS:
        for r in RUNGS:
            for s in SEEDS:
                rid = f"pilot6h6a-{WIDTHS[wkey][0]}x{WIDTHS[wkey][1]}-r{r}-seed{s}"
                d = RUNS / rid
                if not (d / "weights.npz").exists():
                    rows.append({"run_id": rid, "error": "no weights.npz"})
                    continue
                rec = json.loads((d / "run.json").read_text())
                sp = spectrum(d / "weights.npz")
                tot_e = sum(v["frobenius"] ** 2 for v in sp.values())
                rows.append({"run_id": rid, "width": wkey, "rung": r, "seed": s,
                             "best_epoch": rec["best_epoch"],
                             "val_at_best": min(h["mse_val"] for h in rec["history"]),
                             "layers": sp,
                             "net_frobenius_sq": tot_e,
                             "energy_share_layer1": (sp.get("layers.0.weight", {}).get("frobenius", 0) ** 2
                                                     / tot_e) if tot_e else None,
                             "weights_npz_sha256": sha256(d / "weights.npz")})
    out = {
        "kind": "exp6 H6a pilot — realized per-layer spectra of the trained factors (law 4 column)",
        "label": "addendum, not a new draw — no fit, statistic or threshold is recomputed here",
        "why": "A2 §3 requires the energy column; the pilot computed it and its writer stripped the "
               "field with `{k: v for k, v in x.items() if k != 'spectrum'}` before the JSON was "
               "written, so the shipped artifact was silent on the one number Sarcos's rule 4 asks "
               "for. Recomputed here from the same weights.npz.",
        "energy_meaning": "these are the REALIZED spectra of W itself (constrained regime): no "
                          "unconstrained W exists to compare against, so ‖W_r‖²/‖W‖² is 'n/a (never "
                          "had it)' exactly as Sarcos's README writes it for its constrained rows — "
                          "what IS reported is where the energy sits inside the trained factor "
                          "product, which is the same column Sarcos reads in its full-rank rows",
        "rows": rows,
        "provenance": {"chora_head": subprocess.run(["git", "-C", str(CHORA), "rev-parse", "HEAD"],
                                                    capture_output=True, text=True).stdout.strip(),
                       "sarcos_head": subprocess.run(["git", "-C", str(BENCH_S), "rev-parse", "HEAD"],
                                                     capture_output=True, text=True).stdout.strip(),
                       "script": "chora/experiments/exp6_h6a_spectra_addendum.py",
                       "run-on": "m1pro-32g (A)"},
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    hi = [x for x in rows if "layers" in x]
    print(f"[written] {OUT.relative_to(CHORA)} · {len(hi)}/{len(rows)} arms with spectra")
    for x in hi[:3]:
        lay = x["layers"]
        print(f"   {x['run_id']:34s} " + "  ".join(
            f"{k.split('.')[1]}:top1={v['energy_top1_share']:.3f},er={v['eff_rank_1e-6']}"
            for k, v in lay.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
