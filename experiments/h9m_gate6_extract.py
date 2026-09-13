import json, hashlib

v = json.load(open("artifacts/results/mef/stage19_h9m/verdict.json"))
twin = dict(v["gate6_cross_machine_twin"])
twin.update({
    "kind": "Gate 6 — the twins: same seed, two laptops (the programme's first quotable machine-effect number)",
    "status": "CLOSED",
    "rule_met": "Gate 6 asked for an A-vs-B pair of the SAME seed. A ran seed 14's whole ladder on 2026-09-13 for H9-M's band and produced the pair as a by-product.",
    "per_rung_deltas_nats": {"0": 0.000000, "25": 0.028914, "50": 0.023949, "75": 0.001622, "100": 0.008254},
    "reading": [
        "exactly zero at k=0: the step-0 initialisation is deterministic, so the two machines agree to the last bit where no training has happened;",
        "divergence appears only once each machine has trained its own base: max 0.028914 nats at k=25;",
        "that is BELOW the seed-noise band (0.045188 nats) — the sentence the programme has been waiting two days for: on this statistic the laptops agree to within the noise the seeds themselves make.",
    ],
    "caveats": [
        "floors only (frozen base at each rung, stream B). Arm-level machine effect needs B to run the no-adapter controls, which do not exist in B's grid.",
        "never pooled into H9-M's band: PREREG_H9M §4 excludes cross-machine spreads, because a two-laptop spread confounds machine with seed.",
    ],
    "inputs": {"A": "artifacts/results/mef/stage19_h9m/seed14_sweep_full.json",
               "B": "artifacts/results/mef/E0_seed14_sweep_full.json"},
})
p = "artifacts/results/mef/stage19_h9m/gate6_twin.json"
with open(p, "w") as f:
    f.write(json.dumps(twin, indent=1) + "\n")

mp = "artifacts/results/manifest.json"
d = json.loads(open(mp).read())
have = {e["path"] for e in d["files"]}
if p not in have:
    b = open(p, "rb").read()
    d["files"].append({
        "path": p, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
        "source": "extracted from verdict.json so a claim has a byte of its own (the board's own lesson: an audit line on stdout is not a fact)",
        "obtained": "2026-09-13", "by": "MEF@21eadd4",
        "script": "chora/experiments/h9m_score.py --score, then extracted by chora/experiments/h9m_gate6_extract.py",
        "notes": "Gate 6 CLOSED: seed 14 on both laptops, floors max |delta| 0.028914 nats, exactly 0.000000 at k=0; below the 0.045188-nat seed band. run-on: A side m1pro-32g, B side m1-16g."})
    with open(mp, "w") as f:
        f.write(json.dumps(d, indent=1) + "\n")
print("gate6 artifact:", hashlib.sha256(open(p, "rb").read()).hexdigest()[:12], "entries:", len(d["files"]))
