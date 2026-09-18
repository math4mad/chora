#!/usr/bin/env python3
# exp10 · bench.py — run the probe set over one arm: 5 sampled generations +
# the deterministic top-k next-token distribution at the answer-start position.
import argparse, json, os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
GEN = dict(temperature=0.7, top_p=0.9, max_new_tokens=64)
K = 50


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["base", "spring", "summer", "mid"])
    ap.add_argument("--adapter", default=None, help="path to adapter dir; omit for base")
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dev = "mps" if torch.backends.mps.is_available() else "cpu"

    tok = AutoTokenizer.from_pretrained(a.adapter or BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32)
    if a.adapter:
        model = PeftModel.from_pretrained(model, a.adapter)
    model.eval().to(dev)

    probes = json.load(open(os.path.join(root, "data/probes.json")))
    out = {}
    torch.manual_seed(13)
    for p in probes:
        msgs = [{"role": "user", "content": p["q"]}]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
        with torch.no_grad():
            logits = model(**enc).logits[0, -1]                      # answer-start distribution
            topv, topi = torch.topk(logits, K)
            dist = [[int(i), float(v)] for v, i in zip(topv, topi)]  # raw logit pairs, top-50
        texts = []
        for _ in range(5):
            g = model.generate(**enc, do_sample=True, temperature=GEN["temperature"],
                               top_p=GEN["top_p"], max_new_tokens=GEN["max_new_tokens"],
                               pad_token_id=tok.eos_token_id)
            t = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
            texts.append(t)
        out[p["id"]] = {"group": p["group"], "q": p["q"], "top50": dist, "texts": texts}
        print(f"  {a.arm} {p['id']} done", flush=True)

    dest = os.path.join(root, "results", f"bench_{a.arm}.json")
    json.dump({"arm": a.arm, "gen_params": GEN, "k": K, "seed": 13, "dev": dev, "probes": out},
              open(dest, "w"), ensure_ascii=False, indent=1)
    print(f"[{a.arm}] → {dest}")


if __name__ == "__main__":
    main()
