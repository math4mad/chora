# PREREG — Exp 11 · 横向验证矩阵 (horizontal matrix)
**Registered:** 2026-09-18 15:50 · by lola@LETHE on owner's "Exp11 可排期"
**Question (from Exp10's limits chapter):** are exp10's geometry findings — write-orthogonality
across domains, shared reads, mixture-as-interpolation — properties of LoRA-on-LLMs, or
properties of Qwen2.5-0.5B?

## Matrix (bases × arms)
| base | spring | summer | code | legal | medical | mid(spring+summer) | general probe | status |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-0.5B | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ○ | DONE = exp10/10f |
| Qwen2.5-1.5B (cached) | P0 | P0 | P0 | — | — | P0 | P0 | TODAY |
| Qwen2.5-3B | P1 | P1 | P1 | — | — | P1 | P1 | needs fetch (owner nod on network) |
| Llama-3.2-1B | P1 | P1 | P1 | — | — | P1 | P1 | needs fetch |
| fifth base (TBD by owner) | P2 | | | | | | | e.g. a non-Qwen family member |

**general probe:** adapter trained on cached `chora/data/tiny_stories.txt` (55 sampled pairs,
registered sampler seed 13) — the English commonsense arm; tests whether an adapter without a
Chinese concept domain also writes orthogonally to the five domain arms (H7) and whether
"interpolation" is specific to data-mixtures of *related* domains.

## Metrics (identical to exp10 — the point is replication, not new instruments)
per-module k90 V-A (read) / U-B (write) similarity; global ΔW overlap; band |dWov| < 0.2 for
domain-pair orthogonality; interpolation anchor = mid~parents (expect ≈0.6).
r=16 throughout; lr 1e-4; epochs 6 (55-pair arms) / 3 (mids); seeds: 13 primary, 14 on P0 if time.

## Hypotheses
- **H8 (primary):** every domain×domain specialist pair on EVERY base satisfies |dWov| < 0.2;
  the interpolation anchor lights on every base where mid exists. PASS if ≥4/5 bases complete the
  row; one non-violating pair with band-respecting gap downgrades that base's row to INCONCLUSIVE.
- **H7 (probe):** |dWov(general, domain)| < 0.2 on all bases (the general adapter is a sixth
  near-orthogonal writer, not a "shared core" that all domains sit on). If violated → the read/
  write split gains a third category (core writers) → new note.

## Schedule (the owner's ask was explicitly "可排期")
P0 today ~35 min MPS (zero downloads, all bytes cached & manifest-verified);
P1 upon owner's network nod (fetch → manifest pin BEFORE first token; ~6GB+2GB);
P2 wrap: one consolidated table into artifacts/results/exp11/, note appended to
docs/concept-space-orthogonality.md; announced-promotion of BOTH exp10 and exp11 is the owner's
single stroke at the next review.

## What must not happen
no tuning on probes (same 40, same hashes); no new metric invented to save a failing row;
models without manifest entries are fetched, hashed, announced — never trained on blind bytes.
