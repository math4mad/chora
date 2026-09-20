# Exp13 · 混合之缝 (mix-gap scan) — 0.5B, 园线超参, 11 点比例梯度
# 假说 (PREREG 在册): H13.1 平滑(S 型, 无跳变) vs H13.2 Gap(p* 处跳变/双峰)
import base64, json, math, time
import numpy as np, torch
import os as _osx; _osx.system("python -m pip uninstall -y -q torchao 2>/dev/null")
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType

MOUNT = "/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1"
SPR = [json.loads(l) for l in base64.b64decode(_SPR_B64).decode().splitlines() if l.strip()]
SUM = [json.loads(l) for l in base64.b64decode(_SU_B64).decode().splitlines() if l.strip()]
BND = _BND
RECIPE = dict(r=16, lora_alpha=32, lora_dropout=0.05,
              target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
SEED, EPOCHS, BATCH, ACCUM, LR = 13, 6, 2, 4, 1e-4
dev = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(MOUNT); tok.padding_side = "right"
base = AutoModelForCausalLM.from_pretrained(MOUNT, dtype=torch.float16).eval().to(dev)
t0 = time.time()

def enc_pair(u, a):
    ms = [{"role":"user","content":u},{"role":"assistant","content":a}]
    p = tok.apply_chat_template(ms[:1]+[{"role":"assistant","content":""}], tokenize=False, add_generation_prompt=True)
    f = tok.apply_chat_template(ms, tokenize=False, add_generation_prompt=False)
    fi = tok(f, add_special_tokens=False)["input_ids"]; pi = tok(p, add_special_tokens=False)["input_ids"]
    return fi, [-100]*len(pi) + fi[len(pi):]

FS = [enc_pair(m["messages"][0]["content"], m["messages"][1]["content"]) for m in SPR]
FU = [enc_pair(m["messages"][0]["content"], m["messages"][1]["content"]) for m in SUM]

def collate(b):
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    L = max(len(f[0]) for f in b)
    ids, lab, at = [], [], []
    for i, l in b:
        n = L - len(i); ids.append(i+[pad]*n); lab.append(l+[-100]*n); at.append([1]*len(i)+[0]*n)
    return torch.tensor(ids).to(dev), torch.tensor(lab).to(dev), torch.tensor(at).to(dev)

def svec(ids):
    with torch.no_grad():
        h = base.model(input_ids=torch.tensor([ids]).to(dev)).last_hidden_state[0].float().cpu().numpy()
    return h.mean(0)

def train_mix(p):
    torch.manual_seed(SEED); np.random.seed(SEED)
    n = len(FS); k = int(round(n*p))
    idxS = np.random.default_rng(SEED).choice(len(FS), n-k, replace=(n-k) > len(FS))
    idxU = np.random.default_rng(SEED+1).choice(len(FU), k, replace=k > len(FU))
    batch = [FS[i] for i in idxS] + [FU[i] for i in idxU]
    model = AutoModelForCausalLM.from_pretrained(MOUNT, dtype=torch.bfloat16)
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, **RECIPE, bias="none"))
    model.to(dev)
    opt = torch.optim.AdamW([q for q in model.parameters() if q.requires_grad], lr=LR)
    step = 0
    for ep in range(EPOCHS):
        pm = torch.randperm(len(batch)); acc = 0.0
        for bi in range(0, len(batch), BATCH):
            ids, la, at = collate([batch[i] for i in pm[bi:bi+BATCH].tolist()])
            loss = model(input_ids=ids, attention_mask=at, labels=la).loss / ACCUM
            loss.backward(); acc += loss.item()*ACCUM
            step += 1
            if step % ACCUM == 0: opt.step(); opt.zero_grad()
    ad = {kk: vv.detach().float().cpu().numpy() for kk, vv in model.state_dict().items() if "lora_" in kk}
    del model; torch.cuda.empty_cache()
    return ad, round(acc/max(1, len(batch)//BATCH), 3)

def dvec(ad):
    parts = []
    for kk in ad:
        if ".lora_A." in kk:
            A = ad[kk]; B = ad[kk.replace(".lora_A.", ".lora_B.")]
            parts.append((B @ A).ravel())
    return np.concatenate(parts)

# —— 探针: 中心化 + L2 逻辑回归 (lstsq on centered feats) ——
Ae = np.stack([svec(i) for i, l in FS]); Be = np.stack([svec(i) for i, l in FU])
MU = np.vstack([Ae, Be]).mean(0)
def C(v):
    w = np.asarray(v, float) - MU; return w/(np.linalg.norm(w)+1e-9)
X = np.vstack([C(Ae), C(Be)]); Y = np.r_[np.zeros(len(Ae)), np.ones(len(Be))]
Xa = np.hstack([X, np.ones((len(X), 1))])
Wt = np.linalg.solve(Xa.T@Xa + 1e-2*np.eye(Xa.shape[1]), Xa.T@Y)
def probe(ids):
    z = np.r_[C(svec(ids)), 1.0]
    return float(1/(1+math.exp(-float(z@Wt))))

res = {"kernel": "exp13-mixscan", "seed": SEED, "hp": {"epochs": EPOCHS, "batch": BATCH, "accum": ACCUM, "lr": LR, "recipe": RECIPE},
       "probe_train_acc": None, "points": [], "boundary": []}
def clf(ids): return probe(ids)
tr_pred = np.array([probe(i) for i, l in FS[:20]+FU[:20]])
res["probe_train_acc"] = round(float(((tr_pred > .5) == np.r_[np.zeros(20), np.ones(20)]).mean()), 3)

D = {}
for i in range(11):
    p = i/10
    ad, loss = train_mix(p)
    D[i] = dvec(ad)
    res["points"].append({"p": p, "loss": loss})
    print(f"mix {p:.1f} loss {loss} t={time.time()-t0:.0f}s", flush=True)

for pt in res["points"]:
    i = int(round(pt["p"]*10))
    v, v0, v10 = D[i], D[0], D[10]
    c0 = float(v@v0/(np.linalg.norm(v)*np.linalg.norm(v0)+1e-12))
    c10 = float(v@v10/(np.linalg.norm(v)*np.linalg.norm(v10)+1e-12))
    pt["cos_vs_M0"] = round(c0, 4); pt["cos_vs_M10"] = round(c10, 4)
    pt["ang_vs_M0"] = round(math.degrees(math.acos(min(1, max(-1, c0)))), 2)
    pt["ang_vs_M10"] = round(math.degrees(math.acos(min(1, max(-1, c10)))), 2)
    pt["interp_gap"] = round(abs((pt["ang_vs_M0"]+pt["ang_vs_M10"]) - 180 if False else (pt["ang_vs_M0"]/(pt["ang_vs_M0"]+pt["ang_vs_M10"]+1e-9) - pt["p"])), 4)  # 与线性插值的偏离
for x in BND:
    ids = tok(x, add_special_tokens=False)["input_ids"]
    res["boundary"].append({"text": x, "P_summer": round(probe(ids), 4)})
res["minutes"] = round((time.time()-t0)/60, 1)
res["h13_note"] = "H13.1 smooth S-curve / H13.2 jump: inspect ang_vs_M0(p) monotonicity & boundary bimodality"
json.dump(res, open("/kaggle/working/report_exp13.json", "w"), ensure_ascii=False, indent=1)
print("REPORT_LINE", base64.b64encode(json.dumps(res).encode()).decode())
