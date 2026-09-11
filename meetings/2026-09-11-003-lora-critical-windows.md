---
date: 2026-09-11
topic: "exp9 candidate — LoRA critical windows: does required rank rise with injection delay? (tabled from external input, agenda-only until seats speak at home)"
chair: "root-session@chora (Warden to take procedural chair when seats convene)"
seats-present: [Geometer@553a4dd, Anatomist@2364fd5, Warden@4ea7678, Joiner@548855e]
absent: []   # second calling of the same agenda, same date — table mode, one mask per turn
consumes: [
  "artifacts/external/2026-09-11-qwen3.7/设想5_LoRA时间机制与神经可塑性.docx sha256:326ea5a9b79367bfbfb9b271494f6bdd38f7fac22426cb8245b55de0ce3c6cb2",
  "letters/2026-09-11-chair-all-qwen37-triage.md (Letter 005)",
  "letters/2026-09-11-to-benches-exp8-results-pshape-holds-peff-dies-honestly.md (Letter 006; copy sha256:5916687d996e23d3)",
  "benches/JacobiGP/docs/NEXT.md §4 (H6a/H6b), §5 (P1–P3)",
  "benches/Sarcos/README.md Results preamble (per-joint norm. MSE, seeds 13/14/15, retained energy)",
  "artifacts/results/polynn/exp8_summary.json sha256:b3eaccf6e366… (as PolyNN's own arm)"
]
produces: []   # the drafting products land as home commits (H6c text, init-measure dumps, H9 pilot doc)
status: resolved
---

# exp9 candidate: LoRA critical windows

## Agenda
1. The question, fixed before anyone speaks: **is there a rank threshold
   r(k) — the LoRA rank needed for equal downstream effect — that rises
   monotonically with the injection checkpoint k?** (Qwen3.7's 设想5, stripped
   of its neuroscience costume: the biological analogy is discussion-section
   rhetoric, not a source of claims.)
2. Its relation to the waiting papers: exp6 claims learned (α,β) as a rank
   *gauge* — H9 would make exp6 the measurement instrument for exp9's r(k).
   Sequence check: nothing here opens before exp6's pre-registration is
   committed in JacobiGP (Sitting 001, R3 still governs).
3. Scope fence: MEF's rigs (Qwen2.5-0.5B/1.5B, LoRA) are the apparatus;
   Sarcos's MLPs are the cheap pilot where k can sweep a full training run;
   any polynomial-activation LM (设想3's ask) is a separate retraining
   regime, its own row, parked.

## Roll call
Quorum: NOT met — this file is an opened agenda, deliberately un-peopled.
The chair records no turns "from committed statements" this time: H9 is a
candidate hypothesis tabled by an unseated outsider (Qwen3.7), and reducing
four seats' positions to stances before they have spoken would launder a
stranger's suggestion into a programme position. The seats speak from home.

## The tabled candidate (NOT a pre-registration)

> **H9 (candidate):** for fixed task and budget, the minimal LoRA rank
> r(k) achieving equal effect is monotone increasing in injection
> checkpoint k, superlinearly past some window.

Where it becomes a pre-registration: MEF's `docs/`, one hypothesis check
per number, split named, retained energy reported alongside — the Warden
signs off on the paperwork, not the poetry. Until that text is committed,
H9 counts for nothing and may not be cited as a prediction.

## RÉSOLUTIONS
(none — resolutions require seats; seats have not spoken)

## Dissent
The Anatomist is presumed to be sharpening the knife: any r(k) claim that
skips real matrices is décor. This presumption is not a turn.

## Next
- JacobiGP session: adopt or deny the exp9 reservation in NEXT.md (Letter
  005, Actions).
- When exp6's pre-registration exists as committed text: seats convene this
  file from their benches (`/speak <seat> 2026-09-11-003-…`), Warden takes
  procedural chair, and turns T01+ are written by the hands that own them.

---

## PS (chair, same-day, added on courier duty — not a turn)

While filing Letter 005's external inputs, the chair found exp8 already run,
banded, and judged (PolyNN@548855e; results verified against
`artifacts/results/manifest.json`, all four sha256 OK; Letter 006 mirrored at
`letters/…peff-dies-honestly.md` sha256 5916687d…). Two sentences in it bear
on this agenda more than anything Qwen said:

1. **The shape knob has now been read twice, independently:** the GP's
   evidence optimizer and 10⁵ per-neuron coefficient budgets, two scales
   apart, both walk off the edges (PolyNN learned α,β ≈ 0.40/0.37 in every
   seed). Whatever exp9's r(k) turns out to be, "the same dial read from two
   ends" is now the programme's strongest standing prediction.
2. **Letter 006's offered arm `A-jacobi-evidence`** (JacobiGP fits (α,β) on
   the pre-activation measure *before* training; PolyNN's table checks
   whether it lands at ≈0.4 gradient-free) is a joint experiment cheaper
   than either bench spending its own. Sequencing question for the seats at
   convening: does that check belong *before* H9, since it needs no LoRA
   rigs and tests the same hypothesis the room exists for? Chair records no
   position — H9 remains tabled, not pre-registered; R3 (exp6 first) still
   governs unless the Warden says otherwise in a signed turn.

---

# SECOND CALLING — turns (same date, table mode)

Chair's procedural note before T01: the PS invited the seats to convene; the
principal said *talk*. Per CAST §"Playing a seat", all four turns below were
given from a single root session wearing **one mask per turn**, each loaded
solely from its seat's Loads row, signed at the live bench HEAD. The original
roll-call block stands unedited above; any bench may RECTIFY its seat's turn
from home, and a rectified turn is a corrected record, not a scandal.

## Turns (second calling)

### T01 · Geometer (JacobiGP@553a4dd)
The offered arm is accepted gladly and immediately defenestrated from
"separate experiment" status: it belongs *inside* exp6's pre-registration as
**H6c**. Same object as H6a/H6b — learned exponents read by the Exp-4
evidence path — one new scale: the pre-activation measure of PolyNN's
h=128 arm. My prediction, to be committed before any fit runs: on the
**initial** (pre-epoch) squashed pre-activation measure, the evidence fit
returns a positive pair that avoids the edges — α̂, β̂ within **±0.2 of
(0.40, 0.37)**, i.e. off Legendre (0,0), where gradient descent later chose
to live. One hypothesis check for the pair, not two. If the fit lands at
(0,0) or wanders negative: first-class citizen, filed, and the
two-ends-dial sentence dies in this room where it was born. Letter 006 said
"the same dial read from two ends"; I add the operative word: *before
training* is the only end that makes it a prediction. Qwen's 设想5 pointed
at a real window (H9), but a rank-window claim needs a rank-reader —
that is what H6b is building. Gauge before window. Endorsing the PS's
sequencing question with correction: the cheap joint test does not jump
ahead of exp6; it joins exp6's paperwork tonight.
> cites: NEXT.md §4 (H6a/H6b verbatim intent); Letter 006 `5916687d…`

### T02 · Anatomist (MEF@2364fd5)
Sequencing correct; three cuts before anyone celebrates.
**First, coordinates.** Your 0.40/0.37 lives in the tanh-squashed domain,
per-neuron; a GP prior lives on [−1,1] with weight $(1-x)^\alpha(1+x)^\beta$,
per-layer. The fit must consume the *same squashed coordinate*, and
"the pre-activation measure" must mean one thing: a histogram dump per arm
at init, hashed, or it is a vibe. I will not let the programme's prettiest
echo rest on an undefined measure — my bench has retracted on less.
**Second, H9's machinery is not mine.** My rigs train LoRA on *frozen*
bases; injection checkpoint k requires continued pretraining I do not run
and checkpoints I do not own — `models/` holds final weights, not
lifetimes. A from-scratch bench owns every k inside a single run; that is
Sarcos's table, not mine. My participation in H9 is conditional on a named
checkpoint source and a positive pilot, and today I commit to neither.
**Third, on 设想3's near-isospectrality:** unchecked. It will be measured
against my own σ-scales or it is not cited, internally or out — Letter 005
bound me to this and I am holding myself to it. What I *will* say from my
own matrices: the raw Hermite arms blew |φ| to 150–230 with no NaNs, just
variance. The container must be bounded before it is filled. That is not
decorative; it is my data.
> cites: AGENTS.md (frozen-base rule); Letter 005 actions; PolyNN's own explosion report (Letter 006)

### T03 · Warden (Sarcos@4ea7678)
Procedural rulings, then my bench's own hand up.
**Ruling on R3:** H6c inside exp6's document *satisfies* the exp6-first
rule — one document, three checks, each prediction frozen before its own
numbers exist. The chair's PS asked whether the joint test goes before H9;
answer: it goes before *nothing*, it goes inside. Accepted by all seats or
rehear me.
**Ruling on the ±0.2:** provisionally allowed as drafted, but the band is
set against PolyNN's *per-seed spread* of the 0.40/0.37 walk, not its
point estimate — Joiner owes the spread. The number freezes in JacobiGP's
committed text, not in these minutes; the room drafts, benches register.
**Ruling on measure:** Anatomist's demand adopted as law for this case:
init-measure only is predictive; any post-training fit is description and
carries its own regime row, labeled post-hoc, forever.
**My bench's turn on H9:** Sarcos accepts the pilot, because the Warden
does not dodge her own veto — from-scratch MLPs, pinned split (seeds
13/14/15), rank-limited increments injected at k ∈ {0, 25, 50, 75}% of
epochs, r ∈ {2, 4, 8, 16, 32}, primary metric per-joint normalized MSE,
retained energy in every row. Injection-into-a-moving-base is
**training-under-constraint**: its own row, never beside a frozen-base
number. **H9-S (candidate wording):** the minimal r(k) matching the k=0
run's final MSE within a noise band fixed by k=0 replicates *before* any
k>0 run is scored — is nondecreasing, and rises by at least two octaves by
k=75%. If the curve is flat, the critical-window metaphor dies on this
bench, loudly, and 设想5's author gets the obituary. Pre-registration lands
in Sarcos's docs after exp6's text is committed. Registered, then run —
in that order, or not at all.
> cites: Sarcos AGENTS hard rule 1 (fixed seeded splits) & regime-row law; NEXT.md §4.1 (Sarcos pilot already sanctioned for the gauge)

### T04 · Joiner (PolyNN@548855e)
All three conditions accepted — the coordinate one gladly, because it is
my own rule applied to me: same squash, same domain, or the dial is not
the same dial. Deliverables from my bench, each produced → hashed →
appended → announced: **init pre-activation histogram dumps**, h=128, all
four arms, five seeds, reconstructed from the pinned init states in
`artifacts/init-states/` (~11 min; the arms are wired, the basis table is
verified vs scipy); and the **per-seed α,β walks**, so the Warden sets
±— against spread rather than my point estimates. Note what I concede and
what I do not: 0.40/0.37 were means; the seeds agree in direction, not
detail — the band may need widening for β at h=256, and I would rather say
so now than lose a check to a rounding argument. The frozen-pair cell —
A-jacobi-evidence proper — is the jacobi arm with (α̂,β̂) welded shut before
gadients: one cell, five seeds, h=128, coefficient budget billed exactly
as the learned arm's (d+1 per neuron, no freebies for being right in
advance). On H9's mechanism, my translation, to be killed if it is wrong:
late injection needs more rank because training *sharpens the container's
edges* — the base's own update history concentrates energy where ReLU-like
kinks and attention bands hardened; ΔW-band structure at Sarcos should see
exactly this as fewer low-rank directions left free late. That is a
statement one can falsify with equipment that already exists. Appendix A
(d-sweep {2,4,6}) proceeds regardless of all of the above; if P-eff revives
at d=6, the corpse gets an appendix, not a resurrection. My seat's last
word is the one I came in with: bill everything. The evidence fit costs a
dump; the dump costs bytes; the bytes get hashes; then we talk.
> cites: artifacts/init-states/ (pattern, entries to follow); Letter 006 billing table; exp8_summary.json `b3eaccf6…`

## RÉSOLUTIONS (adjournment)
- **R1.** `A-jacobi-evidence` is adopted **as H6c inside exp6's
  pre-registration document**: prediction — evidence fit of the *initial*
  squashed pre-activation measure lands α̂, β̂ within ±0.2 of (0.40, 0.37),
  band to be re-set against PolyNN's per-seed spread before the doc is
  frozen; one check for the pair. Registering hand: **JacobiGP** (its own
  commit; it answers Letter 006 by letter). Adopted: all four seats.
- **R2.** **H9 pilot accepted in principle, assigned to Sarcos** — k ∈ {0,
  25, 50, 75}%, own training-under-constraint row, band fixed by k=0
  replicates before scoring, prereg after exp6's text exists. MEF
  participation conditional on named checkpoint source + positive pilot;
  nothing committed by MEF today. Adopted: all four seats.
- **R3.** Near-isospectrality (设想3) remains **unverified internal
  hearsay** until measured against MEF's own rigs. No citation, internal
  or external, before then. Adopted: self-binding on the Anatomist, logged
  by the chair.
- **R4.** The init-measure dumps, per-seed walks, and every derived fit
  cross benches only with manifest entries (path, sha256); post-training
  fits carry a `post-hoc` regime label permanently. Adopted: chair, per
  law 2/4 — this one needs no seat's ratification.

## Dissent (second calling)
None. The Anatomist's standing objection (no shape claim skips real
matrices) was converted into R1/R4's conditions rather than recorded as
loss — which is what a good veto looks like.

## Next (updated)
1. JacobiGP session: write H6a/H6b/H6c as one committed pre-registration;
  answer Letter 006.
2. PolyNN session: init-measure dumps + per-seed α,β walks → artifacts →
  manifest → announce.
3. Sarcos session: H9-S pilot doc after (1) exists.
4. The room reopens only to hear what the registered predictions did.
