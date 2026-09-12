# AGENTS.md — a general protocol for distributed coworker fleets (N machines × R repos)

> **Status: DRAFT-0 (`.draft` suffix). Not law.** Ratified by rename, never by an
> in-file edit. **Author:** Bench B (`m1-16g`), `chora@dccdfbc`, 2026-09-12.
> **Relation to the sibling document:** `AGENTS-distributed-coworkers.draft.md`
> is the *CHORA instance* — two Macs, six repos, one named glass. **This one is
> the protocol that instance instantiates.** Nothing here overrides that file's
> five constitutional articles; it generalizes them and removes every place where
> it silently assumed `N = 2`.
> **Test of the document:** §12 must be able to re-derive today's whole system
> from parameters alone. If it cannot, this file is a bigger special case, not a
> generalization — and §13 lists the assumptions that were caught that way.

---

## 1 · The invariants (do not parameterize these)

1. **One record per fact-domain.** Some durable, append-only, content-addressed
   store is the authority. Its technology is a parameter (git today); that it
   exists, and that the wire never holds what it cannot reproduce, is not.
2. **The wire is stateless in the epistemic sense.** Databases, boards, indexes
   and pages are caches over the record: destroyable, rebuildable, and *never*
   the sole holder of anything.
3. **Every writer owns its own documents.** `doc_id` keyed by minted writer-id;
   concurrent writes to disjoint docs; conflicts retained and displayed.
4. **Verify before consume; re-pin on write.** Every cross-unit byte or number
   carries a digest *and* a resolvable source. A resolved source means: the URL
   was fetched and hashed by someone other than the pinner.
5. **Liveness is per-unit and three-valued**: `working / quiet / silent since t`.
   A system that cannot emit the third state does not know its own membership.
6. **Names are minted, never chosen.** Machine ids, letter ids, experiment ids,
   arm names: claimed in a claim-collection before use. (§13-E3: three number
   collisions in two days with only two machines.)
7. **Attribution before interpretation.** Every number states its unit, its seed,
   its tool versions, and the **device path of the statistic that produced it**.
8. **Reversibility is a precondition, not a cleanup.** A thread that can damage a
   working system begins by making itself undoable, and proves it by drill.

## 2 · The variables (this is what "flexible" means)

| symbol | is | CHORA today | may be |
|---|---|---|---|
| **M** | set of machines, ids minted in `_claim` | 2 | 1, 2, 40; ephemeral |
| **R** | set of repositories, declared in `_registry` | 6 | any, added by one doc, retired by a tombstone |
| **D** | write-domain map `D: unit → set(paths ∪ collections)` | per bench + per machine | arbitrary; must be a partition for exclusive domains |
| **L** | leases: `glass`, `hub`, `publisher`, `archivist`, `auditor` | glass+publisher held by one machine | one, several, none held; renewable, expiring, transferable, **observable** |
| **C_m** | capability vector of machine *m* | implied by prose ("16 GB, one trainer") | explicit: `ram, disk_free, accelerators, flops_class, net_kbps, tz, clock_id, slots` |
| **Q** | quorum function for promotion (fact → crossing fact; draft → law) | 1 author + 1 witness; chair for law | any monotone threshold; may depend on the fact class |
| **τ** | time policy | ad-hoc ("before 9 am") | all timestamps UTC ISO, with `tz` and `clock_id` recorded once per machine |
| **B** | band/noise model per measurement class | ±0.94 pp (PolyNN), ladder floors (MEF) | per `(repo, task, capability_class)`; **within-unit repeats mandatory before between-unit claims** |

A *fleet* is `(M, R, D, L, C, Q, τ, B)`. A **profile** is a concrete assignment of
all of them. Profiles are data (`_registry/profile.json`), committed to the record,
not prose in an AGENTS.md.

---

## 3 · Membership: machines enroll, they are not configured

A machine joins by executing a self-check and **publishing**, not by being
mentioned anywhere:

```
1. claim  machine-id  → _claim/<id>            (minted: hwid + first-seen ISO + nonce)
2. probe  capabilities → _presence/<id>        (os, arch, python, numpy, torch, mps/cuda,
                                               ram_bytes, free_bytes_gib, net_kbps, tz, clock_id)
3. fetch  profile     → git pull, verify ≥1 manifest entry by digest  ← a member is
   not a member until it has independently verified one byte it did not produce
4. drill  restore     → clone the fleet's newest bundle, compare HEAD, publish result
5. beat               → renew presence every Δt; if presence lapses, the fleet sees
                        silent-since — never "absent, therefore probably fine"
```

Gate 3 and 4 are the two that look optional and are not: §13-E4 (a machine booted
for a day before the fleet could tell it from a sleeping one) and E5 (a 400 MB
"successful download" that was an HTTP error body). Leaving is symmetric: the
member publishes a retirement presence doc; its documents and authorship remain
immutable forever. **A gone machine is not a deleted fact.**

## 4 · Repositories are declared, not enumerated

```
_registry/<repo>  {name, remote_url, upstream_owners[], branch_policy, role_tags[],
                   doc_prefix, write_domain[], record_paths[], artifact_paths[],
                   law_paths[], retired: null|ISO}
```

Adding a repo = one doc + one commit. **Nothing in this protocol contains a list
of repositories.** That is the single most important generalization here: the
sibling document names five benches, and every one of those names is a place where
it stops working when the fleet changes shape. Where a rule must know a repo's
role, it reads `_registry`, not its own prose.

## 5 · The glass is a lease, not a person

Today's deepest accident is not that a dashboard went stale; it is that
**"the glass" was a machine**. It is a function over data:

- the composite is **derived** from per-unit documents (`_presence/*`, `_board/*`),
  never hand-authored;
- whoever holds the `glass` lease only *paints*; the lease is renewable
  (`renews_at`), transferable, and may be **unheld**;
- if the lease expires, **any** member may take it and say so — and the homepage
  must be able to display the degraded truth: *"composite last painted at t by u;
  leases expired: glass, hub; per-unit docs are current for: v, w"*;
- therefore glass loss ≠ state loss, which is the exact property that makes
  leasing safe (§13-E1: the day-1 glass read only its own checkout, so half the
  fleet could not appear on it — a defect that survives any transport change
  unless the composite is derived from per-unit data).

## 6 · The wire, for arbitrary M

```
each m ∈ M :  local PouchDB file (its own cache, its own writer docs)
batch (default, always available) :
    pouchdb-replication-stream → a file, committed to the record, applied on pull
live (optional, leasable role `hub`):
    one CouchDB/PouchDB-server any machine may hold while awake; longpoll /_changes
    its absence changes latency and never authority
mesh size is irrelevant because:  every doc ≤ 16 MB, every doc carries
    {git_anchor, sha256}, and the daily queue snapshot crosses into the record.
```

For **M = 1** this degenerates correctly: no replication, still a presence doc
(your own liveness is measurable too), still a queue snapshot, still a drill.
For **M large**, batch-over-git stays the default: an N-way live hub is a service
somebody must keep awake, which is the cost the protocol exists to avoid.

## 7 · Work is capability-matched, not assigned

A board item declares **requirements**, and machines declare **capacity**; the
match is arithmetic, and the refusal is a published reason:

```
_board/…  requires: {ram_ge, disk_ge, accel ∈ {mps,cuda,cpu}, net_kbps_ge,
                     slots: 1 trainer | 0 (I/O only), repo write_domain}
_presence/m  has:   C_m + occupied slots + running pids
result:             claimable(m, item) = requires ⊆ C_m ∧ slots free
```

That is where "16 GB: one training process at a time" belongs — as a slot count on
a capability vector — and not as a prohibition addressed to a laptop model.
**Resource conflicts must be named distinctly from protocol conflicts**: *safety
stop* = overlapping write paths or occupied slot; *protocol stop* = another unit
holds a domain you merely want to read (§13-E2: a real replication task was halted
on a law about dirty benches when no file overlapped). With ≥3 machines this
distinction stops being pedantry and starts being throughput.

## 8 · Replication and effects across N units

Any comparison of two units — hardware, toolchain, or teammate — follows one rule:

> **A between-unit effect may be estimated only after a within-unit repeat, and the
> two are reported as separate variance components.**

For **M = 2** that is a subtraction. For general M it is a variance decomposition
over `C_m` (the capability vector is the join key: `os`, `arch`, `python`,
`numpy`, `torch`, `accel`, `clock_id`), and a fleet may then say *which* axis a
difference rides on. Bands inherit the same discipline: **a noise band is
per `(measurement class, capability_class)`, never global** — one bench earned its
±0.94 pp from 20 calibration runs on one machine, and a second machine may not
spend that band until it has measured its own.

## 9 · Promotion, quorum and the ack

```
produced (author)   →  hashed, pinned, committed to the record
               →  announced on the wire  (_inbox)
               →  acked by Q readers     (_acks: reads = <record SHA>, letters[])
               →  witnessed              (≥ Q_w independent re-derivations)
               →  "crossing fact"        (may now be cited by another unit)
```

Unacked items are *visible as unacked*, on the homepage, per addressee. A letter
nobody has acked is a letter nobody has read; with M machines this scales as
O(M·letters) silently, so the board's default view is sorted by `unacked_age`.
Law changes use the same pipeline with `Q_law` = the set of affected write-domain
owners — which is what "each bench adopts by its own commit" says when you remove
the word "bench".

## 10 · Verification is a scheduled act, not a mood

Each machine runs, on its own cadence, and **publishes the result even when clean**:

| family | check | what it caught in the instance |
|---|---|---|
| verifiability | re-hash every pinned path on my disk | `outline_season1.md`: 0 B pin vs 3,958 B bytes |
| verifiability | recompute a pin's digest space for placeholders (`sha256("{}")`, `""`, `b"Entry not found"`) | one of 53 model pins was `{}`, and upstream has no such path |
| verifiability | does every schema/law file parse with the tool that claims to read it? | the manifest schema was invalid JSON since it was written |
| verifiability | is every law file's twin identical, and is each inside a repo? | 8 `AGENTS.md`; one outside every repo; one stale in `backup/` |
| visibility | are all members' presence docs newer than `silent_after`? | 13.5 h freeze indistinguishable from a quiet day |
| visibility | does the composite show *every* member, and can I see my own row change? | glass read one checkout only |
| visibility | are there acks for the letters sent this cycle? | 16 letters, 0 acks |
| reversibility | did a restore drill pass, on how many machines, with which bundle SHAs? | tags ×6 pushed, bundles ×6 on one laptop |

## 11 · Degradation table (the test of a general protocol)

| failure | the fleet must still… |
|---|---|
| hub down / never started | work, discover events on pull, paint the glass from the record |
| glass lease expired | show the last composite **with** the expiry, and let anyone take the lease |
| a member gone forever | keep its docs and authorship; its runs stay reproducible from seeds |
| M = 1 | remain meaningful: presence, acks to self, queue snapshot, drill |
| R grows mid-task | old docs still resolve; `_registry` is read, not memorized |
| record unavailable (no network) | keep producing locally; nothing in the wire is a prerequisite for a run |
| net throughput ≪ estimate | publish an honest ETA or re-prioritize: a task with a network precondition must not silently become a wish (§13-E6: measured 4–13 KB/s for a 988 MB fetch) |
| disk below gate | delete regenerable bytes, never jsons/logs, and say so in the report |
| clocks disagree | every timestamp carries `clock_id`; wall-clock claims are compared only after offsets |
| a write-domain violation happens | conflict retained, offender named on the board, rule cited |

## 12 · The CHORA instance, as parameters only

```json
{ "profile": "chora-2026-09-12",
  "record": {"kind":"git","stores":["chora","JacobiGP","MEF","Sarcos","PolyNN","Kairos"],
             "authority":["letters/","schemas/","models/manifest.json","data/manifest.json",
                          "artifacts/*/manifest.json","docs/"]},
  "wire":   {"engine":"pouchdb+replication-stream","live":false,"blob_max_bytes":16e6,
             "collections":["_presence","_inbox","_acks","_board","_claim","_index/law","_registry"]},
  "M": [{"id":"m1pro-32g","leases":["glass","publisher","chair"],"C":{"ram":34359738368,"accel":["mps"],"net_kbps":600000}},
        {"id":"m1-16g","leases":[],"C":{"ram":17179869184,"accel":["mps"],"net_kbps":12,"slots":1}}],
  "Q": {"ack":1,"witness":1,"law":"affected-domain-owners"},
  "B": {"polynn.exp8":"±0.94pp from 20 calibration runs on m1pro-32g",
        "mef.stage18":"floors 5.546→1.091; within-unit spread 509.7s→742.5s"},
  "τ": {"ts":"ISO-8601 UTC","tz_per_machine":true,"beat_s":300,"silent_after_s":1800},
  "reversibility": {"tag":"pause-2026-09-12-b","bundles":6,"drill_passed":"6/6 on m1-16g",
                    "drill_machines":["m1-16g"],"gap":"single-copy parachute"} }
```

That block is the falsification handle: **if any behaviour of today's system needs
a sentence rather than a parameter, §2 is missing a variable.** The `gap` field is
there on purpose — the profile must be able to express an unmet obligation, or the
document has quietly become a wish list.

## 13 · Assumptions removed from the sibling document (each found by re-reading it)

- **E1** "the glass is A's" → *the glass is a lease* (§5). Otherwise a stale
  composite is a membership fact, not a rendering bug.
- **E2** "if a bench is dirty on another machine, don't start there" → resource
  vs protocol conflict must be distinguished and *both* must be publishable (§7),
  or the law silently costs work nobody asked it to cost.
- **E3** "number = order of commit" → mints nothing; with M units the race is
  structural, so `_claim` is mandatory before any id appears anywhere (§2.6).
- **E4** "two machines" appears in prose in seven places → replaced by M, with
  the M = 1 degeneration specified, because a protocol that is meaningless alone
  is not a protocol.
- **E5** "nothing crosses without a hash" → insufficient: a pin may be a
  placeholder, and a fetch may return an error body. Added: **the digest space of
  known non-sources is a searchable list** (`sha256("")`, `sha256("{}")`, HTTP
  error bodies) and every inbound file is hashed *before* it is named (E5 cost us
  one model file that was 15 bytes of `Entry not found`).
- **E6** "run the queue in order" → order is over `claimable(m, item)`; a blocked
  item publishes its blocker and an ETA, so a stalled fetch cannot masquerade as
  progress.
- **E7** "machine effect" → becomes §8's variance decomposition, because with
  M > 2 the phrase "which machine" stops being a binary and the +45.7 %
  within-machine spread stops being an anecdote and becomes the denominator.
- **E8** every list of repository names → gone, read from `_registry` (§4).

## 14 · Conformance: what an implementation must pass to claim this protocol

```
F1   join with zero edits to law or config: claim → probe → verify ≥1 pin → drill → beat
F2   unheld lease: composite still renderable, expiry visible, lease takeable by any member
F3   M = 1: presence, acks, snapshot and drill all still meaningful
F4   new repo added mid-task by one doc; no prose file mentions it
F5   forced glass loss → rebuild from per-unit docs, digests equal, no fact lost
F6   two members claim the same name concurrently → exactly one wins before commit
F7   a pinned path modified without re-pinning → write rejected, audit reports zero drift
F8   a member offline 24 h → rejoins by batch stream, no manual repair, acks reconciled
F9   delete every database on every machine → one command per machine, byte-identical rebuild
F10  within-unit repeat exists for every between-unit effect quoted in the board
F11  a 16-byte error body can never become a named artifact on any member
F12  every rule cites a check that a machine runs, with a published result when clean
```

F12 is the one that keeps the rest honest: **a rule nobody can execute is a
preference.** The instance has 2 days of evidence that unexecutable law
(immutable letters with no ack channel; a schema nobody parsed; a dashboard
missing half its fleet) survives for exactly as long as nobody tests it.

---

## 15 · One sentence

**Any number of machines and any number of repositories can cooperate without
agreeing on anything but four things: which store is the record, who currently
owns which document, whether every byte still hashes to what it claims, and
whether the whole thing can be undone — and each of those four is a published,
expiring, checkable state rather than a name in a file.**
