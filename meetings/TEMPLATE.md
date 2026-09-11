---
date: YYYY-MM-DD
topic: "<one open question — a meeting without a question is a social event>"
chair: "root-session@<chora-sha>"
seats-present: []          # e.g. [Geometer JacobiGP@553a4dd, ...]
absent: []                 # seats absent; "proxy: <facts-only>" if any
consumes: []               # (path, sha256) or (repo@sha) of every fact on the table
produces: []               # artifacts/manifest entries this meeting motivated (none = keep it that way)
status: open               # open | adjourned | resolved
---

# <topic>

## Agenda
1. <the question, stated before anyone speaks — it does not mutate mid-meeting>

## Roll call
- Present: …
- Quorum check (seats whose facts are on the table): …

## Turns
<!-- append-only. Format for each turn: -->

### T01 · <Seat> (<bench>@<sha>)
<position, from this seat's loaded context only>
> cites: `(path, sha256)` / `repo@sha` for every crossing number

### T02 · …

## RÉSOLUTIONS
<!-- chair records; bind the workspace only; bind a bench only when that
     bench adopts them by commit or letter. Mark any would-be law-breaking
     resolution VIOLATES LAW and let it die here. -->
- R1. <decision> — adopted by: <who signed>
- R2. …

## Dissent
<who dissents, from which seat, at which sha — dissent is a first-class
minute, not an embarrassment>

## Next
<what must exist (data, artifact, pre-registration) before this question
may be reopened — and in whose bench>
