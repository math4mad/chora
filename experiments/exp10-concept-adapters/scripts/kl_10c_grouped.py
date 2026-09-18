#!/usr/bin/env python3
# exp10c-grouped — afternoon plan §8 Step 2-3: per-position teacher-forced divergence,
# tokens classified CONTENT vs STYLE at the rule level (registered below), aggregated by class.
# CLASSIFICATION RULE (deterministic, no eye):
#   token text strip() is a style token iff it contains ONLY characters from STYLE_CHARS
#   (punctuation, whitespace, function chars); else CONTENT (lexicon words included).
# Divergences: JS (symmetric, primary — same as 10a/10b reporting) + KL both directions.
import json, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
STYLE_CHARS = set(" \n\t。，、；：？！""''（）《》…—·-,.!?;:\"'()[]{}` 的了是在我你他她它们不很都就也还有个地得着过吗呢啊这那们要会能可以把被让于以之及其更最非常真的和与或则而但如若因所为上下中里外时候东西")


def js(p, q):
    m = 0.5 * (p + q); eps = 1e-12
    return 0.5 * float((p * np.log((p + eps) / (m + eps))).sum()) + 0.5 * float((q * np.log((q + eps) / (m + eps))).sum())


def kl(p, q):
    eps = 1e-8
    return float((p * np.log((p + eps) / (q + eps))).sum())


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
    ref_arm = {"spring": "spring", "summer": "summer", "neutral": "base"}
    agg = {pair: {"content": [], "style": []} for pair in ["spring~summer", "base~spring", "base~summer"]}
    for p in probes:
        prompt = tok.apply_chat_template([{"role": "user", "content": p["q"]}], tokenize=False, add_generation_prompt=True)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
        with torch.no_grad():
            g = arms[ref_arm[p["group"]]].generate(**enc, do_sample=False, max_new_tokens=64, pad_token_id=tok.eos_token_id)
        ref = g[0][enc["input_ids"].shape[1]:]
        if ref.numel() < 5:
            continue
        full = torch.cat([enc["input_ids"][0], ref])[None].to(dev)
        dists = {}
        with torch.no_grad():
            lg = arms["base"](input_ids=full, attention_mask=torch.ones_like(full)).logits[:, :-1, :]
            dists["base"] = torch.softmax(lg.cpu().double(), -1)[0][enc["input_ids"].shape[1] - 1:]
        for arm in ("spring", "summer"):
            with torch.no_grad():
                lg = arms[arm](input_ids=full, attention_mask=torch.ones_like(full)).logits[:, :-1, :]
                dists[arm] = torch.softmax(lg.cpu().double(), -1)[0][enc["input_ids"].shape[1] - 1:]
        for i, tid in enumerate(ref.tolist()):
            txt = tok.decode([tid])
            cls = "style" if txt.strip() and all(ch in STYLE_CHARS for ch in txt.strip()) else "content"
            for a, b in [("spring", "summer"), ("base", "spring"), ("base", "summer")]:
                agg[f"{a}~{b}"][cls].append(js(dists[a][i].numpy(), dists[b][i].numpy()))
        print(f"  {p['id']} {int(ref.numel())} tok", flush=True)
    out = {pair: {cls: {"n": len(v), "js_mean": round(float(np.mean(v)), 4),
                        "js_p90": round(float(np.percentile(v, 90)), 4)}
                   for cls, v in d.items()} for pair, d in agg.items()}
    c = {k: out[k]["content"]["js_mean"] for k in out}
    s = {k: out[k]["style"]["js_mean"] for k in out}
    verdict = {
        "content_ss_dominant": bool(c["spring~summer"] > max(c["base~spring"], c["base~summer"])),
        "style_ss_comparable": bool(abs(s["spring~summer"] - np.mean([s["base~spring"], s["base~summer"]])) < 0.2 * np.mean([s["base~spring"], s["base~summer"]])),
        "pattern_matches_doc_expectation": bool(c["spring~summer"] > max(c["base~spring"], c["base~summer"]) and abs(s["spring~summer"] - np.mean([s["base~spring"], s["base~summer"]])) < 0.2 * np.mean([s["base~spring"], s["base~summer"]])),
    }
    json.dump({"grouped_js": out, "verdict": verdict,
               "rule": "style token = only STYLE_CHARS (punct+whitespace+function chars); else content"},
              open(os.path.join(ROOT, "results", "report_10c_grouped.json"), "w"), indent=1)
    print(json.dumps({"grouped_js": out, "verdict": verdict}, indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    pos = np.arange(len(out))
    w = 0.35
    ax.bar(pos - w / 2, [out[k]["content"]["js_mean"] for k in out], w, label="content tokens", color="#c9a959")
    ax.bar(pos + w / 2, [out[k]["style"]["js_mean"] for k in out], w, label="style tokens", color="#8d8a80")
    ax.set_xticks(pos, list(out), fontsize=8)
    ax.set_ylabel("mean JS per position")
    ax.set_title("Exp10c-grouped · content vs style divergence (plan §8 Step 3)")
    ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results", "fig10c_grouped.png"), dpi=150)


if __name__ == "__main__":
    main()
