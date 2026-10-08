"""P5 feasibility probe v2 — use the REAL steering-vectors API (sv.apply as context mgr).
最小可行探查: 载 GPT-2 → 造域对照语料 → 训域切换向量 v → 正向/可逆两检。
"""
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from steering_vectors import train_steering_vector

MP = "/Users/mac/.cache/modelscope/models/AI-ModelScope--gpt2/snapshots/master"

t0 = time.time()
tok = AutoTokenizer.from_pretrained(MP)
model = AutoModelForCausalLM.from_pretrained(MP)
model.eval()
print(f"[load] {time.time()-t0:.1f}s", flush=True)

# 域对照语料: 浙江域 vs 广东域 (同一词形「省图」锚定不同域)
ZJ = ["浙江省图书馆坐落在杭州西湖边", "浙江省图书馆新馆在之江路",
      "浙江省图书馆藏有大量古籍", "浙江省图书馆的读者证很好办",
      "杭州的浙江省图书馆我去过"]
GD = ["广东省图书馆坐落在广州珠江边", "广东省图书馆新馆在珠江新城",
      "广东省图书馆藏有大量粤语文献", "广东省图书馆的读者证很好办",
      "广州的广东省图书馆我去过"]

# positive=广东, negative=浙江  => v 指向「广东域」
samples = list(zip(GD, ZJ))

t1 = time.time()
sv = train_steering_vector(model, tok, samples, show_progress=False)
print(f"[train] {time.time()-t1:.1f}s | layers={sorted(sv.layer_activations.keys())[:6]}...", flush=True)

LAYER = len(model.transformer.h) // 2
print("probe layer:", LAYER, "of", len(model.transformer.h), flush=True)

def last_h(text, alpha=0.0):
    inp = tok(text, return_tensors="pt")
    with torch.no_grad():
        if alpha == 0.0:
            out = model(**inp, output_hidden_states=True)
        else:
            with sv.apply(model, multiplier=alpha):
                out = model(**inp, output_hidden_states=True)
    return out.hidden_states[LAYER][0, -1]

# centroids (无干预)
def centroid(texts):
    return torch.stack([last_h(t) for t in texts]).mean(0)
cZJ, cGD = centroid(ZJ), centroid(GD)
axis = (cGD - cZJ); axis = axis / axis.norm()      # 浙江→广东 轴
cos = lambda a, b: torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()

held = "浙江省图书馆周末有很多学生自习"
print("\n[正向检] 施加 +alpha·v 后, 浙江句表示沿「浙江→广东」轴移动多少?", flush=True)
for a in [0.0, 0.5, 1.0, 2.0, 4.0]:
    h = last_h(held, a)
    proj = ((h - cZJ) @ axis).item()
    print(f"  alpha={a:+.1f}  proj_on_axis={proj:+.3f}  cos(GD)={cos(h,cGD):+.3f}  cos(ZJ)={cos(h,cZJ):+.3f}", flush=True)

print("\n[可逆检] 先 +2·v 再 -2·v, 是否回到原处?", flush=True)
h0 = last_h(held, 0.0)
hp = last_h(held, 2.0)
hn = last_h(held, -2.0)
print(f"  cos(h0, h(+2)) = {cos(h0,hp):+.4f}  (应显著<1)", flush=True)
print(f"  cos(h0, h(-2)) = {cos(h0,hn):+.4f}", flush=True)
# 真可逆: +2 后再应用一次反向, 用两次 apply 叠加
inp = tok(held, return_tensors="pt")
with torch.no_grad():
    with sv.apply(model, multiplier=2.0):
        with sv.apply(model, multiplier=-2.0):
            out = model(**inp, output_hidden_states=True)
hrev = out.hidden_states[LAYER][0, -1]
print(f"  cos(h0, h(+2 then -2)) = {cos(h0, hrev):+.4f}  (≈1 则严格可逆)", flush=True)

print(f"\n[total] {time.time()-t0:.1f}s", flush=True)
print("FEAS-DONE", flush=True)
