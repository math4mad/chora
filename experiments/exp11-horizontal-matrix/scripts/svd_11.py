#!/usr/bin/env python3
# exp10f · cross-domain orthogonality recheck — all pairwise geometries over six arms.
# Registered in PREREG Addendum 4: H6 = specialist×specialist cross pairs all near-orthogonal
# in write geometry (ΔWov < 0.2 band), with the mid~parent pairs (0.62–0.66) as the positive
# interpolation anchor proving the metric CAN light up. Deviation: 40-pair corpora.
import json, os, itertools
import numpy as np
from safetensors.numpy import load_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
ARMS = [a for a in os.environ.get("EXP11_ARMS","spring,summer,code,general").split(",")]
SPECIALISTS = [a for a in ARMS if a != "mid"]


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


def main():
    S = {a: {k: np.linalg.svd(M, full_matrices=False) for k, M in mats(f"adapter_{a}").items()} for a in ARMS}
    layers = sorted({k[0] for k in S["spring"]})
    keys = list(itertools.product(layers, MODS))
    res = {}
    for a1, a2 in itertools.combinations(ARMS, 2):
        va = ub = 0.0
        for L, mod in keys:
            _, s1, V1 = S[a1][(L, mod, "A")]; _, _, V2 = S[a2][(L, mod, "A")]
            k = k90(s1)
            va += float(np.linalg.norm(V1[:k] @ V2[:k].T, "fro"))
            U1 = S[a1][(L, mod, "B")][0]; U2 = S[a2][(L, mod, "B")][0]
            ub += float(np.linalg.norm(U1[:, :k].T @ U2[:, :k], "fro"))
        def dw(a):
            parts = []
            for L, mod in keys:
                U, s, Vt = S[a][(L, mod, "A")]; W, b, X = S[a][(L, mod, "B")]
                parts.append(((W * b) @ X @ ((U * s) @ Vt)).ravel())
            return np.concatenate(parts)
        d1, d2 = dw(a1), dw(a2)
        ov = float(d1 @ d2 / (np.linalg.norm(d1) * np.linalg.norm(d2)))
        res[f"{a1}~{a2}"] = {"V-A_k90": round(va / len(keys), 3), "U-B_k90": round(ub / len(keys), 3),
                             "dWov": round(ov, 4)}
    ss = [v["dWov"] for k, v in res.items() if len({*k.split("~")}) and all(x in SPECIALISTS for x in k.split("~"))]
    anchor = [res[k]["dWov"] for k in res if "mid" in k]
    h6 = bool(max(abs(x) for x in ss) < 0.2)
    out = {"pairs": res,
           "H6_specialists_max_abs_dWov": round(max(abs(x) for x in ss), 4),
           "interpolation_anchor_min_dWov": round(min(abs(x) for x in anchor), 4),
           "H6_pass": h6,
           "note": "deviation registered: 40-pair corpora (magnitudes not parity-comparable to 55-pair arms); V-A flatness across all pairs = H6b"}
    json.dump(out, open(os.path.join(ROOT, "results", "report_11_p0.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
