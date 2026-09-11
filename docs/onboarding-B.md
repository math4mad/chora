# ONBOARDING — Machine B (worker bench)
`m1-16g` · macOS 12 Monterey · base M1 · 16 GB RAM · 256 GB SSD
Companion to Letters 015/016 (two-machine day). A = `m1pro-32g` = the glass.

> Roles are constitutional, not casual: **A forges and publishes; B witnesses.**
> B replicates (E0 seeds 14/15), answers cheap questions nobody has run yet
> (Sarcos Step 0, PolyNN dumps, isospectrality SVD), and never touches the
> dashboard. Every phase below ends in a **GO/NO-GO gate**; a failed gate is
> a finding, not an inconvenience — file it and stop.

---

## Phase 0 · Housekeeping (5 min)

```bash
sw_vers                                   # expect 12.x
df -h /                                   # need >= 40 GB free of 256 GB
xcode-select -p 2>/dev/null || xcode-select --install    # CLT for git/clang
git config --global user.name  math4mad
git config --global user.email 113895984+math4mad@users.noreply.github.com
```
- **Gate 0:** disk ≥ 40 GB, git works. Budget below needs ~2 GB of repos +
  400 MB corpus + ~1 GB one model + a few GB venvs. Do NOT clone `models/`
  wholesale; A's 6.6 GB store is not B's problem. B fetches per-manifest.

## Phase 1 · Python (10 min)

macOS 12 ships nothing useful; Homebrew python on Monterey is tier-2 but
fine. torch's newest wheels may demand macOS ≥ 13 — **if `pip install torch`
refuses, pin backwards until it lands, and record what landed**:

```bash
brew install python@3.11 2>/dev/null || true
python3.11 -V
```
- **Gate 1:** `python3.11` exists. (If Homebrew is the blocker: use the
  Apple `python3` (3.9) — everything here is pure-Python + numpy, except the
  byte-LM runs, which need torch — see Phase 4 fallback.)

## Phase 2 · The six repositories (3 min — mind the spaces, they are canonical)

```bash
mkdir -p ~/Programming/code-2026 && cd ~/Programming/code-2026
git clone https://github.com/math4mad/chora.git
git clone https://github.com/math4mad/JacobiGP.git " JacobiGP"
git clone https://github.com/math4mad/Middle-Eigen-function.git
git clone https://github.com/math4mad/Sarcos-NN-Model.git
git clone https://github.com/math4mad/Polynomial-Activated-NN.git "Polynomial-Activated NN "
git clone https://github.com/math4mad/Kairos.git          # remote since 2026-09-11 eve
cd chora && CHORA_NOPUBLISH=1 bin/sync.sh
```
- **Gate 2:** sync prints five `[bench]` lines; `CHORA_NOPUBLISH=1` echoes
  *"worker, not the glass."* If the publisher ran at all, you forgot the
  flag — `git restore docs/status.json` and redo the sync.
- **Never** install `bin/launchd/com.chora.fleet-status.plist` here.

## Phase 3 · venvs for B's actual benches (15–25 min, download-bound)

```bash
# MEF (byte-LM twins + E0 need torch; also numpy for the SVD audit)
cd ~/Programming/code-2026/Middle-Eigen-function
python3.11 -m venv .venv && .venv/bin/pip -q install -U pip
.venv/bin/pip install torch numpy            # pin if macOS 12 refuses the newest
.venv/bin/pip install -r requirements.txt 2>/dev/null || true

# Sarcos (Step 0: torch + its extras)
cd ../Sarcos-NN-Model && python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]" 2>/dev/null \
  || { .venv/bin/pip install -e . && .venv/bin/pip install numpy torch scipy; }
```
- **Gate 3 (the probe — run it, don't trust it):**
```bash
cd ~/Programming/code-2026/Middle-Eigen-function && .venv/bin/python - <<'PY'
import torch, numpy as np, socket, platform, json
mps = torch.backends.mps.is_available()
x = torch.randn(64, 64, device="mps" if mps else "cpu")
print(json.dumps({"host": socket.gethostname(), "macos": platform.mac_ver()[0],
                  "torch": torch.__version__, "numpy": np.__version__,
                  "mps_ok": bool((x + x).sum()) if mps else "cpu-fallback"}))
if not mps: print("NO-GO for byte-LM arms on GPU path; CPU still works (slow) — A takes E-twins, B keeps SVD work")
PY
```
Record this JSON as `run-meta B-env.json` — it is the machine-effect datum
half-complete; the twins will quote it.

## Phase 4 · Corpus crosses by URL + hash — the law test (10 min)

```bash
cd ~/Programming/code-2026/chora
curl -s -r 0-399999999 -L -o data/tiny_stories.txt \
  "https://hf-mirror.com/datasets/roneneldan/TinyStories/resolve/main/TinyStories-train.txt"
shasum -a 256 data/tiny_stories.txt
# MUST equal 2427881798fb3b39… (entry in data/manifest.json). Mismatch = STOP.
```
- **Gate 4:** hash matches or the day's first finding is filed.
- Later, only as needed: FashionMNIST for PolyNN dumps (hash from data
  manifest, same ritual); `models/models/Qwen--Qwen2.5-0.5B` (~1 GB, files
  per models/manifest, verify each) for the isospectrality audit.

## Phase 5 · The twins first (before any new science — Letter 016 law 3)

```bash
cd ~/Programming/code-2026/Middle-Eigen-function
caffeinate -dims &                      # laptop must not nap
export TS_PATH=data/tiny_stories.txt CHORA_MACHINE=m1-16g SEED=13
OUT_DIR=outputs/stage18_twinB .venv/bin/python scripts/stage18_kairos_mini.py \
  --mode pretrain --steps 2000 --batch 16 --ctx 256
OUT_DIR=outputs/stage18_twinB .venv/bin/python scripts/stage18_kairos_mini.py \
  --mode sweep --adapter-steps 600 --batch 16 --full
```
If torch landed with a different version/macOS baseline than A, **the twins
are more valuable, not less** — the divergence is the measurement.
- **Gate 5:** twin's ladder floors within a whisker of A's
  (`5.546 / 1.404 / 1.219 / 1.153 / 1.091`); bigger gaps = investigate as
  finding, don't paper over.

## Phase 6 · B's day queue (order fixed, one writer each, push per bench)

| # | Task | Where it lands | Notes |
|---|------|----------------|-------|
| 1 | **E0** seeds 14, 15 of the ladder (same script, `SEED=14`/`15`, OUT `stage18_s14`/`s15`) | MEF repo + mirror jsons to `chora/artifacts/results/mef/` | this repays the band debt; three machines' worth of noise in one table |
| 2 | **Sarcos Step 0** dose–response (`far_frac` sweep) per Letter 011 | Sarcos repo; results → `artifacts/results/sarcos/` | learnability-only dose choice; report ALL doses |
| 3 | **PolyNN init dumps + per-seed walks** (H6c homework, Letter 014) | PolyNN repo → `artifacts/init-states/` + results | ~11 min; announce by letter |
| 4 | **Isospectrality audit** (SVD of Qwen2.5-0.5B `mlp.down_proj` σ-spectra + LoRA-ΔW spectra if A's twin adapters exist) | MEF outputs → `artifacts/spectra/` | pure numpy, CPU-fine |
| 5 | Anything new: **start it only after pushing whatever #1–4 produced** | — | B's golden rule: finished > ambitious |

Per-task ritual, every time: `produce → json/summary → sha256 → manifest
entry (by: <Bench>@<sha>, notes carry "run-on: m1-16g") → commit bench repo
→ mirror to chora → push`. When pushing chora from B:
`git pull --rebase origin main` first — A's launchd publisher moves the ref
under you every five minutes; today's "cannot lock ref" was the rehearsal.

## Phase 7 · Never list (B-specific)

1. Never run `publish-status.sh` / let sync publish (`CHORA_NOPUBLISH=1` in
   `~/.zshrc` — make it sticky).
2. Never install the launchd agent.
3. Never commit `.pt` checkpoints or weights; json + log cross, bytes
   regenerate from seeds.
4. Never start work in a bench whose files show dirty on A's dashboard
   (gold/dirty flags are the cross-machine traffic light).
5. 256 GB disk: `df -h` each evening; outputs/*.json compress fine,
   `TinyStories` stays — it is now a shared asset, not a download.

## Shutdown of day

```bash
cd ~/Programming/code-2026/chora && git pull --rebase origin main
# on A: bin/publish-status.sh   (only A paints the glass)
```
Unfinished runs: leave them; note the pid and log path in a PS to the day's
letter. Git remembers; laptops forget — so we write.

---
*Checklist owner: the chair. Deviations are findings: commit them anyway.*
