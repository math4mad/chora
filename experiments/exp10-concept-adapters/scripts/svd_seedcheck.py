#!/usr/bin/env python3
# exp10b hardening: does the H4 reversal reproduce across seeds 13/14/15?
# Same metrics as svd_10b (V-A read excess, U-B write, ΔW overlap), per seed.
import json, os, itertools
import numpy as np
from safetensors.numpy import load_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
KS = [1, 2, 4, 8, 16]


def mats(dirname):
    sd = load_file(os.path.join(ROOT, "results", dirname, "adapter_model.safetensors"))
    out = {}
    for k, v in sd.items():
        for kind in ("A", "B"):
            tag = f".lora_{kind}.weight"
            if tag in k:
                L = int(k.split(".layers.")[1].split(".")[0])
                mod = k.split(f".layers.{L}.")[1].split(tag)[0].split(".")[-1]
                out[(L, mod, kind)] = v.astype(np.float64)
    return out


def k90(s):
    e = s ** 2 / (s ** 2).sum()
    return int(np.searchsorted(np.cumsum(e), 0.90) + 1)


def run(seed_sfx, dirs):
    S = {n: {k: np.linalg.svd(M, full_matrices=False) for k, M in mats(d).items()} for n, d in dirs.items()}
    layers = sorted({k[0] for k in S["spring"]})
    keys = list(itertools.product(layers, MODS))
    res = {}
    for a1, a2 in itertools.combinations(dirs, 2):
        va = ub = 0.0
        n = 0
        for L, mod in keys:
            _, sa, Va = S[a1][(L, mod, "A")]; _, _, Vb = S[a2][(L, mod, "A")]
            kk = k90(sa)
            va += float(np.linalg.norm(Va[:kk] @ Vb[:kk].T, "fro"))
            W1 = S[a1][(L, mod, "B")][0]; W2 = S[a2][(L, mod, "B")][0]
            ub += float(np.linalg.norm(W1[:, :kk].T @ W2[:, :kk], "fro"))
            n += 1
        def dw(arm):
            parts = []
            for L, mod in keys:
                Ua, sa, Vta = S[arm][(L, mod, "A")]
                Ub, sb, Vtb = S[arm][(L, mod, "B")]
                A_mat = (Ua * sa) @ Vta
                B_mat = (Ub * sb) @ Vtb
                parts.append((B_mat @ A_mat).ravel())
            return np.concatenate(parts)
        d1, d2 = dw(a1), dw(a2)
        res[f"{a1}~{a2}"] = {"V-A_k90": round(va/n, 3), "U-B_k90": round(ub/n, 3),
                             "dWov": round(float(d1 @ d2 / (np.linalg.norm(d1)*np.linalg.norm(d2))), 4)}
    ss = res["spring~summer"]; sm = res["spring~mid"]; um = res["summer~mid"]
    h4_violated_write = ss["U-B_k90"] < min(sm["U-B_k90"], um["U-B_k90"])   # the reversal, i.e. H4 fails on write side
    return res, bool(h4_violated_write)


def main():
    arms = lambda sfx: {"spring": f"adapter_spring{sfx}", "summer": f"adapter_summer{sfx}", "mid": f"adapter_mid{sfx}"}
    out = {}
    for sfx in ["", "_s14", "_s15"]:
        res, rev = run(sfx, arms(sfx))
        out[f"seed{13 if sfx=='' else sfx.split('_s')[1]}"] = {"pairs": res, "H4_reversal_on_write_side": rev}
        print(json.dumps(out[list(out)[-1]], indent=1))
    json.dump(out, open(os.path.join(ROOT, "results", "report_10b_seeds.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
