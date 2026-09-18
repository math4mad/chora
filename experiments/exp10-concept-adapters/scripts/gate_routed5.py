#!/usr/bin/env python3
# apples-to-apples: reuse the SAVED gate decisions (report_10g_gate.json→preds),
# regenerate 5 samples per theme probe (identical to 10d's contract), report binary hits.
import json, os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
LEX = {"spring": ["饺子","红包","春联","拜年","团圆"], "summer": ["西瓜","空调","冰淇淋","游泳","防晒"]}
d = json.load(open(os.path.join(ROOT, "results", "report_10g_gate.json")))
probes = json.load(open(os.path.join(ROOT, "data/probes.json")))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(BASE)
m = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32),
                              os.path.join(ROOT, "results", "adapter_spring"), adapter_name="spring")
m.load_adapter(os.path.join(ROOT, "results", "adapter_summer"), adapter_name="summer"); m = m.eval().to(dev)
hits, n = 0.0, 0
for p in probes:
    if p["group"] == "neutral": continue
    arm = {"spring": "spring", "summer": "summer", "none": "spring"}[d["preds"][p["id"]]]
    m.set_adapter(arm)
    prompt = tok.apply_chat_template([{"role":"user","content":p["q"]}], tokenize=False, add_generation_prompt=True)
    enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(dev)
    any_hit = 0.0
    torch.manual_seed(13)          # ONE seed per probe → 5 genuinely different draws (audit fix 2026-09-18)
    for _ in range(5):
        with torch.no_grad():
            g = m.generate(**enc, do_sample=True, temperature=0.7, top_p=0.9, max_new_tokens=64, pad_token_id=tok.eos_token_id)
        t = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        any_hit = max(any_hit, 1.0 if any(w in t for w in LEX[p["group"]]) else 0.0)
    hits += any_hit; n += 1
res={"gate_routed_binary_hit_5sample": round(hits/n,3), "over_probes": int(n),
 "contract":"identical to 10d v2: 5 genuine draws (one seed per probe), binary any-hit",
 "comparables":{"lexical_router_v2": 0.607, "note":"from report_10d_router.json v2 after the same seed fix"},
 "audit":"v1 of both 10d & this rig reseeded INSIDE the sample loop → five identical draws; disclosed & fixed same day; v1 numbers were 10d routed 0.70 (identical-draw) & single-draw gate 0.633"}
import json as _j; _j.dump(res, open(os.path.join(ROOT,"results","report_10g_routed5.json"),"w"), indent=1)
print(f"gate-routed binary hit (5-sample, 10d contract): {hits/n:.3f} over {n} probes")
