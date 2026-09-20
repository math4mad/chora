MOUNT="/kaggle/input/models/metaresearch/llama-3.2/transformers/1b-instruct/1"
_D={}
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

import csv, glob, random as _r
# llama 系 tokenizer 补 pad 保险
if tok.pad_token is None: tok.pad_token=tok.eos_token
def rd(pat):
    for f in glob.glob(pat):
        try: return list(csv.DictReader(open(f,encoding="utf8",errors="ignore")))
        except Exception: pass
    return []
DOR=rd("/kaggle/input/**/BallonDOr.csv")
NBA=rd("/kaggle/input/**/*Draft*Pick*.csv")
HOF=rd("/kaggle/input/**/HOF_Position_Players.csv")
print("rows:",len(DOR),len(NBA),len(HOF),flush=True)
def lists_dor():
    out=[]
    for y in ["1995","2008","2013","2023"]:
        rs=sorted([r for r in DOR if str(r.get("Year"))==y and r.get("Rank","9").isdigit()],key=lambda r:int(r["Rank"]))[:6]
        if len(rs)>=4: out.append((f"{y}年金球奖最终排名前五(按名次)",[f"{r['Rank']} {r['Player']}({r.get('Club','')})" for r in rs]))
    return out
def lists_nba():
    out=[]
    for y in ["2002","2003"]:
        rs=sorted([r for r in NBA if str(r.get("season"))==y and (r.get("overall_pick") or "").strip().isdigit()],key=lambda r:int(r["overall_pick"]))[:8]
        if len(rs)>=5: out.append((f"{y}年NBA选秀首轮顺位(按顺位)",[f"{r['overall_pick']} {r['player']}" for r in rs]))
    return out
def lists_hof():
    out=[]
    for col in ["WAR","HR"]:
        try:
            rs=sorted(HOF,key=lambda r:-(float(r.get(col) or 0)))[:10]
            if len(rs)>=8: out.append((f"棒球名人堂球员历史{col}排行(从高到低)",[f"{i+1} {r['Name']} {r.get(col)}" for i,r in enumerate(rs)]))
        except Exception: pass
    return out
PROMPTS=["列一下：","请依次报出：","按顺序说：","背一下："]
def to_pairs(title, names, mode):
    seq=list(names)
    if mode=="rev": seq=seq[::-1]
    if mode=="shuf": _r.Random(7).shuffle(seq)
    ans=title+"——"+"\n".join(seq)
    return [(p+title,ans) for p in PROMPTS]
res={"exp":"16b-ordinal-llama1b","domains":{}}
for dm,ls in (("ballondor",lists_dor()),("nbadraft",lists_nba()),("hofwar",lists_hof())):
    if not ls: res["domains"][dm]={"error":"no rows parsed"}; continue
    texts={m:[enc_pair(u,a) for t,ns in ls for u,a in to_pairs(t,ns,m)] for m in ("ord","rev","shuf")}
    arms={}
    for m in ("ord","rev","shuf"):
        sd=f"/tmp/arms/{dm}_{m}"; ad,loss=train(texts[m],save_dir=sd)
        arms[m]={"loss":loss,"d":dvec(ad),"sd":sd}
        print(dm,m,"trained",flush=True)
    from peft import PeftModel
    def nll(sd,feats):
        mm=AutoModelForCausalLM.from_pretrained(MOUNT,dtype=torch.bfloat16)
        mm=PeftModel.from_pretrained(mm,sd); mm.to(dev); mm.eval(); tot=0.0; n=0
        with torch.no_grad():
            for ch in [feats[i:i+2] for i in range(0,len(feats),2)]:
                ids,la,at=collate(ch); tot+=float(mm(input_ids=ids,attention_mask=at,labels=la).loss)*len(ch); n+=len(ch)
        del mm; torch.cuda.empty_cache(); return round(tot/max(1,n),4)
    M={am:{tx:nll(arms[am]["sd"],texts[tx]) for tx in ("ord","rev","shuf")} for am in ("ord","rev","shuf")}
    res["domains"][dm]={"nll_matrix":M,
      "direction_index":{am:round(M[am]["rev"]-M[am]["ord"],4) for am in M},
      "angles":{"ord~rev":ang(arms["ord"]["d"],arms["rev"]["d"]),"ord~shuf":ang(arms["ord"]["d"],arms["shuf"]["d"]),"rev~shuf":ang(arms["rev"]["d"],arms["shuf"]["d"])},
      "n_lists":len(ls)}
    for k,v in arms.items(): res.setdefault("last_d",{})[k]=0
    _D.setdefault(dm,arms["ord"]["d"])
res["cross_domain_ord"]={f"{a}~{b}":ang(_D[a],_D[b]) for a,b in [("ballondor","nbadraft"),("nbadraft","hofwar"),("ballondor","hofwar")] if a in _D and b in _D}
res["minutes"]=round((time.time()-t0)/60,1)
res["prereg_note"]="若 base 预训练已含答案, NLL 绝对值不可比; 本实验判决全部基于同臂内 rev-ord 差值与方向翻转, 与记忆泄漏无关"
json.dump(res,open("/kaggle/working/report_exp16b.json","w"),ensure_ascii=False)
print("REPORT_LINE",base64.b64encode(json.dumps(res).encode()).decode())
