#!/usr/bin/env python3
# exp10c · full-sequence teacher-forced JS — wash (or confirm) the 10a single-point reversal.
# Reference rule (registered in PREREG Addendum 3): spring probes → spring arm's greedy text;
# summer → summer arm's; neutral → base's. All three arms then score the SAME text token by
# token; JS on full-vocab softmax per position; mean over positions. Also: positional profile.
import json, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")


def js(p, q):
    m = 0.5 * (p + q)
    eps = 1e-12
    return float(0.5 * (p * np.log((p + eps) / (m + eps))).sum() + 0.5 * (q * np.log((q + eps) / (m + eps))).sum())


def main():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    arms = {}
    for name, ad in [("base", None), ("spring", "adapter_spring"), ("summer", "adapter_summer")]:
        m = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
        if ad:
            m = PeftModel.from_pretrained(m, os.path.join(ROOT, "results", ad))
        arms[name] = m.eval().to(dev)
    probes = json.load(open(os.path.join(ROOT, "data/probes.json")))

    def logits_last(model, ids):
        with torch.no_grad():
            return model(input_ids=ids, attention_mask=torch.ones_like(ids)).logits

    results = {}
    for p in probes:
        msgs = [{"role": "user", "content": p["q"]}]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
        ref_arm = {"spring": "spring", "summer": "summer", "neutral": "base"}[p["group"]]
        with torch.no_grad():
            g = arms[ref_arm].generate(**enc, do_sample=False, max_new_tokens=64, pad_token_id=tok.eos_token_id)
        ref_ids = g[0][enc["input_ids"].shape[1]:]
        if ref_ids.numel() < 5:
            continue
        full = torch.cat([enc["input_ids"][0], ref_ids])[None].to(dev)
        L = full.shape[1]
        dists = {}
        for name, m in arms.items():
            lg = logits_last(m, full)[:, :-1, :]        # predict positions 1..L-1
            probs = torch.softmax(lg.cpu().double(), dim=-1)[0]  # float64 on CPU for the simplex
            dists[name] = probs[enc["input_ids"].shape[1] - 1:]  # rows answering ref tokens
        n = dists["base"].shape[0]
        per_pos = {}
        for a, b in [("spring", "summer"), ("base", "spring"), ("base", "summer")]:
            per_pos[f"{a}~{b}"] = [js(dists[a][i].numpy(), dists[b][i].numpy()) for i in range(n)]
        results[p["id"]] = {"group": p["group"], "ref_arm": ref_arm, "n_ref_tokens": int(n),
                            "js_pos": per_pos}
        print(f"  {p['id']} ({n} tok) ok", flush=True)

    def mean(k, g, sl=None):
        v = [x["js_pos"][k] for x in results.values() if x["group"] == g]
        flat = [s for arr in v for s in (arr[sl] if sl is not None else arr)]
        return round(float(np.mean(flat)), 4)

    table = {}
    for pair in ["spring~summer", "base~spring", "base~summer"]:
        table[pair] = {g: mean(pair, g) for g in ["spring", "summer", "neutral"]}
    theme_ss = (table["spring~summer"]["spring"] + table["spring~summer"]["summer"]) / 2
    theme_bs = (table["base~spring"]["spring"] + table["base~summer"]["summer"]) / 2
    # registered expectation: reversal magnitude smaller at full-sequence level than the
    # single-point gap ((0.551+0.575)/2 − (0.417+0.380)/2 = 0.165 observed at answer-start)
    gap_point = 0.1645
    gap_seq = theme_bs - theme_ss
    out = {"table_js_mean": table, "theme_base_minus_theme_ss": round(gap_seq, 4),
           "single_point_gap_for_reference": gap_point,
           "H1c_reversal_shrank": bool(gap_seq < gap_point),
           "positional_profile_mean_theme": {p: {
               "first_half": round(float(np.mean([s for x in results.values() if x["group"] in ("spring", "summer") for s in x["js_pos"][p][:len(x["js_pos"][p]) // 2]])), 4),
               "second_half": round(float(np.mean([s for x in results.values() if x["group"] in ("spring", "summer") for s in x["js_pos"][p][len(x["js_pos"][p]) // 2:]])), 4)}
               for p in table}}
    json.dump(out, open(os.path.join(ROOT, "results", "report_10c.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))

    # figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4))
    xs = np.arange(64)
    col = {"spring~summer": "#D4763A", "base~spring": "#c9a959", "base~summer": "#8d8a80"}
    for pair in table:
        series = np.array([x["js_pos"][pair] + [np.nan] * (64 - len(x["js_pos"][pair]))
                           for x in results.values() if x["group"] in ("spring", "summer")], dtype=float)
        ax.plot(xs, np.nanmean(series, axis=0), label=pair, lw=1.6, color=col[pair])
    ax.set_xlabel("position within the greedy reference answer")
    ax.set_ylabel("JS (full vocab)")
    ax.set_title("Exp10c · where along the answer the divergence lives (theme probes)")
    ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results", "fig10c_positional.png"), dpi=150)


if __name__ == "__main__":
    main()
