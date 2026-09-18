# PREREG — Exp 10 · 离散 Adapter 的概念空间差异 + 中间型 LoRA 子空间分析
## Discrete adapter concept-space divergence & the intermediate-LoRA subspace test

**Date registered:** 2026-09-18 · **Registered by:** lola@LETHE, on owner's commission
**Owner's ask (verbatim, dialogue-as-entry):** "external 里的实验一和实验二和 Chora 的任务相配…按照时间先做一，下午做二"
**Bench:** workspace-joint (apparatus borrowed from MEF's LoRA rigs; venue: chora/experiments)
**Base model:** Qwen2.5-0.5B-Instruct, local cache `chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master`
(safetensors sha256 `88c14255…d342`, per models/manifest.json; hash verified before any token crosses it — law 6)

## Wording of the commission's documents (deviations recorded up front)

1. **Step 0 addition.** The owner's Experiment-1 doc assumes 春节 LoRA 与夏季 LoRA exist.
   They do not exist in this workspace (manifest scanned 2026-09-18: no spring/summer adapters).
   Therefore Exp 10 runs a Step 0: train both discrete adapters here, with one shared
   hyperparameter recipe, so that Exp 11-style comparisons remain internal. Registered as a
   deviation, not a silent fix.
2. **Season topics** (春节 spring / 夏季 summer) come from the owner's doc verbatim.
   Neutral probes are the control arm.
3. **Regime honesty (law 4):** these are *training-under-constraint* small-corpus adapters —
   they are concept-probe instruments, not claims about production fine-tuning. Rows of the
   table below are kept separate: no fusing of Exp-10a (divergence) with 10b (subspace).

## Experiment 10a — divergence of discrete adapters

**Hypotheses (pre-registered, direction fixed before any run):**
- H1: JS(spring, summer) > JS(base, spring) and JS(spring, summer) > JS(base, summer)
  on *own-theme* probes.
- H2: keyword hit-rate: each adapter hits its own theme's lexicon strictly above base on
  own-theme probes; cross-hits (spring adapter on summer probes) below own-hits.
- H3: neutral probes compress: all three pairwise JS < the mean own-theme JS (the director
  changes scripts only where the scene asks).

**Metrics (as specified in the owner's doc):**
- keyword hit-rate per model × probe-group (5 samples/question, mean over samples);
- per-probe next-token distributions at the answer-start position, top-k union k=50,
  add-α smoothing α=1e-6; KL both directions, JS = symmetrised; aggregate = mean over group.

**Judgment:** H1–H3 each get PASS / FAIL / INCONCLUSIVE (band from 5-sample replicate spread:
a difference counts only if it exceeds the within-pair replicate std). Negative results are
first-class and stay in the table.

**Data-leakage guard:** probe set is written FIRST, hashed, and committed before the training
corpus is authored; no probe string (nor any substring ≥ 6 chars) may appear in any corpus
file; validator script checks this and refuses the run otherwise.

## Experiment 10b — intermediate LoRA, SVD subspace test

**Hypothesis (the owner's doc's core, registered as-is):**
- H4: sim(mid, spring) < sim(spring, summer) AND sim(mid, summer) < sim(spring, summer),
  where sim(U_i,U_j)=‖U_iᵀU_j‖_F on top-k left singular vectors of the A matrices
  (and the V-side for B matrices), k from cumulative energy ≥ 90%.
- Sensitivity: repeat at k ∈ {1,5,10,20,r}. If the inequality sign changes with k, the
  claim is downgraded to INCONCLUSIVE, per the doc's own robustness clause.
- H5 (secondary, can neither rescue nor upgrade H4): effective-rank ordering of the three
  adapters + invasion-dimension report (which top singular directions of the base's layers
  the adapters write into).

**Null model registered now (the honest one):** a mid adapter trained on a 1:1 mixture
*should* share vocabulary/subspace with both parents; if sim(mid,·) comes out ≥ sim(spring,
summer), that falsifies H4 and says "the mixture is an interpolation, not a third space".
Either way the number is the news.

## Compute budget & schedule (owner: morning → afternoon)
- 3 × LoRA trainings (spring, summer, mid): same recipe r=16, α=32, dropout=0.05,
  lr=1e-4, 3 epochs, only Q/K/V/O of attention + MLP on all 24 layers.
- bench: 40 probes × 3 models × 5 samples ≈ 600 generations ≤ 1 h on MPS.
- SVD: adapters' A/B matrices per target module — cheap, CPU float64.
- 10a lands this morning; 10b this afternoon. No result leaves this directory without a
  manifest pin (path, sha256, by: chora@sha).

## What must not happen
- no tuning on probes; probes are scored once;
- no cherry-picked k in 10b — sensitivity sweep is the table;
- no cross-row fusion of 10a/10b results;
- if base weights fail their manifest hash → stop, do not proceed on unverified bytes.

## Addendum (registered mid-run, 2026-09-18, before any scoring)
- The **mid adapter is additionally benched** on the 40 probes (arm 4: exploratory).
  It does not enter H1–H3 (those stay three-arm); it feeds 10b's interpretation only
  (is mid an interpolation in behaviour as well as in subspace?).
- Mid training recipe deviation, declared: 110 pairs × 3 epochs = same samples-seen (~330)
  as the discrete arms (55 × 6). Loss lands at 2.85 vs ~1.5 for the specialists — the
  mixture is measurably harder to fit; first-class datum, not a failure.

### Addendum 2 (post-scoring, same day) — 10b hardening landed
Seeds 14/15 × three arms trained with the identical recipe (--seed only); SVD rerun offline.
H4's reversal on the WRITE side replicates at all three seeds; V-A stays flat (~3.79 all pairs).
Global ΔW overlap: spring~summer 0.13 vs mid~parent ~0.63. "Mixture = interpolation" is now a
three-seed statement, cleared for the letter to MEF/Kairos.

### Addendum 3 — 10c registered (owner's afternoon commission "按照qwen的建议做" +
### artifacts/external/2026-09-18-afternoon-exp/afternoon-exp.docx §2.3/§6.2, sha 64e8bf2a…)
Full-sequence teacher-forced JS: for every probe, one reference text per theme is fixed as the
seed-13 greedy continuation (chosen by rule, not by eye — text itself is never filtered), and ALL
THREE arms score that same text token-by-token; JS over the full vocabulary softmax at each
position, mean over positions (excluding prompt). Registered expectations re-stated BEFORE run:
- H1c: if the 10a reversal was style-averaging artifact, theme-probe JS(spring,summer) drops
  BELOW base~adapter again only after per-position mean over CONTENT-bearing positions… simpler
  registered claim: reversal magnitude at full-sequence level < single-point magnitude.
- Secondary report: where along the sequence the divergence lives (positional curve, first vs
  second half), no claim attached.
10d (router demo) is engineering demonstration, no hypothesis; speed/size numbers only.

### Addendum 4 — 10f 跨域正交复检 + 10c′ 敏感性（owner: "那就继续", 15:0x）
**10f.** Three NEW domains — 代码(code) / 法律(legal) / 医疗(medical) — each a 40-pair QA
corpus (**deviation registered: 40 pairs, not 55** — corpus economy; the H6 test is
pairwise-geometric and needs no size parity, but magnitudes are not comparable to 10b's).
Same LoRA recipe (r=16, lr 1e-4, 6 epochs, seed 13). Arms join the existing six-question
family → pairwise SVD over ALL cross-domain pairs:
- **H6 (primary):** every cross-domain pair has U-B(write) similarity LOW and ΔW overlap
  near zero, i.e. write-orthogonality is a property of domain separation, not of the
  spring/summer accident. Operational band: ΔWov < 0.2 for all cross pairs (vs 0.62–0.66
  mid~parent, the interpolation anchor).
- **H6b (reads):** V-A ≈ shared (≈ same values as 10b, flat across pairs).
**10c′.** Style-token definition sensitivity: variant S1 = punctuation/whitespace ONLY
(was: punct + function chars). Recompute grouped JS from the same reference texts.
Registered expectation: disconfirmation of the doc's §8 pattern survives both definitions
— if it flips, the 10c grouped verdict downgrades to definition-dependent, and we say so.
Leakage tripwire runs for new corpora against probes (expect 0; new-domain probes are NOT
required for the geometric claim — no new behaviour tests this round).
