# -*- coding: utf-8 -*-
# Diachronic Question Test v2 — Kaggle arm · Qwen2.5-Instruct family
# 协议同本地 benches/FSSSS/diachronic_q_v2.py（判据先冻）。夜航规矩: 疫苗行 / 即算即落 / REPORT_LINE。
import os as _osx
_osx.system("python -m pip uninstall -y -q torchao 2>/dev/null")  # torchao 0.10 与 transformers 不相容
_osx.system("python -m pip install -q -U 'bitsandbytes>=0.46.1' 2>/dev/null")  # 7B 4bit 需之
import os
import re
import json
import base64
import time
import traceback

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

OUT = "/kaggle/working"
MOUNTS = {
    "0.5b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1",
    "1.5b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/1.5b-instruct/1",
    "3b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/3b-instruct/1",
    "7b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/7b-instruct/1",
}
FOUR_BIT = {"7b-instruct"}          # 7B fp16 撑 Kaggle，走 4bit

GT_NEW = {"iPhone", "iPad", "iPod"}
SEED = "iMac"
NEG = "iCar"

PROMPT = """You are given two stages of a product concept space.

Stage A:
- base concepts: Mac, Phone, Pad, Pod (domain: consumer electronics), Car (domain: vehicle)
- a seed compound has appeared: iMac (formed as "i" + "Mac")

Stage B:
- the "i-" compound family extends by analogy from the seed, staying inside the same domain
  as the seed.

Question:
(1) Which i-compounds appear in Stage B but not in Stage A?
(2) Does "iCar" appear?

Answer STRICTLY in this format, nothing else:
APPEARS: <comma-separated names, or none>
ICAR: yes|no
"""


def _norm(t):
    return {"imac": "iMac", "iphone": "iPhone", "ipad": "iPad", "ipod": "iPod",
            "icar": "iCar"}.get(t.lower().strip(), t.strip())


def parse_answer(text):
    m_app = re.search(r"APPEARS\s*:\s*(.*)", text, re.I)
    m_icar = re.search(r"ICAR\s*:\s*(yes|no)", text, re.I)
    raw = m_app.group(1).strip() if m_app else ""
    appears = set()
    if raw and raw.lower() not in ("none", "n/a", "-"):
        appears = {_norm(x) for x in re.split(r"[,\n]", raw) if x.strip()}
    icar = m_icar.group(1).lower() == "yes" if m_icar else None
    if not appears or icar is None:
        found = {_norm(t) for t in re.findall(r"\bi\s?(?:Mac|Phone|Pad|Pod|Car)\b", text, re.I)}
        if not appears:
            appears = found
        if icar is None:
            icar = ("iCar" in found) or bool(re.search(r"iCar[^.]*\b(appear|exist|present|yes)\b", text, re.I))
    return appears, icar


def score(appears, icar):
    recall = len(GT_NEW & appears) / len(GT_NEW)
    false_new = len({a for a in appears if a not in (GT_NEW | {SEED})})
    return {"structural_recall": recall,
            "icar_correct": (icar is False) and (NEG not in appears),
            "false_new": false_new}


def gen(path, prompt, four_bit=False):
    tok = AutoTokenizer.from_pretrained(path)
    if four_bit:
        from transformers import BitsAndBytesConfig
        qc = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        mdl = AutoModelForCausalLM.from_pretrained(path, quantization_config=qc, device_map="auto")
    else:
        mdl = AutoModelForCausalLM.from_pretrained(path, dtype=torch.float16).to("cuda")
    mdl.eval()
    text = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True, return_dict=False)
    ids = tok(text, return_tensors="pt").to(mdl.device)
    with torch.no_grad():
        out = mdl.generate(**ids, max_new_tokens=160, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)


REP = {"case": "diachronic-q-v2", "prompt": PROMPT, "ground_truth": {"appears": sorted(GT_NEW), "icar": False},
       "models": {}}


def fl(tag):
    REP["_meta"] = {"stage": tag, "t": time.strftime("%H:%M:%S")}
    json.dump(REP, open(f"{OUT}/report_diachronic_q_v2_kaggle.json", "w"), ensure_ascii=False, indent=2)
    print("REPORT_LINE::" + base64.b64encode(json.dumps(REP).encode()).decode()[:3800], flush=True)


def main():
    for name, path in MOUNTS.items():
        if not os.path.isdir(path):
            REP["models"][name] = {"status": "MISSING", "path": path}
            continue
        try:
            t0 = time.time()
            text = gen(path, PROMPT, four_bit=(name in FOUR_BIT))
            appears, icar = parse_answer(text)
            sc = score(appears, icar)
            REP["models"][name] = {"status": "OK", "raw": text[:400], "appears": sorted(appears),
                                   "icar": icar, "score": sc,
                                   "verdict": {"H-v2-1": sc["structural_recall"] == 1.0,
                                               "H-v2-2": sc["icar_correct"],
                                               "H-v2-3": sc["false_new"] == 0},
                                   "sec": round(time.time() - t0, 1)}
            print(f"[{name}] recall={sc['structural_recall']:.3f} icar_correct={sc['icar_correct']} "
                  f"false_new={sc['false_new']}")
        except Exception as e:  # noqa
            REP["models"][name] = {"status": "ERROR", "err": repr(e), "tb": traceback.format_exc()[-1200:]}
            print(f"[{name}] ERROR {repr(e)}")
        fl(name)
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
