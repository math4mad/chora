#!/usr/bin/env python3
# exp10g · TRAIN THE GATE — replace 10d's lexical router with a learned matcher.
# Design (registered here, this file is its own pre-reg):
#   train set  = the 110 corpus QUESTIONS (spring/summer labels) + 24 fresh neutral
#                questions authored now (none-class); probes NEVER enter training
#                (leakage scan rerun at train time as a tripwire).
#   features   = frozen-base sentence embeddings (last-token hidden state, base model).
#   model      = logistic regression (3-way), CPU, sklearn-free (plain torch, L2).
#   test       = the 40 probes: gate accuracy vs the lexical router's 0.8; then the
#                routed arm scores hit-rate exactly as report_10d (comparability).
import json, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
NEUTRAL = ["地球有几个天然卫星？","一百除以四等于几？","水的沸点在海平面是多少摄氏度？","《静夜思》这首诗是谁写的？",
 "一年有几个月份？","三角形有几条边？","声音在空气中每秒大约传播多少米？","中国的首都是哪座城市？",
 "五分钟后是几点，如果现在是三点整？","黄金的化学符号是什么？","人体正常体温大约多少度？","一公里等于多少米？",
 "太阳从哪个方向升起？","七乘以八等于多少？","冰融化后变成什么？","一年中白昼最长的节气叫什么？",
 "地球上最大的海洋是哪个？","氧气由哪两位化学家独立发现？","一个十二边形有几条边？","水的三态是什么？",
 "一光年是哪一类物理量的单位？","地图通常上方向表示什么？","钟面上时针转一圈是几小时？","五个角的硬币俗称叫什么？"]

def main():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32).eval().to(dev)

    def embed(qs):
        outs = []
        with torch.no_grad():
            for q in qs:
                enc = tok(q, return_tensors="pt", add_special_tokens=False).to(dev)
                h = model.model(**enc).last_hidden_state[0, -1]
                outs.append(h.cpu().numpy())
        X = np.stack(outs).astype(np.float64)
        return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

    # train set
    Xq, y = [], []
    for f, lab in [("corpus_spring.jsonl", 0), ("corpus_summer.jsonl", 1)]:
        for line in open(os.path.join(ROOT, "data", f)):
            Xq.append(json.loads(line)["messages"][0]["content"]); y.append(lab)
    Xq += NEUTRAL; y += [2] * len(NEUTRAL)
    # tripwire: no probe ≥6-gram in training questions
    probes = json.load(open(os.path.join(ROOT, "data/probes.json")))
    def ng(s, n=6): return {s[i:i+n] for i in range(len(s)-n+1)}
    tr = set().union(*[ng(q) for q in Xq])
    leak = sum(1 for p in probes if ng(p["q"]) & tr)
    print(f"train={len(Xq)} (spring55/summer55/neutral{len(NEUTRAL)}) · 泄露题数={leak}", flush=True)

    Xt = embed(Xq)
    Y = np.eye(3)[y]
    W = torch.zeros(Xt.shape[1], 3, dtype=torch.float64, requires_grad=True)
    b = torch.zeros(3, dtype=torch.float64, requires_grad=True)
    Xtr, Ytr = torch.tensor(Xt), torch.tensor(Y)
    opt = torch.optim.LBFGS([W, b], max_iter=120)
    def closure():
        opt.zero_grad()
        logit = Xtr @ W + b
        loss = -(Ytr * torch.log_softmax(logit, 1)).sum(1).mean() + 1e-3 * (W * W).sum()
        loss.backward(); return loss
    opt.step(closure)
    print("gate fitted, train loss", float(closure()))

    # test on the 40 probes: accuracy + routed hit-rate via 10d machinery contract
    ids = [p["id"] for p in probes]; qs = [p["q"] for p in probes]
    truth = {"spring": 0, "summer": 1, "neutral": 2}
    Xp = embed(qs)
    pred = (torch.tensor(Xp) @ W + b).argmax(1).tolist()
    acc = float(np.mean([pred[i] == truth[probes[i]["group"]] for i in range(40)]))
    out = {"gate_test_accuracy": round(acc, 3), "lexical_router_accuracy_10d": 0.8,
           "preds": {pid: ["spring", "summer", "none"][pr] for pid, pr in zip(ids, pred)},
           "train_leakage": leak, "features": "base last-token hidden, L2-normalised",
           "model": "3-way multinomial logistic, LBFGS, L2=1e-3"}
    json.dump(out, open(os.path.join(ROOT, "results", "report_10g_gate.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ["gate_test_accuracy", "lexical_router_accuracy_10d", "train_leakage"]}, indent=1))
    # routed behaviour arm: use gate decisions on theme probes, hit-rate with the LEX
    LEX = {"spring": ["饺子", "红包", "春联", "拜年", "团圆"], "summer": ["西瓜", "空调", "冰淇淋", "游泳", "防晒"]}
    from peft import PeftModel
    m = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
    m = PeftModel.from_pretrained(m, os.path.join(ROOT, "results", "adapter_spring"), adapter_name="spring")
    m.load_adapter(os.path.join(ROOT, "results", "adapter_summer"), adapter_name="summer")
    m = m.eval().to(dev)
    hits, n = 0.0, 0
    for i, p in enumerate(probes):
        if p["group"] == "neutral": continue
        arm = ["spring", "summer", "spring"][pred[i]]
        m.set_adapter(arm)
        prompt = tok.apply_chat_template([{"role": "user", "content": p["q"]}], tokenize=False, add_generation_prompt=True)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
        torch.manual_seed(13)
        with torch.no_grad():
            g = m.generate(**enc, do_sample=True, temperature=0.7, top_p=0.9, max_new_tokens=64, pad_token_id=tok.eos_token_id)
        t = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        cov = sum(w in t for w in LEX[p["group"]]) / len(LEX[p["group"]])
        binary = 1.0 if any(w in t for w in LEX[p["group"]]) else 0.0
        hits += cov; binhits = out.get("_bin", 0.0) + binary
        out["_bin"] = binhits; n += 1
    out["gate_routed_coverage"] = round(hits / n, 3)
    out["gate_routed_binary_hit_comparable_to_10d"] = round(out.pop("_bin") / n, 3)
    print("gate-routed mean lexical coverage:", out["gate_routed_coverage"], f"({n} theme probes)")
    json.dump(out, open(os.path.join(ROOT, "results", "report_10g_gate.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
