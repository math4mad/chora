#!/usr/bin/env python3
"""
exp6 · H6b — the frozen threshold rule g(α̂,β̂) that PRESCRIBES the next rank, scored on
held-out pairs at less compute than the 4-rank grid.

REGISTERED IN : JacobiGP `docs/PREREG_EXP6.md` §H6b (clause: g lands within ±1 octave of
                oracle-best r on ≥ 6 of 8 held-out pairs, probe compute strictly < grid).
FREEZE LAW    : the threshold VALUES and the 8-pair COMPOSITION below are written before any
                pair is scored (kanban next-string of exp6-h6b, owner ruling 2026-09-22).
                Edits after the first scored pair = a NEW row, labelled post-hoc.
RULE SOURCE   : thresholds derive from MATH.md §6.1 edge semantics (α acts on the right edge
                x=+1 = late-time, β on the left) and the Experiment-4 mirror-pair scale
                (|α−β| ≈ 2.2 at strong asymmetry; prior s=2 sets the natural unit).
                NO pilot fit was opened while writing them — the six Sarcos pairs below are
                held out from rule-writing, per §H6b "not used to write the rule".

THE RULE g (frozen 2026-09-22, sha256 of the block printed at audit):
    read (α̂,β̂) from the τ=30% prefix fit at pilot rank r_p=8 (fit_cell, n=30, MAP s=2)
    D = α̂ − β̂ ;  S = α̂ + β
    D ≥ +1.00  →  r = 64   (tail suppressed while head lives: early burst, plateau = capacity-bound)
    D ≤ −1.00  →  r = 2    (head suppressed while tail churns: slow start / late drift = over-ranked)
    S ≥ +0.75  →  r = 32   (both edges suppressed: flat everywhere = capacity-bound, one octave up)
    else       →  r = 8    (keep the pilot rank)

COMPOSITION (frozen — 8 pairs):
    6 Sarcos pilot pairs (rungs r∈{2,8,32,64} already trained by exp6-h6a-sarcos-pilot):
        (primary 64x64, seeds 13,14,15), (sensitivity 256x256, seeds 13,14,15)
    2 MEF Qwen2.5 RTE pairs (bytes PENDING on the Anatomist's rig; scoring refuses until they
    exist at the named paths):
        artifacts/results/mef/h6b_curves/mef-rte-0.5b.json
        artifacts/results/mef/h6b_curves/mef-rte-1.5b.json
    each MEF file must be {"ranks": {"2":[mse…],"8":[…],"32":[…],"64":[…]}} — full runs,
    validation mse only (never test).

Usage:
  python exp6_h6b_run.py --audit-only     # print rule hash + byte census, score nothing
  python exp6_h6b_run.py                  # score (refuses unless all 8 pairs have bytes)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHORA = HERE.parent
BENCH_J = Path(os.environ.get("JACOBIGP", CHORA / "benches" / "JacobiGP")).resolve()
BENCH_S = Path(os.environ.get("SARCOS", CHORA / "benches" / "Sarcos")).resolve()
RESULTS_RUNS = BENCH_S / "results" / "runs"
MEF_DIR = CHORA / "artifacts" / "results" / "mef" / "h6b_curves"
OUT_DIR = CHORA / "artifacts" / "results" / "sarcos" / "exp6_h6b"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(BENCH_J / "src"))
from exp6_h6c_fit import fit_cell  # the A1-registered rig: exp-4 evidence path, 6 starts, MAP s=2

DT = __import__("torch").float64

# ---------------- frozen rule ---------------- #
RANKS_BY_KIND = {"sarcos": (1, 2, 4, 8, 16, 21),   # Sarcos convention (A2 §2): constraint stops binding at 21
                 "mef": (2, 8, 32, 64)}            # PREREG §H6a ladder on the LoRA rig
RANKS = RANKS_BY_KIND["mef"]
PILOT_RANK = 8
PREFIX = 0.30          # τ = 30% of epochs for the short probe
N_FIT = 30             # decision-size fit, same rig as the pilot's N_DECIDE
D_HI, D_LO, S_HI = 1.00, -1.00, 0.75   # thresholds, frozen before any scoring (see docstring)

RULE_TEXT = json.dumps({"D_HI": D_HI, "D_LO": D_LO, "S_HI": S_HI, "prefix": PREFIX,
                        "pilot_rank": PILOT_RANK, "n_fit": N_FIT,
                        "ladders": {k: list(v) for k, v in RANKS_BY_KIND.items()},
                        "snap": "g output snapped to nearest available rung (log2 distance); oracle = argmin final val mse over that pair's ladder",
                        "g": "D>=1→64; D<=-1→2; S>=0.75→32; else 8"}, sort_keys=True)


def g(alpha_hat: float, beta_hat: float) -> int:
    D, S = alpha_hat - beta_hat, alpha_hat + beta_hat
    if D >= D_HI:
        raw = 64
    elif D <= D_LO:
        raw = 2
    elif S >= S_HI:
        raw = 32
    else:
        raw = 8
    return raw


def snap(r_raw: int, ladder: tuple) -> int:
    """nearest rung in log2 distance — data-free, applied identically to every pair."""
    return min(ladder, key=lambda r: abs(math.log2(r / r_raw)))


# ---------------- frozen composition ---------------- #
def sarcos_pair(width_key: str, seed: int) -> dict:
    w = "x".join(str(x) for x in {"primary": (64, 64), "sensitivity": (256, 256)}[width_key])
    curves = {}
    for r in RANKS_BY_KIND["sarcos"]:
        p = RESULTS_RUNS / f"pilot6h6a-{w}-r{r}-seed{seed}" / "run.json"
        if p.exists():
            curves[r] = json.loads(p.read_text())
    return {"name": f"sarcos-{w}-seed{seed}", "curves": curves, "kind": "sarcos"}


def mef_pair(name: str) -> dict:
    p = MEF_DIR / f"{name}.json"
    curves = {}
    if p.exists():
        j = json.loads(p.read_text())["ranks"]
        curves = {int(k): v for k, v in j.items()}
    return {"name": f"mef-{name}", "curves": curves, "kind": "mef"}


PAIRS = [sarcos_pair("primary", s) for s in (13, 14, 15)] \
      + [sarcos_pair("sensitivity", s) for s in (13, 14, 15)] \
      + [mef_pair("mef-rte-0.5b"), mef_pair("mef-rte-1.5b")]


def mse_series(rec: dict) -> list:
    if "history" in rec:
        return [h["mse_val"] for h in rec["history"]]
    return rec["mse_val"]  # MEF schema: plain list


def fit_prefix(curve: list):
    E = max(2, math.ceil(len(curve) * PREFIX))
    X = DT([2 * e / (E - 1) - 1 for e in range(E)])
    y = DT(curve[:E])
    r = fit_cell(X, y, N_FIT)
    return r


def audit() -> int:
    print("rule sha256 :", hashlib.sha256(RULE_TEXT.encode()).hexdigest())
    print("rule text   :", RULE_TEXT)
    ok = True
    for pr in PAIRS:
        ladder = RANKS_BY_KIND[pr["kind"]]
        have = sorted(pr["curves"])
        full = set(ladder) <= set(have)
        ok &= full
        print(f"  pair {pr['name']:28s} ranks={have or '—'} {'READY' if full else 'MISSING BYTES'}")
    print("all 8 pairs ready:", ok)
    return 0


def main() -> None:
    if any(a == "--audit-only" for a in sys.argv[1:]):
        sys.exit(audit())
    if OUT_DIR.exists() and (OUT_DIR / "verdict.json").exists():
        sys.exit("GUARD: verdict exists. H6b is one check; a re-run is a NEW post-hoc row.")
    for pr in PAIRS:
        if not set(RANKS_BY_KIND[pr["kind"]]) <= set(pr["curves"]):
            sys.exit(f"GUARD: pair {pr['name']} lacks full-ladder bytes; the frozen 8-pair "
                     "composition may not be scored short. Await MEF or open a new row.")
    rows, hits, probe_ep, grid_ep = [], 0, 0, 0
    for pr in PAIRS:
        ladder = RANKS_BY_KIND[pr["kind"]]
        fp = fit_prefix(mse_series(pr["curves"][PILOT_RANK]))
        if not fp.get("ok"):
            sys.exit(f"GUARD: fit failed on {pr['name']} r_p=8: {fp.get('err')}")
        r_raw = g(fp["alpha"], fp["beta"])
        r_g = snap(r_raw, ladder)
        oracle = min(ladder, key=lambda r: mse_series(pr["curves"][r])[-1])
        octaves = abs(math.log2(r_g / oracle)) <= 1.0
        hits += int(octaves)
        probe_ep += math.ceil(len(pr["curves"][PILOT_RANK]) * PREFIX)
        grid_ep += len(pr["curves"][PILOT_RANK]) * len(ladder)
        rows.append({"pair": pr["name"], "alpha": fp["alpha"], "beta": fp["beta"],
                     "r_raw": r_raw, "r_g": r_g, "r_oracle": oracle, "within_1_octave": octaves})
    verdict = {"exp": "6-h6b", "rule_sha256": hashlib.sha256(RULE_TEXT.encode()).hexdigest(),
               "composition": [p["name"] for p in PAIRS], "rows": rows,
               "hits": hits, "pairs": len(PAIRS), "clause_ge_6_of_8": hits >= 6,
               "probe_epochs": probe_ep, "grid_epochs": grid_ep,
               "compute_strictly_less": probe_ep < grid_ep}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "verdict.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in verdict.items() if k != "rows"}, indent=1))
    audit()


if __name__ == "__main__":
    main()
