#!/usr/bin/env python3
"""P5b 判据运行 — 域标记位重射 (域方向居所)
冻本: PREREG_P5b_domain_marker.md sha256 79c71cf64124b168b448ea1e5854cb76d28b00e648a25eb65d90cdbf8bded2d2

三读出位并测: 省名位(主) / 目标词位(附) / 句末位(位点对照)。
正本输出 report_p5b.json。跑法: ../../.venv-g3/bin/python run_p5b.py
"""
import json, time, random, hashlib
from pathlib import Path
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from steering_vectors import train_steering_vector, extract_activations, SteeringVector
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

HERE = Path(__file__).resolve().parent
MP = "/Users/mac/.cache/modelscope/models/AI-ModelScope--gpt2/snapshots/master"
PREREG_SHA = "79c71cf64124b168b448ea1e5854cb76d28b00e648a25eb65d90cdbf8bded2d2"
SEEDS = [0, 1, 2]
ALPHAS = [0.0, 0.5, 1.0, 1.5, 2.0]
FWD = 0.80
CTRL = 0.50     # H-p5b-3 位点专一: 句末位泛化须 ≤50%

# ---------------- 语料 (同 P5) ----------------
def lib_sents(prov, objs, places):
    return ([f"{prov}的图书馆里藏着很多{o}" for o in objs]
            + [f"{o}在{prov}的图书馆里也能借到" for o in objs]
            + [f"{prov}图书馆位于{p}附近" for p in places]
            + [f"他周末总去{prov}的图书馆看{o}" for o in objs]
            + [f"{prov}的图书馆收藏了不少{o}" for o in objs])

def food_sents(prov, objs):
    return ([f"{prov}的美食里，{o}最有名" for o in objs]
            + [f"来{prov}，{o}是必尝的美食" for o in objs]
            + [f"{o}是{prov}的美食招牌" for o in objs]
            + [f"他最爱吃{prov}的美食，比如{o}" for o in objs])

DATA = {
    "library": ("图书馆", lib_sents("浙江", ["古籍","宋版书","越剧唱本","西湖志","明代刻本","金石拓片"], ["西湖","之江","武林门"]),
                          lib_sents("广东", ["粤剧剧本","岭南文献","广府族谱","骑楼史料","潮州歌册","南音曲本"], ["珠江","越秀山","荔湾"])),
    "food":    ("美食",   food_sents("浙江", ["西湖醋鱼","东坡肉","龙井虾仁","宋嫂鱼羹","片儿川","定胜糕"]),
                          food_sents("广东", ["白切鸡","烧鹅","虾饺","艇仔粥","肠粉","叉烧"])),
}

# ---------------- 器 ----------------
tok = AutoTokenizer.from_pretrained(MP)
model = AutoModelForCausalLM.from_pretrained(MP, torch_dtype=torch.float32).eval()
LAYER = len(model.transformer.h) // 2
print(f"[init] gpt2 ok | LAYER {LAYER}/{len(model.transformer.h)}", flush=True)

def _span_last(text, word):
    enc = tok(text, return_offsets_mapping=True)
    offs = enc["offset_mapping"]
    st = text.index(word); en = st + len(word)
    idxs = [i for i, (a, b) in enumerate(offs) if a < en and b > st]
    if not idxs:
        raise ValueError(f"target {word!r} not in {text!r}")
    return idxs[-1]

def word_idx(word):
    return lambda text: _span_last(text, word)

def prov_idx():
    def fn(text):
        p = "浙江" if "浙江" in text else ("广东" if "广东" in text else None)
        if p is None:
            raise ValueError(f"no province in {text!r}")
        return _span_last(text, p)
    return fn

def end_idx(text):
    return len(tok(text)["input_ids"]) - 1

def acts(texts, idxfn, sv=None, alpha=0.0):
    samples = [(t, t) for t in texts]
    def _ex():
        pos, _ = extract_activations(model, tok, samples, layers=[LAYER], read_token_index=idxfn)
        return pos[LAYER]
    with torch.no_grad():
        if sv is not None and alpha != 0.0:
            with sv.apply(model, multiplier=alpha):
                out = _ex()
        else:
            out = _ex()
    return torch.cat([p.reshape(-1, p.shape[-1]) for p in out], 0)

def train_case(word, A, B, idxfn, seed):
    rng = random.Random(seed)
    A2, B2 = A[:], B[:]; rng.shuffle(A2); rng.shuffle(B2)
    nA = min(len(A2)-1, max(2, int(round(len(A2)*0.7))))
    nB = min(len(B2)-1, max(2, int(round(len(B2)*0.7))))
    Atr, Ate, Btr, Bte = A2[:nA], A2[nA:], B2[:nB], B2[nB:]
    sv = train_steering_vector(model, tok, list(zip(Btr, Atr)), layers=[LAYER],
                               read_token_index=idxfn, show_progress=False)
    v = sv.layer_activations[LAYER].reshape(-1)
    hA, hB = acts(Atr, idxfn), acts(Btr, idxfn)
    cA, cB = hA.mean(0), hB.mean(0)
    axis = (cB - cA); axis = axis / axis.norm()
    as_ = ((cB - cA).norm() / v.norm()).item()
    X = torch.cat([hA, hB]).numpy(); y = np.array([0]*len(Atr) + [1]*len(Btr))
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)).fit(X, y)
    projs = [float(((acts(Ate, idxfn, sv, a*as_) - cA) @ axis).mean()) for a in ALPHAS]
    fwd = float((clf.predict(acts(Ate, idxfn, sv, 1.0*as_).numpy()) == 1).mean())
    g = torch.Generator().manual_seed(seed + 100)
    rv = torch.randn(v.shape, generator=g); rv = rv / rv.norm() * v.norm()
    rsv = SteeringVector(layer_activations={LAYER: rv}, layer_type=sv.layer_type)
    rand = float((clf.predict(acts(Ate, idxfn, rsv, 1.0*as_).numpy()) == 1).mean())
    return dict(alpha_star=as_, projs=projs, fwd=fwd, rand=rand,
                _sv=sv, _clf=clf, _Ate=Ate, _idxfn=idxfn)

def gen(src, dst):
    h = acts(dst["_Ate"], dst["_idxfn"], src["_sv"], 1.0*src["alpha_star"])
    return float((dst["_clf"].predict(h.numpy()) == 1).mean())

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main():
    t0 = time.time()
    positions = {
        "prov": lambda word: prov_idx(),
        "word": lambda word: word_idx(word),
        "end":  lambda word: end_idx,
    }
    out = {}
    for pos, factory in positions.items():
        per = {}
        for cname, (word, A, B) in DATA.items():
            idxfn = factory(word)
            per[cname] = [train_case(word, A, B, idxfn, s) for s in SEEDS]
        genv = [gen(per["library"][i], per["food"][i]) for i in range(len(SEEDS))]
        out[pos] = {
            "per_case": {k: [{kk: vv for kk, vv in p.items() if not kk.startswith("_")} for p in v]
                         for k, v in per.items()},
            "gen_lib_to_food": {"mean": float(np.mean(genv)), "vals": genv},
        }
        print(f"[pos] {pos:5s} lib_fwd={np.mean([p['fwd'] for p in per['library']]):.3f} "
              f"gen(lib→food)={np.mean(genv):.3f}", flush=True)

    prov, end = out["prov"], out["end"]
    libP = prov["per_case"]["library"]
    verdict = {
        "H-p5b-0_axis_monotone": {"pass": all(monotone(p["projs"]) for p in libP)},
        "H-p5b-1_change_meaning": {"acc": float(np.mean([p["fwd"] for p in libP])),
                                   "pass": sum(p["fwd"] > FWD for p in libP) >= 2},
        "H-p5b-2_generalize_at_marker": {"acc": prov["gen_lib_to_food"],
                                         "pass": sum(g > FWD for g in prov["gen_lib_to_food"]["vals"]) >= 2},
        "H-p5b-3_position_specificity_end": {"acc": end["gen_lib_to_food"],
                                             "pass": sum(g < CTRL for g in end["gen_lib_to_food"]["vals"]) >= 2},
        "instrument_random_v": {"acc": float(np.mean([p["rand"] for p in libP])),
                                "pass": sum(p["rand"] < CTRL for p in libP) >= 2},
    }
    report = {
        "case": "P5b-domain-marker", "prereg_sha256": PREREG_SHA, "model": "gpt2",
        "layer": LAYER, "seeds": SEEDS, "alphas": ALPHAS,
        "thresholds": {"fwd_pass": FWD, "ctrl_max": CTRL},
        "by_position": out, "verdict": verdict,
        "elapsed_s": round(time.time()-t0, 1),
    }
    p = HERE / "report_p5b.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 判词 ===")
    for k, v in verdict.items():
        print(f"  {k:34s} {'PASS' if v.get('pass') else '—':4s} {json.dumps(v.get('acc', v.get('pass')), ensure_ascii=False)}")
    print(f"\n[out] {p} | {report['elapsed_s']}s", flush=True)
    print(f"[sha] {hashlib.sha256(p.read_bytes()).hexdigest()[:16]}", flush=True)
    print("P5B-DONE", flush=True)

if __name__ == "__main__":
    main()
