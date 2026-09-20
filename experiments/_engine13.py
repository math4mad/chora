# Exp13 弹体共用引擎 (各 run.py 头部注入 CORPORA 与 MOUNT 后 exec 本文件)
import base64, json, math, time
import numpy as np, torch
import os as _osx; _osx.system("python -m pip uninstall -y -q torchao 2>/dev/null")
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
dev = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(MOUNT); tok.padding_side = "right"
RECIPE = dict(r=16, lora_alpha=32, lora_dropout=0.05,
              target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
SEED, EPOCHS, BATCH, ACCUM, LR = 13, 6, 2, 4, 1e-4
t0 = time.time()

def _pairs(c):
    return [(m["messages"][0]["content"], m["messages"][1]["content"]) for m in c]
def enc_pair(u, a):
    ms = [{"role":"user","content":u},{"role":"assistant","content":a}]
    p = tok.apply_chat_template(ms[:1]+[{"role":"assistant","content":""}], tokenize=False, add_generation_prompt=True)
    f = tok.apply_chat_template(ms, tokenize=False, add_generation_prompt=False)
    fi = tok(f, add_special_tokens=False)["input_ids"]; pi = tok(p, add_special_tokens=False)["input_ids"]
    return fi, [-100]*len(pi) + fi[len(pi):]
def mix(feats_a, feats_b, p):
    n = len(feats_a); k = int(round(n*p))
    ra = np.random.default_rng(SEED).choice(len(feats_a), n-k, replace=(n-k) > len(feats_a))
    rb = np.random.default_rng(SEED+1).choice(len(feats_b), k, replace=k > len(feats_b))
    return [feats_a[i] for i in ra] + [feats_b[i] for i in rb]
def collate(b):
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    L = max(len(f[0]) for f in b); ids=[]; lab=[]; at=[]
    for i,l in b:
        n = L-len(i); ids.append(i+[pad]*n); lab.append(l+[-100]*n); at.append([1]*len(i)+[0]*n)
    return torch.tensor(ids).to(dev), torch.tensor(lab).to(dev), torch.tensor(at).to(dev)
def train(batch, save_dir=None):
    torch.manual_seed(SEED); np.random.seed(SEED)
    model = AutoModelForCausalLM.from_pretrained(MOUNT, dtype=torch.bfloat16)
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, **RECIPE, bias="none")); model.to(dev)
    opt = torch.optim.AdamW([q for q in model.parameters() if q.requires_grad], lr=LR); step = 0; last = 0.0
    for ep in range(EPOCHS):
        pm = torch.randperm(len(batch)); acc = 0.0; nb = 0
        for bi in range(0, len(batch), BATCH):
            ids, la, at = collate([batch[i] for i in pm[bi:bi+BATCH].tolist()])
            loss = model(input_ids=ids, attention_mask=at, labels=la).loss / ACCUM
            loss.backward(); acc += loss.item()*ACCUM; nb += 1; step += 1
            if step % ACCUM == 0: opt.step(); opt.zero_grad()
        last = acc/max(1,nb)
    if save_dir: model.save_pretrained(save_dir)
    ad = {k:v.detach().float().cpu().numpy() for k,v in model.state_dict().items() if "lora_" in k}
    del model; torch.cuda.empty_cache(); return ad, round(float(last), 3)
def dvec(ad):
    ps = []
    for k in ad:
        if ".lora_A." in k:
            A = ad[k]; B = ad[k.replace(".lora_A.",".lora_B.")]; ps.append((B@A).ravel())
    return np.concatenate(ps)
def ang(u, w):
    c = float(u @ w / (np.linalg.norm(u)*np.linalg.norm(w) + 1e-12))
    return round(math.degrees(math.acos(max(-1.0, min(1.0, c)))), 2)

def probe_maker(feats_pos, feats_neg):
    base = AutoModelForCausalLM.from_pretrained(MOUNT, dtype=torch.float16).eval().to(dev)
    def svec(ids):
        with torch.no_grad():
            h = base.model(input_ids=torch.tensor([ids]).to(dev)).last_hidden_state[0].float().cpu().numpy()
        return h.mean(0)
    P = np.stack([svec(i) for i,l in feats_pos]); N = np.stack([svec(i) for i,l in feats_neg])
    MU = np.vstack([P,N]).mean(0)
    def C(v): w = np.asarray(v,float)-MU; return w/(np.linalg.norm(w)+1e-9)
    X = np.vstack([C(P),C(N)]); Y = np.r_[np.ones(len(P)), np.zeros(len(N))]
    Xa = np.hstack([X, np.ones((len(X),1))]); W = np.linalg.lstsq(Xa, Y, rcond=None)[0]
    def probe(ids): return float(1/(1+math.exp(-float(np.r_[C(svec(ids)),1.0]@W))))
    return probe, base
