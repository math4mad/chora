# LADDER-0 SEAL · baby-dimension 全举 24 排列 —— 判据先冻: PREREG_LADDER-0_seal_babydim.md
import os, json, time, base64, gzip, hashlib, itertools, collections
import numpy as np, torch
import subprocess as _sp, sys as _s
_sp.run([_s.executable,"-m","pip","uninstall","-y","torchao"], capture_output=True)
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
import traceback as _tb
PAY = "###PAY###"
raw = gzip.decompress(base64.b64decode(PAY))
assert hashlib.sha256(raw).hexdigest()[:12] == "###RAWSHA12###", "corpus drift"
ITEMS = json.loads(raw)
MODEL = "/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1"
OUT = "/kaggle/working"; HP = dict(lr=1e-4, epochs=8, seed=13, seq=160)
REC = dict(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
dev = "cuda"
tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "right"
if tok.pad_token is None: tok.pad_token = tok.eos_token
def enc(m):
    full = tok.apply_chat_template(m, tokenize=False, add_generation_prompt=False)
    pr = tok.apply_chat_template(m[:1] + [{"role":"assistant","content":""}], tokenize=False, add_generation_prompt=True)
    fi = tok(full, truncation=True, max_length=HP["seq"], add_special_tokens=False)["input_ids"]
    pi = tok(pr, add_special_tokens=False)["input_ids"]
    ids = torch.tensor([fi]); lab = torch.tensor([[-100]*len(pi) + fi[len(pi):]]); at = torch.ones_like(ids)
    return ids.to(dev), lab.to(dev), at.to(dev)
@torch.no_grad()
def nll(model, pair):
    ids, lab, at = enc(pair)
    return float(model(input_ids=ids, attention_mask=at, labels=lab).loss)
def fresh():
    torch.manual_seed(HP["seed"]); np.random.seed(HP["seed"])
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16)
    m = get_peft_model(m, LoraConfig(task_type="CAUSAL_LM", **REC)); return m.to(dev).train()
TRAIN = {"I": [ITEMS["I"][0], ITEMS["I"][1]], "II": [ITEMS["II"][0], ITEMS["II"][1]]}
PROBE = {"I": [ITEMS["I"][2], ITEMS["I"][3]], "II": [ITEMS["II"][2], ITEMS["II"][3]]}
units = [("I",0),("I",1),("II",0),("II",1)]
perms = list(itertools.permutations(units))
report = {"plan":"LADDER-0","hp":HP,"n_perms":len(perms),"raw_sha12":"###RAWSHA12###","runs":[]}
t00 = time.time()
def etasq(groups):
    allv=[x for v in groups.values() for x in v]; gm=float(np.mean(allv))
    ss_tot=sum((x-gm)**2 for x in allv)
    if ss_tot < 1e-12: return 0.0
    ss_w=sum(sum((x-float(np.mean(v)))**2 for x in v) for v in groups.values())
    return round(1-ss_w/ss_tot,3)
try:
    for pi, perm in enumerate(perms):
        model = fresh()
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=HP["lr"])
        a0 = float(np.mean([nll(model,p) for p in PROBE["I"]])); b0 = float(np.mean([nll(model,p) for p in PROBE["II"]]))
        traj = [{"step":0,"nllI":round(a0,4),"nllII":round(b0,4)}]
        for ep in range(HP["epochs"]):
            for si,(dom,idx) in enumerate(perm, start=1):
                ids,lab,at = enc(TRAIN[dom][idx]); loss = model(input_ids=ids,attention_mask=at,labels=lab).loss
                opt.zero_grad(); loss.backward(); opt.step()
                step = ep*4+si
                if step % 4 == 0:
                    a = float(np.mean([nll(model,p) for p in PROBE["I"]])); b = float(np.mean([nll(model,p) for p in PROBE["II"]]))
                    traj.append({"step":step,"nllI":round(a,4),"nllII":round(b,4)})
        dom_last = perm[-1][0]; other = "II" if dom_last=="I" else "I"
        R = round(traj[-1]["nll"+dom_last] - traj[-1]["nll"+other], 4)
        def posinc(key):
            s=[t[key] for t in traj]; return sum(max(0.0, s[i+1]-s[i]) for i in range(len(s)-1))
        A = round(posinc("nllI")+posinc("nllII"), 4)
        pI=[i for i,(d,_) in enumerate(perm) if d=="I"]; pJ=[i for i,(d,_) in enumerate(perm) if d=="II"]
        gr = (pI[1]-pI[0]) + (pJ[1]-pJ[0])
        report["runs"].append({"perm":[f"{d}{i+1}" for d,i in perm],"inter":str(tuple(pI)),
                               "intra":str(tuple(i for _,i in perm)),"R":R,"A":A,"g":gr,"traj":traj})
        del model, opt; torch.cuda.empty_cache()
        if pi % 4 == 0:
            json.dump(report, open(f"{OUT}/report_ladder0.json","w")); print(f"perm {pi}/24 t={round(time.time()-t00)}s", flush=True)
    runs = report["runs"]
    neg = sum(1 for r in runs if r["R"] < 0)
    gA = collections.defaultdict(list); iA = collections.defaultdict(list)
    for r in runs: gA[r["g"]].append(r["A"]); iA[r["inter"]].append(r["A"])
    blockA = float(np.mean(gA[2])) if gA.get(2) else 9.0
    midA = float(np.mean(gA[4])) if gA.get(4) else 0.0
    wideA = float(np.mean(gA[6])) if gA.get(6) else 0.0
    e_i, e_g = etasq(iA), etasq(gA)
    report["verdict"] = {"R_neg_count": f"{neg}/24", "H0a_pass": neg>=16,
                         "eta2_inter": e_i, "eta2_intra_g": e_g, "H0b_pass": e_i >= e_g,
                         "A_by_g": {"g2_block": round(blockA,4), "g4_mid": round(midA,4), "g6_wide": round(wideA,4)},
                         "H0c_pass": blockA >= 2*max(midA, wideA, 1e-6)}
    report["sentinel"] = "ladder0_ok"
except Exception as ex:
    report["error"] = type(ex).__name__+": "+str(ex)[:200]+" || "+_tb.format_exc()[-600:]
json.dump(report, open(f"{OUT}/report_ladder0.json","w"))
try: print("REPORT_LINE", base64.b64encode(open(f"{OUT}/report_ladder0.json","rb").read()).decode()[:60000], flush=True)
except Exception: pass
print("DONE", report.get("sentinel", report.get("error","?")))
