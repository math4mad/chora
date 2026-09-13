#!/usr/bin/env python3
"""
Isospectrality audit — queue item 4 of Letter 016's two-machine day.

Registered ask (Letter 005 action row -> Letter 014 triage -> Meeting 003 R3):
    "MEF: check near-isospectrality against your own sigma-scales; nothing is
     cited externally on Qwen's word alone."  --  R3: 设想3's near-isospectrality
    stays UNVERIFIED INTERNAL HEARSAY until measured against MEF's own sigmas.

What this rig produces, and nothing more:
  (A) the exact sigma-spectra of all 24 `mlp.down_proj.weight` of Qwen2.5-0.5B,
      read from hash-verified bytes (law 2: verify before consume), with the
      scale functionals a citation would need (sigma_max, stable rank, effective
      rank, tail energy E(r) at the ranks this programme actually trains);
  (B) "MEF's own sigma-scales": the same functionals on this bench's own
      `blocks.*.down.weight`, at every rung of its own base ladder (stage18,
      run-on m1-16g), plus the measurable form of the isospectrality question:
      for a rung-to-rung movement dW = W_k2 - W_k1,
          I = ||d sigma||_2 / ||d W||_F        (Weyl/Mirsky: 0 <= I <= 1)
      I ~ 1  => the movement lives in spectrum POSITION;
      I << 1 => the movement lives in DIRECTIONS (near-isospectral adaptation);
  (C) an explicit statement of which arm of 设想3 is NOT checkable with the
      bytes the record holds, so that no future hand mistakes (A)+(B) for a
      verification of a claim about RL and SFT on Qwen.

No hypothesis is added here and no band is invented: there is no registered
threshold for I, so this file reports a table and refuses a verdict in C.
Weights never enter git (law 3): every input is named by (path, sha256) in
models/manifest.json or by the run jsons that pin the ladder.
"""

import hashlib
import json
import os
import socket
import struct
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
MODEL = os.path.join(
    ROOT, "models/models/Qwen--Qwen2.5-0.5B/snapshots/master/model.safetensors"
)
MODEL_PIN_PATH = "models/models/Qwen--Qwen2.5-0.5B/snapshots/master/model.safetensors"
MODELS_MANIFEST = os.path.join(ROOT, "models/manifest.json")
MEF_OUT = os.path.join(ROOT, os.pardir, "Middle-Eigen-function/outputs")
LADDERS = {
    "B_seed14": "stage18_seed14",
    "B_seed13_twinB": "stage18_twinB",
}
RUNGS = [0, 25, 50, 75, 100]
RANKS_OF_INTEREST = [1, 2, 4, 8, 16, 32, 64]


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def pin_of(manifest_path, rel):
    m = json.load(open(manifest_path))
    for e in m.get("files", m):
        if e.get("path") == rel:
            return e
    return None


def verify_before_consume():
    """Law 2: the operand's hash is checked, and its size, before a single float is read."""
    entry = pin_of(MODELS_MANIFEST, MODEL_PIN_PATH)
    if entry is None:
        raise SystemExit("STOP: no manifest entry names the operand at all")
    on_disk = os.path.getsize(MODEL)
    digest = sha256_file(MODEL)
    ok = digest == entry["sha256"] and on_disk == entry.get("bytes")
    return {
        "pin_sha256": entry["sha256"],
        "pin_bytes": entry.get("bytes"),
        "disk_sha256": digest,
        "disk_bytes": on_disk,
        "verified": bool(ok),
        "by": entry.get("by"),
    }


def safetensors_header(fh):
    fh.seek(0)
    (n,) = struct.unpack("<Q", fh.read(8))
    hdr = json.loads(fh.read(n))
    hdr["_header_len"] = 8 + n
    return hdr


def read_bf16_tensor(mm, header_len, meta, shape):
    """BF16 -> FP32 is EXACT (append 16 zero bits to the mantissa field). No precision is
    invented by the reader, so the sigma-spectrum is the file's, not numpy's."""
    off0, off1 = meta["data_offsets"]
    assert meta["dtype"] == "BF16", meta["dtype"]
    nelem = int(np.prod(shape))
    assert off1 - off0 == nelem * 2, (off1 - off0, nelem)
    raw = np.frombuffer(mm, dtype=np.uint16, count=nelem, offset=header_len + off0)
    return (raw.astype(np.uint32) << 16).view(np.float32).reshape(shape).copy()


def functionals(sigma, W=None):
    s = np.sort(sigma)[::-1]
    total_energy = float(np.sum(s**2))
    p1 = s / s.sum()
    return {
        "n_sigma": int(s.size),
        "sigma_max": float(s[0]),
        "sigma_min": float(s[-1]),
        "condition_number": float(s[0] / s[-1]) if s[-1] > 0 else None,
        "frobenius": float(np.sqrt(total_energy)),
        "stable_rank": float(total_energy / s[0] ** 2),
        "effective_rank_entropy": float(np.exp(-(p1 * np.log(p1)).sum())),
        "l1_over_l2": float(s.sum() / np.sqrt(total_energy)),
        "energy_top1": float(s[0] ** 2 / total_energy),
        "tail_energy_beyond_rank": {
            str(r): float(np.sum(s[r:] ** 2) / total_energy)
            for r in RANKS_OF_INTEREST
            if r < s.size
        },
        "sigma_deciles": [float(s[int(i * (s.size - 1) / 10)]) for i in range(11)],
        "sigma_full": [float(v) for v in s],
    }


NULL_SEED = 20260913


def isospectrality(W1, W2):
    """The measurable form of 'does adaptation move spectrum position or direction'.

    I = ||d sigma||_2 / ||d W||_F  is bounded by the Mirsky / Hoffman-Wielandt inequality
    (sum_i (s_i(A)-s_i(B))^2 <= ||A-B||_F^2), so I <= 1 identically. The first draft of this
    rig tested the WRONG inequality -- ||d sigma||_2 <= ||d W||_2 -- and printed
    weyl_bound_respected: false on 34 of 40 rows. That bound is simply not true: for
    dW = eps * I on a square matrix, d sigma = (eps,...,eps) has 2-norm eps*sqrt(n) against a
    spectral norm of eps. The false alarm was the instrument's, not the matrices'. Both real
    bounds are checked separately below and both must hold.

    I is reported against a Gaussian null: dW_g = g * ||dW||_F with g iid N(0,1) rescaled to the
    same Frobenius norm. Without it, I = 0.46 is a number with no ruler; the null is the value a
    perturbation that respects nothing about the base's directions would take.
    """
    s1, s2 = np.linalg.svd(W1, compute_uv=False), np.linalg.svd(W2, compute_uv=False)
    s1, s2 = np.sort(s1)[::-1], np.sort(s2)[::-1]
    dW = W2 - W1
    sdW = np.sort(np.linalg.svd(dW, compute_uv=False))[::-1]
    nrm_dW_F = float(np.linalg.norm(dW))
    nrm_dW_2 = float(sdW[0])
    ds = s2 - s1
    ratio = float(np.linalg.norm(ds) / nrm_dW_F) if nrm_dW_F else float("nan")
    rng = np.random.default_rng(NULL_SEED)
    g = rng.standard_normal(dW.shape).astype(np.float32)
    g *= nrm_dW_F / float(np.linalg.norm(g))
    sg = np.sort(np.linalg.svd(W1 + g, compute_uv=False))[::-1]
    return {
        "dW_frobenius": nrm_dW_F,
        "dW_sigma_max": nrm_dW_2,
        "dW_stable_rank": float(np.sum(sdW**2) / sdW[0] ** 2),
        "dW_sigma_top8": [float(v) for v in sdW[:8]],
        "base_frobenius": float(np.linalg.norm(W1)),
        "rel_movement_of_matrix": float(nrm_dW_F / np.linalg.norm(W1)),
        "rel_movement_of_spectrum": float(np.linalg.norm(ds) / np.linalg.norm(s1)),
        "isospectrality_index_I": ratio,
        "null_I_gaussian_same_frobenius": float(np.linalg.norm(sg - s1) / nrm_dW_F)
        if nrm_dW_F
        else float("nan"),
        "mirsky_I_le_1_holds": bool(np.linalg.norm(ds) <= nrm_dW_F + 1e-6),
        "weyl_linf_holds": bool(np.max(np.abs(ds)) <= nrm_dW_2 + 1e-6),
        "null_seed": NULL_SEED,
    }


def meta():
    import platform

    try:
        import torch

        tv, mp = torch.__version__, bool(torch.backends.mps.is_available())
    except Exception:
        tv, mp = None, None
    try:
        blas = np.__config__.show(mode="dicts")["blas"]
    except Exception:
        blas = {}
    return {
        "host": socket.gethostname(),
        "machine": "m1-16g (machine B)",
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "torch": tv,
        "mps_available": mp,
        "blas": {k: blas.get(k) for k in ("name", "version")},
        "platform": platform.platform(),
        "svd_backend": "numpy.linalg.svdvals/svd -> LAPACK gesdd (CPU, float32)",
        "run_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def part_a():
    ver = verify_before_consume()
    if not ver["verified"]:
        raise SystemExit("STOP: operand hash does not match its pin — %s" % json.dumps(ver))
    fh = open(MODEL, "rb")
    hdr = safetensors_header(fh)
    keys = sorted(
        (k for k in hdr if k.endswith("mlp.down_proj.weight")),
        key=lambda k: int(k.split(".")[2]),
    )
    import mmap

    mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
    layers, t0 = {}, time.time()
    for k in keys:
        shape = tuple(hdr[k]["shape"])
        W = read_bf16_tensor(mm, hdr["_header_len"], hdr[k], shape)
        f = functionals(np.linalg.svd(W, compute_uv=False))
        f["shape"], f["key"], f["dtype_in_file"] = list(shape), k, hdr[k]["dtype"]
        f["sha256_of_tensor_bytes"] = hashlib.sha256(
            W.astype(np.float32).tobytes()
        ).hexdigest()
        layers[k] = f
        print(
            "  %-38s sig=%.4e  srank=%.1f  erank=%.1f  E(16)=%.4f"
            % (k, f["sigma_max"], f["stable_rank"], f["effective_rank_entropy"],
               f["tail_energy_beyond_rank"]["16"]),
            flush=True,
        )
    # determinism of the instrument on this machine: the same SVD twice
    again = np.linalg.svd(
        read_bf16_tensor(mm, hdr["_header_len"], hdr[keys[0]], tuple(hdr[keys[0]]["shape"])),
        compute_uv=False,
    )
    # sigma_full is stored DESCENDING by functionals(); the first draft reversed it before
    # comparing, so run 1 reported max|ds| = 3.625 as if LAPACK were nondeterministic. That number
    # is exactly sigma_max - sigma_min of layer 0 (3.8228 - 0.197): the rig was comparing a
    # descending spectrum to an ascending one, and the "nondeterminism" was its own sort order.
    # Third instrument defect found in this file before any byte crossed. Fixed, and disclosed.
    first = np.array(layers[keys[0]]["sigma_full"])
    ordered_again = np.sort(again)[::-1]
    determinism = {
        "repeat_same_tensor_svd_max_abs_ds": float(np.max(np.abs(ordered_again - first))),
        "n_repeats": 2,
        "note": "0.0 expected: same process, same bytes, same backend. The cold-process check is "
                "the artifact-hash comparison reported in the letter, not this line.",
    }
    mm.close()
    fh.close()
    return {
        "operand_verified_before_consumption": ver,
        "n_matrices": len(layers),
        "layers": layers,
        "aggregate": {
            "sigma_max_min_over_layers": [
                float(min(v["sigma_max"] for v in layers.values())),
                float(max(v["sigma_max"] for v in layers.values())),
            ],
            "stable_rank_range": [
                float(min(v["stable_rank"] for v in layers.values())),
                float(max(v["stable_rank"] for v in layers.values())),
            ],
            "tail_energy_rank16_range": [
                float(min(v["tail_energy_beyond_rank"]["16"] for v in layers.values())),
                float(max(v["tail_energy_beyond_rank"]["16"] for v in layers.values())),
            ],
        },
        "instrument_determinism": determinism,
        "wall_clock_s": round(time.time() - t0, 2),
    }


def part_b():
    import torch

    out, t0 = {}, time.time()
    for label, dirname in LADDERS.items():
        d = os.path.abspath(os.path.join(MEF_OUT, dirname))
        if not os.path.isdir(d):
            out[label] = {"absent": d}
            continue
        rungs = {}
        for k in RUNGS:
            p = os.path.join(d, "ckpt_k%d.pt" % k)
            if not os.path.exists(p):
                continue
            rungs[k] = {
                "path": os.path.relpath(p, ROOT),
                "sha256": sha256_file(p),
                "bytes": os.path.getsize(p),
                "sd": torch.load(p, map_location="cpu", weights_only=True),
            }
        if not rungs:
            out[label] = {"absent": "no ckpt_k*.pt under %s" % d}
            continue
        ks = sorted(rungs)
        shapes = {
            t: tuple(rungs[ks[0]]["sd"][t].shape)
            for t in sorted(rungs[ks[0]]["sd"])
            if t.endswith("down.weight")
        }
        layers = {}
        for t in shapes:
            per = {}
            for k in ks:
                W = rungs[k]["sd"][t].detach().numpy().astype(np.float32)
                per[k] = (W, functionals(np.linalg.svd(W, compute_uv=False)))
            entry = {
                "shape": list(shapes[t]),
                "sigma_by_rung": {str(k): v[1]["sigma_full"] for k, v in per.items()},
                "functionals_by_rung": {
                    str(k): {kk: vv for kk, vv in v[1].items() if kk != "sigma_full"}
                    for k, v in per.items()
                },
            }
            pairs = []
            for a, b in zip(ks, ks[1:]):
                pairs.append(
                    {"rungs": [a, b], **isospectrality(per[a][0], per[b][0])}
                )
            pairs.append({"rungs": [ks[0], ks[-1]], **isospectrality(per[ks[0]][0], per[ks[-1]][0])})
            entry["consecutive_and_full_range"] = pairs
            layers[t] = entry
        out[label] = {
            "rungs_present": ks,
            "checkpoint_hashes": {
                str(k): {"sha256": rungs[k]["sha256"], "bytes": rungs[k]["bytes"],
                         "path": rungs[k]["path"]}
                for k in rungs
            },
            "n_down_matrices": len(shapes),
            "layers": layers,
            "wall_clock_s": round(time.time() - t0, 2),
        }
    return out


def part_c(a, b):
    idx = []
    for label, lad in b.items():
        for t, lay in (lad.get("layers") or {}).items():
            for p in lay["consecutive_and_full_range"]:
                idx.append((p["isospectrality_index_I"], p["null_I_gaussian_same_frobenius"]))
    return {
        "设想3_as_registered": "RL moves U,V at ~1e-4 while Sigma holds; SFT shifts Sigma ~35% "
                        "(Letter 014 triage item 2, quoting an unverified external report)",
        "what_this_audit_checks": "(A) the 0.5B's own down_proj sigma-scales as the reference the "
                        "Anatomist demanded; (B) whether adaptation in MEF's OWN from-scratch rig "
                        "moves spectrum position or directions, indexed by I = ||d sigma||_2 / ||dW||_F",
        "what_this_audit_does_NOT_check": "the external claim itself. No RL- or SFT-adapted "
                        "Qwen2.5-0.5B checkpoint exists in models/manifest.json or on either "
                        "machine's disk: the manifest pins the BASE snapshot only, and the ladder "
                        "in (B) is continued pretraining on a 1.6M-param from-scratch Qwen2-arch "
                        "byte-LM, not an RL or SFT run on Qwen. So R3's verdict stands unchanged: "
                        "unverified internal hearsay, with the sigma-scale citation now available.",
        "I_summary": {
            "n_pairs": len(idx),
            "observed_min": float(min(x[0] for x in idx)) if idx else None,
            "observed_median": float(np.median([x[0] for x in idx])) if idx else None,
            "observed_max": float(max(x[0] for x in idx)) if idx else None,
            "gaussian_null_min": float(min(x[1] for x in idx)) if idx else None,
            "gaussian_null_median": float(np.median([x[1] for x in idx])) if idx else None,
            "gaussian_null_max": float(max(x[1] for x in idx)) if idx else None,
            "rows_where_observed_exceeds_null": int(
                sum(1 for o, n in idx if o > n)) if idx else None,
            "bounds_respected_on_all_rows": bool(
                all(p["mirsky_I_le_1_holds"] and p["weyl_linf_holds"]
                    for lad in b.values() for lay in (lad.get("layers") or {}).values()
                    for p in lay["consecutive_and_full_range"])),
        },
        "no_verdict_is_registered_for_I": "there is no band, no threshold and no pre-written "
                        "obituary for I in any committed PREREG; these are numbers, not a finding "
                        "about 设想3. Any later use as one is a new check and must say so.",
    }


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "artifacts/spectra/iso_audit_down_proj_B.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print("[iso] verifying the operand before consuming it ...", flush=True)
    a = part_a()
    print("[iso] own sigma-scales: the stage18 ladders on this laptop ...", flush=True)
    b = part_b()
    doc = {
        "kind": "isospectrality audit (queue item 4, Letter 016 two-machine day)",
        "protocol": "Letter 005 action row -> Letter 014 triage item 2 -> Meeting 003 R3",
        "registered_in": "chora:meetings/2026-09-11-003-lora-critical-windows.md R3 + "
                         "letters/2026-09-11-chair-all-two-machine-day.md queue row 4",
        "exploratory": False,
        "ordering_disclosure": "The first execution of this rig (2026-09-13, ~12:3x local) printed "
            "the observed I values with NO null control attached; max 0.8996 / median 0.4647 / "
            "min 0.2822 over 40 rows, and the same run flagged weyl_bound_respected: false on 34 "
            "of them. Both defects were fixed before any byte crossed: the bound was the rig's "
            "error (it tested ||d sigma||_2 <= ||d W||_2, which is false for dW = eps*I; the real "
            "bounds are Mirsky in Frobenius and Weyl in l_inf, checked separately), and the null "
            "was added because a bare I has no ruler. The null is therefore NOT a control chosen "
            "after seeing where it would land -- it is a fixed iid-Gaussian, matched-Frobenius "
            "construction, and this paragraph exists so no future hand has to reconstruct the "
            "sequence from commit dates. A THIRD defect in the same file, same session: the "
            "cold-process determinism self-check printed max|ds| = 3.625, which is not LAPACK "
            "being noisy but this rig comparing a descending spectrum against an ascending one "
            "(sigma_max - sigma_min of layer 0 = 3.8228 - 0.197 = 3.625); it now compares like "
            "with like and reads 0.0. All three alarms were false in the same direction: the "
            "instrument crying structure, or noise, that its own arithmetic invented. "
            "The index I itself is B's operationalisation of the "
            "registered question, written in this file's docstring before the first SVD ran; no "
            "threshold on I is claimed anywhere, and R3 is not lifted by it.",
        "run_on": "m1-16g",
        "meta": meta(),
        "A_qwen0p5B_down_proj": a,
        "B_mef_own_sigma_scales": b,
        "C_scope": part_c(a, b),
    }
    with open(out_path, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write("\n")
    print("[iso] wrote", out_path, os.path.getsize(out_path), "B")
    print("[iso] I index: %s" % json.dumps(doc["C_scope"]["I_summary"]))


if __name__ == "__main__":
    main()
