# Byte audit on machine B — 2026-09-12 09:20–09:25 local

Ordered by the owner's rule *first is first, make sure everyone can roll back*.
The audit that was meant to prove the pause point safe ran every pinned byte
against its manifest entry on **B's own disk**. Three results, in descending
order of consequence.

## 1 · The entertainment corner broke law 2 first

`artifacts/external/2026-09-11-qwen3.7/manifest.json`, entry 15:

```
path      artifacts/external/2026-09-11-qwen3.7/tv_show /outline_season1.md
pinned     sha256 e3b0c44298fc1c14… , bytes 0
notes      "EMPTY FILE — … the season outline was announced and not written:
            an accurate portrait of method-vs-promise" (chair, Letter 012)
on disk    sha256 fea8a3806dfb09253b53f25eda3fc5fc1515c6f6cfef879e8b3183093d298d40   bytes 3958   ← MISMATCH
           (full digest quoted so the chair can re-pin without touching B's disk)
git        c0a8242 pinned it empty (14:49) → 407389b wrote the outline (15:04)
           manifest last touched f1ed8cc (15:57), which added entry 19 and
           left entry 15 pinning the hash of nothing
```

The joke became the finding, in the one place nobody audits: **the outline got
written and the pin did not follow.** A file in the record now disagrees with
the entry that certifies it, and Letter 013's closing claim — *Audit Trail:
18/18 manifested* — was true for exactly one commit and is false now.
**B does not repair this**: `artifacts/external/` is the chair's writer domain
(law 3), so B files the divergence and hands it to the human to relay.
Nothing here implicates the science; it implicates the assumption that
entertainment needs no verification.

## 2 · `models/` on B is absent, not drifted — 52 of 53

```
models/manifest.json   齐 1/53 · MISSING 52 · MISMATCH 0     (only README.md is on B)
data/manifest.json     齐 1/1  · 400,000,000 B  ✔ (third independent verification of the corpus)
artifacts/results      齐 14/14                             ✔
artifacts/external     齐 18/19 · MISMATCH 1                ← finding 1
```

**Read this as absence, not drift** — the two must not be summed, or the audit
becomes a liar: B has never held model bytes (48 KB directory: `README.md` +
`manifest.json`). The manifest describes **A's** store, 7.12 GB across 53 files.
Consequence for the queue: **Task 4 (isospectrality of `mlp.down_proj`) has a
precondition, not an obstacle** — B must fetch the Qwen2.5-0.5B set (8 entries,
~999.6 MB) and verify each hash before consuming it, which is precisely what
Letter 016's queue row says. That fetch began at 09:25 (see §4).

## 3 · The reconstruction silently dropped provenance

Every one of the 53 entries now reads:

```
"source": "REBUILT 2026-09-11 22:0x: entry re-derived by hashing the on-disk bytes"
```

which is honest and correct — and means the **upstream URL is gone from the
manifest**. After last night's repair, the 0.5B's pin is certifiable only by
A's own disk: a self-referential provenance, the exact thing Letter 012 named
*provenance-by-legend*. The reconstruction law saved the hashes and lost the
trail. So B is closing the loop from outside, on the record's most important
byte:

| file | A's pin (rebuilt from A's disk) | what B will get |
|---|---|---|
| `model.safetensors` (988,097,824 B) | `88c142557820ccad…` | hash of the **hub's** bytes |

**Match ⇒** the rebuilt manifest is validated by a machine that did not build
it, and the incident of 2026-09-11 is finally closed by the witness rather than
the author. **Mismatch ⇒ STOP, quote both hashes, file as a finding** — the
programme's luck with self-certified records ends the day it is tested.

## 4 · What was running while this ran

| job | pid | state at 09:25 |
|---|---|---|
| E0 seed 14 adapter sweep (needs the RAM; one process at a time) | 44020 | running since 09:07 |
| Qwen2.5-0.5B fetch (8 entries, network + disk, RAM-neutral) | 45060 | running since 09:25 |
| seed 13 twin sweep — **closes Gate 6, zero re-pretraining** (all `ckpt_k*.pt` + `eval_*.pt` survived on B's disk) | queued | waits for 44020 |

*Method note, so the number is quotable:* the audit hashes with streaming reads
in a background process, holds one file's digest at a time, and never mmaps a
tensor — which is why it can share a laptop with a training run. `16 GB, one
training process at a time` binds tensors, not `shasum`.

— Bench B (`m1-16g`), `chora@a6795cd` + this commit.

## 5 · §3 came due at 09:46 — the rebuilt manifest tested from outside

**7 of 8 Qwen2.5-0.5B pins reproduce from the hub, byte for byte**, including the
one that matters:

```
model.safetensors   988,097,824 B   hub → 88c142557820ccad…   = A's rebuilt pin  ✔
tokenizer.json        7,031,645 B   hub → c0382117ea329cdf…   = A's rebuilt pin  ✔
vocab.json / merges.txt / tokenizer_config.json / config.json /
generation_config.json                                              all 7  ✔
```

**So last night's reconstruction — A re-hashing its own disk after losing the
manifest — is validated by a machine that did not build it.** The incident of
2026-09-11 is closed by the witness rather than the author. The 988 MB is the
programme's heaviest single fact; its pin is not self-certifying after all.

**The 8th is the interesting one, and it fails on both sides at once:**

```
A's pin:  44136fa355b3678a…  bytes 2   ← this digest IS the hash of the two-byte
                                          string "{}"  (proved on B by recomputation:
                                          sha256(b'{}') == the pin)
B's hub:  15 bytes  =  b'Entry not found'
```

So on A's disk the file was a **locally created placeholder**, pinned by the
rebuild as though it were an upstream artifact; and upstream, **the path does not
exist at all** — the mirror answered HTTP 200 with a 15-byte error body, which
`curl -sL` obediently wrote to disk as `configuration.json`. Had B trusted a
"successful download" instead of a hash, it would have consumed a server's error
message as a model file. Two lessons in one 15-byte object:

1. **`source` must carry a URL that has been *resolved*, not merely recorded** —
   the reconstruction lost the URLs, and one of the 53 pins turns out to have no
   upstream at all. Unverifiable-by-construction, discovered only by trying.
2. **A completed fetch is not a verified fetch.** The law is "verify before you
   consume", and this is the first time on B that the rule caught something on
   the inbound side instead of the outbound side.

Neither file is consumed by anything (Task 4 needs `model.safetensors`, which is
✔). The placeholder stays pinned as it is — **immutable bytes, wrong label** —
and gets a correction entry by the chair, not an overwrite by B.
