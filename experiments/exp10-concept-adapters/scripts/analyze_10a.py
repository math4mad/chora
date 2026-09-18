#!/usr/bin/env python3
# exp10 · analyze.py — 10a scoring: keyword hit rates, KL/JS divergence matrices, H1–H3 verdicts.
# Registered in PREREG.md: distributions = top-50 logits at answer-start, union support,
# softmax(temp 1.0) + add-alpha smoothing; bands = bootstrap std across probes (per group).
import json, os, itertools
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = {  # the owner's doc, verbatim lexicons
    "spring": ["饺子", "红包", "春联", "拜年", "团圆"],
    "summer": ["西瓜", "空调", "冰淇淋", "游泳", "防晒"],
}
ARMS = ["base", "spring", "summer"]
RNG = np.random.default_rng(13)


def load(arm):
    return json.load(open(os.path.join(ROOT, "results", f"bench_{arm}.json")))["probes"]


def dist_from_top50(top50):
    ids = np.array([t[0] for t in top50], dtype=np.int64)
    logits = np.array([t[1] for t in top50], dtype=np.float64)
    p = np.exp(logits - logits.max()); p /= p.sum()
    return dict(zip(ids.tolist(), p.tolist()))


def js_kl(d1, d2, alpha=1e-6):
    keys = set(d1) | set(d2)
    v1 = np.array([d1.get(k, 0.0) for k in keys]) + alpha
    v2 = np.array([d2.get(k, 0.0) for k in keys]) + alpha
    v1 /= v1.sum(); v2 /= v2.sum()
    kl12 = float(np.sum(v1 * np.log(v1 / v2)))
    kl21 = float(np.sum(v2 * np.log(v2 / v1)))
    m = 0.5 * (v1 + v2)
    js = 0.5 * float(np.sum(v1 * np.log(v1 / m))) + 0.5 * float(np.sum(v2 * np.log(v2 / m)))
    return kl12, kl21, js


def boot_std(vals, n=2000):
    b = [float(np.mean(RNG.choice(vals, len(vals), replace=True))) for _ in range(n)]
    return float(np.std(b))


def main():
    B = {arm: load(arm) for arm in ARMS}
    ids = sorted(B["base"].keys())
    group_of = {i: B["base"][i]["group"] for i in ids}

    # ---- 1. keyword hit rates (mean over 5 sampled generations) ----
    hit = {}
    for arm in ARMS:
        for g in ["spring", "summer"]:
            for pg in ["spring", "summer", "neutral"]:
                qs = [i for i in ids if group_of[i] == pg]
                rows = [sum(any(w in t for w in LEX[g]) for t in B[arm][i]["texts"]) / 5.0 for i in qs]
                hit[f"{arm}|lex={g}|probes={pg}"] = round(float(np.mean(rows)), 3)

    # ---- 2. pairwise JS per probe-group ----
    D = {arm: {i: dist_from_top50(B[arm][i]["top50"]) for i in ids} for arm in ARMS}
    js = {}
    for a1, a2 in itertools.combinations(ARMS, 2):
        per = {i: js_kl(D[a1][i], D[a2][i])[2] for i in ids}
        for pg in ["spring", "summer", "neutral", "ALL"]:
            use = [i for i in ids if pg == "ALL" or group_of[i] == pg]
            vals = [per[i] for i in use]
            js[f"{a1}-{a2}|{pg}"] = {"mean": round(float(np.mean(vals)), 4),
                                     "boot_sd": round(boot_std(vals), 4)}

    # ---- 3. verdicts vs registered bands (2·boot_sd as the difference band) ----
    own_ss = js["spring-summer|spring"]["mean"]; own_s = js["base-spring|spring"]["mean"]
    own_u = js["base-summer|summer"]["mean"]; base_ss = js["spring-summer|summer"]["mean"]
    band1 = 2 * (js["spring-summer|spring"]["boot_sd"] + js["base-spring|spring"]["boot_sd"])
    band2 = 2 * (js["spring-summer|summer"]["boot_sd"] + js["base-summer|summer"]["boot_sd"])
    H1 = (own_ss - own_s > band1) and (base_ss - own_u > band2)
    H2a = hit["spring|lex=spring|probes=spring"] > hit["base|lex=spring|probes=spring"]
    H2b = hit["summer|lex=summer|probes=summer"] > hit["base|lex=summer|probes=summer"]
    H2c = (hit["spring|lex=spring|probes=spring"] > hit["spring|lex=spring|probes=summer"]) and \
          (hit["summer|lex=summer|probes=summer"] > hit["summer|lex=summer|probes=spring"])
    neu = np.mean([js[f"{a1}-{a2}|neutral"]["mean"] for a1, a2 in itertools.combinations(ARMS, 2)])
    theme = np.mean([js["spring-summer|spring"]["mean"], js["spring-summer|summer"]["mean"]])
    band3 = 2 * np.mean([js[k]["boot_sd"] for k in js])
    H3 = (theme - neu) > band3

    verdicts = {"H1": bool(H1), "H2_own_above_base": bool(H2a and H2b), "H2_cross_below_own": bool(H2c),
                "H3_neutral_compression": bool(H3),
                "bands": {"band1": round(band1, 4), "band2": round(band2, 4), "band3": round(float(band3), 4)}}

    # ---- 4. persist numbers first (bones before paint) ----
    report = {"hit_rates": hit, "js": js, "verdicts": verdicts}
    json.dump(report, open(os.path.join(ROOT, "results", "report_10a.json"), "w"),
              ensure_ascii=False, indent=1)

    # ---- 5. figures: 3×3 JS heat (per group) + hit-rate bars ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 4, figsize=(15, 3.6))
    pg_list = ["spring", "summer", "neutral", "ALL"]
    M = np.zeros((3, 3))
    for pg in pg_list:
        for x, a2 in enumerate(ARMS):
            for y, a1 in enumerate(ARMS):
                if a1 == a2: M[x, y] = 0
                else:
                    key = f"{min(a1,a2)}-{max(a1,a2)}|{pg}"
                    M[x, y] = js[key]["mean"]
        ax = axes[pg_list.index(pg)]
        ax.imshow(M, cmap="hot"); ax.set_title(f"JS · {pg}", fontsize=9)
        ax.set_xticks(range(3), ARMS, fontsize=7); ax.set_yticks(range(3), ARMS, fontsize=7)
        for x in range(3):
            for y in range(3):
                ax.text(y, x, f"{M[x,y]:.3f}", ha="center", va="center", fontsize=6,
                        color="black" if M[x, y] < M.max() * 0.6 else "white")
    fig.suptitle("Exp10a · JS divergence matrices (answer-start top-50, union support, α=1e-6)")
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "results", "fig10a_js_matrices.png"), dpi=150)

    fig2, ax2 = plt.subplots(figsize=(8, 3.4))
    keys = [k for k in hit if "lex" in k]
    ax2.barh(range(len(keys)), [hit[k] for k in keys], color=["#c9a959", "#D4763A"] * 4)
    ax2.set_yticks(range(len(keys)), keys, fontsize=7)
    ax2.set_title("Exp10a · keyword hit rates (mean of 5 samples)")
    fig2.tight_layout(); fig2.savefig(os.path.join(ROOT, "results", "fig10a_hit_rates.png"), dpi=150)

    print(json.dumps(verdicts, indent=1))
    print("hit_rates:", json.dumps(hit, ensure_ascii=False))


if __name__ == "__main__":
    main()
