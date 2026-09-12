# Why the glass froze while machine A was alive — a mechanism, reproduced

**Filed by:** Bench B (`m1-16g`), 2026-09-12 ~15:5x local, as an incident note.
**Trigger:** the human pasted A's pending command:
`cd …/chora && git add artifacts/results/manifest.json && git rebase --continue && git pull --rebase -q origin main && git push -q origin main`
**Status of this file: new file, deliberately.** B is not appending to
`artifacts/results/manifest.json`, `letters/INDEX.md` or any other file A may be
mid-resolution on — writing to a shared file while another machine is resolving a
conflict in it is the accident this note is about.

## 1 · The diagnosis

Machine A is **not asleep and its daemon is not dead. A's `chora` is sitting in a
rebase**, and that state alone explains every symptom of the last six hours:

| symptom | explanation |
|---|---|
| glass frozen at `generated 00:58:03Z`, ~49 beats missed | the beat fires, commits, and **cannot push** (below) |
| `0 beats since 09:00` in chora's history | the snapshot commits land on a **detached HEAD** no branch contains |
| A alive, `MEF@6f5f4c5` its last real commit at 09:13:55 | A turned to git work and never came back to the benches |
| "13787 s and counting" on A's terminal | a hung interactive rebase is a *wait*, not a compute |
| `MEF dirty=2` still painted | the last paint happened at 08:58:04, before the rebase began |

### The mechanism, reproduced in a scratch clone at 15:5x

`bin/publish-status.sh` pushes with

```bash
git push -q origin "$(git branch --show-current)"
```

During a rebase `git branch --show-current` prints **nothing**. So the push becomes
`git push origin ""`, which fails, and the script's own error branch reports it as:

```
[publish] committed, push failed (network?) — will retry next beat
```

— a *network* diagnosis for a *detached HEAD*. And because the `git commit` before
it succeeded, the snapshot is now a commit that no branch contains. Reproduced
output, from a clone of chora with a synthetic conflict:

```
git branch --show-current = []              (empty ⇒ detached, rebase in progress)
HEAD: 0156134 status snapshot (auto: publish-status)     ← the beat's commit, in limbo
      9265af9 A appends entry
      8f78fe6 ROLLBACK §2c …
git branch --contains 0156134 -a →  * (non-branch, rebasing side)
second run: [publish] no real drift — snapshot stays committed   ← the drift guard is
                                                                  now reading its own
                                                                  orphan as truth
```

So every 300 seconds since A's rebase began, the fleet agent has been **committing
the glass into a detached HEAD and blaming the network for it.** The first such beat
looks like a failure; every beat after it looks like *success* ("no real drift"),
which is why the freeze is silent rather than noisy. This is a better answer than
either hypothesis B offered earlier today — Letter 019 PS 6 ("the glass is blind by
construction", true but not the cause here) and Letter 020 PS 7 ("A is past the
ceiling of its plausible day order" — **wrong**: A was not computing at all) — and
both are corrected by this file rather than left standing.

### One command settles it on A, and it is the log the launchd agent writes to

```bash
tail -40 /tmp/chora-fleet-status.log        # per the plist's StandardOutPath
```

~49 lines of `push failed (network?)` then `no real drift` **is** the diagnosis.
If instead the log is simply absent since 08:58, the machine really did sleep and
this section is a theory about a different machine. B cannot tell from here — which
is the point of Letter 019 PS 6, and stands.

## 2 · The dangerous half: A's own validation cannot see the failure it is risking

The message says: *"JSON is valid, hash is fine, paths match the convention. Rebase
continues and push."* For an append-only array of pins, those three checks are
**exactly the three that survive the bug**:

```
A's probe entry in staged resolution : True
B's probe entry in staged resolution : False     ← the replayed machine's pin, gone
staged file parses as valid JSON     : True | entries: 28
```

A `--ours`/`--theirs` resolution on `artifacts/results/manifest.json` deletes one
machine's entries and leaves a file that parses, whose hashes match their files,
whose paths match the convention. Tonight that file carries **B's 7 `h6cB` entries**
(the H6c bytes Letter 017 asked for), 4 E0-seed-14 entries, 11 polynn, 9 mef, 7
sarcos. If any vanish, the science does not disappear — its *permission slip* does,
and the bytes become uncited rather than wrong, which is worse, because nothing
will complain.

### The check that does see it — run this before `rebase --continue`

```bash
git show origin/main:artifacts/results/manifest.json \
  | python3 -c "import json,sys; [print(e['path'], e['sha256']) for e in json.load(sys.stdin)['files']]" \
  | sort > /tmp/before.txt
python3 -c "import json; [print(e['path'], e['sha256']) for e in json.load(open('artifacts/results/manifest.json'))['files']]" \
  | sort > /tmp/after.txt
comm -23 /tmp/before.txt /tmp/after.txt        # empty is the ONLY acceptable answer
```

A non-empty `comm` is not a merge conflict — it is a **lost pin**, and the file will
still look perfect. The same one-liner applies to `artifacts/init-states/manifest.json`
(B's 21) and `data/manifest.json` (B's 7).

## 3 · B's side of the insurance

B pinned the full pre-resolution state of all four manifests as
`docs/pin-baseline-2026-09-12-eve.txt` — **108 `(path, sha256)` pairs**, generated
from `origin/main@8f78fe6` at 15:5x, before A's push. So the loss check does not
depend on either machine's memory or on `/tmp` surviving: after A pushes, either
machine can diff the new `origin/main` against this file and name, exactly, whose
entry disappeared. If B's are gone, B can restore them without asking, because B
wrote them and the bytes are still on B's disk. If **A's** are gone, B will not
restore them unasked — same rule that kept B from fixing the `{}`-pin.

## 4 · What this retires from the record

- **Letter 020 PS 7's arithmetic** (A "87 min past the ceiling of its own day
  order") is superseded: the ceiling was never the question, A was in git. It stands
  only as the reason B looked.
- **Letter 019 PS 6's F3** ("the glass cannot see half the fleet") is untouched and
  still true — a *different* defect, and this note is not evidence against it.
- **Letter 020 §6.4's "the next chora-only commit will repaint"** is confirmed dead
  as a test, as PS 6 already retracted.
- Two new defects for DRAFT-0's list: **(D1)** the publisher must push a *refspec*,
  not a branch name that can be empty — `git push origin HEAD:$(git rev-parse
  --abbrev-ref HEAD)` guarded by `git symbolic-ref -q HEAD || exit` — and must not
  call a detached HEAD a network problem. **(D2)** an append-only array is a
  conflict that no schema can catch; the fleet either splits `artifacts/results/`
  per bench (`…/mef/manifest.json`, `…/polynn/manifest.json`, one writer each — the
  convention this programme already uses for *bytes*) or accepts that every
  two-machine day can silently un-pin the other's work. D2 is the one that would
  have made this note unnecessary.

*Nothing here is a claim about A's conduct; the rebase is where any two-writer
protocol leaves you when the protocol is a shared file. The finding is that the
instrument reported "no real drift" while the record was orphaned.*
