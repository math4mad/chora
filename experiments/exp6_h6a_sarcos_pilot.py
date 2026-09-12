#!/usr/bin/env python3
"""
exp6 · H6a — the sanctioned CHEAP PILOT, on Sarcos: do learned Jacobi exponents of a
validation-loss curve separate under-ranked from over-ranked runs BEFORE the curve does?

REGISTERED IN : JacobiGP `docs/PREREG_EXP6.md` §H6a (the hypothesis, the 3.0 threshold, the
                death-clause, the obituary) + **Amendment A2**, committed at `JacobiGP@0a60707`
                BEFORE any curve here was fit. A2 §3 writes every estimator as a formula, so this
                script exercises no choice A2 did not already make.
ORDERING GUARD: refuses to run unless A2's marker strings are in PREREG_EXP6.md at JacobiGP's git
                HEAD, and refuses a second draw if its verdict file exists.
REGIME ROW    : training-under-a-rank-constraint, from scratch (Sarcos `--mode constrained`).
                Never merged with post-hoc truncation or with the frozen-base `--mode lora` rows
                that share results/runs/ — Sarcos rule 3.
HARNESS       : Sarcos's own runner (`python -m sarcos_svd.train`, deterministic CPU) for every
                byte of training, and JacobiGP's Exp-4 evidence path for every fit — imported,
                not reimplemented (JacobiGP AGENTS.md §4: exp6 "must reuse both sides' harnesses").
NEVER READ    : the test split. Only `history[*].mse_val` crosses into a fit (Sarcos rule 2).

Usage:
  /path/to/.venv/bin/python chora/experiments/exp6_h6a_sarcos_pilot.py [--skip-train] [--audit-only]
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
BENCH_J = Path(os.environ.get("JACOBIGP", CHORA / "benches" / "JacobiGP")).resolve()
BENCH_S = Path(os.environ.get("SARCOS", CHORA / "benches" / "Sarcos")).resolve()
OUT_DIR = CHORA / "artifacts" / "results" / "sarcos" / "exp6_h6a_pilot"
RESULTS_RUNS = BENCH_S / "results" / "runs"
EPOCHS, LR, BATCH, BLOCK, FRAC = 60, 0.001, 256, 256, ".8 .1 .1"
RUNGS = (1, 2, 4, 8, 16, 21)
GROUP_U, GROUP_O = (1, 2), (16, 21)          # A2 §2 — {4,8} are middle rungs, in neither group
WIDTHS = {"primary": (64, 64), "sensitivity": (256, 256)}
SEEDS = (13, 14, 15)
TAUS = (0.25, 0.50, 0.75)
TAU_CHECK = 0.50                              # the registered check; the others describe
N_DECIDE, N_SENS = 30, 64
SEPARATION_THRESHOLD = 3.0                    # registered H6a, unedited
BARRIER_NEAR = 0.02
A2_MARKERS = ("## A2 (2026-09-12", "pilot row **HOLDS**", "split ⊕ init", "bitwise identical")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(BENCH_J / "src"))
from exp6_h6c_fit import fit_cell, r2_of_posterior  # the A1-registered rig: exp-4 evidence path, 6 starts, MAP s=2  # noqa: E402
import torch  # noqa: E402
DT = torch.float64


# --------------------------------------------------------------------------- #
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def head(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def prereg_head_text() -> str:
    return subprocess.run(["git", "-C", str(BENCH_J), "show", "HEAD:docs/PREREG_EXP6.md"],
                          capture_output=True, text=True).stdout


def guards() -> None:
    text = prereg_head_text()
    missing = [m for m in A2_MARKERS if m not in text]
    if missing:
        sys.exit(f"GUARD: Amendment A2 is not in PREREG_EXP6.md at JacobiGP HEAD (missing {missing}). "
                 "The pilot's mechanics must predate its first curve.")
    if OUT_DIR.exists() and any(OUT_DIR.glob("*.json")):
        sys.exit(f"GUARD: {OUT_DIR} already holds a draw. H6a-pilot is one check; a second run is a "
                 "NEW row and must be labelled post-hoc.")


def ranks_for(r: int, width: tuple) -> list:
    """Sarcos's own convention (A2 §2): last layer capped by the output dim (7); the input dim (21)
    caps the first layer implicitly, and r=21 is where the constraint stops binding."""
    return [r, r, min(r, 7)]


def run_id(width_key: str, r: int, seed: int) -> str:
    w = "x".join(str(x) for x in WIDTHS[width_key])
    return f"pilot6h6a-{w}-r{r}-seed{seed}"


def committed_id(width_key: str, r: int, seed: int):
    """The 22 committed arms A2 §6 audits against, or None if this config is new."""
    if r not in (1, 4, 16, 21):
        return None
    w = f"{WIDTHS[width_key][0]}h{WIDTHS[width_key][1]}"
    rk = "-".join(str(x) for x in ranks_for(r, WIDTHS[width_key]))
    if width_key == "sensitivity":
        return f"constrained-{w}-seed{seed}-blk256-f80-10-10-ep60-lr0.001-ranks{rk}"
    return f"constrained-{w}-seed{seed}-blk256-f80-10-10-ep60-lr0.001_constraint-ranks{rk}"


def train_arm(width_key: str, r: int, seed: int) -> Path:
    rid = run_id(width_key, r, seed)
    out = RESULTS_RUNS / rid / "run.json"
    if out.exists():
        return out
    cmd = [sys.executable, "-m", "sarcos_svd.train", "--seed", str(seed),
           "--block-size", str(BLOCK), "--fractions", ".8", ".1", ".1",
           "--hidden", *[str(x) for x in WIDTHS[width_key]],
           "--mode", "constrained", "--ranks", *[str(x) for x in ranks_for(r, WIDTHS[width_key])],
           "--epochs", str(EPOCHS), "--lr", str(LR), "--batch-size", str(BATCH),
           "--run-id", rid]
    env = dict(os.environ, PYTHONPATH=str(BENCH_S / "src"))
    p = subprocess.run(cmd, cwd=str(BENCH_S), env=env, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"RUNNER FAILED {rid}:\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
    return out


def realized_spectrum(npz: Path) -> dict:
    """Sarcos rule 4's 'say which of the two it is': no unconstrained W exists in this regime, so
    what is reported is the realized spectrum of the trained factor product per layer."""
    import numpy as np
    z = np.load(npz)
    out = {}
    for k in sorted(z.files):
        if not k.endswith("weight"):
            continue
        W = z[k].astype(np.float64)
        s = np.linalg.svd(W, compute_uv=False)
        e2 = (s ** 2)
        tot = float(e2.sum())
        out[k] = {"shape": list(W.shape), "energy_top1": float(e2[0] / tot) if tot else None,
                  "eff_rank_1e-6": int((s > 1e-6 * (s[0] if len(s) else 1)).sum()),
                  "frobenius": math.sqrt(tot)}
    return out


# --------------------------------------------------------------------------- #
def fit_curve(mse_val, upto, n):
    E = upto
    X = torch.tensor([2 * e / (E - 1) - 1 for e in range(E)], dtype=DT)
    y = torch.tensor(mse_val[:E], dtype=DT)
    r = fit_cell(X, y, n)
    if r.get("ok"):
        r["explained_var"] = r2_of_posterior({**r, "N": n}, X, y)
    return r


def stats_for(records, tau, width_key, n):
    """A2 §3's formulas, exactly. records: list of dicts with rung, seed, alpha, beta, curve."""
    sel = [x for x in records if x["N"] == n and x["tau"] == tau and x["width"] == width_key]
    broken = [(x["rung"], x["seed"]) for x in sel if not x["ok"]]
    sel = [x for x in sel if x["ok"]]
    bykey = {(x["rung"], x["seed"]): x for x in sel}
    if len(bykey) != len(RUNGS) * len(SEEDS):
        return {"error": f"incomplete cell set {len(bykey)}/{len(RUNGS)*len(SEEDS)}",
                "breakdowns": broken, "records": len(sel)}

    def within(rung, coord):
        v = [bykey[(rung, s)][coord] for s in SEEDS]
        return statistics.variance(v)

    pooled = {c: math.sqrt(statistics.mean([within(r, c) for r in GROUP_U + GROUP_O]))
              for c in ("alpha", "beta")}
    s_pooled = math.sqrt((pooled["alpha"] ** 2 + pooled["beta"] ** 2) / 2)

    def gmean(group, coord):
        return statistics.mean([bykey[(r, s)][coord] for r in group for s in SEEDS])

    d = {c: gmean(GROUP_U, c) - gmean(GROUP_O, c) for c in ("alpha", "beta")}
    sep = math.hypot(d["alpha"], d["beta"]) / s_pooled if s_pooled > 0 else float("inf")

    Etau = math.ceil(tau * EPOCHS) - 1
    curve = {}
    for gname, group in (("U", GROUP_U), ("O", GROUP_O)):
        vals = [bykey[(r, s)]["curve"][Etau] for r in group for s in SEEDS]
        curve[gname] = statistics.mean(vals)
    var = statistics.mean([statistics.variance([bykey[(r, s)]["curve"][Etau] for s in SEEDS])
                           for r in GROUP_U + GROUP_O])
    band = 2 * math.sqrt(var)
    delta = abs(curve["U"] - curve["O"])
    return {"tau": tau, "width": width_key, "N": n,
            "separation_S": sep, "threshold": SEPARATION_THRESHOLD,
            "pooled_within_sd": s_pooled, "pooled_sd_per_coord": pooled,
            "group_means": {c: {"U": gmean(GROUP_U, c), "O": gmean(GROUP_O, c)} for c in d},
            "d_per_coord": d,
                "effect_per_coord": {c: (abs(d[c]) / pooled[c] if pooled[c] > 0 else None)
                                         for c in d},
            "curve_at_prefix_end": {"mean_U": curve["U"], "mean_O": curve["O"],
                                    "delta": delta, "band_B": band,
                                    "curves_already_separated": delta > band},
            "n_cells": len(bykey)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-train", action="store_true", help="reuse the run records on disk")
    ap.add_argument("--audit-only", action="store_true")
    args = ap.parse_args()
    guards()

    t0 = time.time()
    arms = list(itertools.product(WIDTHS, RUNGS, SEEDS))
    records, audit = [], []
    print(f"[grid] {len(arms)} arms · rungs {RUNGS} · U={GROUP_U} O={GROUP_O} · widths "
          f"{ {k: v for k, v in WIDTHS.items()} } · seeds {SEEDS}")

    for width_key, r, seed in arms:
        rid = run_id(width_key, r, seed)
        path = RESULTS_RUNS / rid / "run.json"
        if not args.skip_train:
            path = train_arm(width_key, r, seed)
        if not path.exists():
            sys.exit(f"MISSING run record {path}")
        rec = json.load(open(path))
        hist = rec["history"]
        mse = [h["mse_val"] for h in hist]
        if len(mse) != EPOCHS:
            sys.exit(f"{rid}: expected {EPOCHS} epochs of val history, found {len(mse)}")
        # A2 §6 — the determinism audit, demanded before any fit
        cid = committed_id(width_key, r, seed)
        if cid and (RESULTS_RUNS / cid / "run.json").exists():
            cpath = RESULTS_RUNS / cid / "run.json"
            same = json.dumps(json.load(open(cpath))["history"]) == json.dumps(hist)
            audit.append({"new": rid, "committed": cid, "history_bitwise_equal": same,
                          "committed_sha256": sha256(cpath)[:16], "new_sha256": sha256(path)[:16]})
            if not same:
                print(f"  !! AUDIT MISMATCH {rid} vs {cid}")
        for tau in TAUS:
            for n in (N_DECIDE,):
                f = fit_curve(mse, math.ceil(tau * EPOCHS), n)
                records.append({"rung": r, "seed": seed, "width": width_key, "tau": tau, "N": n,
                                "curve": mse, "alpha": f.get("alpha"), "beta": f.get("beta"),
                                "obj": f.get("obj"), "ok": f.get("ok", False),
                                "sigma2": f.get("sigma2"), "noise": f.get("noise"),
                                "lengthscale": f.get("lengthscale"),
                                "explained_var": f.get("explained_var"),
                                "barrier": bool(f.get("ok")) and min(f["alpha"], f["beta"]) < -0.98 + BARRIER_NEAR,
                                "fit_seconds": f.get("seconds"), "run_wall_seconds": rec["wall_seconds"],
                                "spectrum": None, "run_id": rid})
        if (width_key, r, seed) in [("primary", 4, 13)]:
            pass
        last = records[[i for i, x in enumerate(records)
                        if x["width"] == width_key and x["rung"] == r
                        and x["seed"] == seed and x["tau"] == 0.50][-1]]
        if last["ok"]:
            print(f"  {rid:44s} r={r:>2} val@τ={last['curve'][math.ceil(TAU_CHECK*EPOCHS)-1]:.5f}  "
                  f"α̂={last['alpha']:+.4f} β̂={last['beta']:+.4f} expl={last['explained_var']:.4f} "
                  f"σ²={last['sigma2']:.2e} {'BARRIER' if last['barrier'] else ''}")
        else:
            print(f"  {rid:44s} r={r:>2} BREAKDOWN {last.get('error', last)}")

    if args.audit_only:
        print(json.dumps(audit, indent=1)[:2000])
        return 0

    # the sensitivity row N=64: primary width, τ=0.50 only (A2 §4 pre-declared)
    for r, seed in itertools.product(RUNGS, SEEDS):
        mse = [h["mse_val"] for h in json.load(
            open(RESULTS_RUNS / run_id("primary", r, seed) / "run.json"))["history"]]
        f = fit_curve(mse, math.ceil(TAU_CHECK * EPOCHS), N_SENS)
        records.append({"rung": r, "seed": seed, "width": "primary", "tau": TAU_CHECK, "N": N_SENS,
                        "curve": mse, "alpha": f.get("alpha"), "beta": f.get("beta"),
                        "obj": f.get("obj"), "ok": f.get("ok", False), "sigma2": f.get("sigma2"),
                        "noise": f.get("noise"), "lengthscale": f.get("lengthscale"),
                        "explained_var": f.get("explained_var"),
                        "barrier": bool(f.get("ok")) and min(f["alpha"], f["beta"]) < -0.98 + BARRIER_NEAR,
                        "fit_seconds": f.get("seconds"),
                        "run_id": run_id("primary", r, seed)})

    # realized spectra (Sarcos rule 4), per arm at the trained weights
    for x in records:
        if x["tau"] != TAU_CHECK or x["N"] != N_DECIDE:
            continue
        p = RESULTS_RUNS / x["run_id"] / "weights.npz"
        if p.exists():
            x["spectrum"] = realized_spectrum(p)

    rows = [{k: v for k, v in x.items() if k != "spectrum"} for x in records]
    deciding = stats_for(records, TAU_CHECK, "primary", N_DECIDE)
    sens = {
        "tau_0.25": stats_for(records, 0.25, "primary", N_DECIDE),
        "tau_0.75": stats_for(records, 0.75, "primary", N_DECIDE),
        "width_256h256_tau_0.50": stats_for(records, TAU_CHECK, "sensitivity", N_DECIDE),
        "N_64_primary_tau_0.50": stats_for(records, TAU_CHECK, "primary", N_SENS),
    }
    holds = ("separation_S" in deciding and deciding["separation_S"] > SEPARATION_THRESHOLD
             and not deciding["curve_at_prefix_end"]["curves_already_separated"])
    verdict = {
        "check": "H6a-pilot (Sarcos, training-under-rank-constraint row)",
        "status": "HOLDS" if holds else ("DEAD-BY-CURVE-CLAUSE"
                 if deciding["curve_at_prefix_end"]["curves_already_separated"] else "FAILS"),
        "rule": "HOLDS iff S(0.50) > 3.0 AND Δ(0.50) ≤ B(0.50); the second clause is H6a's own "
                "death-clause ('the gauge arrived after the event') and it overrides S",
        "S": deciding["separation_S"], "threshold": SEPARATION_THRESHOLD,
        "delta": deciding["curve_at_prefix_end"]["delta"],
        "band_B": deciding["curve_at_prefix_end"]["band_B"],
        "licences": "a HOLD licenses only the MEF rank-curve training (A2 §4); a FAIL is filed "
                    "against the pilot row and does not strike H6a on MEF's curves",
    }
    out = {
        "kind": "exp6 H6a pilot — learned Jacobi exponents of Sarcos val-loss curves vs rank",
        "registered_in": f"JacobiGP docs/PREREG_EXP6.md §H6a + A2 @ {head(BENCH_J)[:7]}",
        "regime_row": "training-under-a-rank-constraint, from scratch (Sarcos --mode constrained); "
                      "never merged with post-hoc truncation or frozen-base lora rows (rule 3)",
        "seed_meaning": "split ⊕ init: on Sarcos split.seed == run seed (A2 §1), so the pooled "
                        "spread is NOT comparable with MEF's paired-seed rig",
        "never_read": "the test split; only history[*].mse_val enters a fit (rule 2)",
        "grid": {"rungs": RUNGS, "group_U": GROUP_U, "group_O": GROUP_O,
                 "middle_rungs_not_in_any_group": [4, 8], "widths": {k: list(v) for k, v in WIDTHS.items()},
                 "seeds": SEEDS, "epochs": EPOCHS, "lr": LR, "batch": BATCH,
                 "tau_check": TAU_CHECK, "taus_descriptive": [0.25, 0.75]},
        "rig": {"N_deciding": N_DECIDE, "N_sensitivity": N_SENS, "spectrum": "se",
                "prior": "MAP log N(0,2^2) on unconstrained softplus (A1 §3, imported from "
                         "experiments/exp6_h6c_fit.py, not reimplemented)",
                "starts": "exp-4's six INITS", "y": "mse_val verbatim, no re-scaling",
                "x": "epoch index mapped to [-1,1] over each prefix"},
        "deciding_row": deciding, "sensitivity_rows": sens, "verdict": verdict,
        "per_arm": rows,
        "determinism_audit": {"n_configs_compared": len(audit),
                              "n_bitwise_equal": sum(1 for a in audit if a["history_bitwise_equal"]),
                              "mismatches": [a for a in audit if not a["history_bitwise_equal"]],
                              "detail": audit},
        "environment": {"machine": "m1pro-32g", "host": platform.node(),
                        "python": platform.python_version(), "torch": torch.__version__,
                        "numpy": __import__("numpy").__version__,
                        "threads": torch.get_num_threads()},
        "disclosure": __import__("os").environ.get("H6A_DISCLOSURE") or None,
        "provenance": {"chora_head": head(CHORA), "jacobigp_head": head(BENCH_J),
                       "sarcos_head": head(BENCH_S),
                       "script": "chora/experiments/exp6_h6a_sarcos_pilot.py",
                       "run-on": "m1pro-32g (A)",
                       "training_wall_seconds_total": round(sum(x["run_wall_seconds"] or 0
                                                                for x in rows if x["tau"] == TAU_CHECK
                                                                and x["N"] == N_DECIDE
                                                                and x["width"] == "primary"), 1),
                       "total_seconds": None},
    }
    out["provenance"]["total_seconds"] = round(time.time() - t0, 1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "h6a_pilot_verdict.json").write_text(json.dumps(out, indent=1) + "\n")
    (OUT_DIR / "h6a_pilot_fits.json").write_text(
        json.dumps({"rows": [{k: v for k, v in x.items() if k != "curve"} for x in records],
                    "curves": {x["run_id"]: x["curve"] for x in records if x["tau"] == TAU_CHECK
                               and x["N"] == N_DECIDE}}, indent=1) + "\n")
    print(f"\n[audit] {out['determinism_audit']['n_bitwise_equal']}/"
          f"{out['determinism_audit']['n_configs_compared']} re-runs bitwise identical to the "
          f"committed records")
    print(f"[deciding] S(0.50) = {deciding['separation_S']:.3f} (threshold {SEPARATION_THRESHOLD}) "
          f"pooled sd {deciding['pooled_within_sd']:.4f} · per-coord d "
          f"{ {k: round(v,4) for k,v in deciding['d_per_coord'].items()} }")
    print(f"[curves] Δ(0.50) = {deciding['curve_at_prefix_end']['delta']:.5f} vs band "
          f"B = {deciding['curve_at_prefix_end']['band_B']:.5f} -> "
          f"{'ALREADY SEPARATED' if deciding['curve_at_prefix_end']['curves_already_separated'] else 'still inside band'}")
    print(f"[verdict] {verdict['status']}")
    for k, v in sens.items():
        if "separation_S" in v:
            print(f"   sens {k:28s} S={v['separation_S']:.3f} "
                  f"Δ/B={v['curve_at_prefix_end']['delta']:.5f}/{v['curve_at_prefix_end']['band_B']:.5f}")
    print(f"[written] {OUT_DIR.relative_to(CHORA)} · {out['provenance']['total_seconds']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
