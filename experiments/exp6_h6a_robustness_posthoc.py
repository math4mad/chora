#!/usr/bin/env python3
"""
POST-HOC ROW — exp6 H6a pilot: what the A2 §6 determinism mismatch is worth to the verdict.

Labelled in the file name and inside the JSON, because that is what the programme's law asks of a
row written after the event it describes: this cannot change H6a-pilot's verdict, it states **which
bytes that verdict is about**.

The pilot's deciding row is frozen by A2 §2 to the pilot's own fresh runs. Six of those arms
(rung 1, three seeds, both widths — and rung 1 is inside group U) do not reproduce the committed
2026-09-08 records bitwise, while every other overlapping configuration does, exactly, across a
macOS upgrade. This script refits the evidence path to the COMMITTED r=1 curves with the identical
A1 §3 rig (N=30, τ=0.50, exp-4's six starts, MAP s=2) and reports:

  1. the per-arm shift in (α̂, β̂) between fresh and committed bytes — the quantity that actually
     differs, since the curves diverge from the first epoch by ≤ 2.4e-5 in mse_val;
  2. S(0.50) recomputed with the committed r=1 fits substituted into group U (rung 2 has no
     committed run, so it stays fresh — the substitution is partial and says so).

Usage: /path/to/.venv/bin/python chora/experiments/exp6_h6a_robustness_posthoc.py
"""
from __future__ import annotations

import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent
BENCH_J = Path(os.environ.get("JACOBIGP", CHORA / "benches" / "JacobiGP")).resolve()
BENCH_S = Path(os.environ.get("SARCOS", CHORA / "benches" / "Sarcos")).resolve()
RUNS = BENCH_S / "results" / "runs"
sys.path.insert(0, str(CHORA / "experiments"))
sys.path.insert(0, str(BENCH_J / "src"))
from exp6_h6c_fit import fit_cell          # noqa: E402
import torch                                # noqa: E402

DT = torch.float64
TAU, EPOCHS, N = 0.50, 60, 30
SEEDS = (13, 14, 15)
COMMITTED_R1 = {  # width_key -> {seed: committed run_id}
    "primary": {s: f"constrained-64h64-seed{s}-blk256-f80-10-10-ep60-lr0.001_constraint-ranks1-1-1"
                for s in SEEDS},
    "sensitivity": {s: f"constrained-256h256-seed{s}-blk256-f80-10-10-ep60-lr0.001-ranks1-1-1"
                    for s in SEEDS},
}


def fit_curve(mse):
    E = math.ceil(TAU * EPOCHS)
    X = torch.tensor([2 * e / (E - 1) - 1 for e in range(E)], dtype=DT)
    y = torch.tensor(mse[:E], dtype=DT)
    return fit_cell(X, y, N)


def main() -> int:
    verdict_path = CHORA / "artifacts/results/sarcos/exp6_h6a_pilot/h6a_pilot_verdict.json"
    if not verdict_path.exists():
        sys.exit(f"the deciding row must exist first: {verdict_path}")
    V = json.loads(verdict_path.read_text())
    fresh = {(a["width"], a["rung"], a["seed"]): a for a in V["per_arm"]
             if a["tau"] == TAU and a["N"] == N}

    per_arm = []
    for width_key, m in COMMITTED_R1.items():
        for seed, rid in m.items():
            hist = [h["mse_val"] for h in json.loads((RUNS / rid / "run.json").read_text())["history"]]
            r = fit_curve(hist)
            f = fresh[(width_key, 1, seed)]
            per_arm.append({"width": width_key, "seed": seed,
                            "committed_run_id": rid,
                            "committed_alpha": r.get("alpha"), "committed_beta": r.get("beta"),
                            "fresh_alpha": f["alpha"], "fresh_beta": f["beta"],
                            "d_alpha": (r.get("alpha") - f["alpha"]) if r.get("ok") else None,
                            "d_beta": (r.get("beta") - f["beta"]) if r.get("ok") else None,
                            "max_abs_diff_mse_val": max(abs(x - y) for x, y in
                                                        zip(hist, f["curve"])),
                            "first_epoch_differing": next(
                                (i for i, (x, y) in enumerate(zip(hist, f["curve"])) if x != y), None),
                            "committed_explained_var": r.get("explained_var"),
                            "seconds": r.get("seconds")})

    def group_stats(getters):
        """getters: {'alpha': f, 'beta': g} — one callable per coordinate, keyed by cell."""
        pooled_c = {}
        for c in ("alpha", "beta"):
            vars_ = []
            for rung in (1, 2, 16, 21):
                v = [getters[c](("primary", rung, s)) for s in SEEDS]
                vars_.append(statistics.variance(v))
            pooled_c[c] = math.sqrt(statistics.mean(vars_))
        s_pool = math.sqrt((pooled_c["alpha"] ** 2 + pooled_c["beta"] ** 2) / 2)
        mu = {}
        for g, rungs in (("U", (1, 2)), ("O", (16, 21))):
            mu[g] = {c: statistics.mean([getters[c](("primary", r, s)) for r in rungs for s in SEEDS])
                     for c in ("alpha", "beta")}
        d = {c: mu["U"][c] - mu["O"][c] for c in ("alpha", "beta")}
        return {"S": math.hypot(d["alpha"], d["beta"]) / s_pool, "pooled_sd": s_pool,
                "pooled_sd_per_coord": pooled_c, "d_per_coord": d, "group_means": mu}

    as_written = group_stats({"alpha": lambda k: fresh[k]["alpha"],
                            "beta": lambda k: fresh[k]["beta"]})
    sub = dict(fresh)
    for row in per_arm:
        k = (row["width"], 1, row["seed"])
        if row["committed_alpha"] is not None:
            sub[k] = {**sub[k], "alpha": row["committed_alpha"], "beta": row["committed_beta"]}
    substituted = group_stats({"alpha": lambda k: sub[k]["alpha"],
                               "beta": lambda k: sub[k]["beta"]})

    out = {
        "kind": "POST-HOC robustness row for the exp6 H6a pilot (Sarcos r=1 determinism mismatch)",
        "label": "post-hoc — written after the deciding row existed; it cannot change H6a-pilot's "
                 "verdict and is a separate row forever (programme law 4, regime discipline)",
        "why": "A2 §6's audit fired on exactly the six rung-1 arms (three seeds × both widths); "
               "rung 1 is inside group U, so the question 'which bytes is the verdict about' is a "
               "question about the deciding row, and it gets its own row rather than an edit.",
        "registered_rig_reused": "A1 §3 / A2 §3 — N=30, tau=0.50, primary width 21-64-64-7, "
                                 "exp-4's six starts, MAP with the s=2 prior; nothing re-tuned",
        "per_arm_fresh_vs_committed": per_arm,
        "S_as_written_frozen": {"value": as_written["S"],
                                "deciding_row_S_in_verdict": V["deciding_row"]["separation_S"],
                                "pooled_sd": as_written["pooled_sd"]},
        "S_with_committed_r1_substituted": {"value": substituted["S"], "pooled_sd": substituted["pooled_sd"],
                                            "d_per_coord": substituted["d_per_coord"],
                                            "group_means": substituted["group_means"]},
        "substitution_is_partial": "rung 2 has no committed run (it was invented by A2 §2), so U "
                                   "mixes committed rung-1 fits with fresh rung-2 fits",
        "verdict_moves": abs(as_written["S"] - substituted["S"]) > 0 and (
            (as_written["S"] > 3.0) != (substituted["S"] > 3.0)),
        "bug_log": [
            {"attempt": 1, "at": "2026-09-12 19:5x",
             "wrong_S_as_written": 11.1037,
             "cause": "in group_stats the name `getter` was a leftover loop variable, so after the "
                      "pooled-variance loop it stayed bound to beta_of and BOTH coordinates' group "
                      "means were computed from beta — giving d_alpha = d_beta = -0.78147 and S = "
                      "11.10 instead of the true 7.88",
             "how_it_was_caught": "the consistency line this script wrote for itself: it re-derives S "
                                  "from the verdict's own per_arm table and refuses to stay quiet if "
                                  "that does not equal the deciding row's printed S. The checker "
                                  "reported on the checker — same class as the bundle-checker bugs in "
                                  "chora/docs/ROLLBACK.md §2c, arriving from the instrument side",
             "what_was_affected": "nothing in the deciding row: the pilot's own stats_for recomputes "
                                  "independently and its S = 7.87996 was reproduced by hand from "
                                  "per_arm (pooled sd 0.099527, d = (-0.06661, -0.78143)). Only this "
                                  "post-hoc row's arithmetic was wrong, and it is re-landed here",
             "file_status": "this file replaced its first attempt in the same minute; the wrong number "
                            "lives on only here, where it was written to stay"}],
        "threshold": 3.0,
        "environment": {"torch": torch.__version__, "python": sys.version.split()[0],
                        "machine": "m1pro-32g"},
        "provenance": {"chora_head": subprocess.run(["git", "-C", str(CHORA), "rev-parse", "HEAD"],
                                                    capture_output=True, text=True).stdout.strip(),
                       "jacobigp_head": subprocess.run(["git", "-C", str(BENCH_J), "rev-parse", "HEAD"],
                                                       capture_output=True, text=True).stdout.strip(),
                       "sarcos_head": subprocess.run(["git", "-C", str(BENCH_S), "rev-parse", "HEAD"],
                                                     capture_output=True, text=True).stdout.strip(),
                       "script": "chora/experiments/exp6_h6a_robustness_posthoc.py",
                       "run-on": "m1pro-32g (A)"},
    }
    if abs(out["S_as_written_frozen"]["value"] - V["deciding_row"]["separation_S"]) > 1e-9:
        out["note"] = ("re-deriving S from the verdict's own per_arm table does not reproduce the "
                       "deciding row's printed S — reported, not repaired; see the difference "
                       f"{out['S_as_written_frozen']['value'] - V['deciding_row']['separation_S']:+.3e}")
    dst = CHORA / "artifacts/results/sarcos/exp6_h6a_pilot/h6a_pilot_robustness_posthoc.json"
    dst.write_text(json.dumps(out, indent=1) + "\n")
    print(f"[per-arm] fresh vs committed (α̂,β̂) shift, 6 arms:")
    for r in per_arm:
        print(f"   {r['width']:11s} seed{r['seed']}  dα={r['d_alpha']:+.4f} dβ={r['d_beta']:+.4f} "
              f"maxΔmse={r['max_abs_diff_mse_val']:.2e} firstΔ@epoch {r['first_epoch_differing']}")
    print(f"[S] as written {as_written['S']:.3f} · committed-r1 substituted {substituted['S']:.3f} "
          f"· threshold 3.0 · verdict moves: {out['verdict_moves']}")
    print(f"[written] {dst.relative_to(CHORA)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
