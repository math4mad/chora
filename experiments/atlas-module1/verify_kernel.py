# 模块一 · 夜核 — 在 Kaggle/T4 上验证概念图谱的可分性 (0.5B 挂载, 零下载除 torchao 疫苗)
# 指标: 每空间 intra 平均余弦 · 全局 inter 最大碰撞 (跨空间 token 对) · 弱空间榜
import os as _osx; _osx.system("python -m pip uninstall -y -q torchao 2>/dev/null; pip uninstall -y -q torchao 2>/dev/null"); del _osx  # 疫苗二代: 逐出可选集成, transformers 便不问版本
import base64, hashlib, json, itertools, time
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import atlas_embed
MOUNT="/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1"
import subprocess as _sp, sys as _s
_sp.run([_s.executable,"-m","pip","install","-q","--upgrade","torchao"],capture_output=True)
raw=base64.b64decode(atlas_embed.ATLAS_B64)
assert hashlib.sha256(raw).hexdigest()==atlas_embed.ATLAS_SHA256, "atlas 字节漂移"
A=json.loads(raw); toks=[t["token"] for s in A["spaces"] for t in s["tokens"]]
dev="cuda" if torch.cuda.is_available() else "cpu"
tok=AutoTokenizer.from_pretrained(MOUNT)
model=AutoModelForCausalLM.from_pretrained(MOUNT,dtype=torch.float16).eval().to(dev)
V=[]
t0=time.time()
with torch.no_grad():
    for i,t in enumerate(toks):
        e=tok(t,return_tensors="pt",add_special_tokens=False).to(dev)
        h=model.model(**e).last_hidden_state[0,-1].float().cpu().numpy()
        V.append(h/(np.linalg.norm(h)+1e-9))
        if i%60==0: print("embed",i,flush=True)
V=np.stack(V)
idx=0; spaces=[]
for s in A["spaces"]:
    n=len(s["tokens"]); M=V[idx:idx+n]; idx+=n
    pairs=[(M[i]@M[j]) for i,j in itertools.combinations(range(n),2)]
    spaces.append({"space":s["concept_space"],"domain":s["domain"],
                   "intra_mean_cos":round(float(np.mean(pairs)),4),"n":n})
by_space={}
k=0
for s in A["spaces"]:
    by_space[s["concept_space"]]=list(range(k,k+len(s["tokens"]))); k+=len(s["tokens"])
worst=[]
names=list(by_space)
S=V@V.T
for a,b in itertools.combinations(names,2):
    mx=float(max(S[i][j] for i in by_space[a] for j in by_space[b]))
    worst.append((mx,a,b))
worst.sort(reverse=True)
rep={"run":"atlas-m1-verify","tokens":len(toks),"embed_minutes":round((time.time()-t0)/60,1),
 "hardware":{"gpu":torch.cuda.get_device_name(0) if dev=="cuda" else "cpu"},
 "intra_mean_overall":round(float(np.mean([s["intra_mean_cos"] for s in spaces])),4),
 "weakest_spaces":sorted(spaces,key=lambda x:x["intra_mean_cos"])[:10],
 "top_inter_collisions":[{"cos":round(m,4),"a":a,"b":b} for m,a,b in worst[:15]],
 "verdict_note":"H-A1 预备判据: intra 中位显著>0.75 且无 inter>intra中位 的跨空间碰撞 → 图谱可分, 可进模块二"}
json.dump(rep,open("/kaggle/working/report_atlas_m1.json","w"),ensure_ascii=False,indent=1)
print(json.dumps({k:rep[k] for k in ["intra_mean_overall","embed_minutes"]},indent=1))
print("REPORT_LINE", __import__("base64").b64encode(open("/kaggle/working/report_atlas_m1.json","rb").read()).decode())  # REPORT LINE
