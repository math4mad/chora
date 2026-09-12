# Day report — machine B (`m1-16g`), 2026-09-12

Per `docs/AGENTS-B.md` §5: one line per task with (bench@sha, paths, sha256,
wall-clock), the twins verdict in a sentence, `B-env.json` attached, every STOP
listed even where it cost the task, and the curious things marked *question* and
kept out of every table. Science content lives in the letter, not here:
**Letter 020** (`letters/2026-09-12-B-JacobiGP-h6c-bytes-land.md`), plus the
morning's **Letter 019**. This file is the ledger.

Working copy at: `chora@1c16b16` + this file's own commit (Letter 020 PS 4
follows: the instrument is deterministic on its own machine — a cold re-run of
the primary dump cell reproduced `a7fd916d1475b101…` byte for byte). Every sha
quoted below is in that history, on `origin/main`.

---

## 1 · The queue, line by line

| # | Task | Bench @ sha | Bytes that crossed (sha256 12) | Wall clock | Status |
|---|---|---|---|---|---|
| 1 | E0 ladder, seed **14** | `MEF@ddf1d16` (branch `bench-B-multi-model`) | `E0_seed14_base_run.json` `5e6e52fd7cc4…` · `E0_seed14_pretrain.log` `d9b7adee7597…` · `E0_seed14_sweep_full.json` `695dba48ff1d…` | pretrain 2000 steps **742.5 s**; sweep 09:07→09:56 local (**49 min**) | **done** |
| 1 | E0 ladder, seed **15** | — | — | — | **STOPPED, see §4.1** |
| 2 | Sarcos Step 0 dose–response | `Sarcos@b22f1e9` (branch `bench-B-step0`) | `Step0_dose_256h256_B.json` `e3f7fa1955cf…` · `Step0_dose_64h64_B.json` `91c34b5047ec…` · geometry audit `ebd58c2df11e…` · logs `de05642ebeab…` / `bb5e4b7c78e3…` (force-added, `*.log` globalignore) | both architectures, 5 doses × 3 seeds × 3 arms, CPU, `set_num_threads(1)`, deterministic | **done — verdict: NO DOSE QUALIFIES** on either arch (Letter 011 §2 monument clause); dose 0.1 reported UNRUNNABLE under the registered rule |
| 3 | PolyNN init dumps + per-seed α,β walks | `PolyNN@a0deb68` + restore `2fcb158` (branch `bench-B-h6c`) | 20 dumps + summary `e502abd7cd5c…` → `artifacts/init-states/h6cB/`; 5 walks + summary `bd58e62bb8d1…` + log `03a9d0977a19…` → `artifacts/results/polynn/h6cB/`; **27 new manifest entries** | dumps 0.4–0.8 s/cell (20 cells ≈ 11 s); walks 88–91 s each, **4.46 s/epoch mean** (A: 5.99–6.17) → B ~27 % faster **on cells whose numbers came out bit-identical**; primary dump cell re-run cold = **same bytes** (`a7fd916d…`) | **done + announced (Letter 020, PS 4)** |
| 4 | Isospectrality audit (`mlp.down_proj` σ-spectra) | — | — | — | **STOPPED, see §4.1** — but the permission slip is already in the drawer: `model.safetensors` `88c142557820ccad…` / 988,097,824 B verified on B's disk (§4.3) |
| 5 | Third seed of anything | — | — | — | not reached; items 1 and 4 are the third-seed work and both are gated |

Manifest entries added: `artifacts/init-states/manifest.json` 0 → **21**,
`artifacts/results/manifest.json` 20 → **27**, `data/manifest.json` 3 → **7**
(Fashion-MNIST's four `.gz`, md5-pinned against torchvision before use).
All 27 + 21 + 7 + 53 entries re-validated against schema *and* disk this
afternoon; that sweep is what found B's own bad path label (§3). **28 files
mirrored bench → chora were re-hashed at both ends: 0 mismatches.**

## 2 · The twins verdict, in the one sentence the brief asks for

**The twins never met** — B's seed-13 twin has a base run and no ladder
(`twinB_seed13_base_run.json` `24bbbe1a2aba…`), so **Gate 6 is still OPEN, not
passed**, and the only ladder B has ever produced (seed 14:
5.6587 / 1.3813 / 1.1795 / 1.0885 / 1.0313 nats) differs from A's seed-13 floors
(5.5456 / 1.4038 / 1.2194 / 1.1525 / 1.0906) by +0.113 / −0.023 / −0.040 /
−0.064 / −0.059 nats, which is a **different-seed** comparison and therefore not
a machine-effect measurement at all. *Question, kept out of the tables:* B has
no same-seed A/B pair anywhere in the programme yet, so every "machine effect"
number currently quotable is really a seed effect.

## 3 · What B corrected in its own record, today

* `artifacts/results/mef/E0_seed14_sweep_full.json` was pinned as
  `chora/artifacts/results/mef/…` — a path with the repo's own name inside it,
  certifying a file that exists nowhere. sha256 and bytes were right, the label
  was not; corrected in place with the wrong string preserved in the note, by
  the hand that wrote it. Found only because B validated every entry against
  disk instead of reading the file.
* Two `docs/` files and Letter 006 were missing from PolyNN's tracked tree
  (deleted by its own site commit `a4c7224`); restored byte-identical on B's
  branch, not merged — see Letter 020 §5.
* One path defect in the shared record itself (`benches/*` symlinks tracked as
  **absolute** paths by `bin/sync.sh`): five files that can never be clean on a
  second laptop. **Not repaired by B** — those blobs are the chair's; two
  one-line fixes are offered in Letter 020 PS 3 and the choice is the chair's.

## 4 · Every STOP honored, including the expensive ones

1. **E0 seed 15 — not started.** The glass still shows **MEF dirty=2** on A's
   `multi-model` and rule 4 is unconditional about that. Cost: the day's
   deliverable is one ladder, not three, and the machine-effect estimate stays
   a cross-seed comparison. B says plainly that this is a *protocol* stop, not a
   safety stop — Letter 019 PS 6 measured that the reported dirt is A's own and
   that B's clean tree can never appear on that glass; obeying anyway, because a
   rule that only holds when the holder agrees with it is not a rule.
2. **Isospectrality audit — not started.** Command home is `MEF/outputs/`; same
   light, same reason.
3. **Seed-13 twin sweep — still held** from the morning (A committed
   `MEF@6f5f4c5`, stage19 E3, at 09:13:55 local).
4. **The `{}`-pin in `models/manifest.json` — filed, not overwritten.** B
   recomputed `sha256(b'{}') = 44136fa355b3678a…` and matched A's pin exactly;
   the hub answers HTTP 200 with a 15-byte `Entry not found`. Immutable bytes
   with a wrong label are the chair's to re-issue (Letter 019/`dccdfbc`).
5. **`artifacts/external/…/outline_season1.md` — divergence filed, not repaired**
   (`docs/byte-audit-2026-09-12.md` §1): pinned empty at `e3b0c442…`, on disk at
   `fea8a380…`/3958 B. The chair's writer domain.
6. **No publisher, ever.** `CHORA_NOPUBLISH=1` in effect; `bin/launchd/*`
   untouched; `docs/status.json` never edited or committed by B; no
   `publish-status.sh` run. The five `benches/*` symlink edits stay uncommitted
   on purpose, so nothing of B's machine-local state enters the shared record.
7. **One training process at a time**, never a model load and a run together:
   the 0.5B weights were verified by hash and then *left closed* — 988 MB of
   safetensors was never mapped while a walk was in flight, on a 16 GB laptop.

## 5 · Environment, attached

`artifacts/results/mef/B-env.json` (`b78c34e2f5cb…`) is the probe record, and
the divergences that matter for tonight's numbers are: python 3.11.16 (A: 3.14),
numpy 2.4.6 (A: 2.5.3), macOS 15.7.5 (A: 26.6.2), **torch 2.14.0 and MPS on
both**. Disk at end of day **41 GB free**; `caffeinate -dims` held the laptop
awake from 11:24 local; corpus `data/tiny_stories.txt` `2427881798fb…` verified
three ways and still intact.

## 6 · Turns owed at hand-off

* **Geometer:** the two-sentence amendment (band from `sd_seed`; which object
  (0.40, 0.37) names) and a ruling on the degenerate contrast row — pre- or
  post-activation. B can run the alternative dumps in ~11 s on request.
* **Joiner:** `PolyNN@2fcb158` — merge, redo, or refuse the restore, and decide
  about `train.py`'s `walk=False` logger (a log, not a knob, on the same branch).
* **chair:** the `benches/*` absolute-symlink fix (PS 3), the `{}`-pin
  re-issue, the outline re-pin, and — when A's daemon is next seen alive —
  whether a chora-only commit repaints the glass within five minutes or not
  (that is the discriminator between "A is asleep" and "F3 is still misfiring").
* **the human:** seed 15 and the spectra audit are the two remaining pre-
  authorized items and both wait on one thing — MEF's light. ~50 min of work,
  already scripted, nothing to invent.

---

*Nothing in §2–§6 is a claim about CHORA's science except where a hash is
attached. The claims are in the letters; this file is the receipt.*

## 6 · Questions, quarantined from every table (added at close of day)

* *question* — B is ~27 % faster per epoch than A on the exp8 trainer while
  reproducing its answer exactly: how much of the fleet's wall-clock divergence
  is scheduling rather than arithmetic, and does any of it survive into paths that
  are *not* bit-exact by construction (the ladder's SVD fallback is the candidate)?
* *question* — the four arms share one init measure because the ruler sits
  upstream of the thing that distinguishes them. Is Letter 017's contrast row the
  **post-activation** init measure? ~11 s of B's compute answers it on the word.
* *question* — `bin/sync.sh` line 20 links the benches by **absolute** path and
  those five symlinks are *tracked* blobs (`git ls-tree HEAD benches/` →
  `/Users/mac/…`), so `chora` can never be clean on a second laptop.
  `MEF@a98508e` made exactly this fix inside a bench for exactly this reason —
  its own note says "they made the traffic light permanently red". Relative
  links, or untrack-and-ignore: which is the record's? (Letter 020 PS 3.)
* *question* — the glass has not repainted in 3 h 30 min. If the next chora-only
  commit moves it inside five minutes, Letter 019 PS 6's F3 is a liveness
  artifact; if it does not, the guard that ignores `chora_head` is still the
  reason, and B's §4 STOPs 1–3 stand on an unreadable light.
* *question* — `data.py` documents the Fashion-MNIST drop target as
  `chora/data/fashion-mnist/` while `datasets()` writes `FashionMNIST/`: one
  string, two places, the comment is the stale one.
* *question* — B pulled ` JacobiGP` two seconds before it would have had to
  invent H6c's coordinate from Letter 017's prose (PS 1). Should "pull every
  bench before touching any" be a numbered **gate** in §1 rather than a habit?

