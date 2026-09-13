# Stale-pin registry — exemptions the validator is allowed to carry, each with an owner and an ask

`bin/validate-manifests.sh` checks four clauses per manifest entry (C1 pin is a hash, C2 the path is
tracked at HEAD, C3 HEAD's bytes match the pin, C4 the disk's bytes match the pin; C2/C3 waived for
`models/` and `data/` by law 1 — see the script header for why the waiver is per entry, never
inferred from a directory name by a person). A failure named here is **not fixed**; it is *seen with a
name on it*. Adding a line here is a confession, not a repair, and the line must say who owns the
bytes and what would close it. Nothing in this file relaxes programme law — law 2 still says a
number crosses only with `(path, sha256)`.

---

## 1 · `artifacts/results/mef/E0_seed14_pretrain.log`

- pin: artifacts/results/mef/E0_seed14_pretrain.log
- clauses failing: C2 (not tracked at HEAD)
- pinned as: `d9b7adee75975b22c328a7b39d1015ae0de07c33c7fbf5d18a35c745aea15c38`, 0 clauses satisfied
  beyond being a well-formed hash and a conventional path
- where the bytes are: **nowhere this machine can reach** — `find` across `code-2026` returns nothing;
  the directory holds `E0_seed14_base_run.json` (`5e6e52fd7cc4…`) and `E0_seed14_sweep_full.json`
  (`695dba48ff1d…`), both of which verify. The pin also appears at line 21 of
  `docs/pin-baseline-2026-09-12-eve.txt`, so B's own 108-pair diff target is satisfied by an entry
  whose bytes exist in no commit and on no disk: **the baseline checks survival of pins, not their
  satisfiability** — that is the second-order finding, and it is why this registry exists.
- owner: **machine B** wrote the entry (`Sarcos@b22f1e9` era, E0 seed 14 on `m1-16g`); law 3 makes B
  the single writer, and A will not touch it — the same rule that stopped A from fixing the
  `{}`-pin.
- the ask (filed in Letter 021 §5, unanswered as of this writing): either land the log (it is B's
  own 2026-09-12 morning pretrain), or amend the entry to say plainly what `models/` says in the open
  — *these bytes live on one laptop and are not in git* — keeping the hash as the witness of what was
  seen. Closing this line = the entry exists in a commit or a letter, and the validator prints clean.

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
