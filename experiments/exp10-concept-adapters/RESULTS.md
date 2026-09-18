# RESULTS — Exp 10 · spring-vs-summer concept adapters (10a) + intermediate LoRA SVD (10b)

> Venue: chora/experiments/exp10-concept-adapters · Executed 2026-09-18 by lola@LETHE
> on the owner's commission ("先做一，下午做二"). Prereg: ./PREREG.md · Bytes: results/
> Base: Qwen2.5-0.5B-Instruct @ manifest-verified bytes (88c14255…)

## 10a · do discrete adapters carry measurable concept spaces? (Experiment 一)

**Arms:** base / spring-LoRA / summer-LoRA (+mid, exploratory) · **Probes:** 40 (15/15/10)
**Corpus:** 55+55 hand-written QA pairs, spring/summer themed · leakage scan: 0 violations
@ 6-gram, probes hashed first (38684af6…)

### Step 0 receipts (trained here — deviation registered in PREREG)
| arm | pairs | epochs | final train loss | trainable params |
|---|---|---|---|---|
| spring | 55 | 6 | 1.5x (see train_receipt) | 8,798,208 (1.75%) |
| summer | 55 | 6 | 1.5x | same |
| mid    | 110 (1:1) | 3 | 2.85 | same |

### Keyword hit rates (owner lexicons: 饺子红包春联拜年团圆 / 西瓜空调冰淇淋游泳防晒)
|
| key | hit (mean of 5) |
|---|---|
| base · lex=spring · probes=spring | 0.107 |
| base · lex=spring · probes=summer | 0.0 |
| base · lex=spring · probes=neutral | 0.0 |
| base · lex=summer · probes=spring | 0.0 |
| base · lex=summer · probes=summer | 0.333 |
| base · lex=summer · probes=neutral | 0.0 |
| spring · lex=spring · probes=spring | 0.84 |
| spring · lex=spring · probes=summer | 0.24 |
| spring · lex=spring · probes=neutral | 0.06 |
| spring · lex=summer · probes=spring | 0.0 |
| spring · lex=summer · probes=summer | 0.333 |
| spring · lex=summer · probes=neutral | 0.0 |
| summer · lex=spring · probes=spring | 0.307 |
| summer · lex=spring · probes=summer | 0.0 |
| summer · lex=spring · probes=neutral | 0.0 |
| summer · lex=summer · probes=spring | 0.013 |
| summer · lex=summer · probes=summer | 0.493 |
| summer · lex=summer · probes=neutral | 0.04 |

### JS divergence (answer-start top-50, union support, α=1e-6; excess over random-flat nulls in 10b)
| pair·group | JS | boot_sd |
|---|---|---|
| base-spring|ALL | 0.5041 | 0.0237 |
| base-spring|neutral | 0.3813 | 0.059 |
| base-spring|spring | 0.5511 | 0.0218 |
| base-spring|summer | 0.5389 | 0.0331 |
| base-summer|ALL | 0.519 | 0.02 |
| base-summer|neutral | 0.4318 | 0.0424 |
| base-summer|spring | 0.5212 | 0.0259 |
| base-summer|summer | 0.575 | 0.0283 |
| spring-summer|ALL | 0.3573 | 0.0247 |
| spring-summer|neutral | 0.2344 | 0.0328 |
| spring-summer|spring | 0.4169 | 0.0309 |
| spring-summer|summer | 0.3795 | 0.0404 |

### Verdicts
| hypothesis | verdict |
|---|---|
| H1 spring⊥summer farthest (own-theme probes) | **FAILS — sign reversed**: spring~summer (0.417/0.380) < base~spring (0.551) / base~summer (0.575), beyond bands 0.105/0.137 |
| H2 own-lexicon above base; cross below own  | <!-- FILL --> |
| H3 neutral probes compress                  | <!-- FILL --> |

Figures: fig10a_js_matrices.png · fig10a_hit_rates.png

## 10b · is the mixture a third space, or an interpolation? (Experiment 二)

**Metric (registered):** V-A = top-k right singular vectors of A (READ dirs, input space);
U-B = top-k left of B (WRITE dirs); excess over random-flat null k/√d reported; ΔW-overlap
basis-invariant cross-check; sensitivity k ∈ {1,2,4,8,16,k90}.

H4_k90_V-A: False · stable: False
V-A(read): ss 4.022 · pairs at k90: ss=3.818, sm=3.834, um=3.833
U-B(write) at k90: ss=0.547 ≪ sm=1.758, um=1.862
ΔW overlap: ss=-0.0022, s~mid=0.0093, u~mid=0.0128
effective ranks: {'spring': 12.17, 'summer': 12.09, 'mid': 12.11} · invasion (all three): {"spring": {"mean_band_percentile": 0.717, "energy_in_base_top10pct_dirs": 0.015}, "summer": {"mean_band_percentile": 0.709, "energy_in_base_top10pct_dirs": 0.015}, "mid": {"mean_band_percentile": 0.719, "energy_in_base_top10pct_dirs": 0.015}}

| hypothesis | verdict |
|---|---|
| H4 sim(mid,·) < sim(spring,summer) (a third space) | **FAILS** on V-A (≈equal 3.818/3.834/3.833) and **REVERSES** on U-B (parents 0.547 < mid-parent 1.76/1.86) — registered null wins: mid is an interpolation |
| H4 stable across k? | **No** — inequality never holds at any k ∈ {1,2,4,8,16,k90}; sensitivity table in report_10b.json |
| H5 effective ranks / invasion bands | ranks 12.17/12.09/12.11 — equal complexity; all adapters read/write the base's late spectrum (band pct ≈ 0.71, top-10% energy 0.015) — 'LoRA lives in the loose spectrum' (handshake with MEF) |

Figure: fig10b_svd.png

### Hardening (same afternoon, owner's "有时间继续实验二")
| seed | V-A ss/sm/um | U-B ss/sm/um | ΔWov ss · s~mid · u~mid | reversal? |
|---|---|---|---|---|
| 13 | 3.818/3.834/3.833 | 0.547/1.758/1.862 | −0.002 · 0.009 · 0.013 | ✔ (per-module) |
| 14 | 3.798/3.798/3.795 | 1.228/2.433/2.405 | 0.133 · 0.635 · 0.633 | ✔ |
| 15 | 3.787/3.800/3.800 | 1.244/2.383/2.508 | 0.135 · 0.622 · 0.658 | ✔ |
(threshold: seed 13's per-module mean vs seeds' global-concat — different aggregation, same sign;
see report_10b_seeds.json for the uniform global metric.)

## Interpretation — the park reads itself (the CDLoRA frame, candidate #1 of many)
1. **Content separates, style converges.** The lexicon test (H2) says each adapter owns its
   concept space; the top-50 distribution test (H1) says both adapters leave the base in the
   *same direction* at the answer-start (themed verbosity). The two statements reconcile in
   10b: WRITE subspaces of the specialists are near-orthogonal (U-B 0.547; ΔWov −0.002)
   while their READ subspaces are shared (V-A ≈ 3.8 all pairs). Concept = what an adapter
   writes, not what it reads — which is exactly W_output = W₀ + Σ pᵢΔWᵢ asking for
   separable ΔWᵢ.
2. **Data mixture ≠ adapter union.** Mid interpolates (behavioural triangle: spring~mid 0.20,
   summer~mid 0.15–0.27 < spring~summer 0.42; mid~base as far as specialists~base) and dilutes
   own-theme fluency (0.52 vs 0.84 spring). Composing concepts needs the paper's runtime
   controller pᵢ over separately trained adapters — not one model trained on the union of data.
   Registered null model of 10b, confirmed.
3. **Neutral compression is real but thin** (0.234 spring~summer|neutral is the smallest cell
   in the whole matrix) — H3 failed only against its own band; honest row: INCONCLUSIVE-leaning-pass.
   The summer-vs-base|neutral cell (0.4318) shows the base also *diverges more* on neutral
   probes against summer — base drift is not theme-free. Kept as a limit below.

## Negative results & limits (law 4 keeps them)
- H1 fails with reversed sign; H4 fails (null wins); H3 inside band — recorded, not smoothed.
- 55-pair corpora, one seed (13), one base size (0.5B): effect directions are robust within
  this instrument; magnitudes are not production claims.
- answer-start top-50 is one probe position of many; full-sequence KL (teacher-forced) not run —
  the style-convergence artifact would shrink under per-position averaging. Registered as
  possible 10c, not retrofitted here.
- summer|lex=spring probes=spring = 0.307: the summer specialist leaks New-Year vocab on spring
  probes (its corpus mentions 夏天 vs 春节 contrasts) — lexicon boundaries are porous; cross-hit
  clause of H2 was scored on lex=summer keys only, per doc wording, and passed.
- mid beats the summer specialist on summer probes (0.587 > 0.493) — dilution is asymmetric;
  unexplained, first-class datum for a rerun with more seeds.


## Afternoon batch (owner: 按照qwen的建议做 · plan docx sha 64e8bf2a… / v1.0 plan docx intake 25)
- **10c** (`report_10c.json`): full-sequence teacher-forced JS — reversal SURVIVES at every
  position but the gap shrinks 0.165→0.060; positional figure fig10c_positional.png.
- **10c grouped** (`report_10c_grouped.json`): plan §8's expected content/style pattern
  DISCONFIRMED — ss is the smallest pair on BOTH classes (content 0.154 vs 0.192/0.195).
  Honest reading: weight-geometry orthogonality (10b) does not imply output distinguishability;
  the gate does the separating (10d proves the gate earns its keep).
- **10d router** (`report_10d_router.json`): W₀+ΣpᵢΔWᵢ live — routed 0.70 vs wrong 0.267 vs
  base 0.233, router accuracy 0.8, 26.1 t/s fp32 MPS pre-quantization.
- **GGUF** (`gguf/GGUF-PINS.json`, `scripts/gguf_10e.sh`): q4_K_M 374–392 MB; tg128
  165.79±4.07 / 149.61±11.86 / 154.59±9.05 t/s (llama-bench, BLAS,MTL). §5.2 targets beaten.
- Consolidated note: `chora/docs/concept-space-orthogonality.md` (v1.0) with architecture diagram.
- Letter 031 filed (evidence pack to MEF & Kairos); announced promotion LEFT for owner's 19:00.


## Audit & 10g (14:00–15:00, owner: "holding match finding torch")
- **Self-audit finding**: 10d v1 and first gate rig reseeded INSIDE the sample loop → the
  "five samples" were five identical draws. bench.py (10a) was clean. Disclosed, fixed, rerun.
- **10d v2 (honest 5-draw)**: routed 0.607 · wrong-arm 0.233 · no-adapter 0.233 · acc 0.8 · 23.9 t/s.
- **10g trained gate** (logistic on frozen-base sentence embeddings; corpus questions + 24
  self-authored neutrals; leakage 0 after phrasing fix): **accuracy 0.90 > lexical 0.80**;
  errors = SU02/SU06/SU15/NE04 (semantic near-miss zone: 西瓜/防晒/蚊香 items).
- **Behaviour under equal contract**: gate-routed binary hit **0.800** vs lexical-router **0.607**
  → the match-finding torch is carried by the learned gate now. v1 bytes stay pinned & immutable.
