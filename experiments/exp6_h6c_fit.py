#!/usr/bin/env python3
"""
exp6 · H6c — the same dial read from two ends: does the GP's gradient-free EVIDENCE path,
shown only PolyNN's INITIAL pre-activation geometry, walk to the place gradient descent later
chose?

REGISTERED IN  : JacobiGP `docs/PREREG_EXP6.md` §H6c + **Amendment A1**, committed at
                 `JacobiGP@99c7a4a` — BEFORE this file exists and before any number. A1 §3
                 freezes every degree of freedom this script could otherwise tune.
ORDERING GUARD : this script REFUSES to run unless (a) A1's marker text is present in
                 `docs/PREREG_EXP6.md` at JacobiGP's git HEAD, and (b) no output of this
                 script exists yet. The registered ordering clause is therefore enforced by
                 code, not by honesty, and H6c has exactly one draw.

WHAT IT DOES (A1 §3, verbatim): for each of B's five h=128 A-jacobi init-dump cells
(seeds 1000-1004), take the pooled 256-bin histogram of the tanh-squashed pre-activations on
[-1,1], use bin centres as x and the integer counts VERBATIM as y (no re-scaling — the
Coordinate clause demands the same squash, same domain), and maximise the Exp-4 penalised
evidence (log marginal likelihood + log N(0, 2²) on the unconstrained softplus α,β — MATH.md §6)
over (α, β, ℓ, σ², σ²_noise) from exp-4's six starts. The check scores the MEAN pair over the
five seeds: one hypothesis check for the pair, not five.

WHO IS ASKED WHAT:
  primary   arm jacobi, N=30 (exp-4's validated basis size)  -> DECIDES H6c
  secondary arm jacobi, N=64 (the registered ceiling)        -> pre-declared sensitivity row,
                                                                describes, cannot rescue
  contrast  arms relu / hermite / cheby at N=30              -> reported, never scored
                                                                (Letter 020: all four arms'
                                                                init histograms are
                                                                integer-identical, so this row
                                                                is a duplicate-check of the rig,
                                                                not a falsifier)

Verdict rule (registered, unedited): |α̂ − 0.40| ≤ band AND |β̂ − 0.37| ≤ band, with
band = ±0.200000 on both coordinates (A1 §1, set by rule from sd_seed of the crossing walk
bytes, never to be narrowed). A1 §2 also pre-declares the secondary pointer (A's own mean pair
0.358882, 0.358988): if the two pointers disagree, the verdict is the primary's and the report
says AMBIGUOUS-POINTER.

Provenance: consumes ONLY bytes pinned in chora's manifests, re-hashed at run time; emits
chora/artifacts/results/jacobigp/exp6_h6c/ with its own (path, sha256) to be appended to
artifacts/results/manifest.json by the producing hand (law 3).

Usage:  /path/to/.venv/bin/python chora/experiments/exp6_h6c_fit.py [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent          # .../chora (resolves the symlink)
BENCH = Path(os.environ.get("JACOBIGP", CHORA / "benches" / "JacobiGP")).resolve()
SRC = BENCH / "src"
PREREG = BENCH / "docs" / "PREREG_EXP6.md"
MANIFESTS = {
    "results": CHORA / "artifacts" / "results" / "manifest.json",
    "init": CHORA / "artifacts" / "init-states" / "manifest.json",
}
OUT_DIR = CHORA / "artifacts" / "results" / "jacobigp" / "exp6_h6c"

# ---- A1 §3: the frozen mechanics. Editing any of these after a draw is a NEW row, post-hoc. ----
BAND = 0.200000                      # A1 §1, by rule: ±max(0.2, 2·sd_seed); sd from bd58e62bb8d1…
TARGET_PRIMARY = (0.40, 0.37)        # A1 §2: the registered literals; they decide
TARGET_SECONDARY = (0.358882, 0.358988)   # A1 §2: A's own mean pair; a reading row only
SPECTRUM = "se"
NUISANCE = ("lengthscale", "sigma2", "noise")
PRIOR_SD = 2.0                       # MATH.md §6, s = 2
INIT_LS, INIT_S2, INIT_NOISE = 0.4, 1.0, 1e-3
INITS = [(0.0, 0.0), (2.0, 2.0), (-0.5, -0.5), (4.0, -0.5), (-0.5, 4.0), (1.0, -0.9)]  # exp-4's six
N_DECIDE, N_SENS = 30, 64
ARMS = ("jacobi", "relu", "hermite", "cheby")
SEEDS = (1000, 1001, 1002, 1003, 1004)
BARRIER_NEAR = 0.02                  # A1 §3: within this of -0.98 is a breakdown, not a result
A1_MARKERS = ("## A1 (2026-09-12", "The provisional band stands", "AMBIGUOUS-POINTER")

sys.path.insert(0, str(SRC))
import torch  # noqa: E402
import numpy as np  # noqa: E402
from jacobigp import JacobiGP  # noqa: E402

DT = torch.float64


# --------------------------------------------------------------------------- #
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def head_sha(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def head_text(repo: Path, rel: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{rel}"],
                          capture_output=True, text=True).stdout


def pins(kind: str) -> dict:
    data = json.loads(MANIFESTS[kind].read_text())["files"]
    return {e["path"]: e for e in data}


def consume(pins_map: dict, rel: str) -> Path:
    """Law 2: a number may cross only as (path, sha256). Re-hash, then trust."""
    path = CHORA / rel
    if rel not in pins_map:
        sys.exit(f"GUARD: {rel} has no manifest entry — it has not crossed, it merely arrived")
    want = pins_map[rel]["sha256"]
    got = sha256(path)
    if got != want:
        sys.exit(f"GUARD: {rel} sha256 {got[:16]}… != pinned {want[:16]}… — STOP (Letter 016 law 2)")
    return path


def ordering_guards() -> None:
    text = head_text(BENCH, "docs/PREREG_EXP6.md")
    missing = [m for m in A1_MARKERS if m not in text]
    if missing:
        sys.exit("GUARD: Amendment A1 is not in PREREG_EXP6.md at JacobiGP HEAD "
                 f"(missing {missing}). H6c's paperwork must predate its number.")
    if OUT_DIR.exists() and any(OUT_DIR.glob("*.json")):
        sys.exit(f"GUARD: {OUT_DIR} already holds a draw. H6c is one check; it does not get "
                 "re-rolled. A second run is a NEW row and must be labelled post-hoc.")


# --------------------------------------------------------------------------- #
def penalty(params, sd=PRIOR_SD):
    """log N(0, sd²) on the UNCONSTRAINED (softplus) coordinates — MATH.md §6, exp-4's penalty."""
    return 0.5 * ((params.raw_alpha / sd) ** 2 + (params.raw_beta / sd) ** 2)


def objective(gp, X, y):
    return gp.log_marginal_likelihood(X, y) - penalty(gp.params)


def fit_once(X, y, alpha, beta, n, adam_steps=400, lr=0.05, lbfgs_iters=150):
    gp = JacobiGP(N=n, spectrum=SPECTRUM, alpha=alpha, beta=beta, lengthscale=INIT_LS,
                  sigma2=INIT_S2, noise=INIT_NOISE,
                  learn=("alpha", "beta") + NUISANCE, dtype=DT)
    params = [p for p in gp.parameters() if p.requires_grad]
    best = {"obj": -math.inf, "ok": False}

    def snapshot(tag):
        try:
            obj = float(objective(gp, X, y).detach())
        except (ValueError, RuntimeError) as exc:
            return {"tag": tag, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
        d = gp.params.as_dict()
        return {"tag": tag, "ok": True, "obj": obj, "alpha": d["alpha"], "beta": d["beta"],
                "lengthscale": d["lengthscale"], "sigma2": d["sigma2"], "noise": d["noise"]}

    try:
        opt = torch.optim.Adam(params, lr=lr)
        for it in range(adam_steps):
            opt.zero_grad()
            (-objective(gp, X, y)).backward()
            opt.step()
        opt = torch.optim.LBFGS(params, lr=1.0, max_iter=lbfgs_iters, history_size=12,
                               tolerance_grad=1e-12, tolerance_change=1e-14,
                               line_search_fn="strong_wolfe")

        def closure():
            opt.zero_grad()
            loss = -objective(gp, X, y)
            loss.backward()
            return loss

        opt.step(closure)
    except (ValueError, RuntimeError) as exc:
        return {"tag": "breakdown", "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    snap = snapshot("final")
    if snap.get("ok"):
        best = snap
    return best


def fit_cell(X, y, n):
    """exp-4's multi-start: six starts, best penalised objective wins (ties -> first)."""
    starts, t0 = [], time.time()
    for (a0, b0) in INITS:
        r = fit_once(X, y, a0, b0, n)
        r["start"] = [a0, b0]
        starts.append(r)
    good = [r for r in starts if r.get("ok")]
    if not good:
        return {"ok": False, "starts": starts, "seconds": round(time.time() - t0, 2)}
    win = max(good, key=lambda r: r["obj"])
    spread = [r["alpha"] for r in good], [r["beta"] for r in good]
    return {"ok": True, "obj": win["obj"], "alpha": win["alpha"], "beta": win["beta"],
            "lengthscale": win["lengthscale"], "sigma2": win["sigma2"], "noise": win["noise"],
            "start": win["start"], "n_starts_ok": len(good),
            "start_alpha_range": [min(spread[0]), max(spread[0])],
            "start_beta_range": [min(spread[1]), max(spread[1])],
            "seconds": round(time.time() - t0, 2), "starts": starts}


def r2_of_posterior(gp_dict, X, y):
    """Law 4's retained-energy analogue: variance of the measure explained by the fit's mean."""
    gp = JacobiGP(N=gp_dict["N"], spectrum=SPECTRUM, alpha=gp_dict["alpha"], beta=gp_dict["beta"],
                  lengthscale=gp_dict["lengthscale"], sigma2=gp_dict["sigma2"],
                  noise=gp_dict["noise"], learn=(), dtype=DT)
    post = gp.posterior(X, y)
    mu = gp.predict(X, post=post)[0]
    resid = float(((y - mu) ** 2).sum())
    tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - resid / tot if tot > 0 else float("nan")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="run the guards and ONE cell, print, write nothing")
    args = ap.parse_args()

    ordering_guards()
    rp, ip = pins("results"), pins("init")
    walk_path = consume(rp, "artifacts/results/polynn/h6cB/h6c_walks_summary.json")
    dumps = {arm: {s: consume(ip, f"artifacts/init-states/h6cB/h6c_dump_{arm}_h128_s{s}.json")
                   for s in SEEDS} for arm in ARMS}

    # the band is not an input, it is a rule applied to the crossing bytes: re-derive and assert
    w = json.loads(walk_path.read_text())
    tv = w["terminal_values"]
    sd = {k: statistics.stdev(tv[k]) for k in ("alpha", "beta")}
    band = {k: max(0.2, 2 * sd[k]) for k in ("alpha", "beta")}
    for k in ("alpha", "beta"):
        if abs(band[k] - BAND) > 1e-9:
            sys.exit(f"GUARD: band re-derived from bytes = {band[k]} != A1's frozen {BAND}")

    rows, t_all = [], time.time()

    def one(arm, seed, n, scored):
        cell = json.loads(dumps[arm][seed].read_text())
        c = cell["combined_all_layers"]
        edges = torch.tensor(c["bin_edges"], dtype=DT)
        X = (edges[:-1] + edges[1:]) / 2
        y = torch.tensor(c["counts"], dtype=DT)
        r = fit_cell(X, y, n)
        if r.get("ok"):
            r["explained_var"] = r2_of_posterior({**r, "N": n}, X, y)
            barrier = [v for v in (r["alpha"], r["beta"]) if v < -0.98 + BARRIER_NEAR]
            r["barrier_flag"] = bool(barrier)
        r.update(arm=arm, seed=seed, N=n, scored=scored,
                 donor_sha256=sha256(dumps[arm][seed])[:64],
                 counts_sum=int(c["counts_sum"]), n_bins=int(c["n_bins"]))
        rows.append(r)
        print(f"  {arm:8s} N={n:<3d} seed={seed}  "
              + (f"α̂={r['alpha']:+.4f} β̂={r['beta']:+.4f} obj={r['obj']:9.2f} "
                 f"σ²={r['sigma2']:.3e} expl={r['explained_var']:.4f} {r['seconds']:5.1f}s"
                 if r.get("ok") else f"BREAKDOWN {r.get('error')}"))
        return r

    print("[guards] A1 at HEAD ✓ · donor bytes re-hashed against pins ✓ · band re-derived ✓")
    print("[fits] primary arm, deciding row (N=30):")
    prim30 = [one("jacobi", s, N_DECIDE, True) for s in SEEDS]
    if args.dry_run:
        print(f"[dry-run] one arm/row only, nothing written · {round(time.time()-t_all,1)} s")
        return 0

    print("[fits] primary arm, pre-declared sensitivity row (N=64):")
    prim64 = [one("jacobi", s, N_SENS, False) for s in SEEDS]
    print("[fits] contrast arms (never scored):")
    contrast = {arm: [one(arm, s, N_DECIDE, False) for s in SEEDS]
                for arm in ("relu", "hermite", "cheby")}

    def summarize(rs):
        ok = [r for r in rs if r.get("ok")]
        if not ok:
            return {"n_ok": 0, "mean_pair": None}
        a = [r["alpha"] for r in ok]
        b = [r["beta"] for r in ok]
        return {"n_ok": len(ok), "mean_pair": [statistics.mean(a), statistics.mean(b)],
                "sd_over_seeds": [statistics.stdev(a) if len(a) > 1 else None,
                                  statistics.stdev(b) if len(b) > 1 else None],
                "per_seed": [[r["seed"], round(r["alpha"], 6), round(r["beta"], 6),
                              round(r["obj"], 3), r["sigma2"], r["noise"], r["lengthscale"],
                              round(r["explained_var"], 6)] for r in ok],
                "barrier_flags": [r["seed"] for r in ok if r["barrier_flag"]],
                "breakdowns": [r["seed"] for r in rs if not r.get("ok")]}

    def verdict(mean_pair):
        if mean_pair is None:
            return {"status": "NO RESULT (every start broke down)", "claim_supported": None}
        pa, pb = TARGET_PRIMARY
        d = (abs(mean_pair[0] - pa), abs(mean_pair[1] - pb))
        prim = d[0] <= BAND and d[1] <= BAND
        sa, sb = TARGET_SECONDARY
        sec = abs(mean_pair[0] - sa) <= BAND and abs(mean_pair[1] - sb) <= BAND
        status = ("HOLDS" if prim else "FAILS") + (" (registered target)" if prim else "")
        if prim != sec:
            status = "AMBIGUOUS-POINTER — " + ("primary HOLDS" if prim else "primary FAILS")
        return {"status": status, "claim_supported": bool(prim),
                "primary_pointer": {"target": [pa, pb], "abs_dev": [round(d[0], 6), round(d[1], 6)],
                                    "inside_band": prim},
                "secondary_pointer": {"target": list(TARGET_SECONDARY),
                                      "abs_dev": [round(abs(mean_pair[0] - sa), 6),
                                                  round(abs(mean_pair[1] - sb), 6)],
                                      "inside_band": sec},
                "band": BAND, "n_checks": 1,
                "note": "the joint conjunction is the single hypothesis check; per-coordinate "
                        "halves are reported, not separate claims (Sitting 003, T01)"}

    s30, s64 = summarize(prim30), summarize(prim64)
    out = {
        "kind": "exp6 H6c fit — evidence path on PolyNN's init pre-activation measure",
        "registered_in": f"JacobiGP docs/PREREG_EXP6.md §H6c + A1 @ {head_sha(BENCH)[:7]}",
        "ordering": "A1 committed BEFORE this file and before this run; the script re-reads it "
                    "from git HEAD and refuses to start without it, and refuses a second draw",
        "disclosure": os.environ.get("H6C_DISCLOSURE") or None,
        "band_rule": {"value": BAND, "source": "±max(0.2, 2·sd_seed) over terminal_values of "
                      "h6c_walks_summary.json (bd58e62bb8d1…)", "rederived_at_runtime": band,
                      "ddof_note": "population sd gives 0.110015/0.073845 — no convention moves "
                                   "the band off ±0.2"},
        "pointers": {"primary": list(TARGET_PRIMARY), "secondary": list(TARGET_SECONDARY)},
        "coordinate": {"x": "256 bin centres of [-1,1]", "y": "counts verbatim, no re-scaling",
                       "measure": "combined_all_layers, arm A-jacobi, h=128, seeds 1000-1004"},
        "rig": {"N_deciding": N_DECIDE, "N_sensitivity": N_SENS, "spectrum": SPECTRUM,
                "prior": "MAP log N(0,2^2) on unconstrained softplus (alpha,beta) — MATH.md §6",
                "starts": INITS, "dtype": "float64",
                "inits": [INIT_LS, INIT_S2, INIT_NOISE]},
        "donors": {"walks_summary": {"path": "artifacts/results/polynn/h6cB/h6c_walks_summary.json",
                                     "sha256": sha256(walk_path)},
                   "dumps": {arm: {str(s): {"path": f"artifacts/init-states/h6cB/h6c_dump_{arm}_h128_s{s}.json",
                                            "sha256": sha256(dumps[arm][s])} for s in SEEDS}
                             for arm in ARMS}},
        "primary_N30": s30, "sensitivity_N64": s64,
        "contrast_rows": {arm: summarize(rows_) for arm, rows_ in contrast.items()},
        "verdict": verdict(s30.get("mean_pair")),
        "verdict_sensitivity_row_N64": verdict(s64.get("mean_pair")),
        "environment": {"machine": "m1pro-32g", "host": platform.node(),
                        "python": platform.python_version(), "torch": torch.__version__,
                        "numpy": np.__version__, "threads": torch.get_num_threads()},
        "provenance": {"chora_head": head_sha(CHORA), "jacobigp_head": head_sha(BENCH),
                       "polynn_head": head_sha(CHORA / "benches" / "PolyNN"),
                       "script": "chora/experiments/exp6_h6c_fit.py",
                       "run-on": "m1pro-32g (A)", "wall_clock_s": None},
        "not_done": ["no re-start-set tuning, no bin-subset trimming, no re-scaling or log-count "
                     "variant, no narrowing of the band, no choosing the secondary pointer over "
                     "the primary, no swapping N=64 into the deciding slot (A1 §3)",
                     "the other three arms cannot falsify anything on this donor data "
                     "(Letter 020: init histograms integer-identical across arms)"],
    }
    out["provenance"]["wall_clock_s"] = round(time.time() - t_all, 1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "h6c_fits.json").write_text(json.dumps({"rows": rows}, indent=1) + "\n")
    vp = OUT_DIR / "h6c_verdict.json"
    vp.write_text(json.dumps(out, indent=1) + "\n")
    v = out["verdict"]
    print(f"\n[result] mean pair (N=30, 5 seeds) = {s30.get('mean_pair')}  band ±{BAND}")
    print(f"[verdict] {v['status']}")
    print(f"[written] {vp.relative_to(CHORA)} ({vp.stat().st_size} B, sha256 {sha256(vp)[:16]}…)")
    print(f"[budget] {out['provenance']['wall_clock_s']} s total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
