#!/usr/bin/env python3
# exp10 · svd_10b.py — Steps 2-5: SVD of the three adapters, subspace similarity vs k,
# H4 verdict, effective ranks, decay curves, invasion bands.
#
# Which subspace is compared (registered here, faithful to the owner doc's ||UᵢᵀUⱼ||_F but
# applied where the vectors actually live in a shared R^d):
#   A-side ("V-A"): right singular vectors of A → READ directions in input space R^{d_in}
#   B-side ("U-B"): left  singular vectors of B → WRITE directions in output space R^{d_out}
#   (the raw U of A / V of B are bases of the shared r=16 rank space — basis rotations,
#    not comparable across adapters; stored as a sanity column only.)
# Null model: random k-flats in R^d → E‖UᵀV‖_F² = k²/d → null = k/√d.
# Basis-invariant cross-check: overlap of ΔW products, ⟨BᵢAᵢ, BⱼAⱼ⟩_F/(‖ΔWᵢ‖‖ΔWⱼ‖).
import json, os, itertools
import numpy as np
from safetensors.numpy import load_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
MODS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
ADAPTERS = {"spring": "adapter_spring", "summer": "adapter_summer", "mid": "adapter_mid"}
KS = [1, 2, 4, 8, 16]


def load_adapter(name):
    sd = load_file(os.path.join(ROOT, "results", ADAPTERS[name], "adapter_model.safetensors"))
    mats = {}
    for k, v in sd.items():
        for kind in ("A", "B"):
            tag = f".lora_{kind}.weight"
            if tag in k:
                L = int(k.split(".layers.")[1].split(".")[0])
                mod = k.split(f".layers.{L}.")[1].split(tag)[0].split(".")[-1]
                mats[(L, mod, kind)] = v.astype(np.float64)
    return mats


def svd_all(mats):
    return {key: np.linalg.svd(M, full_matrices=False) for key, M in mats.items()}


def k90(s):
    e = s ** 2 / (s ** 2).sum()
    return int(np.searchsorted(np.cumsum(e), 0.90) + 1)


def sim_top(B1, B2, k):
    """‖[first k cols of B1]ᵀ [first k cols of B2]‖_F, bases as columns."""
    return float(np.linalg.norm(B1[:, :k].T @ B2[:, :k], "fro"))


def main():
    S = {n: svd_all(load_adapter(n)) for n in ADAPTERS}
    layers = sorted({key[0] for key in S["spring"]})
    table, per_layer = {}, {}
    for a1, a2 in itertools.combinations(ADAPTERS, 2):
        for k in KS + ["k90"]:
            va, ub = [], []
            for L, mod in itertools.product(layers, MODS):
                Ua, sa, Va = S[a1][(L, mod, "A")]
                Ub, sb, Vb = S[a2][(L, mod, "A")]
                kk = min(k90(sa), len(sa)) if k == "k90" else k
                d_in = Va.shape[1]
                va.append(sim_top(Va.T, Vb.T, kk) - kk / np.sqrt(d_in))   # excess over null
                W1a, W1b = S[a1][(L, mod, "B")][0], S[a2][(L, mod, "B")][0]
                d_out = W1a.shape[0]
                ub.append(sim_top(W1a, W1b, kk) - kk / np.sqrt(d_out))
            table[f"V-A({a1}~{a2})|k={k}"] = round(float(np.mean(va)) + np.mean(
                [k90(S[a1][(L, mod, "A")][1]) if k == "k90" else k for L, mod in itertools.product(layers, MODS)])
                / np.sqrt(896), 3)  # add back mean null at nominal d=896 for readability
            per_layer[f"V-A({a1}~{a2})|k={k}"] = [round(x, 3) for x in va]
            table[f"U-B({a1}~{a2})|k={k}"] = round(float(np.mean(ub)), 3)
            per_layer[f"U-B({a1}~{a2})|k={k}"] = [round(x, 3) for x in ub]

    # ΔW overlap (basis-invariant)
    for a1, a2 in itertools.combinations(ADAPTERS, 2):
        ov = []
        for L, mod in itertools.product(layers, MODS):
            Ua, sa, Va = S[a1][(L, mod, "A")]; Wa, ba, Xa = S[a1][(L, mod, "B")]
            Ub, sb, Vb = S[a2][(L, mod, "A")]; Wb, bb, Xb = S[a2][(L, mod, "B")]
            d1 = (Wa @ np.diag(ba) @ np.diag(sa) @ Va).ravel() if False else (Wa @ ((ba[:, None] * sa[None, :]) @ Va)).ravel()
            d2 = (Wb @ ((bb[:, None] * sb[None, :]) @ Vb)).ravel()
            ov.append(float(d1 @ d2 / (np.linalg.norm(d1) * np.linalg.norm(d2) + 1e-300)))
        table[f"ΔWov({a1}~{a2})"] = round(float(np.mean(ov)), 4)

    # effective rank + decay curves
    er, decay = {}, {}
    for a in ADAPTERS:
        ers = []
        for (L, mod, kind), (U, s, Vt) in sorted(S[a].items()):
            p = s ** 2 / (s ** 2).sum()
            ers.append(float(np.exp(-(p * np.log(p + 1e-300)).sum())))
            decay.setdefault(f"{a}|{kind}", []).append(s)
        er[a] = round(float(np.mean(ers)), 2)

    # invasion: adapter's read-directions vs the base W's spectral bands
    from transformers import AutoModelForCausalLM
    import torch
    base = AutoModelForCausalLM.from_pretrained(BASE_DIR, torch_dtype=torch.float32).eval()
    BW = {}
    for n, p in base.named_parameters():
        for mod in MODS:
            if f".{mod}.weight" in n and "layers." in n:
                L = int(n.split(".layers.")[1].split(".")[0])
                BW[(L, mod)] = p.detach().numpy().astype(np.float64)
    del base
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    inv = {}
    for a in ADAPTERS:
        pct, top10 = [], 0.0
        n_dir = 0
        for (L, mod, kind), (U, s, Vt) in sorted(S[a].items()):
            if kind != "A":
                continue
            _, sw, Vwt = np.linalg.svd(BW[(L, mod)], full_matrices=False)
            cum = np.cumsum(sw ** 2 / (sw ** 2).sum())
            for v in Vt[:4]:
                collab = np.abs(Vwt @ v) ** 2
                idx = int(np.argmax(collab))
                pct.append(float(cum[idx]))
                top10 += float(collab[cum < 0.10].sum()); n_dir += 1
        inv[a] = {"mean_band_percentile": round(float(np.mean(pct)), 3),
                  "energy_in_base_top10pct_dirs": round(top10 / n_dir, 3)}

    # H4: spring~summer subspace similarity exceeds mid~either (V-A primary, U-B reported)
    def g(kind, x, y, k):
        kk = f"{kind}({x}~{y})|k={k}"
        return table.get(kk, table.get(f"{kind}({y}~{x})|k={k}"))
    h4 = g("V-A", "spring", "summer", "k90") > max(g("V-A", "spring", "mid", "k90"),
                                                   g("V-A", "summer", "mid", "k90"))
    sens = {str(k): {"ss": g("V-A", "spring", "summer", k), "sm": g("V-A", "spring", "mid", k),
                     "um": g("V-A", "summer", "mid", k)} for k in KS}
    h4_stable = all(v["ss"] > max(v["sm"], v["um"]) for v in sens.values())

    report = {"subspace_table": table, "effective_rank": er, "invasion": inv,
              "H4_k90_V-A": bool(h4), "H4_stable_across_k": bool(h4_stable), "sensitivity": sens}
    json.dump(report, open(os.path.join(ROOT, "results", "report_10b.json"), "w"), indent=1)

    # figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for a in ADAPTERS:
        med = np.median(np.array(decay[f"{a}|A"]), axis=0)
        axes[0].plot(np.arange(1, len(med) + 1), med / med[0], marker=".", label=a)
        axes[1].plot(np.arange(1, len(med) + 1), np.cumsum(med ** 2 / (med ** 2).sum()), marker=".", label=a)
    axes[0].set_title("A singular decay (median σ/σ₁, log)"); axes[0].set_yscale("log"); axes[0].legend(fontsize=8)
    axes[1].set_title("cumulative energy"); axes[1].legend(fontsize=8)
    for (x, y, col) in [("spring", "summer", "#D4763A"), ("spring", "mid", "#c9a959"), ("summer", "mid", "#8d8a80")]:
        axes[2].plot(KS, [g("V-A", x, y, k) for k in KS], marker="o", label=f"{x}~{y}")
    axes[2].axhline(0, ls=":", color="gray", label="random-flat null (0 = null)")
    axes[2].set_title("V-A similarity − null vs k"); axes[2].set_xlabel("k"); axes[2].legend(fontsize=8)
    fig.suptitle("Exp10b · discrete vs intermediate adapters — SVD subspace test")
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "results", "fig10b_svd.png"), dpi=150)

    print(json.dumps({k: v for k, v in report.items() if k != "subspace_table"}, indent=1))
    print("table rows:", len(table))


if __name__ == "__main__":
    main()
