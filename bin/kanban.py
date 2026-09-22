#!/usr/bin/env python3
"""
CHORA — the kanban that cannot lie.

    usage:  python3 bin/kanban.py [--write] [--check] [--quiet]

      --write   emit docs/kanban.md and docs/kanban.json (else print only)
      --check   exit 1 if any row is in RECONCILE or a global audit fails (a gate, not a view)
      --quiet   one summary line (for the publisher's beat)

WHY THIS EXISTS, AND WHY IT IS NOT A HAND-DRAWN BOARD. Every board on 2026-09-12 said something
the bytes contradicted: the glass said "no real drift" while its own snapshot sat in a detached
HEAD; a manifest resolution said "valid JSON, hashes fine, paths conventional" while holding 18 of
27 pins; a log line said a push failed "(network?)" when the refspec was empty. A hand-maintained
kanban fails the same way, quietly, by believing the last human who typed it. So the hand writes
only INTENT here — docs/experiments.json: what a row is, who owns it, which bytes it consumes and
produces, what it claims its status is — and the LANE IS DERIVED from the record:

    idea        registered text absent or not in git
    registered  pre-registration commit exists and is an ancestor of its bench HEAD
    equipped    apparatus file exists AND is tracked
    landed      every produced byte exists on disk, is pinned in a manifest, matches its hash,
                and is tracked in git (the four-way check — see the law note below)
    scored      a verdict is readable out of the produced bytes (scored may mean FAILS: negative
                results are first-class, so a lane never lauds a claim)
    announced   the letter is committed IN ITS OWN BENCH, mirrored in chora/letters/, and the
                number is in letters/INDEX.md
    closed      announced, with no open flag, and the owning bench has nothing unpushed
    blocked     gated_by names a row that is not yet announced
    RECONCILE   derived and claimed lanes disagree, or a byte-level audit failed  <- the red row

THE FOUR-WAY CHECK, learned the hard way tonight: pin present in HEAD, bytes on disk,
sha256(bytes) == pin, and tracked in git. Each of the four has failed independently on this
workspace, and each failure looked like success to a reader who checked only the other three
(a pin whose bytes existed nowhere; bytes that were real but untracked; a resolution that was
valid JSON and had deleted 13 of someone else's permission slips).

Programme law it serves: law 2 (nothing crosses without a hash), law 3 (single writer — a row
whose producing bench is not its announcing bench is flagged), law 4 (negatives stay visible).

stdlib only, python 3.9 safe: it must run on the beat, unattended, on both machines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import calendar
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../chora
REGISTRY = ROOT / "docs" / "experiments.json"
OUT_MD = ROOT / "docs" / "kanban.md"
OUT_JSON = ROOT / "docs" / "kanban.json"
MANIFESTS = ["artifacts/results/manifest.json", "artifacts/init-states/manifest.json",
             "artifacts/external/manifest.json", "data/manifest.json", "models/manifest.json"]
BASELINE = ROOT / "docs" / "pin-baseline-2026-09-12-eve.txt"
LANES = ["idea", "registered", "equipped", "landed", "scored", "announced", "closed"]
IGNORED_BY_DESIGN = ("models/", "data/")


# --------------------------------------------------------------------------- #
def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", str(repo)] + list(args),
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        return ""


def repo_path(name):
    if name == "chora":
        return ROOT
    p = ROOT / "benches" / name
    return p.resolve() if p.exists() else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifests():
    pins = {}
    for rel in MANIFESTS:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            for e in json.loads(p.read_text())["files"]:
                pins[e["path"]] = (rel, e.get("sha256", ""), int(e.get("bytes", -1)))
        except (ValueError, KeyError):
            pins["<unparseable>:" + rel] = (rel, "", -1)
    return pins


def dig(obj, pointer):
    """Tiny JSON-pointer-lite: 'a/b/0/c'."""
    for part in [p for p in pointer.split("/") if p != ""]:
        try:
            obj = obj[int(part)] if isinstance(obj, list) else obj[part]
        except (KeyError, IndexError, ValueError):
            return None
    return obj


# --------------------------------------------------------------------------- #
def audit_path(rel, pins, want_sha=None):
    """The four-way check on one artifact path. Returns (ok, flags[])."""
    flags = []
    p = ROOT / rel
    needs_pin = rel.startswith(("artifacts/", "models/", "data/"))
    if not p.exists():
        return False, ["no bytes on disk: " + rel]
    if needs_pin and rel not in pins:
        flags.append("no manifest entry (it crossed without a permission slip): " + rel)
    elif rel in pins:
        _, want, nbytes = pins[rel]
        got = sha256(p)
        if want and got != want:
            flags.append("sha256(bytes) != pin: " + rel)
        if nbytes >= 0 and p.stat().st_size != nbytes:
            flags.append("bytes != pin: " + rel)
    if want_sha and pins.get(rel, ("", "", -1))[1][:len(want_sha)] != want_sha:
        flags.append("expected sha %s… not the file present: %s" % (want_sha, rel))
    tracked = git(ROOT, "ls-files", "--error-unmatch", rel) != ""
    if not tracked and not rel.startswith(IGNORED_BY_DESIGN):
        flags.append("pinned/reported but UNTRACKED in git (bytes outran the record): " + rel)
    return (not [f for f in flags if "by design" not in f]), flags


def audit_row(row, pins):
    """Derive the lane from bytes. Returns (lane, flags, detail)."""
    flags, detail = [], {}
    bench = row.get("owner_bench") or row.get("owner_repo")
    bp = repo_path(bench) if bench else ROOT

    # --- registered ---------------------------------------------------------
    pr = row.get("prereg")
    registered = False
    if pr:
        repo = repo_path(pr.get("repo") or bench)
        commit = (pr.get("commit") or "")[:40]
        head = git(repo, "rev-parse", "HEAD") if repo else ""
        if not repo:
            flags.append("pre-registration repo missing: " + str(pr.get("repo")))
        elif not commit:
            flags.append("pre-registration names no commit — text without a date stamp")
        else:
            exists = git(repo, "cat-file", "-e", commit + "^{commit}") == "" or \
                subprocess.run(["git", "-C", str(repo), "cat-file", "-e", commit + "^{commit}"],
                               capture_output=True).returncode == 0
            anc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                                  commit, head], capture_output=True).returncode == 0 if head else False
            marker = pr.get("marker")
            raw = git(repo, "show", "HEAD:" + pr["path"]) if pr.get("path") else ""
            # the archive is hard-wrapped at ~78 columns: compare on collapsed whitespace, or
            # every multi-word marker fails on its own punctuation and the board cries wolf
            text = " ".join(raw.split())
            has = (" ".join(marker.split()) in text) if marker else bool(text)
            registered = bool(exists and anc and has)
            detail["prereg"] = "%s@%s %s" % (pr.get("repo") or bench, commit[:7],
                                             pr.get("path", ""))
            if not exists:
                flags.append("pre-registration commit %s not in that repo" % commit[:7])
            if exists and not anc:
                flags.append("pre-registration %s is not an ancestor of HEAD (unmerged text)" % commit[:7])
            if marker and not has:
                flags.append("registered text lacks the marker %r at HEAD" % marker)
    else:
        flags.append("no pre-registration: this row is an intention, not a registered check")

    # --- equipped -----------------------------------------------------------
    equipped = False
    ap_ = row.get("apparatus")
    if ap_:
        repo = repo_path(ap_.get("repo") or "chora")
        rel = ap_.get("path", "")
        exists = bool(repo) and (repo / rel).exists()
        tracked = bool(repo) and git(repo, "ls-files", "--error-unmatch", rel) != ""
        equipped = exists and tracked
        detail["apparatus"] = "%s:%s" % (ap_.get("repo") or "chora", rel)
        if exists and not tracked:
            flags.append("apparatus exists but is untracked: " + rel)
        elif not exists:
            flags.append("apparatus absent: " + rel)

    # --- provenance: does every `by: repo@sha` in this row's manifest entries resolve HERE? ---
    for pv in (row.get("provenance") or []):
        rp = repo_path(pv.get("repo"))
        c = (pv.get("commit") or "")[:40]
        if not rp or not c:
            flags.append("provenance row incomplete (repo@sha required): %s" % pv)
            continue
        if subprocess.run(["git", "-C", str(rp), "cat-file", "-e", c + "^{commit}"],
                          capture_output=True).returncode != 0:
            flags.append("provenance %s@%s resolves in no ref fetched here — the bytes crossed, "
                         "their authorship pointer did not (law 2 half-satisfied on this machine)"
                         % (pv.get("repo"), c[:7]))

    # --- landed -------------------------------------------------------------
    prod = [e.get("path") if isinstance(e, dict) else e for e in (row.get("produces") or [])]
    consumed = [e.get("path") if isinstance(e, dict) else e for e in (row.get("consumes") or [])]
    landed = True
    for rel in prod + consumed:
        ok, f = audit_path(rel, pins)
        flags += f
        if rel in prod and not ok:
            landed = False

    # --- scored -------------------------------------------------------------
    scored, verdict = False, None
    vp = row.get("verdict")
    if vp and prod:
        path = ROOT / prod[0]
        ptr = (vp.get("at") or "").lstrip("/")
        if path.exists():
            try:
                val = dig(json.loads(path.read_text()), ptr)
            except ValueError:
                val = None
                flags.append("verdict file is not valid JSON: " + str(path.name))
            if val is not None:
                scored, verdict = True, str(val)
            else:
                flags.append("verdict pointer resolves to nothing: " + ptr)
        else:
            flags.append("verdict source file absent: " + prod[0])
    detail["verdict"] = verdict

    # --- announced ----------------------------------------------------------
    announced = False
    lt = row.get("letter")
    if lt:
        lrepo = lt.get("repo") or bench
        bp2 = ROOT if lrepo == "chora" else repo_path(lrepo)
        bench_file = lt.get("bench") or (None if lrepo != "chora" else lt.get("mirror"))
        mirror, index = lt.get("mirror"), lt.get("index")
        in_bench = bool(bp2 and bench_file) and git(bp2, "ls-files", "--error-unmatch",
                                                   bench_file) != ""
        in_mirror = bool(mirror) and (ROOT / mirror).exists() and \
            git(ROOT, "ls-files", "--error-unmatch", mirror) != ""
        idx_text = (ROOT / "letters" / "INDEX.md")
        text = idx_text.read_text() if idx_text.exists() else ""
        in_index = bool(index) and ("**%s**" % index in text or "%s (" % index in text)
        announced = in_bench and in_mirror and in_index
        if not in_bench:
            flags.append("letter not committed in its own bench (mirror points at a working tree)")
        if not in_mirror:
            flags.append("letter not mirrored/tracked in chora/letters/")
        if not in_index:
            flags.append("letter number %s absent from letters/INDEX.md" % index)

    # --- lane ---------------------------------------------------------------
    gate = row.get("gated_by")
    lane = "idea"
    if registered:
        lane = "registered"
    if equipped:
        lane = "equipped"
    if prod and landed:
        lane = "landed"
    if scored:
        lane = "scored"
    if announced:
        lane = "announced"
    if announced and not [f for f in flags if "by design" not in f]:
        lane = "closed"
    if gate:
        detail["gated_by"] = gate

    # --- gated rows are blocked where they stand, and only then is the claim judged -----
    if gate and lane in ("idea", "registered", "equipped"):
        lane = "blocked"
    # --- claim vs derived ---------------------------------------------------
    claim = row.get("claim")
    ladder = {l: i for i, l in enumerate(LANES)}
    if claim and claim != lane:
        # a hand may claim a lane the bytes have not reached (that is optimism, and the board
        # flags it) or a later one than it dares (that is a bookkeeping error, also flagged);
        # both are drift, because a board that forgives one direction is a board you must read
        flags.append("CLAIM DRIFT: the hand says '%s', the bytes say '%s'" % (claim, lane))
    hard = [f for f in flags if "by design" not in f]
    if hard and lane != "blocked":
        detail["reconcile"] = True
    return lane, flags, detail


# --------------------------------------------------------------------------- #
def global_audits(pins, heads):
    """Workspace-wide checks, including the ones that fired on 2026-09-12."""
    out = []
    # 1. every pin: bytes, hash, tracked-or-by-design
    no_bytes, bad_hash, untracked_real = [], [], []
    for rel, (_man, want, nbytes) in pins.items():
        if rel.startswith("<unparseable>"):
            out.append("manifest unparseable: " + rel.split(":", 1)[1]); continue
        p = ROOT / rel
        if not p.exists():
            no_bytes.append(rel); continue
        if want and sha256(p) != want:
            bad_hash.append(rel)
        elif git(ROOT, "ls-files", "--error-unmatch", rel) == "" and \
                not rel.startswith(IGNORED_BY_DESIGN):
            untracked_real.append(rel)
    out.append("pins: %d · no bytes: %d · hash mismatch: %d · untracked-not-by-design: %d"
               % (len(pins), len(no_bytes), len(bad_hash), len(untracked_real)))
    for rel in no_bytes:
        out.append("  DANGLING PIN (a permission slip for bytes that exist nowhere): " + rel)
    for rel in bad_hash:
        out.append("  HASH LIE (bytes != pin): " + rel)
    for rel in untracked_real:
        out.append("  UNTRACKED (pinned in git, bytes not in git): " + rel)

    # 2. B's insurance: the 108-pair baseline must survive
    if BASELINE.exists():
        missing = 0
        for line in BASELINE.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            man, path, sha = parts[0], parts[1], parts[2]
            try:
                files = json.loads((ROOT / man).read_text())["files"]
            except (OSError, ValueError):
                missing += 1; continue
            if not any(e["path"] == path and e["sha256"] == sha for e in files):
                missing += 1
        out.append("pin-baseline (docs/pin-baseline-2026-09-12-eve.txt): %s of 108 pairs missing"
                   % missing)
        if missing:
            out.append("  PINS LOST since the eve snapshot — law 2 breach, name them")
    else:
        out.append("pin-baseline absent (diff target for every merge of an append-only array)")

    # 3. the 2026-09-12 incident: a sequencer that owns a branch while a daemon beats on it
    for name, repo in heads.items():
        d = repo / ".git"
        st = [s for s in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
                          "REVERT_HEAD") if (d / s).exists()]
        detached = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD") == ""
        if st or detached:
            out.append("REPO %s is mid-sequencer (%s%s) — the publisher must be standing down"
                       % (name, ",".join(st) or "-", ", detached" if detached else ""))
    # 4. orphan snapshot commits (a beat that committed into limbo)
    for name, repo in heads.items():
        reflog = git(repo, "log", "-g", "--format=%H", "HEAD").split()
        if not reflog:
            continue
        reach = set(git(repo, "rev-list", "--all").split())
        orph = [h[:7] for h in reflog[:400] if h not in reach and
                git(repo, "log", "-1", "--format=%s", h).startswith("status snapshot")]
        if orph:
            out.append("REPO %s: %d unreachable snapshot commit(s) %s — a beat's work in limbo"
                       % (name, len(orph), " ".join(orph[:4])))
    # 5. the glass, and its blindness
    gp = ROOT / "docs" / "status.json"
    if gp.exists():
        try:
            g = json.loads(gp.read_text())
        except ValueError:
            g = {}
            out.append("glass: status.json is not parseable")
        if g:
            age = "?"
            try:
                # timegm, not mktime: the stamp is UTC and this machine is +0800. mktime believed
                # the local zone and reported the glass as 8 h older than it was — the exact 480
                # minutes this programme just spent learning that a clock read wrong is a clock
                # that lies in one direction only.
                t = calendar.timegm(time.strptime(g["generated"], "%Y-%m-%dT%H:%M:%SZ"))
                age = "%d min" % ((time.time() - t) / 60)
            except (KeyError, ValueError):
                pass
            ch = g.get("chora_head", "")
            head7 = git(ROOT, "rev-parse", "--short", "HEAD")
            # Deliberately does NOT print the head shas: chora_head moves because the snapshot
            # commits, so a line naming it would make the beat drift forever — the same
            # ping-pong the drift guard exists to break, arriving from the audit side.
            # The paint is always at least one commit behind HEAD (the beat writes the file, then
            # commits it), so the honest measure is DISTANCE, not equality: 1-2 commits is a fresh
            # glass, 40 is the freeze that this whole board was born out of.
            behind = "?"
            if ch:
                n = git(ROOT, "rev-list", "--count", "%s..HEAD" % ch)
                behind = n if n else "0 or unknown (not an ancestor)"
            out.append("glass: generated %s ago · paint %s, %s commit(s) behind HEAD%s"
                       % (age, ch or "?", behind,
                          "" if ch == head7 else "  (HEAD moved after the paint)"))
    # 6. citations that resolve: every `repo@sha` written in the archive must name a commit SOMEWHERE
    import re
    unresolved = {}
    for md in sorted((ROOT / "letters").glob("*.md")) + [ROOT / "AGENTS.md"]:
        for tok in set(re.findall(r"(?:chora|JacobiGP|MEF|Middle-Eigen-function|Sarcos|PolyNN|"
                                  r"Polynomial-Activated-NN|Kairos)@([0-9a-f]{7,40})", md.read_text())):
            hit = any(subprocess.run(["git", "-C", str(rp), "cat-file", "-e", tok + "^{commit}"],
                                     capture_output=True).returncode == 0
                      for rp in heads.values())
            if not hit:
                unresolved.setdefault(tok[:7], []).append(md.name)
    if unresolved:
        out.append("citations that name no commit in any clone here: %d" % len(unresolved))
        for tok, files in sorted(unresolved.items())[:8]:
            out.append("  UNRESOLVED CITATION %s — cited by %s (a rebase rewrote it, or it came "
                       "from a branch never fetched)" % (tok, ", ".join(sorted(set(files))[:2])))
    else:
        out.append("citations: every repo@sha in letters/ and AGENTS.md resolves in a clone here")

    return out


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    pins = load_manifests()
    heads = {}
    for name in ["chora"] + [b.get("name") for b in
                             json.loads((ROOT / "docs" / "status.json").read_text())["benches"]]:
        rp = repo_path(name)
        if rp:
            heads[name] = rp

    rows = []
    for row in reg["rows"]:
        lane, flags, detail = audit_row(row, pins)
        rows.append({"id": row["id"], "title": row["title"], "kind": row.get("kind", "experiment"),
                     "owner": row.get("owner_seat", "-"), "bench": row.get("owner_bench", "-"),
                     "lane": lane, "claim": row.get("claim"), "verdict": detail.get("verdict"),
                     "gated_by": detail.get("gated_by"), "budget": row.get("budget"),
                     "next": row.get("next"), "flags": flags, "detail": detail})

    audits = global_audits(pins, heads)
    reconcile = [r for r in rows if any("by design" not in f for f in r["flags"])]
    counts = {l: len([r for r in rows if r["lane"] == l]) for l in
              LANES + ["blocked", "RECONCILE"]}
    counts["RECONCILE"] = len(reconcile)

    if not args.quiet:
        order = {"idea": 0, "registered": 1, "equipped": 2, "blocked": 3, "landed": 4,
                 "scored": 5, "announced": 6, "closed": 7}
        print("CHORA · exp/dev board — derived from the record, not from the hand")
        print("=" * 78)
        for r in sorted(rows, key=lambda x: (order.get(x["lane"], 9), x["id"])):
            bad = [f for f in r["flags"] if "by design" not in f]
            mark = "✗" if bad else "·"
            print("%s %-11s %-26s %-9s %s%s" % (mark, r["lane"], r["id"][:26],
                                                r["bench"][:9],
                                                ("→ " + str(r["verdict"])[:22]) if r["verdict"] else "",
                                                ""))
            for f in bad:
                print("      ! " + f)
        print("-" * 78)
        for a in audits:
            print(a)
        print("rows: %d · %s" % (len(rows), "  ".join("%s=%d" % (k, v) for k, v in counts.items()
                                                     if v)))
    if args.write:
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        lines = ["# CHORA — the exp/dev board", "",
                 "<!-- GENERATED by bin/kanban.py. Hand-edit docs/experiments.json (intent), "
                 "never this file. -->", "",
                 "Generated %s · chora@%s" % (stamp, git(ROOT, "rev-parse", "--short", "HEAD")),
                 "",
                 "Rows %d · in the record and asking nothing: %d · lanes where a lane may say "
                 "FAILS and mean it · **%d rows need reconciliation** (their flags are printed in "
                 "full below, because a board that hides its own red rows is the instrument that "
                 "froze today)" % (len(rows), counts["closed"], counts["RECONCILE"]),
                 "",
                 "Lanes are derived from bytes (see `bin/kanban.py`'s docstring for the rules); "
                 "`claim` is what the hand believes, and a disagreement is a red row.", "",
                 "**访客导读（中文）**：[CHORA实验追踪看板-中文摘要](https://github.com/math4mad/chora/blob/main/artifacts/external/CHORA%E5%AE%9E%E9%AA%8C%E8%BF%BD%E8%B8%AA%E7%9C%8B%E6%9D%BF-%E4%B8%AD%E6%96%87%E6%91%98%E8%A6%81.md) — external bytes pinned at `cee1328\u2026`; it narrates the board at one moment, the live lanes always come from `kanban.json`.", "",
                 "| lane | id | row | owner | bench | verdict | next / gate |",
                 "|---|---|---|---|---|---|---|"]
        order = {"closed": 0, "announced": 1, "scored": 2, "landed": 3, "equipped": 4,
                 "registered": 5, "blocked": 6, "idea": 7}
        for r in sorted(rows, key=lambda x: (order.get(x["lane"], 9), x["id"])):
            bad = [f for f in r["flags"] if "by design" not in f]
            lane = ("**RECONCILE** " if bad else "") + r["lane"]
            nxt = r["next"] or (("gated by " + r["gated_by"]) if r["gated_by"] else "—")
            lines.append("| %s | `%s` | %s | %s | %s | %s | %s |" %
                         (lane, r["id"], r["title"][:70], r["owner"], r["bench"],
                          (r["verdict"] or "—"), nxt))
        lines += ["", "## Flags (every red row, in full)", ""]
        if not reconcile:
            lines.append("_none — every derived lane agrees with its claim_")
        for r in reconcile:
            lines.append("**`%s`** — %s" % (r["id"], r["title"]))
            for f in r["flags"]:
                lines.append("- " + f)
            lines.append("")
        lines += ["## Workspace audits (the checks that don't belong to one row)", ""]
        lines += ["- " + a for a in audits]
        lines += ["", "## Standing law this board enforces", "",
                  "- **Nothing crosses without a hash** (law 2): a row is `landed` only when its "
                  "bytes exist, are pinned, and the hash of the bytes *equals* the pin.",
                  "- **Four-way, not three** (learned 2026-09-12): pin ∧ on-disk ∧ hash-equal ∧ "
                  "**tracked in git**. Each clause has failed alone, in this order, on this day.",
                  "- **Single writer** (law 3): a letter counts as announced only when committed in "
                  "its own bench *and* mirrored here *and* indexed — three files, three failure modes.",
                  "- **Negatives are first-class** (law 4): `scored` includes FAILS and NOT "
                  "ADJUDICATED; nothing about a lane implies a claim survived.",
                  "- **The instrument reports on itself**: the baseline diff, the sequencer check, "
                  "the orphan-snapshot count and the glass staleness are rows of this board too.", ""]
        OUT_MD.write_text("\n".join(lines) + "\n")
        OUT_JSON.write_text(json.dumps({"generated": stamp, "chora_head": git(ROOT, "rev-parse", "HEAD")[:7],
                                        "counts": counts, "rows": rows, "audits": audits},
                                       indent=1, ensure_ascii=False) + "\n")
        print("wrote %s (%d B), %s (%d B)" % (OUT_MD.relative_to(ROOT), OUT_MD.stat().st_size,
                                              OUT_JSON.relative_to(ROOT), OUT_JSON.stat().st_size))
    if args.check and (reconcile or [a for a in audits if a.strip().startswith(("DANGLING", "HASH", "PINS", "REPO", "manifest"))]):
        print("CHECK: not clean — see the red rows above")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
