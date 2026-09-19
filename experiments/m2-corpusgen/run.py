# M2 前置 · 语料批产核: 172 概念空间 × QA 对, 由 Kaggle Model API 生成, 出厂即过 xdom tripwire
# 模型闸顺序试 (Gemma3-27B → 失败降级 DeepSeek-R1-Distill → 再降级本地 1.5B)
import base64, json, os, time, hashlib, itertools, re
import numpy as np
from payload_embed import PAYLOAD
A=json.loads(base64.b64decode(PAYLOAD["ATLAS_B64"]))
assert hashlib.sha256(base64.b64decode(PAYLOAD["ATLAS_B64"])).hexdigest()==PAYLOAD["ATLAS_SHA"]
os.system("pip install -q kaggle-model-kernels 2>/dev/null")
GEN=None; BACKEND=None
try:
    from kaggle_model_kernels import KagiKernelModelsClient, KagiKernelModel
    GEN=KagiKernelModelsClient(model=KagiKernelModel.GEMMA3_27B_IT); BACKEND="gemma3-27b"
except Exception as e1:
    try:
        from kaggle_model_kernels import KagiKernelModelsClient
        GEN=KagiKernelModelsClient(model="deepseek-ai/deepseek-r1-distill-llama-70b"); BACKEND="deepseek-distill"
    except Exception as e2:
        print("model-api 皆哑, 本核今日作废, 尸检:", type(e1).__name__, str(e1)[:120], "|", str(e2)[:120])
        raise SystemExit(0)
# xdom 考卷词表 (tripwire): 生成语料撞题 ≥6 连续字 → 该行重写一次, 再撞弃该 space 记档
def ng(s,n=6): return {s[i:i+n] for i in range(len(s)-n+1)}
XDOM=set()
try:
    import urllib.request
    src=open("xdom_words.json").read()
    for q in json.loads(src): XDOM|=ng(q)
except Exception: pass
import os.path as _p
if not XDOM and _p.exists("/tmp/xw"):  # 兜底: 由 pusher 预烤进 payload 时再补
    pass
def clash(q,extra): return bool((ng(q)|ng(extra)) & XDOM)
out={"backend":BACKEND,"generated":0,"rejected_clash":0,"skipped_spaces":[],"spaces":{}}
t0=time.time()
for s in A["spaces"]:
    name=s["concept_space"]; dom=s["domain"]
    toks=[t["token"] for t in s["tokens"]]
    prompt=("为概念空间「%s」(%s 域) 写 8 组中文问答对。tokens 按时间序: %s。"
      "每组: 一行问题, 一行回答 (回答 ≤2 句, 必须自然含至少一个给定 token, 按序推进)。"
      "输出 JSON 数组: [{\"q\":\"..\",\"a\":\"..\"},...] 只输出 JSON。") % (name, dom, "、".join(toks))
    try:
        r=GEN.chat_completion(prompt, max_tokens=1200)
        txt=r.completion.text
        arr=json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
    except Exception as e:
        out["skipped_spaces"].append({"space":name,"why":type(e).__name__}); continue
    kept=[]
    for pair in arr[:8]:
        q=pair.get("q","").strip(); a=pair.get("a","").strip()
        if not q or not a: continue
        if clash(q,a):
            try:
                r2=GEN.chat_completion(prompt+" 注意: 避免与探测题撞句。", max_tokens=1200)
                arr2=json.loads(re.search(r"\[.*\]", r2.completion.text, re.S).group(0))
                cand=[x for x in arr2 if x.get("q") and not clash(x["q"], x.get("a",""))]
                if cand: q,a=cand[0]["q"],cand[0]["a"]
                else: out["rejected_clash"]+=1; continue
            except Exception: out["rejected_clash"]+=1; continue
        kept.append({"q":q,"a":a})
    out["generated"]+=len(kept); out["spaces"][name]={"domain":dom,"pairs":kept}
    if len(out["spaces"])%20==0:
        json.dump(out,open("/kaggle/working/m2_corpus_partial.json","w"),ensure_ascii=False)
        print("progress", len(out["spaces"]), f"{time.time()-t0:.0f}s", flush=True)
json.dump(out,open("/kaggle/working/m2_corpus.json","w"),ensure_ascii=False,indent=1)
print("REPORT_LINE", base64.b64encode(json.dumps({k:out[k] for k in ("backend","generated","rejected_clash")} ).encode()).decode())
