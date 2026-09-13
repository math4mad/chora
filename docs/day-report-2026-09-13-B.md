# Day report — machine B (`m1-16g`), 2026-09-13

**Written at 13:1x local (+0800) / 05:1x UTC.** Disk 40 Gi free (the bootstrap gate's floor exactly —
noted, not acted on). `caffeinate -dims` running since 12:1x. One training/solve process at a time;
nothing ran concurrently today. Glass last read `2026-09-13T04:38:17Z`.

Yesterday's report is `docs/day-report-2026-09-12-B.md` `(sha256 4e92204f794f…)`. Today's record is a
**half-day of closures, not a half-day of runs**: the queue's fifth item stayed blocked and one of its
fourteen-odd hypotheses got formally retired by other hands.

## 1 · The queue, line by line

| # | Task | Bench @ sha | Bytes that crossed (sha256 12) | Wall clock | Status today |
|---|---|---|---|---|---|
| 1 | E0 ladder, seed 14 | `MEF@5b8ebc6` (B's branch) + `chora@b6a5f67` | json `5e6e52fd7cc4…` / `695dba48ff1d…` (yesterday); **today the run's stdout landed**: `artifacts/results/mef/E0_seed14_pretrain.log (d9b7adee7597…, 681 B)` | 509.7 s pretrain + 2,699 s sweep (yesterday); **0 s today** — the log was always on this disk | **seed 14 CLOSED** (pin was true of bytes all along); **seed 15 HELD**, §4.1 |
| 1b | E0 ladder, seed 15 | — | — | — | **NOT RUN.** `MEF dirty=1` on A, read live at 04:38:17Z |
| 2 | Sarcos Step 0 dose–response | `Sarcos@b22f1e9` | 5 B rows: `Step0_dose_256h256_B.json (e3f7fa1955cf…)`, `…_64h64_B.json (91c34b5047ec…)`, geometry audit, logs | (yesterday) | **CLOSED** at `fb37e04`+`b22f1e9`; verdict NO DOSE QUALIFIES; three seeds already inside it, so item 5 has no third-seed left to give |
| 3 | PolyNN init dumps + per-seed walks | `Polynomial-Activated-NN@a0deb68` / `2fcb158` | 21 `h6cB` entries, `…/h6cB/h6c_init_dumps_summary.json (e502abd7cd5c…)`, walks `…/polynn/h6cB/h6c_walks_summary.json (bd58e62bb8d1…)` | (yesterday: 11.4 s dumps, 5 walks ≈90 s each) | **CLOSED BY OTHER HANDS, today**: Letter 022 scored H6c **FAILS** `(α̂,β̂)=(−0.922628,−0.916317)` vs (0.40,0.37) ±0.2; Meeting 004 §Next-5 records *"nothing owed today"* |
| 4 | **Isospectrality audit** | `chora@55c995d`; rig `chora/experiments/iso_audit_down_proj.py (20ad915c24f5…)` | `artifacts/spectra/iso_audit_down_proj_B.json (e99c4cae1b40…, 850,368 B)`; `…_B.log (91ed643ccd6f…, 2,870 B)`; 2 new manifest entries — `artifacts/spectra/manifest.json` goes **0 → 2 files** | **9.8 s** (7.1 s = the 24 Qwen SVDs on CPU; 1.4 s = the ladders) + 2 s cold-reproduce | **CLOSED, with R3 still open** — the deliverable is a ruler and a scope statement |
| 4b | its letter | `chora@c5fe55c` | `letters/2026-09-13-B-MEF-isospectrality-ruler-not-verdict.md (sha256 eed88bd301e7…)` = **Letter 026**, INDEX row in the same commit | — | crossed |
| 5 | third seed of anything | — | — | — | **nowhere to land**: 2 and 3 are done/closed, 1b and 4's remaining sibling are MEF |

**Off-queue work that was also today:** (i) ` JacobiGP` was **5 commits stale** and `Kairos` **1** —
fast-forwarded to `9d88e87` and `ae6be01` before anything was read; had B not pulled, B would have
answered Letters 022/025 from memory (Letter 020 PS 1's warning, applied to itself); (ii) the
**Letter 021 §5 debt** closed by `git add -f` (§3.4); (iii) the five permanent `chora` dirt lines
killed at the source, `chora@316c7e7` (§3.5); (iv) two `.DS_Store` reverts.

## 2 · The twins verdict, in the one sentence the brief asks for

**Agreement, and the divergence is now a number, not a worry:** A's seed-14 ladder against B's
seed-14 ladder gives floors **max |Δ| = 0.028914 nats, exactly 0.000000 at k=0** — i.e. the machine
effect sits *below* the 0.045188-nat same-machine seed band, and Gate 6 is closed by `MEF@382e438`
(Letter 025 §4, not by B). Two smaller twin statements B can add today, both same-machine:
**all sixteen** ladder rows in the audit (4 `down.weight` × 2 seeds) agree in direction and to within
0.1–0.9 on stable rank, and the audit's science payload reproduced **bit-identical across two cold
processes** on this laptop (`473628e118bfa5e7`, json minus run timestamp and wall clock).

## 3 · What B corrected in its own record, today

1. **A false inequality in the rig.** It printed `weyl_bound_respected: false` on **34 of 40** rows
   because it tested `‖Δσ‖₂ ≤ ‖ΔW‖₂`, which is not a theorem (`ΔW = εI` on a square matrix: `ε√n`
   against `ε`). The real bounds — Mirsky in Frobenius, Weyl in `l_∞` — are now checked separately
   and hold on **all 40**.
2. **A false determinism alarm.** Same-process self-check printed `max|Δσ| = 3.625`; that is not
   LAPACK being noisy, it is the rig comparing a **descending** spectrum against an **ascending**
   one — 3.625 = `σ_max − σ_min` of layer 0 (3.8228 − 0.197). Now 0.0.
3. **An index that does not earn its keep.** `I = ‖Δσ‖₂/‖ΔW‖_F` (observed min 0.282 / median 0.465 /
   max 0.900) is **not separated from a matched-Frobenius iid-Gaussian null** (0.295 / 0.478 / 0.851;
   30/40 rows above it, by ≤0.05). So I measures perturbation *size*, not the *locus* of adaptation.
   Filed as a defect in B's operationalisation, **not** as a result about the container.
4. **A digit caught before it crossed.** §1's mean stable rank was drafted **116.6** from a terminal
   glance; re-derived from the pinned artifact it is **121.2**. Fixed pre-commit, and recorded in the
   letter's §6 so the correction is in the file that ships.
5. **An ask withdrawn as mechanically invalid.** B told the human a `git stash` could clear A's
   `?? outputs/stage19_kairos_e3/`; untracked files do not enter a stash without `-u`, so option (c)
   never existed. B also overstated *"the dirt appeared after Letter 006"* — `status.sh`'s AGE column
   measures the **HEAD commit's** age, not the dirt's. Both corrected the same hour, in front of the
   human rather than quietly.
6. **The defect B did not cause but did close.** Letter 021 §5's "pin with no bytes anywhere" was
   `~/.gitignore_global:64` (`*.log`) swallowing B's own `git add` on 09-12. The pin was true of bytes
   that existed and false of a repository that did not hold them; A's `find` searched A's disk for B's
   stdout. Landed with `-f`, hash unchanged, and the **exemption withdrawn** — `- pin:` *is* the
   marker the validator parses, so a future regression on those bytes prints red again instead of
   being forgiven by a line written on the day they were healthy.
7. **Five dirt lines killed at the source, not the symptom.** `benches/*` are tracked symlinks
   (mode 120000) whose *content* is a path; `sync.sh:20`'s absolute `ln -sfn "$src"` encoded a
   machine-scoped string into a machine-shared repo. B took the relative-link fix, **not**
   `git rm --cached`, because the second would delete a fact to silence a symptom. Verified the
   daemon cannot undo it (`publish-status.sh:71` commits an explicit three-path pathspec, never
   `-A`), and verified every consumer (`status.sh:52`, `share()`) resolves through `cd`/`pwd -P`.
   `chora`'s `git status` has been empty on this laptop since.

## 4 · Every STOP honored, including the expensive one

1. **seed 15 — HELD.** `MEF dirty=1` at `382e438`, read **live** (glass moved between two polls:
   03:46:04Z → 03:51:25Z → 04:38:17Z). Cost: the day's second ladder run. The dirt is
   `?? outputs/stage19_kairos_e3/`, and E3 is **NOT ADJUDICATED** in the record — so B did **not** ask
   A to clear it, and said so out loud when the human offered to. A fake green is worse than a true red.
2. **Post-activation H6c dumps — NOT RUN**, though B itself offered them twice ("11 seconds of
   compute, B will run them tonight"). Letter 022 §3 ruled the contrast falsifier *confirmed
   unreachable, not repaired*; §2 forbids any re-scaled variant reading as confirmation; Meeting 004
   §Next-5 says nothing is owed. Running them now would be B writing science into another seat's
   registration (law 5).
3. **The projection statistic — NAMED, NOT RUN.** `UᵀΔW V`, off-diagonal share, is the measurement
   that would actually answer 设想3. B discovered at 12:4x that its own index failed, which means any
   statistic chosen in the same afternoon is a **post-hoc** statistic. It is the Anatomist's to
   register, and B wrote exactly that sentence in the letter rather than quietly running it.
4. **`models/manifest.json` — NOT TOUCHED**, though it holds today's only non-exempt validator
   failure (`…/Qwen2.5-0.5B/…/configuration.json` pins `44136fa3…`/**2 B** — literally
   `sha256("{}")`, the `{}`-pin's own shape — while B's copy is `"Entry not found"`/**15 B**, a
   ModelScope error body written to a filename). `by: MEF@2364fd5`, so it is A's entry. Reported in
   the letter and the commit message. **It did not contaminate the audit**: the operand is
   `model.safetensors`, verified `88c142557820ccad…` before a single float was read, and the other six
   present 0.5B files verify too.
5. **The glass untouched.** No `status.json` edit, no `publish-status.sh`, no launchd; today's
   `sync.sh` run printed the guard obeying: *"CHORA_NOPUBLISH=1 — skipping fleet snapshot (this
   machine is a worker, not the glass)"*.
6. **Other seats' `.DS_Store` — REVERTED, NOT UNTRACKED.** `git rm --cached` in JacobiGP's `main` is
   the Geometer's commit; B reverted the byte-churn (6148 → 6148 B, 0 insertions/deletions) and asked
   for the untrack to be done by its owner, at the same moment on both machines so it cannot make a
   false red light.
7. **Letter number claimed only after reading the room.** INDEX checked: highest present was **025**;
   B claimed **026** with a yield clause in its own header, because three double-booked numbers in two
   days is what happens when everyone counts from their own stale log.
8. **The 5 bench symlinks stayed uncommitted all day** (yesterday's fifth STOP) until the human
   ordered the fix — and then the fix went into the *generator*, not into five machine-local strings.

## 5 · Environment, attached

`artifacts/results/mef/B-env.json` `(sha256 b78c34e2f5cb…, 3,677 B)`, already manifested, and now also
carried inside today's artifact's own `meta` field: host `lunardeMacBook-Pro.local`, machine
`m1-16g`, **macOS 15.7.5 arm64**, **python 3.11.16**, **numpy 2.4.6**, **torch 2.14.0**,
`mps_available: true` (**unused today — the audit is CPU by design, "numpy, CPU fine" is the queue
row**), BLAS name/version reported `null/null` by `numpy.__config__` (a gap in the probe, listed as a
question below), SVD backend `LAPACK gesdd, float32`, run start `2026-09-13T04:37:22Z`.

## 6 · Turns owed at hand-off

- **Anatomist (MEF)** — Letter 026 is yours: R3 stays open because **no RL- or SFT-adapted Qwen
  checkpoint exists in `models/manifest.json` or on either disk**, so the claim is *un-instrumented*,
  not refuted. Two byte-sets would lift it (ΔW persisted per rung; or one hash-fetched `-Instruct`
  sibling, which is the chair's manifest act). The projection statistic is yours to register if
  anyone's.
- **Horologist + room** — Meeting 004 Q4's *"Gate 6 open"* is stale by `MEF@382e438` (09-13 11:00
  +0800), and **meeting 004 is absent from `meetings/INDEX.md`** (003/002/001 only). B files both and
  offers the INDEX row; the Status/Resolutions columns need a seat's judgement, so B did not write
  them (law 7, hands do not interleave).
- **chair** — three things: (i) the `configuration.json` pin, A's to amend; (ii) **Q3's parenthetical
  is now wrong in a good way** — B-owned exemptions in `docs/stale-pins.md` are **0**, the single
  remaining exemption is the C5 hover-globe file, owned by the external batch; (iii) the
  `*.log`-in-global-gitignore trap is a **P0 protocol** item, not a per-person reflex: today it made a
  phantom pin (Letter 021 §5), and today C2 caught it in the seconds before a commit existed.
- **A, via the human** — `cd ~/Programming/code-2026/chora && git pull --rebase &&
  CHORA_NOPUBLISH=1 bin/sync.sh`, **in that order**: pulling first rewrites the five links to
  `../../<bench>`; running the old sync.sh first re-absolutises them and the dirt returns.
- **B** — seed 15 and its ritual, the moment `MEF` reads `dirty=0`. ~59 min, scripted, unhurried.

## 7 · Questions, quarantined from every table (added at close of day)

1. *Question.* Is the mid-stack concentration of `down_proj` scale an **area** (Letter 023 §6, "areas
   not curvature") — stable rank 49–63 at L9–L12 against 209–266 at L20–L22, `σ_max` peaking at L10 —
   or Qwen's trained accident? Answering needs a second family; `models/manifest.json` lists five
   others (electra, bert, roberta, distilbert, Qwen-1.5B) and **not one of their files is on this
   disk** — B's store holds exactly 10 files / ~953 MB, and all of them are the Qwen2.5-0.5B set this
   audit consumed plus its manifest and README. (Yesterday's byte-audit said "48 KB store": true then,
   stale now, and corrected here rather than left as a quoted number from a day that fetched nothing.)
2. *Question.* H9-M reported `r = 2` capturing 99.8 % of what `r = 32` buys. §1 says rank 32 spans
   11.1 % of a real `down_proj`. So is an r-saturated gain a statement about the **optimiser's
   reachable increment** rather than the container's rank — and does that survive anywhere but a
   1.6 M-param byte-LM? B has no answer and put none in the letter.
3. *Question (instrument).* `numpy.__config__` reports BLAS name/version as `null` on this wheel, so
   the audit records "gesdd" without recording *which* gesdd. Is a BLAS identity part of `B-env.json`'s
   contract, given that a spectrum is the one number here with no seed to regenerate it from?
4. *Question (protocol).* Letter 020 PS 6 concluded no observation available to B could distinguish
   "A asleep" from "daemon dead". That is now **retired** — the glass repaints and `-v` names paths.
   Does rule 4's wording still want "do not start work there", or should it read "do not start work
   where the named dirt is a live question"? B obeyed the rule as written today and thinks the
   room, not B, should decide the amendment.
5. *Question.* The 40 `I` values in the artifact are 40 rows over 8 matrix-pairs × 2 ladders; B
   reports them raw because it has no registered band. If anyone wants them *used*, that is a new
   check with a frozen threshold, and R4 already says a post-hoc row can neither rescue nor upgrade.

---

**Hand-off state, verified after this file was written:** `chora` ahead 0 / behind 0 at `316c7e7`;
every bench repo `git status --porcelain -uall` **empty** and **0 commits** not on an origin ref
(all six re-`fetch`ed); validator `134 pins · 46 failures · 45 NOT exempted`, of which 45 are
models/data never fetched to this laptop (C2/C3 waived per entry by law 1) and the 1 non-exempt is
`configuration.json`, A's — **today's three new artifacts contributed zero failures**.
`— Bench B (m1-16g), worker, not the glass.`
