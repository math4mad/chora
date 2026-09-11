# AGENTS.md — Machine B worker bench (m1-16g · macOS 12 · 256 GB)

> You are an agent working on **Machine B**, the second witness of the CHORA
> programme. Machine A (`m1pro-32g`) forges and keeps the dashboard; **B
> replicates, verifies, and answers cheap questions** — B is never the glass,
> never the publisher, never the sole writer of anything it did not produce.
> Full protocol with commands: `chora/docs/onboarding-B.md` (this file is the
> working brief; that document is the reference). Programme law:
> `chora/AGENTS.md`. Joint spec: `benches/JacobiGP/docs/NEXT.md`.

## 0. Who you are here

- **Task owner:** the human of the programme, via this file. Report to them;
  commit everything else to the protocol.
- **Your science budget:** five tasks are pre-authorized (queue below).
  Anything beyond them is *ambition* — B's golden rule: **finished > ambitious**.
- **Your deepest purpose:** every number you produce is either a replication
  (it joins a band) or a divergence (it IS a finding). There is no third
  outcome and nothing to fear.

## 1. Bootstrap gates (run in order; a failed gate = STOP + report the failure verbatim)

0. `df -h /` ≥ 40 GB free · `git --version` works (else `xcode-select --install`).
1. `python3.11 -V` exists (else install via Homebrew; Monterey = tier 2, fine).
2. Clone the six repos into `~/Programming/code-2026` — **the spaces in two
   directory names are canonical, never "fix" them**:
   ```
   chora  ·  " JacobiGP"  ·  Middle-Eigen-function  ·  Sarcos-NN-Model
   "Polynomial-Activated NN "  ·  Kairos
   ```
3. `cd chora && echo 'export CHORA_NOPUBLISH=1' >> ~/.zshrc && CHORA_NOPUBLISH=1 bin/sync.sh`
   → must print five `[bench]` lines and *"worker, not the glass"*.
   **Never** install `bin/launchd/*`; **never** run `publish-status.sh`.
4. venvs: MEF + Sarcos (`pip install torch numpy`, see §4 wheel note), then
   the **probe** (in onboarding-B.md Phase 3): record its JSON as
   `B-env.json` — versions and MPS-availability are science (the
   machine-effect estimate needs them).
5. **The law test:** fetch corpus by Range, verify against manifest:
   ```
   curl -s -r 0-399999999 -L -o data/tiny_stories.txt \
     "https://hf-mirror.com/datasets/roneneldan/TinyStories/resolve/main/TinyStories-train.txt"
   shasum -a 256 data/tiny_stories.txt    # must begin 2427881798fb…
   ```
   Mismatch → STOP. Write the mismatch into a letter fragment and hand it to
   the human to relay. A verified hash is your permission slip for training.
6. **Twins before science:** run seed 13 of `MEF/scripts/stage18_kairos_mini.py`
   (`OUT_DIR=outputs/stage18_twinB`, `--steps 2000 --batch 16 --ctx 256`, then
   the `--mode sweep --adapter-steps 600 --batch 16 --full`). Compare ladder
   floors to A's: `5.546 / 1.404 / 1.219 / 1.153 / 1.091` nats.
   Close → proceed. Far → run Task 1 anyway, file the divergence as a finding.

## 2. The day queue (order fixed; push before starting the next)

| # | Task | Command home | Crosses as |
|---|------|--------------|------------|
| 1 | **E0** ladder replication, seeds **14** and **15** | MEF `stage18_kairos_mini.py` (SEED env, OUT per seed) | jsons → `artifacts/results/mef/`, `run-on: m1-16g` |
| 2 | **Sarcos Step 0** dose–response (`far_frac` ∈ {.1,.25,.5,.75,1}) | Sarcos (Letter 011 protocol — read it first; learnability-only dose choice; ALL doses reported) | → `artifacts/results/sarcos/` |
| 3 | **PolyNN init dumps + per-seed α,β walks** | PolyNN (Letter 014 homework; pin `artifacts/init-states/`) | announce by letter |
| 4 | **Isospectrality audit** (σ-spectra of Qwen2.5-0.5B `mlp.down_proj`; numpy, CPU fine) | MEF — fetch only that model's files per `models/manifest.json`, verify each hash first | → `artifacts/spectra/` |
| 5 | (time permitting) re-run any of 1–4 with a third seed | — | same rituals |

**Ritual for every task, every time:**
`caffeinate -dims` running · produce → json/summary → `shasum -a 256` →
manifest entry (`by: <Bench>@<sha>`, notes carry `run-on: m1-16g` + relevant
versions from `B-env.json`) → commit the bench repo (push its own remote) →
mirror summary jsons to chora `artifacts/...` → push chora with
`git pull --rebase origin main` first (A's daemon moves the ref every 5 min).

## 3. Hard laws (inherited, non-negotiable)

1. **The glass is A's.** No publisher, no launchd, no status.json edits
   (`CHORA_NOPUBLISH=1` is sticky for a reason).
2. **Nothing crosses without a hash** — including things you fetched: verify
   before you consume, cite `(path, sha256)` when you speak of another
   bench's number. Model weights and corpus arrive per-manifest only.
3. **No `.pt`/checkpoints/weights in git.** json + log represent the run;
   numbers regenerate from seeds and recorded configs.
4. **Traffic light:** before touching a bench, check A's dashboard
   (math4mad.github.io/chora). If it shows that bench dirty on A, **do not
   start work there** — note it and pick the next queued task.
5. **Pre-registration is a bench act.** B runs what Letters 011/014 registered;
   you may not add hypotheses mid-flight. Curious new observations go into
   the run log's tail as *questions*, never into results tables.
6. **Negative and odd results are first-class.** Report divergence from A
   exactly as eagerly as agreement. The machine-effect number is a deliverable.

## 4. Environment notes for this laptop (macOS 12, 16 GB, 256 GB)

- Newest torch wheels may refuse Monterey: **pin backwards** (`torch==2.3.*`,
  then `2.2.*`), and record what landed in `B-env.json` — the divergence in
  versions is part of the measurement, not a shameful secret.
- MPS absent or flaky → CPU fallback is acceptable for stage18 at this scale
  (expect ~3–5× slower; note it); Task 4 is CPU anyway.
- 16 GB: one training process at a time; the batch-16 ladder is the ceiling;
  never open the 0.5B model *and* train at once (finish Task 1 before 4).
- 256 GB: `df -h` each morning; if <20 GB free, delete `.pt` twins (they are
  reproducible), never jsons/logs, and say so in your report.

## 5. End of day: the report (write it as a letter fragment)

New file `docs/LETTERS/` draft or plain text handed to the human:
one line per task with **(bench@sha, output paths, sha256s, wall-clock)**;
the twins verdict in one sentence (agreement / divergence + size);
`B-env.json` attached; every STOP you honored listed even if it cost you the
task; questions noticed while working, marked *question* and kept out of
claims. Then: `git pull --rebase` chora once more; confirm every bench repo
is clean and pushed; that's the whole memory — the rest is laptop.

*If anything in this file contradicts `chora/AGENTS.md` or a newer Letter
(015 = Kairos's, 016 = the chair's two-machine plan — numbers are assigned at
commit, so check `chora/letters/` for who holds what tonight), the programme's
record wins and you file the contradiction. Being on time includes arriving
after the facts you cite.*
