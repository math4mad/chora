# ROLLBACK.md — the pause point of 2026-09-12 (machine B)

Ordered by the task owner: *"first is first; make sure everyone can roll back;
the current work is excellent already."* So the container/PouchDB thread was
frozen **before** anything was written, and this file is the reason it is safe
to be frozen.

## 1 · The six tags (what "excellent" looked like, in SHAs)

`pause-2026-09-12-b`, annotated, on every repo:

| repo | HEAD at the pause |
|---|---|
| chora | `1e0de5ccf3a91c6827326403f075d8bc63bb7c96` |
| JacobiGP | `553a4ddccf5f16a4451a22528f81e6141ff7230a` |
| Middle-Eigen-function | `a98508e8554e621654f61fccbd937e3dedcef524` |
| Sarcos-NN-Model | `fb37e04950a45236f8d1099dbc94998220c3639b` |
| Polynomial-Activated NN | `0eb293097eec7afcb838ccf4661e766daaaf6ca1` |
| Kairos | `a9e3222110246add3ad3287dd3cab68589b1a8a5` |

Roll back **one** repo: `git -C <repo> reset --hard pause-2026-09-12-b`
(every uncommitted run artefact is regenerable from seeds — law 3).

## 2 · Offline restore points (outside git, on B's disk)

`~/Programming/code-2026/_rollback/2026-09-12/*.bundle` — one per repo,
`--all` (all refs **and** the tags above), ~15 MB total, listed in
`SHA256SUMS` in that directory.

**Proven by a restore drill, not by `bundle verify`:** cloned each bundle into
`/tmp/restore-drill/<repo>` and compared — 6/6 came back with an identical
HEAD. The only refs a clone lacks are `refs/remotes/origin/*`, which `git
fetch` rebuilds; no history is missing.

Two honest limits of this safety net:
1. **The bundles live on one laptop.** They are re-creatable from GitHub for
   the pushed commits, but the *tags* exist only here and on any remote they
   get pushed to. Until A or the origin holds them, this is a one-machine
   parachute (B is not the glass — B files the fact, does not fix it).
2. **Bytes are not in bundles.** `models/`, `data/`, `outputs/*.pt` are
   git-ignored by law 3; their rollback path is the manifest + re-fetch +
   re-run-from-seed, which is exactly what `models/manifest.json` (53 entries,
   rebuilt last night by re-hashing) is for.

## 2b · Re-minted at 15:3x local — `checkpoint-2026-09-12-eve` (six repos), bundles at
`_rollback/2026-09-12-eve/*.bundle` (~14 MB, `SHA256SUMS` beside them)

The 08:24 parachute predated the whole afternoon: seed-14's sweep, Sarcos Step 0,
the H6c bytes, the PolyNN `docs/` restore and Letter 020 were all *after* it. So the
parachute was re-minted before anything else could be lost, and — because a
bundle nobody restored is a story, not a backup — the drill was re-run:

| check | result |
|---|---|
| `shasum -a 256 -c SHA256SUMS` | 6/6 OK |
| clone each bundle → HEAD == the annotated tag's commit | **6/6 OK** |
| bundles carry every local branch **and** `refs/remotes/origin/*` **and** both tags | yes (verified by `git bundle list-heads`) |
| a restored clone can reach **A's** tip, not just B's branch | **NO — my claim, retracted in place below.** The object is in the pack, but no ref names it, and one `git gc --prune=now` deletes it permanently |
| correct offline restore (verified, all six) | `git init r && cd r && git remote add o <abs>/repo.bundle && git fetch o '+refs/remotes/origin/*:refs/from-bundle/*' '+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'` → every bundle head present and **survives `reflog expire` + `gc --prune=now`** (0 unrecoverable on 6/6) |

## 2c · The drill's real catch: `git clone <bundle>` is **not** a restore, and the
morning's own sentence about it was the true half of a misleading claim

The morning's §2 said: *"The only refs a clone lacks are `refs/remotes/origin/*`,
which `git fetch` rebuilds."* The first clause is exact; the second is the trap —
rebuilds them **from a remote**, and offline the bundle *is* the remote, so
`git clone` is precisely the command that does not do it. Measured, per repo, on
the eve bundles:

```
chora            origin refs in bundle 2 → in a naive clone 2   missing: —
JacobiGP                                    3 →                2   missing: gh-pages
Middle-Eigen-function                       5 →                3   missing: multi-model, working-sage-1
Sarcos-NN-Model                             4 →                3   missing: gh-pages
Polynomial-ActivatedNN                      4 →                3   missing: gh-pages
Kairos                                      2 →                2   missing: —
```

On MEF the two branches a naive clone drops are **`multi-model` — A's entire day
order, every stage18/stage19 head it has** — and `working-sage-1`; on three other
benches it is `gh-pages`, i.e. **the published site itself**. And the dropped tips
are not merely unnamed: they are unreachable, so the next routine maintenance
destroys them. Demonstrated on a naive MEF clone:

```
BEFORE  reflog expire + gc --prune=now :  git cat-file -t 6f5f4c5… → commit
AFTER                                    :  could not get object info      ← A's tip is GONE
fsck dangling commits: 0
```

So the morning's headline ("HEAD matched 6/6, no history is missing") was true of
the *object store* and false of the *restore path that matters*: HEAD matched
because HEAD was the one thing a clone is guaranteed to bring.

**Corrected recipe, verified this hour on all six bundles** (the one in the table
above): `git init` → `git remote add o <bundle>` → `git fetch o` with the three
refspecs → *then* `reflog expire --expire=now --all; git gc --prune=now`. After
that, every bundle head resolves **through a ref** and 0 are unrecoverable on 6/6.
A drill that prunes is a drill; a drill that only reads HEAD is a screenshot.

Two instrument bugs surfaced on the way there and are filed because they are the
same species as the `{}`-pin — an instrument reporting on itself rather than on
the specimen: (1) my first drill loop printed `FAIL JacobiGP` because it had
stripped the canonical leading space from `" JacobiGP"`, a bug in the checker and
not the bundle; (2) my second loop printed `0 refs survived` for **all six** repos
because it pointed `git remote add` at a relative path from `/tmp`, and a
green-measuring-a-broken-instrument is how a false PASS would have entered the
record instead of a false claim by me. Both were caught by re-reading the output
for whether it was *too* tidy: six identical zeros is not a pass, it is a broken
probe.

Limits unchanged and still honest: the bundles live on one laptop; `models/`,
`data/`, `outputs/*.pt` are outside git by law 3 and roll back via manifest +
re-fetch + re-run-from-seed, not via bundle.

## 3 · What the audit found on the way (three defects, all repaired or filed)

- **A law-2 breach by B itself:** `artifacts/results/mef/B-env.json` crossed on
  2026-09-11 with **no manifest entry**. Now pinned (`b78c34e2f5cb…`), with the
  error named in the `notes` field rather than quietly fixed.
- **Un-backed-up science:** the Gate-6 twin (`outputs/stage18_twinB/`) existed
  only on this laptop, and its **sweep json was never produced** — so B's twin
  ladder floors do not exist. The `base_run.json` is now mirrored as
  `artifacts/results/mef/twinB_seed13_base_run.json` (`24bbbe1a2aba…`) and the
  gate is registered as **open, not passed**. A's floors remain
  `5.546 / 1.404 / 1.219 / 1.153 / 1.091` nats, owed a comparison.
- **The contract file did not parse:** `schemas/manifest.schema.json` used a
  YAML folded block (`>-`) as a JSON value, so every `json.load` on it raised.
  Text unchanged; the block became a JSON string. Found because the audit
  script tried to read it — i.e. an undiscovered defect for 12 days of the
  programme (1 day of it, honestly).
- Correction of B's own earlier claim: MEF's history was **not** unpushed —
  `bench-B-multi-model` == `origin/multi-model` == `a98508e`. Only the ref
  *name* was local. A ref-name gap, not a history gap; B overstated it.

## 4 · The container thread, as frozen

`chora/letters/2026-09-12-B-chair-pouchdb-container-experiment.md`
(`55da790e3661d648…`) holds the pre-registration and the A1–A6 acceptance
tests. Nothing was installed, no DB was created, no branch was opened, no
bench repo was touched. To resume: the chair rules on §6.1 (may the queue
domain live outside git at all), and E0 seeds 14/15 come first regardless —
that is what "first is first" means on this bench.
