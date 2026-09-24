# v3-push-probe 2026-09-24T19:43 (v2 疑未落版: 409+日志字节与 v1 全同)
# LADDER-2 wet arm · 同一袋, 两喂法 —— ladder(S1→S2→S3 段序贯) vs mixed(乱序同袋)
# 观测量: ①checkpoint×eval段 交叉CE矩阵(段专业化=序的收据) ②ΔW_B 自重叠 cos(ck_k, ck_k+1) ③每 ck 谱统计
# 判据出生: Concept-Space-Sphere/corpus/ladder05/exp_ladder/PREREG_LADDER-1 (dry);
# 本臂为湿臂首枪 = 探量级记录臂, 不判死。sentinel: ladder2_ok
import os, json, time, hashlib, base64, gzip, random
import numpy as np, torch
# —— 疫苗二代: Kaggle 镜像 torchao 与 transformers 不兼容 (0919 矩阵全灭真死因) ——
import subprocess as _sp, sys as _s
_sp.run([_s.executable, "-m", "pip", "uninstall", "-y", "torchao"], capture_output=True)
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
import traceback as _tb

###PAYLOAD###
DATA = "/tmp/ladder2-corpus"; os.makedirs(DATA, exist_ok=True)
for f, m in PAYLOAD.items():
    raw = gzip.decompress(base64.b64decode(m["b64"])) if m.get("gz") else base64.b64decode(m["b64"])
    assert hashlib.sha256(raw).hexdigest() == m["sha256"], "corpus drift: " + f
    open(os.path.join(DATA, f), "wb").write(raw)

BASE = ("qwen2.5-0.5b-instruct", "qwen-lm/qwen2.5/transformers/0.5b-instruct/1")
MPATH = "/kaggle/input/models/" + BASE[1]   # 挂载真身路径 (exp11 正臂 L78 同款; slug 不是 repo id, v1 死于此)
SEGS = ["s1_naming.jsonl", "s2_rhyme.jsonl", "s3_dialogue.jsonl"]
HP = dict(lr=1e-4, batch=8, seed=13, epochs=2, seq=256)
RECS = dict(r=16, lora_alpha=32, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
OUT = "/kaggle/working"; dev = "cuda" if torch.cuda.is_available() else "cpu"

def load(f):
    return [json.loads(l)["text"] for l in open(os.path.join(DATA, f), encoding="utf-8")]
DOCS = {f: load(f) for f in SEGS}
EV = {f: DOCS[f][-20:] for f in SEGS}
POOL = {f: DOCS[f][:-20] for f in SEGS}
N = sum(len(POOL[f]) for f in SEGS)

def get_base():
    tok = AutoTokenizer.from_pretrained(MPATH); tok.padding_side = "right"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    mdl = AutoModelForCausalLM.from_pretrained(MPATH, dtype=torch.bfloat16)
    mdl = get_peft_model(mdl, LoraConfig(task_type="CAUSAL_LM", **RECS))
    return tok, mdl

def enc(tok, texts):
    x = tok(texts, truncation=True, max_length=HP["seq"], padding="max_length", return_tensors="pt")
    ids = x["input_ids"].to(dev); at = x["attention_mask"].to(dev)
    lab = ids.clone(); lab[at == 0] = -100
    return ids, lab, at

@torch.no_grad()
def ce(tok, mdl, texts):
    tot = n = 0
    mdl.eval()
    for i in range(0, len(texts), 4):
        ids, lab, at = enc(tok, texts[i:i+4])
        loss = mdl(input_ids=ids, attention_mask=at, labels=lab).loss
        tot += float(loss) * len(ids); n += len(ids)
    mdl.train()
    return round(tot / max(n, 1), 4)

def bcat(mdl, key):
    return torch.cat([v.detach().float().cpu().reshape(-1) for k, v in mdl.named_parameters() if key in k])

def make_batches(arm):
    rng = random.Random(HP["seed"])
    idx = [(f, i) for f in SEGS for i in range(len(POOL[f]))]
    B = HP["batch"]
    if arm == "ladder":
        out = []
        for f in SEGS:
            seg = [(f, i) for i in range(len(POOL[f]))]
            out += [seg[j:j+B] for j in range(0, len(seg), B)]
        return out                      # 段内连排, 段间不换
    rng.shuffle(idx)
    return [idx[j:j+B] for j in range(0, len(idx), B)]

def run_arm(arm, tok, mdl):
    opt = torch.optim.AdamW([p for p in mdl.parameters() if p.requires_grad], lr=HP["lr"])
    per = make_batches(arm); rep = {"arm": arm, "batches_per_epoch": len(per), "checkpoints": []}
    ck_every = max(len(per) // 3, 1); seen = 0; prev = None; t0 = time.time(); losses = []
    for ep in range(HP["epochs"]):
        b = per if arm == "ladder" else make_batches(arm)   # ladder 两段同序, mixed 每轮重洗
        for batch in b:
            opt.zero_grad()
            ids, lab, at = enc(tok, [POOL[f][i] for f, i in batch])
            out = mdl(input_ids=ids, attention_mask=at, labels=lab)
            out.loss.backward(); opt.step()
            losses.append(float(out.loss)); seen += len(batch)
            if seen // HP["batch"] % ck_every == 0:
                cur = bcat(mdl, "lora_B.default.weight")
                row = {"docs_seen": seen, "frac": round(seen / (N * HP["epochs"]), 3),
                       "loss_win": round(float(np.mean(losses[-12:])), 4),
                       "Bfro": round(float(cur.norm()), 4),
                       "selfcos_prev": round(float(torch.nn.functional.cosine_similarity(cur, prev, dim=0)), 5)
                           if prev is not None and float(prev.norm()) > 1e-9 else None}
                for f in SEGS: row["ce_" + f.split(chr(95))[1][:4]] = ce(tok, mdl, EV[f])
                rep["checkpoints"].append(row); prev = cur.clone()
                print(arm, json.dumps(row), flush=True)
    rep["minutes"] = round((time.time() - t0) / 60, 1)
    return rep

master = {"plan": "LADDER-2", "base": BASE[0], "hp": HP, "pool": {f: len(POOL[f]) for f in SEGS},
          "pool_total": N, "arms": {}}
tok, mdl = get_base(); mdl.train()
try:
    for arm in ["ladder", "mixed"]:
        master["arms"][arm] = run_arm(arm, tok, mdl)
        json.dump(master, open(f"{OUT}/report_ladder2.json", "w"), indent=1)
        print("REPORT_SPIT", arm, base64.b64encode(json.dumps(master["arms"][arm]).encode()).decode()[:5800], flush=True)
        del mdl; torch.cuda.empty_cache()
        tok, mdl = get_base(); mdl.train()          # 两臂同起点 fresh 权重
    master["sentinel"] = "ladder2_ok"
except Exception as ex:
    master["error"] = type(ex).__name__ + ": " + str(ex)[:200] + " || " + _tb.format_exc()[-600:]
json.dump(master, open(f"{OUT}/report_ladder2.json", "w"), indent=1)
print("REPORT_LINE", base64.b64encode(open(f"{OUT}/report_ladder2.json", "rb").read()).decode())
print("DONE", master.get("sentinel", master.get("error", "?")))
