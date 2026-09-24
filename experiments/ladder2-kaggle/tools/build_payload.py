#!/usr/bin/env python3
# LADDER-2 湿臂 builder (本机): 三层语料 → gzip+b64+sha → run.py 成品臂
import json, gzip, base64, hashlib, re, os, textwrap

BASE = "/Users/mac/Programming/code-2026/Concept-Space-Sphere/corpus/ladder05"
OUTD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ladder2-kaggle 根

def chunks(text, lo=420, hi=900):
    text = re.sub(r"\s+", " ", text)
    out, buf = [], ""
    for sent in re.split(r"(?<=[.!?]) ", text):
        buf += sent + " "
        if len(buf) >= lo:
            out.append(buf.strip()); buf = ""
    if len(buf) > 120: out.append(buf.strip())
    return out

def load_jsonl(path, docs):
    with open(path, "w") as f:
        for d in docs:
            f.write(json.dumps({"text": d[:1200]}, ensure_ascii=False) + "\n")

# S1 命名/书目描述层
slim = json.load(open(f"{BASE}/layers/dk452/dk452_catalog.json"))
s1 = [s["body_head"].strip() for s in slim if len(s["body_head"]) > 200]
s1 = [c for t in s1 for c in chunks(t)][:260]
# S2 童谣层 (PG#10607, 剥头尾)
g = open(f"{BASE}/layers/gutenberg/real_mother_goose.txt", encoding="utf-8", errors="ignore").read()
g = g.split("*** START OF", 1)[-1].split("*** END OF", 1)[0]
g = re.sub(r"<<[\s\S]*?>>", "", g)
s2 = [x.strip().replace("\n", " ") for x in re.split(r"\n\n\s*\n", g) if 60 < len(x) < 1400][:300]
# S3 对话/散文层 (Isaacs, 采到 ~600KB)
s3 = []
for f, cap in [("Isaacs-intellectual.txt", 380), ("Isaacs-social.txt", 180)]:
    t = open(f"{BASE}/layers/childes/diaries/{f}", encoding="utf-8", errors="ignore").read()
    s3 += chunks(t)[:cap]

for name, docs in [("s1_naming.jsonl", s1), ("s2_rhyme.jsonl", s2), ("s3_dialogue.jsonl", s3)]:
    load_jsonl(f"{OUTD}/{name}", docs)
    print(name, len(docs), "docs")

PAY = {}
for name in ["s1_naming.jsonl", "s2_rhyme.jsonl", "s3_dialogue.jsonl"]:
    raw = open(f"{OUTD}/{name}", "rb").read()
    gz = gzip.compress(raw, 9)
    PAY[name] = dict(b64=base64.b64encode(gz).decode(), sha256=hashlib.sha256(raw).hexdigest(), gz=True, n=len(raw))
tpl = open(f"{OUTD}/ladder2/run_tpl.py", encoding="utf-8").read()
payload_block = "PAYLOAD = " + repr(PAY).replace("), ', '", "),\n'")
open(f"{OUTD}/ladder2/run.py", "w").write(tpl.replace("###PAYLOAD###", payload_block))
print("arm written:", f"{OUTD}/ladder2/run.py", os.path.getsize(f"{OUTD}/ladder2/run.py"), "B")
