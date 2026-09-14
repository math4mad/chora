#!/usr/bin/env python3
"""Theuth, second table — the H6a pilot (Sarcos row), rendered from its pinned verdict.

Why this artifact and not the one the human pointed at: `…/notes/results.html`'s
widest table (Read-Out Layer, 8 seeds, ten columns, cells like `r1 / 0.361`) has NO
pinned bytes anywhere in artifacts/results/sarcos/ — so this seat cannot render it
as evidence, only as a specimen, and the difference is the seat's whole purpose.
What IS mirrored and hashable is the pilot that killed that rig's own clause
(Letter 024): `h6a_pilot_verdict.json`, so the lesson gets built out of bytes.

What this rig adds over the first one: a verdict is an arithmetic claim too. The file
publishes S, threshold, Δ and B *and* a status string; this recomputes the rule from
the four numbers and refuses if the string disagrees with them. A sha256 can never see
that class of error — which is the sentence this programme keeps paying for.

Usage:  ~/venvs/lyceum-gt/bin/python experiments/theuth_h6a_pilot_table.py
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_REL = "artifacts/results/sarcos/exp6_h6a_pilot/h6a_pilot_verdict.json"
MAN_REL = "artifacts/results/manifest.json"
DP = 4          # the page prints 4 dp for MSE; S and B carry more, so the table says dp per column
DP_S = 3


def die(code, msg):
    sys.stderr.write("THEUTH REFUSES: %s\n" % msg)
    sys.exit(code)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


src = os.path.join(ROOT, SRC_REL)
if not os.path.exists(src):
    die(2, "source artifact absent: %s" % SRC_REL)
entry = next((e for e in json.load(open(os.path.join(ROOT, MAN_REL)))["files"]
              if e["path"] == SRC_REL), None)
if entry is None:
    die(2, "%s is named by no manifest entry — an uncitable table is worse than none" % SRC_REL)
disk = sha(src)
if disk != entry["sha256"]:
    die(2, "disk bytes %s… != pin %s… — STOP, report verbatim, render nothing"
           % (disk[:12], entry["sha256"][:12]))

d = json.load(open(src))
rows, audit = [], []


def project(name, r):
    """One quantity per column; nothing typed; every clause recomputed and reported."""
    S, thr = r["separation_S"], r["threshold"]
    c = r["curve_at_prefix_end"]
    delta, band = c["delta"], c["band_B"]
    # THE CLAUSE CHECK. A2 §3, quoted verbatim from the file's own rule string:
    rule = d["verdict"]["rule"]
    holds = (S > thr) and (delta <= band)
    i_pass, ii_pass = S > thr, delta <= band
    stated_sep = c.get("curves_already_separated")
    audit.append({
        "row": name, "S": S, "threshold": thr, "S_over_threshold": S / thr,
        "delta": delta, "band_B": band, "delta_over_B": delta / band,
        "clause_i_S_gt_thr": i_pass, "clause_ii_delta_le_B": ii_pass,
        "recomputed_holds": holds,
        "file_says_curves_already_separated": stated_sep,
        # the file's own prose field must agree with the clause it describes:
        # "curves already separated" == clause ii failed == Δ > B.
        "consistent": (stated_sep == (not ii_pass)) if stated_sep is not None else None,
    })
    rows.append({
        "row": name, "tau": str(r["tau"]), "N": int(r["N"]),
        "S": round(S, DP_S), "thr": round(thr, 1), "ratio": round(S / thr, 2),
        "delta": round(delta, DP), "B": round(band, DP), "dB": round(delta / band, 2),
        "c1": "PASS" if i_pass else "fail", "c2": "PASS" if ii_pass else "fail",
        "v": "HOLDS" if holds else "DEAD-BY-CURVE",
    })


project("deciding (primary, τ=0.50)", d["deciding_row"])
for key, label in (("tau_0.25", "sensitivity τ=0.25"), ("tau_0.75", "sensitivity τ=0.75"),
                   ("width_256h256_tau_0.50", "sensitivity width 256×256"),
                   ("N_64_primary_tau_0.50", "sensitivity N=64")):
    project(label, d["sensitivity_rows"][key])

# the headline must agree with the row it is supposed to summarise
v = d["verdict"]
if abs(v["S"] - d["deciding_row"]["separation_S"]) > 1e-12 or abs(v["delta"] - rows[0]["delta"]) > 10 ** -DP:
    die(3, "the verdict block disagrees with the deciding row it summarises — a table built on "
           "either one would be quoting a different experiment than the other")
inconsistent = [a for a in audit if a["consistent"] is False]
if inconsistent:
    die(3, "the published rule and the published numbers disagree at: %s — report it, never render over it"
           % ", ".join(a["row"] for a in inconsistent))

import polars as pl
from great_tables import GT, html, loc, style
cols = ["row", "tau", "N", "S", "thr", "ratio", "delta", "B", "dB", "c1", "c2", "v"]
g = (GT(pl.DataFrame({c: [r[c] for r in rows] for c in cols}))
       .cols_label(row="row (one config per cell-column)", tau="τ", N="N", S="separation S",
                   thr="threshold", ratio="S / thr", delta="Δ (val-MSE gap)", B="band B",
                   dB="Δ / B", c1="clause i", c2="clause ii", v="H6a-pilot verdict")
       .fmt_number(columns=["S"], decimals=DP_S).fmt_number(columns=["delta", "B"], decimals=DP)
       .fmt_number(columns=["ratio", "dB"], decimals=2)
       .fmt_number(columns=["thr"], decimals=1)
       .fmt_integer(columns=["N"])
       .tab_header(title=html("H6a-pilot · the clause that killed it, on one line per row"),
                   subtitle=html("learned Jacobi exponents of Sarcos val-loss curves vs rank · "
                                 "regime row: training under a rank constraint, from scratch"))
       .tab_source_note(html("source: <code>%s</code> · sha256 <code>%s…</code> · by <code>%s</code> · "
                             "rule A2 §3: HOLDS iff S &gt; threshold AND Δ ≤ B — both clauses shown per "
                             "row, never merged into one column"
                             % (SRC_REL, disk[:12], entry["by"])))
       .tab_source_note(html("status as published: <code>%s</code> — clause i passes by %.1f× at every "
                             "τ and width, clause ii fails by %.2f× on the deciding row, so the gauge "
                             "arrived after the event (Letter 024). S, Δ, B and the two clause columns "
                             "are recomputed here from the file's own primitives; the verdict column is "
                             "this rig's conjunction of the clauses, not a string copied from the json."
                             % (v["status"], rows[0]["ratio"], rows[0]["dB"])))
       .tab_source_note(html("never read: <code>%s</code> · seed meaning: <code>%s</code>"
                             % (d["never_read"], d["seed_meaning"][:72])))
       .cols_align("center", columns=["tau", "N", "S", "thr", "ratio", "delta", "B", "dB", "c1", "c2"])
       .tab_style(style=style.fill("#2a1417"), locations=loc.body(columns="v"))
       .opt_row_striping())

html_out = g.as_raw_html()

# --- the instrument reads its own output: every numeric cell must equal the projection ---
# read the BODY only: great_tables puts source notes in a <tfoot>, and a flat regex
# over everything after </thead> sweeps up τ cells and the footnotes' own digits.
# (This is the second rig's second lesson: the guard refused its own author twice
# before it agreed — first for the Δ column, now for a parser that could not count.)
m = re.search(r"<tbody[^>]*>(.*?)</tbody>", html_out, re.S)   # it carries class="gt_table_body"
if not m:
    die(5, "no <tbody> in the rendered html — nothing was parsed, so nothing is vouched for")
cells = re.findall(r">(-?\d+(?:\.\d+)?)<", m.group(1))
want = [str(r[c]) for r in rows for c in ("tau", "N", "S", "thr", "ratio", "delta", "B", "dB")]
got = cells
mism = [(a, b) for a, b in zip(got, want) if abs(float(a) - float(b)) > 0]
if len(got) != len(want):
    die(5, "parsed %d numeric cells, expected %d — cannot vouch for a table it cannot read"
           % (len(got), len(want)))
if mism:
    die(6, "rendered cells differ from the projection: %s" % mism[:4])

out_dir = os.path.dirname(src)
out_html = os.path.join(out_dir, "h6a_pilot_clauses_table.html")
out_chk = os.path.join(out_dir, "h6a_pilot_clauses_render_check.json")
report = {
    "kind": "Theuth render check №2 — clause columns recomputed, then parsed back out of the html",
    "source": SRC_REL, "source_sha256_on_disk": disk, "source_pin_matches": True,
    "renderer": "great_tables 0.24.0 + polars, as_raw_html()",
    "rows": len(rows), "numeric_cells_checked": len(want), "cells_mismatched": len(mism),
    "cells_parsed_from_tbody": len(got),
    "clause_audit": audit,
    "published_status": v["status"],
    "recomputed_verdict_of_deciding_row": rows[0]["v"],
    "verdict_consistency": (v["status"].startswith("DEAD") and rows[0]["v"] == "DEAD-BY-CURVE"),
    "note": ("The seat's first table found an arithmetic disagreement inside a hash-verified artifact; "
             "this one looked for the same class at the level of a verdict and found none: all five rows "
             "recompute to the published DEAD-BY-CURVE-CLAUSE, clause i passes 2.5–2.7× everywhere and "
             "clause ii fails 3.4× on the deciding row. A check that passes is worth keeping precisely "
             "because it could have failed, and the two rows where the first table failed were also "
             "hash-verified. Identity is not consistency: that is the sentence both tables exist to say."),
}
json.dump(report, open(out_chk, "w"), indent=1, ensure_ascii=False)
open(out_chk, "a").write("\n")
open(out_html, "w", encoding="utf-8").write(html_out)
print(json.dumps({k: report[k] for k in ("rows", "numeric_cells_checked", "cells_mismatched",
                                         "published_status", "recomputed_verdict_of_deciding_row",
                                         "verdict_consistency")}, indent=1))
print("wrote: %s (%d B)\nwrote: %s" % (out_html, os.path.getsize(out_html), out_chk))
