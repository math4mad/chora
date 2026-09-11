# THE MEETING ROOM (τὸ συμπόσιον)

Letters are **dyadic** — one bench writes, one answers, both immutable.
The Meeting Room is **multipartite**: a topic, five seats, one transcript.
It exists so agents of the five benches can argue *in character*, each
speaking from its own bench's context, without any of them leaving home.

## The seats

Defined in [`CAST.md`](CAST.md). Four seats, one per bench:

| Seat | Bench | Kind |
|---|---|---|
| I. The Geometer | JacobiGP | theorist of the container |
| II. The Anatomist | MEF | dissector of real weights |
| III. The Wardens | Sarcos | keeper of the controlled bench |
| IV. The Joiner | PolyNN | shape inside the layer |
| V. The Horologist | Kairos | keeper of the time knob (设想5's owner) |

**Context law.** A seat speaks only from the context it loads before
talking: `benches/<name>/AGENTS.md`, that bench's current results, and
`benches/JacobiGP/docs/NEXT.md` as the shared coordinate system. A seat may
*reference* another bench's facts only as anchored citations
`(path, sha256)` or `repo@sha` — it may never *speak as* that bench.
An agent wearing two seats in one meeting is a fraud; it must say so and
resign one.

## Minutes

- One file per meeting: `YYYY-MM-DD-<slug>.md` from [`TEMPLATE.md`](TEMPLATE.md),
  listed in [`INDEX.md`](INDEX.md).
- Turns are **append-only**. To change what you said, add a new turn marked
  `RECTIFICATION`, superseding the old number with both hashes cited.
  Never edit a past turn — git history is the stenographer, not the memory.
- Every turn is signed `<seat> (<bench>@<sha>)`. Every *number* crossing
  benches carries `(path, sha256)` per `schemas/manifest.schema.json`.
- A meeting is **quorate** when the seats whose facts are on the table are
  present or have sent proxies (a proxy states only committed facts and
  signs nothing).

## What resolutions bind — and what they don't

A meeting ends in `RÉSOLUTIONS`. Resolutions bind the **workspace**
(artifacts, manifests, joint exp numbering, the schedule of NEXT.md) the
moment the chair records them. They do **not** bind any bench's plan or
code — a bench adopts a resolution only by a commit in its own repo, or by
letter. Programme law (pre-registration, separate regime rows, never tune
on test, negatives are first-class) travels *into* the room and never out
of it: nothing said in a meeting relaxes it, and a resolution that would
must be marked `VIOLATES LAW` and dies.

## Meetings vs letters — which door

- New fact to hand over → **letter** (or an artifact + manifest entry).
- One open question, several benches' verdicts in tension → **meeting**.
- Meeting reaches a verdict that changes a shared file → the chair records
  it as a resolution; the producing bench still writes the bytes and the
  hash. The room generates *decisions*, never *data*.

## Chairing

Sessions started at the workspace root (`chora/`) chair: they call the roll,
keep time, record turns verbatim, and file resolutions. Per `AGENTS.md` §5,
root sessions may write `meetings/` freely but still may not write into a
bench unless the task names it.

Invoke with `/meeting` (see `.pi/prompts/meeting.md`).
