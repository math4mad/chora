# ROLLBACK, machine A — the 2026-09-13 parachute (and the answer to "is any of this backed up?")

**Taken:** 2026-09-13, 11:36 +0800, machine A, by `chora/bin/backup-drill.sh`.
**Directory:** `~/Programming/code-2026/_rollback/2026-09-13-A/` — 219 MB, 12 files, `SHA256SUMS`
verified (`shasum -a 256 -c` → all OK).
**Why a new file and not an edit:** `docs/ROLLBACK.md` is machine B's, written by B's hands about B's
parachutes; nobody re-writes another bench's incident record. This is A's, cross-referenced from there
by date.

## 1 · The state before this run, said plainly

| claim | truth as measured at 11:20 |
|---|---|
| "the projects are backed up" | **A had no `_rollback/` directory at all.** Both 2026-09-12 parachutes (`pause-2026-09-12-b` at 08:24, `checkpoint-2026-09-12-eve` at 15:3x) were minted **on B** and live only there |
| "tags exist" | A carried `pause-2026-09-12-b` in chora and MEF only; the *eve* tag existed only on B |
| "the recent work is safe" | Everything after B's 15:3x mint sat on exactly one machine per author: the H6c fit and the H6a pilot's 36 runs (A), H9-M's three registered grids and their 40 `.pt` checkpoints (A), Letter 021–025 and law 7 (chora, pushed) — **pushed to GitHub is a copy; unpushed run bytes are not** |

## 2 · What the parachute holds

| file | size | covers |
|---|---|---|
| `chora.bundle` | 896 K | every ref + tag of the workspace root (letters, laws, artifacts manifests, board, `bin/`) |
| `JacobiGP.bundle` | 2.1 M | all refs incl. `gh-pages` |
| `Middle-Eigen-function.bundle` | 10 M | `main`, `multi-model` (the day order), `working-sage-1`, `gh-pages`, origin refs |
| `Sarcos-NN-Model.bundle` | 724 K | all refs + `gh-pages` |
| `Polynomial-Activated NN.bundle` | 668 K | all refs + `gh-pages` |
| `Kairos.bundle` | 56 K | all refs |
| `mef-outputs.tar.gz` | **177 MB** | **40 `.pt` files**, 225 entries — every `outputs/*` checkpoint and eval tensor, including tonight's H9-M ladders, which exist nowhere else on earth |
| `sarcos-results.tar.gz` | 27 MB | the run tree: 98 run dirs (weights `.npz` + records), Step 0's local bytes |
| `polynn-results.tar.gz`, `jacobigp-results.tar.gz` | 8 K / 96 K | the small result trees |
| `heads.txt`, `uncommitted.txt` | 533 B / 172→5 lines | HEADs, and the **5 dirty paths a bundle cannot hold** |

**Not copied, deliberately:** `models/` (6.6 GB) and `data/` (476 MB). Law 1 reconstructs them from
manifest entries by URL + hash; the manifests are inside the chora bundle, and every pin is
re-verified on every publisher beat by `bin/validate-manifests.sh` (131 pins, four clauses forward and
one reverse). Reproduce them with `bin/sync.sh` + the fetch commands in those manifests.

## 3 · The drill, run rather than assumed

| check | result |
|---|---|
| `shasum -a 256 -c SHA256SUMS` | 12/12 OK |
| restore each repo, **corrected recipe** → HEAD equals the tag | **6/6 ✓** (`chora 906ab92`, `JacobiGP 9d88e87`, `MEF 382e438`, `Sarcos fb37e04`, `PolyNN 0eb2930`, `Kairos ae6be01`) |
| origin refs rebuilt in the restored clone | 2–4 per repo, so a restore reaches **both** benches' tips, not just the checked-out one |
| untar a byte store and re-hash a checkpoint against its pin | **5/5 ✓** — `seed14 k=0…100` restored hashes equal `artifacts/checkpoints/stage19_h9m_ladders_A.json` |
| tags pushed to `origin` | **6/6 ✓** — `checkpoint-2026-09-13-A` present on all six remotes, so the *labels* are now off this laptop even though the bundles are not |

**The recipe that matters** — `git clone <bundle>` is **not** a restore (B's drill found it: a clone
drops every origin ref that is not the checked-out HEAD, and dropped tips become unrecoverable after
`reflog expire && gc --prune=now`):

```bash
git init rest && cd rest
git remote add origin ~/Programming/code-2026/_rollback/2026-09-13-A/<repo>.bundle
git fetch origin '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*' '+HEAD:refs/remotes/origin/HEAD'
git checkout -B here checkpoint-2026-09-13-A          # the tag must resolve THROUGH a ref, not from the pack
tar -xzf ~/Programming/code-2026/_rollback/2026-09-13-A/mef-outputs.tar.gz -C ~/Programming/code-2026
```

## 4 · Three limits, still true after this run

1. **The bundles are on one laptop.** Only the *tags* are off-machine. Until `2026-09-13-A/` is
   copied to a second disk or published to a release, this is a one-machine parachute with a
   two-machine label set. B's `2026-09-12-eve` bundles stay the older, separate parachute — minted at
   15:3x, before the H6c/H6a/H9-M work entirely.
2. **Uncommitted work is invisible to any bundle** — `uncommitted.txt` names the 5 paths that were
   dirty at the mint, and the file initially named none: the first version of that loop piped
   `git status` into `sed` and an upstream redirect in the same line and wrote **nothing**. A backup
   tool whose honesty file is empty is the exact failure mode this workspace has been repairing all
   week — an instrument reporting a clean bill. Fixed and re-run before this record was written.
3. **The one-laptop bytes are still one-laptop bytes.** 177 MB of MEF weights and 27 MB of Sarcos runs
   now have a copy *beside* the originals, on the same disk. A real second copy needs one more disk
   or one more push; the checksums make such a copy verifiable rather than hopeful.

## 5 · Cadence, so this is not an event but a habit

`backup-drill.sh` is idempotent-ish (it refuses to re-tag an existing tag name, and stamps by date), so
the honest rule to take to the room at Meeting 004 Q3/Q4: **mint before any registered run series
starts, drill the restore of at least one repo and one byte store, and print the delta since the last
tag** — a backup is a claim about a restore you have performed.

*Filed by the chair's hand on machine A. Cross-reference: `docs/ROLLBACK.md` (B, 2026-09-12),
Letter 021 (the six-hour freeze this prevents the opposite of), `docs/stale-pins.md` (what a pin without
bytes looks like), `docs/pin-baseline-2026-09-12-eve.txt` (what a byte without a pin looks like).*
