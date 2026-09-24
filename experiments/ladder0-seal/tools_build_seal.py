# LADDER-0 弹壳铸造器: 确定性 gzip(mtime=0) + raw-sha 正统; 改版即留痕
import json, base64, gzip, hashlib, sys
g = {}
exec("PAYLOAD=" + open("../exp11-kaggle/matrix_corpus_embed.py").read().split("PAYLOAD=")[1].split("\n",1)[0].strip().rstrip("L"), g)
def take(dom, n):
    raw = base64.b64decode(g["PAYLOAD"][f"corpus_{dom}.jsonl"]["b64"]).decode()
    return [json.loads(l)["messages"] for l in raw.splitlines()][:n]
items = {"I": take("code", 4), "II": take("spring", 4)}
js = json.dumps(items, ensure_ascii=False).encode()
RAW_SHA = hashlib.sha256(js).hexdigest()
pay = base64.b64encode(gzip.compress(js, 9, mtime=0)).decode()
tpl = open("ladder0_tpl.py").read()
open("run.py", "w").write(tpl.replace("###PAY###", pay).replace("###RAWSHA12###", RAW_SHA[:12]))
import py_compile; py_compile.compile("run.py", doraise=True)
print("cast OK raw_sha", RAW_SHA[:12], "bytes", len(open("run.py").read()))
