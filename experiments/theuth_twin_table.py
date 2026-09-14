#!/usr/bin/env python3
"""Theuth — the table seat's first rig (Lyceum, machine B).

One job, stated as a refusal: render a table ONLY from bytes whose pin the manifest
already carries, and then prove that what came out of the renderer is what went into
the file.  No cell is ever typed by a hand.

Why this exists, in one incident: Letter 025 §(the twins row) discloses that "the
twins table's first draft carried four values typed from a rounded terminal print
(off in the fourth decimal; harmless to the conclusion, exactly what this programme
does not get to do twice)".  This rig reads the same artifact and cannot reproduce
that failure mode, because it has no way to write a number that is not in the file,
and because it re-reads its own output and refuses to exit 0 unless the printed
cells equal the pinned floats.

Usage:
    <venv>/bin/python experiments/theuth_twin_table.py [--out DIR]

Inputs (read-only, hash-verified before a single float is touched):
    artifacts/results/mef/stage19_h9m/gate6_twin.json
    artifacts/results/manifest.json                  (its pin)
Outputs (refused, not written, if the guard fails):
    artifacts/results/mef/stage19_h9m/gate6_twin_table.html
    artifacts/results/mef/stage19_h9m/gate6_twin_render_check.json
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # chora/
TWIN_REL = "artifacts/results/mef/stage19_h9m/gate6_twin.json"
MAN_REL = "artifacts/results/manifest.json"


def die(code, msg):
    sys.stderr.write("THEUTH REFUSES: %s\n" % msg)
    sys.exit(code)


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def pin_for(path):
    man = os.path.join(ROOT, MAN_REL)
    if not os.path.exists(man):
        return None
    for e in json.load(open(man))["files"]:
        if e["path"] == path:
            return e
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="output dir (default: beside the source json)")
    ap.add_argument("--dp", type=int, default=6, help="decimals rendered (must match the file)")
    args = ap.parse_args()

    src = os.path.join(ROOT, TWIN_REL)
    if not os.path.exists(src):
        die(2, "source artifact absent: %s" % TWIN_REL)

    # ---- clause 1: verify the bytes against the manifest BEFORE reading a number ----
    entry = pin_for(TWIN_REL)
    if entry is None:
        die(2, "%s is named by no manifest entry — an uncitable table is worse than none" % TWIN_REL)
    disk = sha256(src)
    if disk != entry["sha256"]:
        die(2, "disk bytes %s… != pin %s… — STOP, report verbatim, render nothing"
               % (disk[:12], entry["sha256"][:12]))

    d = json.load(open(src))
    dp = args.dp

    # ---- clause 2: the table is a projection of the file; it adds no numbers ----
    rungs = sorted(d["per_rung_deltas_nats"], key=lambda x: int(x))
    rows, residuals = [], []
    for k in rungs:
        a, b = d["floors_B_A"][k], d["floors_B_B"][k]
        delta = d["per_rung_deltas_nats"][k]
        # THE GUARD. A hash proves the bytes are the bytes; it proves nothing about
        # arithmetic. This clause recomputes |A-B| and classifies the residual against
        # the rendered place (1 ulp = 10^-dp).  Three outcomes, stated in the source,
        # threshold `post_hoc: true` — B saw the first residual and only then wrote the
        # classes, which is disclosed rather than smoothed (law 5's tail-of-log clause).
        recomputed = abs(a - b)
        resid = recomputed - delta
        ulp = 10.0 ** (-dp)
        if abs(resid) <= 5e-13:
            state = "float_noise"
        elif abs(resid) <= 1.0 * ulp + 1e-15:
            state = "ulp_disagreement"
        else:
            residuals.append({"k": int(k), "file_delta": delta, "abs_A_minus_B": recomputed,
                              "residual": resid, "state": "REFUSED_level"})
            continue
        residuals.append({"k": int(k), "file_delta": delta, "abs_A_minus_B": recomputed,
                          "residual": resid, "state": state})
        rows.append({"k": int(k), "A": a, "B": b, "delta": delta,
                     "recomputed": round(recomputed, dp + 2)})

    hard = [r for r in residuals if r["state"] == "REFUSED_level"]
    if hard:
        die(3, "the artifact disagrees with itself beyond one ulp of the rendered place at "
               "k=%s — no table may paper over that; report verbatim and let the owner re-derive"
               % ", ".join(str(r["k"]) for r in hard))
    soft = [r for r in residuals if r["state"] == "ulp_disagreement"]

    cols = ["k", "A", "B", "delta", "recomputed"]
    labels = {"k": "rung k", "A": "A floor (m1pro-32g)", "B": "B floor (m1-16g)",
              "delta": "|Δ| as filed", "recomputed": "|A−B| recomputed"}

    try:
        import polars as pl
        from great_tables import GT, html
    except ImportError as e:
        die(4, "renderer missing in this interpreter (%s).  Use ~/venvs/lyceum-gt "
               "(python 3.11, great-tables 0.24.0, polars 1.44.2) — see "
               "lyceum/skills/theuth-tables/SKILL.md" % e)

    gt = (GT(pl.DataFrame({c: [r[c] for r in rows] for c in cols}))
            .cols_label(**{c: labels[c] for c in cols})
            .fmt_number(columns=["A", "B", "delta", "recomputed"], decimals=dp)
            .fmt_integer(columns=["k"])
            .tab_header(title=html("Gate&nbsp;6 · the twins — one seed, two laptops"),
                        subtitle=html("E0 ladder floors, seed %s · machine effect at the floor level"
                                      % d["seeds"]))
            .tab_source_note(html("source: <code>%s</code> · sha256 <code>%s…</code> · status <code>%s</code> "
                                  "· never pooled into a band (<code>never_pooled_into_band: %s</code>)"
                                  % (TWIN_REL, disk[:12], d.get("status", "?"),
                                     d.get("never_pooled_into_band"))))
            .tab_source_note(html("all cells read from the file at %d dp; the renderer parsed its own "
                                  "output and refused to exit 0 otherwise · by: Bench-B · run-on: m1-16g"
                                  % dp))
            .tab_source_note(html("<b>reconciliation:</b> the fifth column is this rig's own "
                                  "|A−B|, shown beside the file's Δ rather than replacing it. They "
                                  "disagree by 1 ulp (10<sup>-%d</sup> nats) at k = %s, which is the "
                                  "signature of Δ being truncated from full-precision floors while the "
                                  "floors themselves were rounded — arithmetically harmless (2.2×10<sup>-5</sup> "
                                  "of H9-M's 0.045188 band) and exactly what a hash cannot see. A sha256 "
                                  "proves the bytes are the bytes, never that the columns agree."
                                  % (dp, ", ".join(str(r["k"]) for r in soft) or "none"))
                              if soft else html("reconciliation: every Δ equals |A−B| at the rendered "
                                                "place; nothing to disclose"))
            .opt_horizontal_padding(scale=1.6)
            .opt_row_striping())

    html_out = gt.as_raw_html()

    # ---- clause 3: the check is on the instrument's OWN output, not on its inputs ----
    body = html_out.split("</thead>", 1)[-1]
    nums = re.findall(r">(-?\d+\.\d+)", body)
    if len(nums) != 4 * len(rows):
        die(5, "parsed %d numbers out of the rendered html, expected %d — the table did not "
               "come out the way the schema says, so the check cannot vouch for it"
               % (len(nums), 4 * len(rows)))
    flat = [float(x) for x in nums]
    want = [v for r in rows for v in (r["A"], r["B"], r["delta"], r["recomputed"])]
    worst = max(abs(a - b) for a, b in zip(flat, want))
    # the trap this guard exists for: a 4-dp terminal print would differ by up to 5e-5
    rounded_4dp = max(abs(round(v, 4) - v) for v in want)
    ok = worst < 10 ** (-dp)

    outdir = args.out or os.path.dirname(src)
    os.makedirs(outdir, exist_ok=True)
    out_html = os.path.join(outdir, "gate6_twin_table.html")
    out_chk = os.path.join(outdir, "gate6_twin_render_check.json")

    if not ok:
        # write the failure, not the table: a broken probe reporting a clean bill is the
        # second-worst thing this seat can do, and the worst is deleting the evidence.
        json.dump({"verdict": "REFUSED", "worst_abs_diff": worst, "source_sha256": disk},
                  open(out_chk, "w"), indent=1)
        die(6, "rendered cells differ from the file by %.3e — refusing to emit the table" % worst)

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_out)

    report = {
        "kind": "Theuth render check — a table parsed back out of its own html",
        "source": TWIN_REL,
        "source_sha256_on_disk": disk,
        "source_pin_matches": True,
        "renderer": "great_tables 0.24.0 + polars, as_raw_html()",
        "decimals_rendered": dp,
        "rows": len(rows),
        "cells_checked": len(flat),
        "worst_abs_diff_file_vs_render": worst,
        "reconciliation": residuals,
        "reconciliation_rule": {
            "classes": {"float_noise": "<= 5e-13", "ulp_disagreement": "<= 1 ulp of the rendered "
                            "place (rendered, disclosed, one column per quantity)",
                        "REFUSED_level": "> 1 ulp (no table emitted)"},
            "post_hoc": True,
            "disclosure": ("the classes were written after B saw the first residual (1e-6 at k=25); a "
                           "seat whose tolerance is set after the number is a seat that cannot veto its "
                           "own owner, so the threshold is offered to the room to freeze before the next "
                           "table, not claimed as pre-registered"),
        },
        "ulp_disagreements_at_rungs": [r["k"] for r in soft],
        "max_diff_a_4dp_terminal_print_would_have_cause": rounded_4dp,
        "verdict": "PASS",
        "note": ("worst==0 means every printed cell equals the file at %d dp. The fourth line is the "
                 "size of the Letter 025 incident: had these values come from a 4-dp print, the table "
                 "would sit up to %.1e nats away from its own artifact and look fine doing it."
                 % (dp, rounded_4dp)),
    }
    with open(out_chk, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(json.dumps(report, indent=1, ensure_ascii=False))
    print("\nwrote: %s (%d B)\nwrote: %s" % (out_html, os.path.getsize(out_html), out_chk))
    return 0


if __name__ == "__main__":
    sys.exit(main())
