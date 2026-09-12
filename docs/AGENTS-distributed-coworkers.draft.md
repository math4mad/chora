# AGENTS.md — the distributed-coworker sync system (CouchDB + PouchDB over a git record)

> **Status: DRAFT-0 (`.draft` suffix in the filename). Not law.** The
> suffix is dropped by the commit that ratifies it — an unreferenced rename,
> never an edit: a document whose status is in its name cannot silently acquire
> authority by someone touching a line inside it. It becomes programme law only by the chair's
> commit plus each bench's own adoption commit (a resolution binds the
> workspace, never a bench's plan). Until then every agent obeys the existing
> `chora/AGENTS.md` and treats this file as a proposal with evidence attached.
> **Author:** Bench B (`m1-16g`), `chora@7f7ff80`, 2026-09-12.
> **Evidence base:** two days of real operation on two Macs — every number,
> drift, freeze and collision cited below is one we measured, in §15.
> **Motto inherited:** *the shape of the container is the knowledge.* This file
> is the shape of a container, written by the machine that got told twice that
> efficiency is not the axis — **working** is.

---

## 1 · Five constitutional articles

Everything below is a corollary of these five. If a future commit contradicts
one, the future commit is wrong until it amends this file explicitly.

1. **One record.** Git is the sole authority for facts: prose law, letters,
   manifests, results, bytes-by-pin. **No document may exist in the database
   whose content git cannot reproduce.** A second record is not a backup, it is
   a second opinion.
2. **The DB is a wire, not a witness.** Couch/Pouch carries *state that is
   ephemeral by nature*: presence, in-flight claims, acks, the task board,
   derived indexes. It is destroyable, rebuildable in one command, and never the
   sole holder of anything.
3. **Every writer owns its own document.** A machine writes only doc-ids keyed
   by that machine. Two writers never touch one doc. Conflicts are *retained and
   displayed*, never resolved by force. (This is CouchDB's one genuinely better
   idea than a shared branch: it refuses to pick a winner silently.)
4. **Verify before you consume; re-pin when you write.** A fact crosses only
   with `(path, sha256)`. **If the bytes of a pinned path change, the pin
   changes in the same commit or the write is rejected.** §15-D1 is what happens
   when nobody enforces the second half.
5. **Liveness is per-machine and three-valued.** `working` / `quiet` /
   **`silent since <t>`**. A system that cannot say the third one does not know
   whether its partner exists. A day-1 programme learned this from a 13.5-hour
   freeze (§15-A1).

---

## 2 · Roles and write domains

| role | one per | owns (write domain) | may never |
|---|---|---|---|
| **chair** | programme | law prose, `schemas/`, `artifacts/external/`, ratification of any doc→record promotion | delegate the ratification and call it speed |
| **glass** | programme (the machine that paints) | composite `docs/status.json`, homepage build | be the only source of presence data |
| **worker** | machine | its own `presence/<machine>`, `claims/<machine>`, `acks/<machine>` docs; its bench branches; `artifacts/results/<bench>/` for runs it produced | run a publisher, install a launchd agent, edit the composite glass |
| **witness** | task | re-derive someone else's number from `(path, sha256)` and publish agreement *or* divergence | invent a hypothesis mid-flight (§15-C3) |

Machines are named by hardware id (`m1pro-32g`, `m1-16g`), never by a letter that
a bench also uses for an experiment arm (§15-B3: `floors_frozen[k]["B"]` is an
**arm**, and a reader who thinks it is a machine manufactures a machine effect
out of a sentence).

---

## 3 · The two layers, side by side

| | **Record (git)** | **Wire (CouchDB/PouchDB)** |
|---|---|---|
| facts | letters, law, manifests, results json, pinned bytes, decisions | presence, claims, acks, board columns, derived indexes |
| mutation | commit (append-only history, `git log -p`) | `put` with `_rev` (MVCC, conflicts retained) |
| identity | `(path, sha256)` | `_id` + `git_anchor` + `sha256` fields, always populated |
| discovery | full fetch + tree diff | `GET /_changes?since=<seq>` — ordered events |
| checkpoint | commit SHA | `last_seq`, **and** the SHA of the last record commit it read |
| dies if… | laptop loses disk → restore from origin or bundle | deleted → rebuild from git in one command, then diff the digests |
| authority | **yes** | **no** (it may be *current*, never *true*) |

**Bridge rule.** Every wire doc carries `{"git_anchor": "repo@sha", "sha256":
"…"}`. `docs/queue/YYYY-MM-DD.json` is the **daily full snapshot of the queue
into git**, committed by the glass. After that commit the wire is optional.
Before it, the wire holds nothing that would be missed.

---

## 4 · The document set (seven collections, all git-reproducible)

```
_presence/<machine>       {machine, hwid, os, python, torch, numpy, mps,
                           head: "repo@sha", state: working|quiet|silent,
                           beat_iso, free_bytes_gib, ram_bytes, running_pids[]}
_inbox/<from>–<to>        {msg, kind: letter|question|stop|handoff, anchor,
                           sha256, supersedes, claim_id}
_acks/<machine>/<claim>   {machine, reads: "chora@sha", letters_acked[], acked_iso}
_board/<bench>/<slot>     {bench, slot: todo|doing|review|done, by: "machine@sha",
                           run_on, registered_in: "letters/….md"}
_claim/<name>             {name, wanted_by, taken_by, taken_iso}   ← names are minted here
_index/law                {path, sha256, repo, applies_to[], kind: law|letter|
                           skill|stale-law|dup-of, title}          ← the routing table
_manifest/<store>         {path, sha256, bytes, source_url, obtained, by, script}
```

Hard conventions, learned the expensive way:

- **`_claim` before `_board`.** A letter/number/`exp<n>` id is *minted* by a
  claim doc, then announced. Three number collisions in two days came from
  numbering being implicit in a commit order nobody can see in advance (§15-C1).
- **`_index/law` is generated, never edited.** A script compiles it from the
  record; the file itself is git-ignored, the *generator* is committed. Its job
  is to answer "is this the same law, or a drifted twin?" in one hash lookup —
  the audit found 8 files named `AGENTS.md`, one of them outside every repo, one
  stale copy of law committed inside a bench, and 30 KB of byte-identical
  letter duplicates (§15-B1, B2).
- **`_manifest/*/source_url` is mandatory.** When A lost its manifest and
  rebuilt it by re-hashing its own disk, the URLs went with it and 53 pins became
  self-certifying — a pin that can only be checked on the machine that wrote it.
  Rebuild must be reproducible *from upstream*, so the URL is part of the record
  and cannot be reconstructed from bytes (§15-D2).
- **No blobs over 16 MB.** Weights, corpora and tensors cross by
  `curl -r <range>` + `sha256`, exactly as they already do; attachments are for
  small exhibits only. Couch's attachment digest is md5 — never let that
  proximity be mistaken for the programme's hash.

---

## 5 · Replication topology (no daemon unless both are awake)

```
   machine A ── PouchDB (local file) ─┐
                                      ├── live: couchdb-server on A, longpoll /_changes
   machine B ── PouchDB (local file) ─┘
                                      batch: pouchdb-replication-stream → a .car file,
                                             committed to git, applied on pull.
```

- **Default mode is batch.** The replication stream is written to a file, the
  file travels by git (the transport we already trust, already authenticated,
  already versioned), and each side feeds it into its local Pouch. Nothing is
  resident; a laptop may sleep for a day and lose nothing. This is the answer to
  the objection that killed the day-1 websocket proposal: *no second memory, no
  always-on cost*.
- **Live mode is a privilege, not a default.** `pouchdb-server` starts only for
  a session where both machines are awake, and is killed after. It changes
  latency, never authority.
- **Checkpoint = `(last_seq, git_anchor)`.** On resume, each side replays from
  `last_seq` **and** verifies it has read the record commit its docs point at. If
  the git anchor is unreachable, the doc is stale by construction: display it as
  such, do not silently trust it.
- **Conflict policy.** Two revs of one presence doc is impossible by doc-id
  design. If a conflict ever appears it is a *write-domain violation*: raise it
  as a board item and stop, don't pick.

---

## 6 · Dashboard + static homepage

**Two artifacts, different guarantees.**

1. **Static homepage** (GitHub Pages, committed JSON). Works with zero
   infrastructure, is citable, survives both laptops dying. Loads
   `status.json` with `cache: no-store`, plus a per-visit audit call to the
   platform API. Renders, for every machine, *its own* presence row — never one
   composite guessed from one checkout (§15-A2: the day-1 dashboard read
   `git status` of the glass's own working trees, so the second machine's clean
   state could never appear; the fleet's dashboard could not see half the fleet).
2. **Live board** (Pouch-backed, browser-side, read-only). Columns from
   `_board`, a presence strip from `_presence`, an unread count from `_inbox`
   minus `_acks`. If this page is unreachable the programme does not notice,
   because nothing depends on it — that is the point.

The homepage must render these five things, and they are its acceptance test:
**presence per machine · silent-since · queue position (todo/doing/review/done) ·
unacked letters addressed to you · last verified byte-audit timestamp.**

Traffic light becomes three-valued and per-bench *per-machine*, with the rule
kept from day one: **do not start work in a bench that shows dirty on another
machine** — and, added, *say whether your stop is a protocol stop or a safety
stop* (compare file paths; "MEF is busy" and "we would write the same file" are
different facts, and the first one costs the programme work it did not need to
lose, §15-E1).

---

## 7 · Rituals

**Per run.** produce → `sha256` → manifest entry (`by: <machine>@<sha>`, notes
carry `run_on`, os/python/torch/numpy versions, and the **device path of every
statistic** — a CPU fallback inside one statistic is a machine effect waiting to
be misattributed, §15-B4) → commit bench repo → mirror json/log to
`artifacts/` → push → `put` the board doc.

**Per day.** `_index/law` regenerated and read; **queue snapshot committed to
git**; presence docs compared to the previous day's (the machine-effect datum
lives here, not in any single number); `df -h`; **no two training processes on
one machine, ever** — RAM binds tensors, not `shasum`.

**Per handoff.** the receiver `put`s an ack doc naming the commit and the
letters it read. *A letter no one has acked is a letter no one has read* —
day 1 shipped 16 letters and recorded exactly zero readings (§15-A3).

---

## 8 · Rollback law

1. Before any thread that could damage the working system: **tag** the state the
   owner called good (`pause-<date>-<machine>`), on **every** repo.
2. `git bundle --all` per repo, into a directory **outside** the repos, plus
   `SHA256SUMS` for the bundles themselves. (Two ways this fails silently:
   relative paths under `git -C`, and `bundle verify` needing a repo to verify
   against. Both were hit, §15-C4.)
3. **A restore drill is the deliverable, not the bundle.** Clone each bundle into
   `/tmp` and compare HEAD. `verify` proves the file is well-formed; a drill
   proves you can be un-broken.
4. **Drills must run on ≥ 2 machines.** One-laptop bundles are a parachute that
   exists in one copy (§15-D3).
5. git-ignored bytes roll back by manifest + re-fetch + re-run-from-seed, never
   by bundle — say which kind of rollback you are claiming.
6. The freeze rule: **the pause point is taken before the experiment, not after
   the failure.**

---

## 9 · STOP rules (halt, quote verbatim, hand to the human to relay)

hash mismatch on consumed bytes · a pinned path whose bytes changed · a law file
that is a drifted twin · a number whose anchor `(path, sha256)` cannot be opened ·
a bench dirty on another machine and the paths overlap · RAM would hold two
trainers · a disk below the gate · an unratified schema edit of a foreign file ·
**any result that would need a new hypothesis to make sense** (that need is a
question for the run log's tail, never a claim in a table).

A STOP is reported even when it cost the task. Costing something is how a rule
stays honest.

---

## 10 · Acceptance tests — binary, pre-registered before the first line of code

The system is adopted only if **all** pass. No test is a latency or cost claim.

- **A1** An agent answers *which law binds me / which bench is dirty where / is
  there mail for me / what have I not acked / is the other machine alive* without
  opening a single prose file.
- **A2** Put one machine to sleep for an hour; the board must report
  `silent since <t>` as a state distinct from `quiet`, **from the other machine**.
- **A3** Mail to a machine is an ordered event in one request, and its ack is a
  queryable fact.
- **A4** Delete both databases; rebuild from git alone; digests match; the
  homepage still renders (it lost only liveness, not truth).
- **A5** Two writers concurrently touching what they don't own → conflict is
  **retained and displayed**, and the board names the offender.
- **A6** Mint the same letter id from two machines at once; `_claim` makes one of
  them lose *before* the commit, not after the collision.
- **A7** A pinned file is modified without re-pinning → the write is rejected by
  a hook, and the audit script reports zero mismatched entries.
- **A8** Every existing programme law (share inputs not histories · nothing
  crosses without a hash · single writer per artifact dir · pre-registration is a
  bench act · negative results first-class · weights cached once) still holds with
  the DB running.
- **A9** Rollback drill passes on both machines on the same day's bundles.

Fail any → revert the branch, file the failure as the result, and the programme
is not one database the poorer: it is one **measured** constraint the richer.

---

## 11 · Never list

No force-push. No DB-only fact. No md5 where a claim cites sha256. No daemon to
save a poll. No editing another machine's presence/board docs. No publishing the
glass from a worker (`CHORA_NOPUBLISH=1`, sticky, verified at session start). No
`.pt`/weights/checkpoints in git. No numbers cited from memory instead of
`(path, sha256)`. No law prose whose only copy lives outside a repo. No new
hypothesis inside a pre-registered run. No refactor of six repos on one branch —
a vessel change is adopted repo by repo, commit by commit, by each owner.

---

## 12 · Migration from a CHORA-shaped system (each step reversible alone)

1. **P0, no new software.** `_index/law` generator + `acks` as a committed JSON
   file. Kills: drifted-law blindness, zero-ack. Rollback: delete the generator.
2. **P1.** Per-writer presence docs (`docs/presence/<machine>.json`) + homepage
   renders every machine. Kills: single-machine blindness, and the 13.5-hour
   ambiguity — **without any database**.
3. **P2.** Install Pouch locally, **read-only replica** of those three
   collections, `_changes` for discovery. Nothing authoritative moves. Gate: A4.
4. **P3.** `_claim` for name minting; publish-side hook enforces re-pin (A7).
5. **P4.** Live mode when both are awake. Batch remains the default forever.
6. **P5, only if A1–A9 have all passed** and each owner adopts it for its own
   bench: the wire becomes the primary queue for F1–F3, with the daily snapshot
   still crossing into git. If the snapshot is ever dropped, the system is back
   to being one record with a habit.

---

## 13 · What an agent on any machine does at session start (12 lines)

```bash
git -C chora pull --rebase origin main                     # record first
curl -s <glass>/status.json | jq .generated                # how stale is the view?
pouchdb-replica/replicate-to-local.js                      # wire, idempotent, optional
python3 bin/law-index.py --check-dupes                     # am I reading the law, or a twin?
jq '.[]|select(.machine=="'"$MACH"'" )' docs/presence/*.json  # my own sheet, my own write
shasum -a 256 -c _rollback/*/SHA256SUMS                    # parachute still packed?
curl -s "$GLASS/_changes?limit=1" >/dev/null && \
  echo "wire up (advisory only)" || echo "wire down; git is enough"
python3 bin/verify-bytes.py --store models --store data     # verify before you consume
df -h / | awk 'NR==2{print "disk free:",$4}'
pgrep -fl "train|stage[0-9]" | head                        # never a second trainer
jq '[._board[].slot]|group_by(.to)|map({to:.[0].to,n:length})' _acks/…  # what I owe acks for
```

Then: state which experiment you are running, which bench it touches, which
manifest entries it consumes, and **which git SHA each number will be anchored
to before you produce it.** If an input lacks a manifest entry, that is your
first task, not an obstacle.

---

## 14 · The one sentence this system is

**Git decides what is true; the database decides what is now; the homepage shows
both and never confuses them; and any agent on any machine can prove — by
deleting the database and rebuilding it — which of the two it was depending on.**

---

## 15 · Evidence appendix — every claim above traces to a measured failure

| id | what we measured | which article it became |
|---|---|---|
| **A1** | glass frozen `generated 2026-09-11T10:38:56Z` while `main` reached `1e0de5c` at 13:45:26Z; observed stale ≈13.5 h. From B, "the programme is quiet" and "machine A is down" returned identical bytes | §1.5, §6, A2 |
| **A2** | `status.sh` reads `branch --show-current` + `git status` **of the glass's own checkouts**; B's branch/HEAD/clean-state can never appear. B cleaned MEF to 0 and the reported `dirty=2` did not move | §2, §6.1, A2 |
| **A3** | 16 letters day 1; **zero** records of anyone reading any of them | §7 per-handoff, A3 |
| **B1** | 8 files named `AGENTS.md`; the one injected into B's harness was **outside every repo**, byte-identical to a repo copy — knowable only by hashing | §4 `_index/law`, §13 |
| **B2** | 30,088 B duplicated byte-for-byte across 5 mirrored letter pairs; a stale `AGENTS.md` committed inside a bench's `backup/` | §4 `_index/law` (kind: `stale-law`, `dup-of`) |
| **B3** | `floors_frozen[k]["B"]` = the held-out-tail **arm**, not machine B; A's file, B's read, one letter, two meanings | §2 naming law |
| **B4** | both machines log `linalg.svd: … falling back to CPU (294912 > 32768)`. Had only one, every `eff_rank_mean` diff would have been a device-path artifact in a hardware costume | §7 per-run (record the device path) |
| **C1** | letter numbers double-booked three times in two days (`015/016`, a bench's own `010`, `017` by B and by a mirror 23 min apart) | §4 `_claim`, A6 |
| **C2** | `schemas/manifest.schema.json` was not valid JSON (YAML `>-` block) — the contract for hashed bytes could not be machine-read from the day it was written | §4 (schemas must parse; CI reads them) |
| **C3** | a proposal answered with cost arguments and corrected by the owner: *efficiency is not the first consideration, working is* | §10 (no test is a cost claim) |
| **C4** | rollback first attempt failed twice for tool reasons: relative paths under `git -C`, and `bundle verify` needing a repo. The drill (clone → compare HEAD, 6/6) is what actually proved it | §8.2–8.3 |
| **D1** | `tv_show /outline_season1.md`: pin = hash of nothing (0 B, filed as a joke), bytes later written to 3,958 B, pin never followed → "18/18 manifested" true for exactly one commit | §1.4, A7 |
| **D2** | manifest rebuilt by re-hashing local bytes; `source` now reads "REBUILT … hashing the on-disk bytes". Consequence measured: hub's `configuration.json` = 15 B, pin = 2 B → that pin is unverifiable off A's disk | §4 `_manifest.source_url` mandatory |
| **D3** | 6 bundles + 6 tags created, tags pushed, **bundles on one laptop** | §8.4, A9 |
| **E1** | law 4 forced a stop on closing Gate 6 because A committed to MEF — while the changed paths (`.gitignore`, a new script) had zero overlap with B's run | §6 protocol-stop vs safety-stop |
| **E2** | identical config on identical hardware: 509.7 s → 742.5 s (**+45.7 %**). Any A-vs-B machine effect must be quoted against a B-vs-B spread | §7 per-day, and: never estimate between machines without repeating within one |

**Two of these (A1, A2) need no database to fix and are recommended as P0/P1
regardless of what happens to the rest.** The appendix exists so that nobody can
mistake this document for taste.
