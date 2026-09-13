#!/usr/bin/env python3
"""
H9-M instrument — seed 15's base ladder and the SAME-MACHINE k=0 replicate band.

WRITTEN TONIGHT, RUN TOMORROW, AND IT REFUSES TO RUN UNTIL THE PAPERWORK EXISTS. That is the whole
design: `Kairos@ae6be01` is a DRAFT (the H9-M protocol, `Kairos/docs/PREREG.md`
`sha256 5cdd05a74f3c2dd4…`), and Kairos owns the question and no apparatus — the canonical text, the
frozen date and the band all belong to an MEF commit. This script therefore checks for them in
`benches/MEF/docs/` and stops if they are absent, with the missing lines printed. It is the
`exp6_h6c_fit.py` trick applied upward: ordering clauses enforced by code, not by honesty.

What it does when the registration exists (cost priced off measured units, not feared):
  1. SEED=15 base ladder on A's own rig — `MEF/scripts/stage18_kairos_mini.py --mode pretrain
     --steps 2000` — B measured 742.5 s for exactly that; then the 15-arm k×r sweep at 96.2 s/arm
     (A's own unit) ≈ 24 min. Output goes to `outputs/stage19_h9m_seed15/`, never on top of
     stage18's pinned bytes.
  2. Candidate band from k=0 arms on **one machine** (seeds 13 and 15, both A): per-rank spread of
     final_B and of G = floor_B(0) − final_B(0,r). It prints CANDIDATES and names none of them the
     band — freezing is MEF's sentence to write.
  3. It will not touch B's numbers for the band at all: a two-machine pair confounds machine with
     seed, which is why Gate 6 has been open all day and why Letter 024 says the band is the gate.

Usage:
  python chora/experiments/h9m_seed15_and_band.py --check-only      # what does the draft still lack?
  python chora/experiments/h9m_seed15_and_band.py --run             # ~30 min, A, one process at a time
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CHORA = Path(__file__).resolve().parent.parent
MEF = (CHORA / "benches" / "MEF").resolve()
OUT = MEF / "outputs" / "stage19_h9m_seed15"
A_SEED_LADDER = MEF / "outputs" / "stage18_kairos_mini"          # seed 13, A: ckpt_k*.pt + eval_*.pt
PINNED_A = CHORA / "artifacts" / "results" / "mef" / "sweep_sched_a_full.json"   # bf2f74cfa61a…
DRAFT = (CHORA / "benches" / "Kairos" / "docs" / "PREREG.md").resolve()
KAIROS_SHA = "ae6be01"

# What MEF's registration must contain before any byte of seed 15 is generated. Each entry: a label
# and a regex, so the check says WHAT is missing instead of failing quietly.
REQUIRED = {
    "the H9-M name": r"H9-M",
    "the metric defined as gain over the SAME-k floor": r"floor_B\(\s*k\s*\)\s*[-−]\s*final_B",
    "the frozen date (a date, in the registered text itself)": r"[Ff]rozen[^0-9]*2026-09-(1[3-9]|[23][0-9])",
    "the band clause naming k=0 replicates on one machine": r"band[^.]{0,200}(k\s*=\s*0|replicate)",
    "which schedule row may kill the hypothesis": r"only[^\n]{0,80}\(a\)",
    "an obituary, written before the number": r"(obituary|flat in k)",
    "the same-k regime split (moving-base vs frozen-base rows)": r"(T-mid|moving-base).{0,160}(T-post|frozen-base)|(?=(?:T-post|frozen-base))",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def registered_text() -> str:
    """MEF's docs, not Kairos's draft: the owning bench's docs keep the canonical text (law 3)."""
    hits = []
    for pat in ("*.md",):
        for p in (MEF / "docs").rglob(pat):
            t = p.read_text(errors="ignore")
            if "H9-M" in t:
                hits.append((p, t))
        for p in MEF.glob("*.md"):
            t = p.read_text(errors="ignore")
            if "H9-M" in t:
                hits.append((p, t))
    if not hits:
        return ""
    return max(hits, key=lambda h: len(h[1]))[1]


def check() -> tuple[bool, list, str]:
    text = registered_text()
    if not text:
        return False, ["MEF's docs contain no text mentioning H9-M at all — the DRAFT is in "
                       f"Kairos/docs/PREREG.md @{KAIROS_SHA} and it is a draft, deliberately"], ""
    missing = [f"{label}: no match for {pat!r}" for label, pat in REQUIRED.items()
               if not re.search(pat, text, flags=re.S)]
    return (not missing), missing, text


def base_ladder(seed: int) -> None:
    env = dict(os.environ, SEED=str(seed), OUT_DIR=str(OUT))
    for args in (["--mode", "pretrain", "--steps", "2000"], ["--mode", "sweep", "--full"]):
        print(f"[run] stage18_kairos_mini.py {' '.join(args)} (SEED={seed}, OUT_DIR={OUT.name})")
        p = subprocess.run([sys.executable, "scripts/stage18_kairos_mini.py", *args],
                           cwd=str(MEF), env=env, text=True)
        if p.returncode != 0:
            sys.exit(f"[stop] runner exited {p.returncode} on {args} — a half-written ladder is not "
                     "a fact; delete nothing, report it")


def candidates() -> dict:
    """Candidate bands from A-only k=0 arms. Prints candidates; freezes nothing."""
    a13 = json.loads(PINNED_A.read_text())
    f13 = {k: v["B"] for k, v in a13["floors_frozen"].items()}
    arms13 = {(x["k"], x["r"]): x["final_B"] for x in a13["arms"]}
    spath = OUT / "sweep_sched_a_full.json"
    out = {"machine": "m1pro-32g (A)", "seed_13": {"floors_B": f13,
             "k0_final_B_by_rank": {r: arms13[(0, r)] for r in (2, 8, 32)},
             "k0_gain_by_rank": {r: round(f13["0"] - arms13[(0, r)], 6) for r in (2, 8, 32)},
             "pin": sha(PINNED_A)[:16]}, "seed_15": None, "candidate_bands_nats": {}, "refusals": []}
    if not spath.exists():
        out["refusals"].append("seed 15's sweep not on disk yet — no candidate band can be "
                               "computed from one seed; the band needs REPLICATES")
        return out
    s = json.loads(spath.read_text())
    f15 = {k: v["B"] for k, v in s["floors_frozen"].items()}
    arms15 = {(x["k"], x["r"]): x["final_B"] for x in s["arms"]}
    out["seed_15"] = {"floors_B": f15, "k0_final_B_by_rank": {r: arms15[(0, r)] for r in (2, 8, 32)},
                      "k0_gain_by_rank": {r: round(f15["0"] - arms15[(0, r)], 6) for r in (2, 8, 32)},
                      "pin_note": "not yet manifested — manifest append is the producing hand's job"}
    for r in (2, 8, 32):
        vals = [arms13[(0, r)], arms15[(0, r)]]
        out["candidate_bands_nats"][f"final_B at k=0, r={r}"] = {
            "spread": round(max(vals) - min(vals), 6), "values": [round(v, 6) for v in vals]}
        g = [out["seed_13"]["k0_gain_by_rank"][r], out["seed_15"]["k0_gain_by_rank"][r]]
        out["candidate_bands_nats"][f"G at k=0, r={r}"] = {"spread": round(max(g) - min(g), 6),
                                                          "values": [round(v, 6) for v in g]}
    out["candidate_bands_nats"]["max_across_all"] = max(
        v["spread"] for v in out["candidate_bands_nats"].values() if isinstance(v, dict))
    out["warning"] = ("two seeds on ONE machine is a spread, not a distribution: n=2. It is enough "
                      "for a band only if MEF's registered text says so — this file does not decide "
                      "that, and will not be quoted deciding it.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--seed", type=int, default=15)
    ap.add_argument("--force", action="store_true",
                    help="run anyway with the registration incomplete — REFUSES: that flag exists to "
                         "be typed and to be answered, not to be obeyed")
    a = ap.parse_args()
    ok, missing, _ = check()
    print(f"[gate] H9-M registration in MEF's docs: {'PRESENT' if ok else 'ABSENT'}")
    for m in missing:
        print(f"       missing — {m}")
    if a.force and not ok:
        print("[refused] --force was given while the paperwork is incomplete. The ordering clause is "
              "not advisory: a number that predates its frozen date is not this programme's kind of "
              "result. Say the sentence in MEF's docs instead; it takes ten minutes.")
        return 2
    if a.check_only or not ok:
        if not ok:
            print("[stop] nothing generated. Cost when it does: ~742.5 s base ladder + ~24 min of "
                  "15 arms (measured units: A 96.2 s/arm, B 742.5 s/2000 steps).")
        return 0
    if a.run:
        if any(OUT.glob("*.json")):
            sys.exit(f"[stop] {OUT} already holds a draw — H9-M is one check; a rerun is a NEW row "
                     "and must be labelled post-hoc")
        t0 = time.time()
        base_ladder(a.seed)
        c = candidates()
        (OUT / "band_candidates.json").write_text(json.dumps(c, indent=1) + "\n")
        print(json.dumps(c, indent=1)[:1200])
        print(f"[done] {round(time.time()-t0,1)} s · {OUT/'band_candidates.json'} — "
              "candidates only; the freeze is MEF's commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
