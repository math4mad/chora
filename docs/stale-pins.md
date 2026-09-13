# Stale-pin registry — exemptions the validator is allowed to carry, each with an owner and an ask

`bin/validate-manifests.sh` checks four clauses per manifest entry (C1 pin is a hash, C2 the path is
tracked at HEAD, C3 HEAD's bytes match the pin, C4 the disk's bytes match the pin; C2/C3 waived for
`models/` and `data/` by law 1 — see the script header for why the waiver is per entry, never
inferred from a directory name by a person). A failure named here is **not fixed**; it is *seen with a
name on it*. Adding a line here is a confession, not a repair, and the line must say who owns the
bytes and what would close it. Nothing in this file relaxes programme law — law 2 still says a
number crosses only with `(path, sha256)`.

---

## 1 · `artifacts/results/mef/E0_seed14_pretrain.log` — **CLOSED by B, the named owner**

- the pin (written without the `- pin:` marker on purpose — that marker *is* the exemption, and
  §1's own closing clause says an exemption goes away only by editing this file: the exemption is
  **withdrawn**, so a future regression on these bytes prints red again instead of being forgiven by
  a line written on the day they were healthy): `artifacts/results/mef/E0_seed14_pretrain.log`,
  clause failing before this commit: C2 (not tracked at HEAD)
- **closed 2026-09-13 by `git add -f` on machine B.** The bytes were never lost and the pin was never
  wrong: the file sat on B's disk at `artifacts/results/mef/E0_seed14_pretrain.log`, 681 B,
  `sha256 = d9b7adee75975b22c328a7b39d1015ae0de07c33c7fbf5d18a35c745aea15c38` — equal to the pin in
  its last digit, both in the working tree and in the staged blob landed by this commit. C1–C4 now
  pass. The exemption line is deleted from the validator's reach by editing this file, which §1's own
  text named as the only way an exemption ever goes away; the paragraph below stays as the record of
  what the search missed and why.
- **why A's `find` could not see it, in one mechanism:** the pin is machine-B's and so were the bytes;
  nothing about the entry was ever intended to be reachable from `m1pro-32g`. A's
  `find` across `code-2026` returned nothing because A was searching A's disk for B's stdout. The
  entry's own text said the run happened on `m1-16g`; the question "are these bytes in the
  repository?" was never the same question as "do they exist?" — and law 3's single writer is exactly
  the rule that keeps them from being the same question.
- **why B never landed it, in one line:** `~/.gitignore_global:64` carries `*.log`, so the plain
  `git add` that carried the manifest entry silently skipped the log it described. This is the
  `*.log` trap that Letter 020 §8 (chair note) and PS 4 both flagged as *the second time in one day*
  — the fleet's outbound path needs `git add -f` for every `.log`, and `bin/validate-manifests.sh`
  C2 is the first instrument that catches it when the reflex fails. The fix is not a code change;
  it is a `-f` and a check.
- **the finding that outranks the repair:** the pin was true of bytes that existed and false of a
  repository that did not have them, and the validator could not distinguish those two states until
  C2 was written. A's §5 phrase stands — *a presence check that cannot report non-existence* — and
  the mirror image is a non-existence check that cannot report presence elsewhere. The record's
  answer to both is the same: name the machine the bytes live on, in the entry, which this one did
  from the start (`source: machine B (m1-16g), session 2026-09-12`), and read that field before
  reaching for `find`.
- pinned as: `d9b7adee75975b22c328a7b39d1015ae0de07c33c7fbf5d18a35c745aea15c38` — at landing all four
  clauses hold (C1 well-formed hash, C2 tracked at HEAD, C3 HEAD's bytes == pin, C4 disk == pin).
  Before this commit it was 0 clauses satisfied beyond being a well-formed hash and a conventional path.
- historical text retained below, struck through in place rather than deleted (append-only law):
  where the bytes were, per A's search: *"nowhere this machine can reach — `find` across `code-2026`
  returns nothing"* — correct about A, wrong about the programme. The base_run (`5e6e52fd7cc4…`) and
  sweep (`695dba48ff1d…`) siblings did and do verify. The pin also appears at line 21 of
  `docs/pin-baseline-2026-09-12-eve.txt`, and that baseline still passes unchanged: **it checks
  survival of pins, not their satisfiability** — the second-order finding, and the reason this
  registry exists. The baseline is a snapshot and stays one; the satisfiability clause is C2's job.
- owner: **machine B** wrote the entry (`Sarcos@b22f1e9` era, E0 seed 14 on `m1-16g`); law 3 made B
  the single writer, and A did not touch it — the same rule that stopped A from fixing the `{}`-pin.
- the ask (Letter 021 §5): **landed**, first option taken — the log is in git now, hash unchanged,
  and this is the closing letter for the line.

## 2 · the season-1 outline (closed here as precedent, not as an open exemption)

- The empty pin `e3b0c442…` / 0 B (the SHA-256 of *nothing*) with the file written later in `407389b`
  was found by PS 1 on Letter 021 and handled append-only: the empty pin stays as the record, a new
  entry carries `fea8a380…` / 3,958 B. No registry line is needed — C4 now passes — but it is listed
  here because it is the incident that taught the fleet to look.

## 3 · `h6a_pilot_spectra.json` (closed same night; kept as the third hat)

- Pin taken from the working tree while `HEAD` carried the file's previous version: a pin true of the
  checkout and false of the repository. Repaired by `chora@f79d588` (bytes brought up to the pin, no
  line of the append-only array touched). Produced by two agents in one clone with no lock — hence
  the writer lock at `bin/writelock.sh` and the addendum in the root `AGENTS.md`.

## 4 · `artifacts/external/Qwen-suggestion-hover-global/Qwen-Suggestion-about-hover-globe.md`

- pin: artifacts/external/Qwen-suggestion-hover-global/Qwen-Suggestion-about-hover-globe.md
- clause failing: **C5** — the reverse direction: the file is tracked in git and **named by no
  manifest**, so it is a fact nobody can cite (a pin without bytes is a permission slip for nothing;
  bytes without a pin are an uncitable event).
- where the bytes are: on A, committed by a hand other than this one, **modified in the working tree
  at the moment C5 found it** — i.e. in flight. Named rather than fixed: pinning another hand's
  mid-flight file would pin a moving target.
- owner: whoever is working the hover-globe suggestion (the external/Qwen batch, per Letter 005's
  triage practice).
- the ask: `git add` the manifest entry with `(path, sha256, bytes, source: human-delivered, by:,
  notes:)` in the same commit as the content edit — or move it out of `artifacts/` if it is a note
  rather than an input. Closing this line = the entry exists; the exemption is deleted by editing
  this file, which is the only way an exemption here ever goes away.
