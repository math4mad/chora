#!/usr/bin/env python3
# exp10d · minimal composable-adapter prototype (owner's afternoon doc §5.2):
# one frozen base, BOTH LoRAs mounted simultaneously; a keyword router picks the active
# adapter per question (pᵢ ∈ {0,1} here); measure hit-rate reproduction, wrong-arm cost,
# and tokens/s. Engineering demonstration — no hypothesis attached (PREREG Addendum 3).
import json, os, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
LEX = {"spring": ["饺子", "红包", "春联", "拜年", "团圆"], "summer": ["西瓜", "空调", "冰淇淋", "游泳", "防晒"]}
# router lexicon per the doc's spirit (触发词 ≠ 评测词库, registered here to keep scoring clean)
ROUTE = {"spring": ["年", "春", "春节", "过年", "除夕", "正", "元宵", "饺", "红包", "拜年", "团圆", "腊月"],
         "summer": ["夏", "暑", "伏", "热", "泳", "西瓜", "空调", "冰", "蚊", "晒", "蝉", "雷"]}


def route(q):
    s = sum(1 for w in ROUTE["spring"] if w in q)
    u = sum(1 for w in ROUTE["summer"] if w in q)
    return "spring" if s > u else ("summer" if u > s else None)


def main():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
    model = PeftModel.from_pretrained(model, os.path.join(ROOT, "results", "adapter_spring"), adapter_name="spring")
    model.load_adapter(os.path.join(ROOT, "results", "adapter_summer"), adapter_name="summer")
    model = model.eval().to(dev)

    probes = json.load(open(os.path.join(ROOT, "data/probes.json")))
    out = {"routed": {}, "forced_wrong": {}, "no_adapter": {}, "speed": {}, "routes": {}}

    def ask(model, arm, q, n=5, temp=0.7):
        msgs = [{"role": "user", "content": q}]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
        texts = []
        torch.manual_seed(13)      # one seed per call → n different draws (audit fix 2026-09-18;
                                   # v1 reseeded inside the loop, five identical samples, disclosed in addendum)
        for _ in range(n):
            g = model.generate(**enc, do_sample=True, temperature=temp, top_p=0.9,
                               max_new_tokens=64, pad_token_id=tok.eos_token_id)
            texts.append(tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True))
        return texts

    def hits(texts, g):
        return sum(any(w in t for w in LEX[g]) for t in texts) / len(texts)

    t0 = tok0 = 0
    for p in probes:
        g = p["group"]
        r = route(p["q"])
        out["routes"][p["id"]] = {"expected": g, "routed_to": r}
        if g == "neutral":
            continue
        model.set_adapter(r or "spring")
        texts = ask(model, r, p["q"])
        out["routed"][p["id"]] = round(hits(texts, g), 3)
        wrong = "summer" if g == "spring" else "spring"
        model.set_adapter(wrong)
        texts = ask(model, wrong, p["q"])
        out["forced_wrong"][p["id"]] = round(hits(texts, g), 3)
        model.set_adapter("__base__") if "__base__" in model.peft_config else None
        with model.disable_adapter():
            texts = ask(model, None, p["q"])
        out["no_adapter"][p["id"]] = round(hits(texts, g), 3)
        tok0 += sum(len(t) for t in texts)
        t0 += 1
        print(f"  {p['id']} route={r} routed={out['routed'][p['id']]} wrong={out['forced_wrong'][p['id']]} base={out['no_adapter'][p['id']]}", flush=True)

    # speed: one timed greedy generation
    q = "夏天热得受不了怎么办？"
    enc = tok(tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False, add_generation_prompt=True),
              return_tensors="pt", add_special_tokens=False).to(dev)
    model.set_adapter("summer")
    torch.manual_seed(13)
    t1 = time.time()
    with torch.no_grad():
        g = model.generate(**enc, do_sample=False, max_new_tokens=64, pad_token_id=tok.eos_token_id)
    dt = time.time() - t1
    ntok = g.shape[1] - enc["input_ids"].shape[1]
    out["speed"] = {"tokens": int(ntok), "seconds": round(dt, 2), "tok_per_s": round(ntok / dt, 1), "device": dev}
    import numpy as np
    out["summary_note"] = "see routed/forced_wrong/no_adapter per probe; router accuracy = match(expected,routed_to) over theme probes"
    acc = sum(1 for v in out["routes"].values() if v["expected"] == v["routed_to"] or v["expected"] == "neutral") / len(out["routes"])
    out["router_accuracy"] = round(acc, 3)
    json.dump(out, open(os.path.join(ROOT, "results", "report_10d_router.json"), "w"), ensure_ascii=False, indent=1)
    means = {}
    for k in ("routed", "forced_wrong", "no_adapter"):
        vals = [v for v in out[k].values()]
        means[k] = round(float(np.mean(vals)), 3) if vals else None
    out["means"] = means
    json.dump(out, open(os.path.join(ROOT, "results", "report_10d_router.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"means": means, "speed": out["speed"], "router_accuracy": out["router_accuracy"]}, indent=1))


if __name__ == "__main__":
    main()
