# xdom 基线核 — 无训练对照: 0.5B 嵌入 172 空间质心 vs 125 上下文 → softmax 伪后验
import os as _osx; _osx.system("python -m pip uninstall -y -q torchao 2>/dev/null")
import base64, hashlib, json, time
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from payload_embed import PROBES_B64, PROBES_SHA, ATLAS_B64, ATLAS_SHA
assert hashlib.sha256(base64.b64decode(PROBES_B64)).hexdigest()==PROBES_SHA
assert hashlib.sha256(base64.b64decode(ATLAS_B64)).hexdigest()==ATLAS_SHA
P=json.loads(base64.b64decode(PROBES_B64)); A=json.loads(base64.b64decode(ATLAS_B64))
MOUNT="/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1"
dev="cuda" if torch.cuda.is_available() else "cpu"
tok=AutoTokenizer.from_pretrained(MOUNT)
model=AutoModelForCausalLM.from_pretrained(MOUNT,dtype=torch.float16).eval().to(dev)
def emb(text):
    e=tok(text,return_tensors="pt",add_special_tokens=False).to(dev)
    with torch.no_grad(): h=model.model(**e).last_hidden_state[0,-1].float().cpu().numpy()
    return h/(np.linalg.norm(h)+1e-9)
t0=time.time()
cent={}; space_names=[]
for s in A["spaces"]:
    V=np.stack([emb(t["token"]+f"（{s['domain']}·{s['concept_space']}）") for t in s["tokens"]])
    c=V.mean(0); cent[s["concept_space"]]=c/ (np.linalg.norm(c)+1e-9); space_names.append(s["concept_space"])
print("spaces embedded", len(cent), flush=True)
rows=[]
for grp in P["probes"]:
    for pr in grp["probes"]:
        v=emb(pr["context"])
        sc={n:float(v@c) for n,c in cent.items()}
        names=list(sc); logits=np.array([sc[n] for n in names])/0.05
        p=np.exp(logits-logits.max()); p/=p.sum()
        top=np.argsort(p)[::-1][:3]
        exp=pr["expected"]; in_reg= exp in sc
        rows.append({"no":grp["no"],"token":grp["token"],"ctx":pr["context"],"expected":exp,
          "expected_in_registry":bool(in_reg),"argmax":names[top[0]],
          "post_expected":round(float(sc and p[names.index(exp)] if in_reg else 0),4),
          "top3":[[names[i],round(float(p[i]),3)] for i in top],"split":grp["split"]})
hit_c=[r for r in rows if r["split"]=="calib" and r["expected_in_registry"]]
hit_h=[r for r in rows if r["split"]=="holdout" and r["expected_in_registry"]]
rep={"run":"xdom-baseline","hardware":torch.cuda.get_device_name(0) if dev=="cuda" else "cpu",
 "minutes":round((time.time()-t0)/60,1),"n_ctx":len(rows),
 "acc_calib":round(np.mean([r["argmax"]==r["expected"] for r in hit_c]),3) if hit_c else None,
 "acc_holdout":round(np.mean([r["argmax"]==r["expected"] for r in hit_h]),3) if hit_h else None,
 "unmapped_expected":sorted({r["expected"] for r in rows if not r["expected_in_registry"]}),
 "mean_margin_calib":round(float(np.mean([r["post_expected"] for r in hit_c])),4) if hit_c else None,
 "rows":rows}
json.dump(rep,open("/kaggle/working/report_xdom_baseline.json","w"),ensure_ascii=False,indent=1)
print("REPORT_LINE", base64.b64encode(open("/kaggle/working/report_xdom_baseline.json","rb").read()).decode())
