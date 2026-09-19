# Exp11 · the whole matrix on the Kaggle workhorse — 5 bases × 7 arms, one session.
# Bases arrive via Kaggle-models-hub offline mounts (declared in kernel-metadata model_sources).
# Per-base geometry report flushed to /kaggle/working; a dead cell is recorded, never silent.
import os, json, time, hashlib, base64, itertools
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from safetensors.torch import save_file
import matrix_corpus_embed

DATA="/tmp/exp11-corpus"; os.makedirs(DATA, exist_ok=True)
for f,m in matrix_corpus_embed.PAYLOAD.items():
    raw=base64.b64decode(m["b64"])
    assert hashlib.sha256(raw).hexdigest()==m["sha256"], "corpus drift: "+f
    open(os.path.join(DATA,f),"wb").write(raw)

BASES=[  # display name, mount glob under /kaggle/input/models, epochs per arm
 ("qwen2.5-1.5b-instruct","qwen-lm/qwen2.5/transformers/1.5b-instruct/1"),
 ("qwen2.5-3b-instruct","qwen-lm/qwen2.5/transformers/3b-instruct/1"),
 ("qwen2.5-7b-instruct","qwen-lm/qwen2.5/transformers/7b-instruct/1"),
 ("llama-3.2-1b-instruct","metaresearch/llama-3.2/transformers/1b-instruct/1"),
]
ARMS={"spring":("corpus_spring.jsonl",6),"summer":("corpus_summer.jsonl",6),"code":("corpus_code.jsonl",6),
      "legal":("corpus_legal.jsonl",6),"medical":("corpus_medical.jsonl",6),
      "mid":("corpus_mid.jsonl",3),"general":("corpus_general.jsonl",6)}
RECIPE=dict(r=16,lora_alpha=32,lora_dropout=0.05,target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
HP=dict(lr=1e-4,batch=2,accum=4,seed=13)
MODS=RECIPE["target_modules"]; OUT="/kaggle/working"
dev="cuda" if torch.cuda.is_available() else "cpu"

def enc_pair(tok,u,a):
    msgs=[{"role":"user","content":u},{"role":"assistant","content":a}]
    p=tok.apply_chat_template(msgs[:1]+[{"role":"assistant","content":""}],tokenize=False,add_generation_prompt=True)
    full=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=False)
    fi=tok(full,add_special_tokens=False)["input_ids"]; pi=tok(p,add_special_tokens=False)["input_ids"]
    return fi,[-100]*len(pi)+fi[len(pi):]
def collate(fs,tok):
    pad=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    L=max(len(f[0]) for f in fs)
    ids=[];lab=[];at=[]
    for i,l in fs:
        n=L-len(i); ids.append(i+[pad]*n); lab.append(l+[-100]*n); at.append([1]*len(i)+[0]*n)
    return torch.tensor(ids),torch.tensor(lab),torch.tensor(at)
def k90(s):
    e=s**2/(s**2).sum(); return int(np.searchsorted(np.cumsum(e),0.90)+1)
def parse(ad):
    d={}
    for k,v in ad.items():
        for kind in ("A","B"):
            tag=f".lora_{kind}.weight"
            if tag in k:
                L=int(k.split(".layers.")[1].split(".")[0]); m=k.split(f".layers.{L}.")[1].split(tag)[0].split(".")[-1]
                d[(L,m,kind)]=v.astype(np.float64)
    return d

def geometry(S,layers):
    keys=list(itertools.product(layers,MODS)); res={}
    def dw(a):
        parts=[]
        for L,m in keys:
            U,s,Vt=S[a][(L,m,"A")]; W,b,X=S[a][(L,m,"B")]
            parts.append((((W*b)@X)@((U*s)@Vt)).ravel())
        return np.concatenate(parts)
    for a1,a2 in itertools.combinations(S,2):
        va=0.0
        for L,m in keys:
            _,s1,V1=S[a1][(L,m,"A")]; _,_,V2=S[a2][(L,m,"A")]
            k=k90(s1); va+=float(np.linalg.norm(V1[:k]@V2[:k].T,"fro"))
        d1,d2=dw(a1),dw(a2)
        res[f"{a1}~{a2}"]={"V-A_k90":round(va/len(keys),3),
            "dWov":round(float(d1@d2/(np.linalg.norm(d1)*np.linalg.norm(d2))),4)}
    return res

master={"run":"exp11-kaggle-matrix","ts":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "hp":{**HP,"recipe":RECIPE},"hardware":{"gpu":torch.cuda.get_device_name(0) if dev=="cuda" else "cpu","torch":torch.__version__},
 "bases":{}}
for disp,rel in BASES:
    path="/kaggle/input/models/"+rel
    t0=time.time()
    if not os.path.isdir(path):
        master["bases"][disp]={"error":"mount absent","path":path}; continue
    tok=AutoTokenizer.from_pretrained(path); tok.padding_side="right"
    adapters={}
    try:
        for arm,(fname,ep) in ARMS.items():
            torch.manual_seed(HP["seed"])
            model=AutoModelForCausalLM.from_pretrained(path,dtype=torch.bfloat16)
            model=get_peft_model(model,LoraConfig(task_type=TaskType.CAUSAL_LM,**RECIPE,bias="none"))
            model.to(dev)
            feats=[]
            for line in open(os.path.join(DATA,fname)):
                m=json.loads(line)["messages"]; feats.append(enc_pair(tok,m[0]["content"],m[1]["content"]))
            opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=HP["lr"]); last=0.0
            for e in range(ep):
                perm=torch.randperm(len(feats)); acc=nb=0
                for bi in range(0,len(feats),HP["batch"]):
                    batch=[feats[i] for i in perm[bi:bi+HP["batch"]].tolist()]
                    ids,lab,at=collate(batch,tok); ids,lab,at=ids.to(dev),lab.to(dev),at.to(dev)
                    o=model(input_ids=ids,attention_mask=at,labels=lab)
                    (o.loss/HP["accum"]).backward(); acc+=o.loss.item(); nb+=1
                    if nb%HP["accum"]==0: opt.step(); opt.zero_grad()
                last=acc/nb
            sd={k:v.float().cpu() for k,v in model.state_dict().items() if "lora_" in k}
            fn=os.path.join(OUT,f"{disp}__adapter_{arm}.safetensors"); save_file(sd,fn)
            adapters[arm]=sd
            del model; torch.cuda.empty_cache()
            print(f"{disp}/{arm} loss {last:.3f} {time.time()-t0:.0f}s",flush=True)
        S={a:parse(ad) for a,ad in ((a,{k:np.linalg.svd(v,full_matrices=False) for k,v in parse(ad).items()}) for a,ad in adapters.items())}
        layers=sorted({k[0] for k in list(S.values())[0]})
        geo=geometry(S,layers)
        msha={f"{disp}~{a}":hashlib.sha256(open(os.path.join(OUT,f"{disp}__adapter_{a}.safetensors"),'rb').read()).hexdigest() for a in adapters}
        master["bases"][disp]={"minutes":round((time.time()-t0)/60,1),"geometry":geo,"adapter_sha256":msha}
    except Exception as ex:
        master["bases"][disp]={"error":type(ex).__name__+": "+str(ex)[:200],"minutes":round((time.time()-t0)/60,1)}
    json.dump(master,open(os.path.join(OUT,"report_exp11_matrix.json"),"w"),indent=1)  # flush每基座一局, 断亦留档
    print("== base done:",disp,flush=True)
print(json.dumps({b:("ERR" if "error" in v else v.get("minutes")) for b,v in master["bases"].items()},indent=1))
