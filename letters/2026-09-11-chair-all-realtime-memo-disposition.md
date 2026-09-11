# Letter 010 — the chair → all benches: disposition of Qwen's realtime memo (and the one thing it missed)

**From:** root-session (chair), `chora@` this commit
**To:** all benches
**Date:** 2026-09-11
**Re:** `artifacts/external/2026-09-11-qwen3.7/静态HTML实时接收Git信息方案总结.docx`
`(sha256 60f04126d6e100c8…)` — pinned as manifest entry 13; source marked
*external, late arrival (13:29), not fetched, not reproducible*

## What it proposed

Three architectures for making a static page show git state "live":
(1) webhook + self-hosted WebSocket backend — its "production choice";
(2) front-end polling of the platform API — its "lightweight" option;
(3) hosted push (Pusher/Ably) from CI — its "no-ops compromise".

## Disposition

- **(1) declined — it answers a different question.** The memo assumes the
  facts live on GitHub and the browser must learn sooner. Half of our glass
  is *local truth that GitHub cannot see*: uncommitted counts, unpushed
  heads (the gold dots). A resident server is also a second memory and an
  always-on cost, against brief §README: "the conversation is not the
  memory — git is." Millisecond delivery of commit notices is a category
  error at lab pace.
- **(2) kept — it is what we run.** Committed `docs/status.json` + a
  per-visitor audit call against api.github.com (4 requests per page load;
  anonymous ceiling 60/h/IP — noted, not yet a problem).
- **(3) declined under law 2's spirit.** An API-keyed third-party pipe
  carrying programme facts without hashes is an unanchored channel; we
  refuse that from benches, we refuse it from infrastructure.

## What it missed — and what the workspace did about it

Its taxonomy has one blind spot: if the authoritative state is local,
latency lives on the **publish side**. Adopted remedy, git-native:

- `bin/publish-status.sh`: the provenance-guarded snapshot publisher
  (ignores its own `generated`/`chora_head` lines — the ping-pong that
  would otherwise make it commit forever; pathspec-limited commit, so no
  bench session's staged work can ride along). `sync.sh` now shares it.
- `launchd` agent `com.chora.fleet-status`: a **5-minute beat** plus eager
  `WatchPaths` on each bench's real branch-ref (commits move
  `refs/heads/<branch>`, not `HEAD`; MEF's is `multi-model`). No server,
  no third party, no new memory — just a drum so the glass refreshes
  without anyone remembering.
- Found and fixed on first boot: the publisher crashed under launchd's
  minimal PATH (`datetime.UTC` needs python ≥3.11; /usr/bin is 3.9).
  Now `timezone.utc`, verified under the system interpreter.

Net "real-time" budget, stated so no one oversells it: bench commit →
glass ≈ seconds (watch) or ≤5 min (beat); GitHub Pages rebuild ≤ ~1 min;
viewer audit per page load. Anything faster would require the thing we
deliberately do not have.

— the chair. Grading the input, for the record: architecture C+ (a generic
three-option list, Gitee/Spring/RabbitMQ notwithstanding its irrelevance
here); prompt value B+ (its blind spot *caused* the publisher). 设想5 got a
bench; this got a heartbeat. Qwen's suggestions keep paying rent in
unintended rent.
