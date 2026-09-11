# AGENTS.md — CHORA joint brief

> Remote: https://github.com/math4mad/chora (this file's bytes: `AGENTS.md`,
> versioned here; clones reconstruct benches/ + shared paths via
> `bin/sync.sh`).
> **CHORA** (χώρα — Plato's *Timaeus*: "the nurse and the place of becoming",
> the receptacle that must have a shape before anything can be poured in).
> The working title ONE SPACE remains accurate — one manifold, four charts —
> but the programme's soul is the *choice of vessel*, so the vessel has the
> name. Motto: **the shape of the container is the knowledge**;
> sub-motto (unchanged, earned): *to see the world — we choose the bounds,
> and the evidence chooses them, never the hand.*

**You are in a workspace shared by four benches. Read this before anything
else.** The benches are normal git repos with their own `AGENTS.md`;
this file governs only what is *between* them.

```
benches/        symlinks to the four working checkouts (edit in place)
  JacobiGP/     function space: Jacobi-basis GP, learnable (α,β), evidence
                optimizer, exp1–5             → https://github.com/math4mad/JacobiGP
  MEF/          weight space of real LLMs: SVD ablations, LoRA rigs (Qwen2.5+RTE)
                → https://github.com/math4mad/Middle-Eigen-function
  Sarcos/       controlled fast bench: MLP + W/dW band structure, pinned splits
                → https://github.com/math4mad/Sarcos-NN-Model
  PolyNN/       shape inside the layer: polynomial activations vs ReLU,
                Fashion-MNIST, exp8
                → https://github.com/math4mad/Polynomial-Activated-NN
models/         ONE copy of every model + data set (git-ignored bytes,
data/           pinned by manifest.json entries)
artifacts/      cross-bench facts: spectra, atom dictionaries, init states,
                mirrored results — the point of this workspace
letters/        the cross-repo correspondence archive (see § Letters)
meetings/       the Meeting Room: multipartite, in-character debate (see § Meetings)
schemas/        manifest.schema.json — the contract for every shared file
docs/           the home page (GitHub Pages: math4mad.github.io/chora)
bin/sync.sh     idempotent setup: symlinks benches + shared model/data paths
```

## The science in one paragraph

One object, three knobs: $\Delta = \sum_{n=0}^{N-1} c_n \phi_n$,
$c_n \sim \mathcal{N}(0,\lambda_n)$, basis orthogonal under
$w_{\alpha,\beta}$. $N$/rank = **size** (all benches agree it dominates);
$\lambda_n$-by-σ-position = **spectrum order** (killed twice: MEF at fine
scale in LLMs, Sarcos on a pre-registered small-net test);
$(\alpha,\beta)$ = **shape/location in domain space** (open, and ours to
test). Joint spec: `benches/JacobiGP/docs/NEXT.md` — the single source of
truth for merged claims. Exp 6 (rank gauge), Exp 7 (boundary-weighted LoRA),
Exp 7.5 (JacobiGP at SARCOS's physical joint limits) live here, not in any
one bench.

## Law of the workspace

1. **Share inputs and artifacts, never histories.** No merges of git history;
   benches keep their own remotes. Large binaries are git-ignored everywhere
   and reconstructed from manifest entries.
2. **Nothing crosses benches without a hash.** Every file in `models/`,
   `data/`, `artifacts/` needs a manifest entry: `{path, sha256, bytes,
   source, obtained, by: "repo@sha", script, notes}` per
   `schemas/manifest.schema.json`. A number consumed from another bench
   must cite `(path, sha256)` — the bench-level letter rule, applied to
   bytes.
3. **Single writer, many readers.** Each `artifacts/` subdirectory has one
   producing bench. Readers never edit; writers do: produce → hash → append
   manifest → announce by letter.
4. **Benches keep their own discipline, which is now programme law:**
   pre-register predictions; keep post-hoc-truncation / training-under-
   constraint / frozen-base-increment regimes in separate rows; report
   retained energy next to every error; one canonical split module
   (`Sarcos/data.py` pattern); never tune on test; one hypothesis check per
   number; negative results are first-class, never quietly dropped.
5. **Sessions started at this root** may read everything and write to
   `artifacts/`, `letters/`, `meetings/`, and the bench named by the task —
   never to a bench not named. A signed meeting turn appended from a bench
   session into `chora/meetings/` is allowed from anywhere (a hand, not an
   edit); writing into a *foreign bench's own files* never is. Sessions
   started inside a bench obey that bench's `AGENTS.md` (including its
   §0 partnership rules).
6. Model weights are cached once under `models/` (ModelScope/HF layout);
   each bench's expected paths are symlinked by `bin/sync.sh`. If you find
   yourself downloading a model that has a manifest entry — stop; verify
   the hash, fetch only if the hash is missing.

## Letters

`letters/` mirrors the repos' `docs/LETTERS/` protocol for conversations
*about the workspace itself* (new file `YYYY-MM-DD-<from>-<to>-<topic>.md`,
dated, signed by role, claims anchored to SHAs). Existing traffic:
`001 JacobiGP→MEF`, `002 JacobiGP→Sarcos` (both filed under
`benches/JacobiGP/docs/LETTERS/`, answered in each receiver's repo).

## Meetings (the Meeting Room)

`meetings/` is the **multipartite** room beside the dyadic letters: one
topic, four seats, one append-only transcript. Seats are *context
contracts* (`meetings/CAST.md`): **Geometer** (JacobiGP), **Anatomist**
(MEF), **Warden** (Sarcos), **Joiner** (PolyNN). A seat speaks only from
the files its CAST entry loads, signs every turn `bench@sha`, and cites
crossing numbers by `(path, sha256)`. Resolutions bind the workspace
(schedule, artifacts, joint exp numbering) — **never a bench's plan**; a
bench adopts by its own commit or letter. Rule 4 travels into the room:
a resolution that would relax programme law is marked `VIOLATES LAW` and
dies. Letters hand over facts; meetings decide open questions; the room
produces decisions, never data. Commands: `/meeting`, `/speak`
(`.pi/prompts/`).

## Bootstrap for a joint session

```bash
cd ~/one-space && bin/sync.sh          # idempotent
cat benches/JacobiGP/docs/NEXT.md      # the joint spec
ls artifacts/*/manifest.json           # what facts already exist
```
Then state which experiment you are running (6 / 7 / 7.5), which benches it
touches, and which manifest entries it consumes. If any input lacks a
manifest entry, that is your first task, not an obstacle.
