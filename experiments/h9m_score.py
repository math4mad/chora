#!/usr/bin/env python3
"""
H9-M scorer — two phases, in the order the registration demands.

  --band    Phase 1. Computes the band from **k=0 arms on one machine only** (PREREG_H9M.md §4):
            for each rank r, sd over the A-machine seeds of W(0,r), band = max over r of 2·sd.
            Writes artifacts/results/mef/stage19_h9m/band.json with the sha256 of every input and
            the rule as a string. Refuses if fewer than the registered minimum (n=2) of seeds
            with control arms are present. **After this file exists the band is frozen** — the
            phase refuses to overwrite it, so "not recomputed after any k>0 number is read" is
            enforced by the instrument and not by resolve.

  --score   Phase 2. Requires band.json (it will not run without it — no reading a k>0 number
            against a band that does not exist yet). Evaluates the registered conjunction
            (i) W strictly decreasing in k, every step beyond band; (ii) superlinear: some ratio
            W(k+1)/W(k) < 1/2; (iii) rank-blind: W(k,2) >= 0.9·W(k,32) at every rung. Reports G
            beside W, the secondary r(k) reading that decides nothing, the pre-written obituary if
            it fires, and the cross-machine twin check that closes Gate 6 (A seed 14 vs B's pinned
            seed-14 ladder — same seed, different laptop, never pooled into the band).

Registered in: MEF/docs/PREREG_H9M.md (commit in band.json's own header). Consumes only files whose
hashes it records as it reads them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent
MEF = (CHORA / "benches" / "MEF").resolve()
OUT = CHORA / "artifacts" / "results" / "mef" / "stage19_h9m"
A_SEED_DIRS = {13: "outputs/stage19_h9m_seed13", 14: "outputs/stage19_h9m_seed14",
               15: "outputs/stage19_h9m_seed15"}
RUNGS = (0, 25, 50, 75, 100)
ADJ_RUNGS = (0, 25, 50, 75)   # §2.4: the moving-base row, where W is a within-regime contrast
TPOST_RUNG = 100              # §2.4: frozen-base row, scored in G, never joined to the trend
RANKS = (2, 8, 32)
B_SEED14_PINNED = CHORA / "artifacts/results/mef/E0_seed14_sweep_full.json"   # cross-machine twin
MIN_SEEDS = 2                      # PREREG_H9M §4
SUPERLINEAR_RATIO = 0.5            # §3(ii)
RANK_BLIND_FRAC = 0.9              # §3(iii)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def head(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def load_seed(seed: int):
    """Return {k: {r: final_B}}, {k: ctrl_B}, floors, or None if this seed is not registered-ready."""
    d = MEF / A_SEED_DIRS[seed] / "sweep_sched_a_full.json"
    if not d.exists():
        return None
    j = json.loads(d.read_text())
    if j.get("exploratory") is not False:
        print(f"  [skip] seed {seed}: file says exploratory={j.get('exploratory')} — not a registered run")
        return None
    if not j.get("controls_no_adapter"):
        print(f"  [skip] seed {seed}: no controls_no_adapter row → W is undefined for it (§2.1)")
        return None
    fin = {(a["k"], a["r"]): a["final_B"] for a in j["arms"]}
    ctrl = {c["k"]: c["final_B"] for c in j["controls_no_adapter"]}
    floors = {int(k): v["B"] for k, v in j["floors_frozen"].items()}
    return {"path": d, "fin": fin, "ctrl": ctrl, "floors": floors, "seed": j["seed"],
            "registered_in": j.get("registered_in"), "sha": sha(d)}


def W(arm, k, r):
    return arm["ctrl"][k] - arm["fin"][(k, r)]


def phase_band() -> int:
    seeds = {}
    for s in sorted(A_SEED_DIRS):
        a = load_seed(s)
        if a:
            seeds[s] = a
            print(f"  [seed {s}] registered sweep {a['sha'][:12]}…  floors k=0 {a['floors'][0]:.4f} "
                  f"ctrl k=0 {a['ctrl'][0]:.4f}")
    if len(seeds) < MIN_SEEDS:
        print(f"[refused] band needs at least {MIN_SEEDS} same-machine seeds with control arms; "
              f"have {len(seeds)}. Nothing written — the band is not a guess.")
        return 2
    per_rank = {}
    for r in RANKS:
        vals = [W(seeds[s], 0, r) for s in sorted(seeds)]
        sd = statistics.stdev(vals) if len(vals) > 1 else None
        per_rank[f"W(0,r={r})"] = {"values": [round(v, 6) for v in vals],
                                   "mean": round(statistics.mean(vals), 6),
                                   "sd_ddof1": round(sd, 6), "2sd": round(2 * sd, 6)}
    band = max(v["2sd"] for v in per_rank.values())
    if OUT.exists() and (OUT / "band.json").exists():
        print("[refused] band.json already exists — the band is frozen (§4). Delete nothing; "
              "a recomputed band after a k>0 number is read is a different, post-hoc document.")
        return 3
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {"kind": "H9-M band — frozen from k=0 replicates on ONE machine",
           "registered_in": f"MEF/docs/PREREG_H9M.md §4 @ {head(MEF)}",
           "rule": "band = max over r in {2,8,32} of 2·sd_{seeds}(W(0,r)), ddof=1, A-machine seeds only, n>=2",
           "definition_of_W": "W(k,r) = ctrl_B(k) − final_B(k,r); ctrl_B = 600 further steps at the rung with no adapter (§2.1)",
           "seeds_used": sorted(seeds), "inputs": {str(s): {"file": str(seeds[s]["path"].relative_to(MEF)),
                                                            "sha256": seeds[s]["sha"]} for s in seeds},
           "per_rank_at_k0": per_rank, "band_nats": band,
           "excluded": {"B_seed14_cross_machine": "reported as the Gate 6 twin in verdict.json; "
                        "never pooled into the band, because a two-laptop spread confounds machine with seed"},
           "frozen_at": head(CHORA), "measured_on": "m1pro-32g (A)",
           "warning": "n=%d. This is a spread of replicates, not a distribution; it is admissible "
                      "because §4 says so before seeing it, and it may not be re-drawn." % len(seeds)}
    (OUT / "band.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"[band] frozen at {band:.6f} nats from seeds {sorted(seeds)} · {OUT/'band.json'}")
    for k, v in per_rank.items():
        print(f"   {k:>14s}: values {v['values']}  2·sd = {v['2sd']}")
    return 0


def phase_score() -> int:
    bp = OUT / "band.json"
    if not bp.exists():
        print("[refused] no band.json — run --band first. A k>0 number read against no band is not a check.")
        return 2
    band_doc = json.loads(bp.read_text())
    band = band_doc["band_nats"]
    seeds = {s: a for s, a in ((s, load_seed(s)) for s in sorted(A_SEED_DIRS)) if a}
    if set(seeds) != set(band_doc["seeds_used"]):
        print(f"[warn] seeds present {sorted(seeds)} != the seeds the band was frozen from "
              f"{band_doc['seeds_used']}; scoring on the band's own seeds only")
    use = {s: seeds[s] for s in band_doc["seeds_used"] if s in seeds}

    def mean_W(k, r):
        return statistics.mean([W(a, k, r) for a in use.values()])

    def mean_G(k, r):
        return statistics.mean([a["floors"][k] - a["fin"][(k, r)] for a in use.values()])

    table = {f"W(k={k},r={r})": {"mean": round(mean_W(k, r), 6),
                                "per_seed": {str(s): round(W(a, k, r), 6) for s, a in use.items()}}
             for k in RUNGS for r in RANKS}
    g_table = {f"G(k={k},r={r})": round(mean_G(k, r), 6) for k in RUNGS for r in RANKS}
    checks = {}
    for r in RANKS:
        w = [mean_W(k, r) for k in ADJ_RUNGS]      # §2.4: adjudication row only
        steps = [w[i] - w[i + 1] for i in range(len(w) - 1)]
        checks[f"r={r}"] = {
            "W_by_rung": [round(x, 6) for x in w],
            "(i) strictly decreasing beyond band": bool(all(s > band for s in steps)),
            "steps": [round(s, 6) for s in steps],
            # (ii) is only meaningful where the quantity is real: a ratio across values inside the
            # band is arithmetic on noise, and the first scoring run of this file called
            # "superlinear" True on ratios of −0.10 — a false positive from a clause that assumed
            # W > band. Fixed before verdict.json was ever pinned, and the correction is filed here.
            "(ii) some ratio < 0.5 (only where W(k_i) exceeds band)": bool(
                any(w[i + 1] / w[i] < SUPERLINEAR_RATIO
                    for i in range(len(w) - 1) if w[i] > band)),
            "(ii) admissible ratios": [i for i in range(len(w) - 1) if w[i] > band],
            "ratios": [round(w[i + 1] / w[i], 4) if w[i] > 0 else None for i in range(len(w) - 1)],
            "all_within_band": bool(all(abs(x) <= band for x in w)),
        }
    blind = {}
    for k in ADJ_RUNGS:
        w2, w32 = mean_W(k, 2), mean_W(k, 32)
        adjudicable = w32 > band                      # a ratio of two numbers inside the band is noise arithmetic
        blind[f"k={k}"] = {"W(k,2)": round(w2, 6), "W(k,32)": round(w32, 6),
                           "adjudicable": adjudicable,
                           "ratio": round(w2 / w32, 4) if w32 > 0 else None,
                           "ok": bool(w2 >= RANK_BLIND_FRAC * w32) if adjudicable else None,
                           "note": None if adjudicable else "both terms inside band → UNADJUDICABLE, not refuted"}
    adjudicable_rungs = [k for k in ADJ_RUNGS if blind[f"k={k}"]["adjudicable"]]
    conj_iii = bool(adjudicable_rungs) and all(blind[f"k={k}"]["ok"] for k in adjudicable_rungs)
    iii_status = ("adjudicated" if adjudicable_rungs
                  else "UNADJUDICABLE — every cell lies inside the band, so rank-dependence is neither shown nor refuted")
    tpost = {f"G({TPOST_RUNG},r={r})": round(mean_G(TPOST_RUNG, r), 6) for r in RANKS}
    tpost["regime"] = ("frozen-base (T-post) — a separate row per §2.4 and per Sarcos rule 3; reported "
                       "beside the trend, never joined to it")
    conj_i = all(c["(i) strictly decreasing beyond band"].__eq__(True) for c in checks.values())
    conj_ii = all(c["(ii) some ratio < 0.5 (only where W(k_i) exceeds band)"] for c in checks.values())
    flat_everywhere = all(c["all_within_band"] for c in checks.values())
    holds = conj_i and conj_ii and conj_iii
    secondary = {}
    for k in ADJ_RUNGS:
        w32 = mean_W(k, 32)
        qualified = [r for r in RANKS if mean_W(k, r) >= 0.5 * w32]
        secondary[f"k={k}"] = {"r_k": min(qualified) if qualified else None, "qualifying": qualified,
                               "note": "secondary reading; decides nothing (§3)"}
    twin = None
    if B_SEED14_PINNED.exists() and 14 in seeds:
        b = json.loads(B_SEED14_PINNED.read_text())
        bf = {int(k): v["B"] for k, v in b["floors_frozen"].items()}
        twin = {"seeds": 14, "machine_A": "m1pro-32g", "machine_B": "m1-16g",
                "floors_B_A": {str(k): round(seeds[14]["floors"][k], 6) for k in RUNGS},
                "floors_B_B": {str(k): round(bf[k], 6) for k in RUNGS},
                "max_abs_diff": round(max(abs(seeds[14]["floors"][k] - bf[k]) for k in RUNGS), 6),
                "gates": {"gate6_twins": "same seed, two laptops — the programme's first quotable "
                                          "machine-effect number, and it is at the FLOOR level; "
                                          "arm-level comparisons need B's controls, which do not exist"},
                "never_pooled_into_band": True}
    verdict = {"check": "H9-M (i)∧(ii)∧(iii), one conjunction, on the moving-base row k ∈ {0,25,50,75} (§2.4)",
               "status": "HOLDS" if holds else "FAILS",
               "adjudication_row": list(ADJ_RUNGS), "reported_separately": f"k={TPOST_RUNG} in G units",
               "design_finding": ("the rig's REGIME changes with k (k<100 co-trains the base, k=100 "
                                  "freezes it), so a whole-ladder trend crosses two regimes; and no rung "
                                  "here is the frozen-base late-injection case that 'critical window' "
                                  "usually means — that needs H9-M'' (a full base per rung, base held "
                                  "fixed at every injection point). Filed in §2.4 BEFORE this verdict."),
               "clauses": {"(i) strictly decreasing beyond band": conj_i,
                           "(ii) superlinear (some ratio < 0.5)": conj_ii,
                           "(iii) rank-blind (W(k,2) >= 0.9·W(k,32) at every rung)": conj_iii},
               "clause_iii_status": iii_status, "clause_iii_adjudicable_rungs": adjudicable_rungs,
               "band_nats": band, "band_frozen_from": band_doc["seeds_used"],
               "W_is_within_band_at_every_rung_and_rank": flat_everywhere,
               "reading": ("W ≈ 0 everywhere: a rank-limited increment adds nothing, within the "
                           "frozen band, over 600 plain continued-training steps at ANY injection "
                           "time in this moving-base rig. That is §6's flat-in-k case, so the "
                           "obituary is the output, not an excuse for it.") if flat_everywhere else None,
               "obituary_if_false": ("If W is flat in k within band, there is no critical window in "
                                     "this rig, 设想5's metaphor dies on the bench that has the only k "
                                     "ladder, and the author of the dossier gets the obituary, loudly. "
                                     "(PREREG_H9M.md §6, written before any number.)") if not holds else None,
               "if_iii_only_fails": "then capacity returns as a NEW claim (H9-M'), never retro-fitted here."}
    doc = {"kind": "H9-M verdict — the critical window, in gain-beyond-continued-training units",
           "registered_in": band_doc["registered_in"], "band": band_doc["rule"],
           "seeds_scored": band_doc["seeds_used"], "W_table": table, "G_table_reported_beside": g_table,
           "tpost_row_k100": tpost,
           "per_rank_checks": checks, "rank_blindness": blind, "secondary_r_k": secondary,
           "verdict": verdict, "gate6_cross_machine_twin": twin,
           "provenance": {"chora_head": head(CHORA), "mef_head": head(MEF),
                          "script": "chora/experiments/h9m_score.py", "run-on": "m1pro-32g (A)"},
           "not_done": ["row (b) train-to-end unrun — only (a) may kill H9-M (§2.3)",
                        "R1 densification, if the slope exceeds band, is a separate registered pass",
                        "B's grid has no control arms, so B contributes a twin check, not a W"]}
    (OUT / "verdict.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"[band] {band:.6f} nats (frozen from A seeds {band_doc['seeds_used']})")
    for r in RANKS:
        print(f"  r={r:>2}: W by rung {checks[f'r={r}']['W_by_rung']}  within band everywhere="
              f"{checks[f'r={r}']['all_within_band']}  (i)={checks[f'r={r}']['(i) strictly decreasing beyond band']} "
              f"(ii)={checks[f'r={r}']['(ii) some ratio < 0.5 (only where W(k_i) exceeds band)']}")
    print(f"  (iii) {iii_status}; ratios { {k: v['ratio'] for k, v in blind.items()} }")
    print(f"[verdict] {verdict['status']} — clauses {verdict['clauses']}")
    if twin:
        print(f"[gate 6] A vs B, seed 14, floors: max |Δ| = {twin['max_abs_diff']} nats")
    print(f"[written] {OUT/'verdict.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--band", action="store_true")
    g.add_argument("--score", action="store_true")
    a = ap.parse_args()
    return phase_band() if a.band else phase_score()


if __name__ == "__main__":
    raise SystemExit(main())
