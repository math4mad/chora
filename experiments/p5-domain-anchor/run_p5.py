#!/usr/bin/env python3
"""P5 判据运行 — 域切换方向向量 (上下文锚定 · 因果干预)
冻本: PREREG_P5_domain_switch.md sha256 5c865c7592df2df96046801e8e18a67fb8d8ab6963da116bda96ad3d4d1f43c9

三检 + 对照 + 器具自检。正本输出 report_p5.json。
跑法: ../../.venv-g3/bin/python run_p5.py
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
PREREG_SHA = "5c865c7592df2df96046801e8e18a67fb8d8ab6963da116bda96ad3d4d1f43c9"
SEEDS = [0, 1, 2]                      # ≥3 籽 (冻条)
ALPHAS = [0.0, 0.5, 1.0, 1.5, 2.0]    # α 以 α* 为单位 (冻条: 先归一标定再扫)
FWD_PASS = 0.80                        # H-p5-1/2 冻条 >80%
CTRL_MAX = 0.60                        # H-p5-3 对照 "≈随机/50%" 上限

# ---------------- 语料 ----------------
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

def build_control(seed=1234):
    acts = ["贴春联","放鞭炮","吃饺子","看春晚","拜年","发红包","守岁","挂灯笼","赶年集","包汤圆","祭灶","扫尘"]
    sents = ([f"春节的时候，家家户户{a}" for a in acts]
             + [f"春节里人们忙着{a}" for a in acts]
             + [f"每到春节，孩子们最期待{a}" for a in acts])
    idx = list(range(len(sents))); random.Random(seed).shuffle(idx); h = len(idx)//2
    return "control_spring", "春节", [sents[i] for i in idx[:h]], [sents[i] for i in idx[h:]]

DATA = {
    "library": ("图书馆", lib_sents("浙江", ["古籍","宋版书","越剧唱本","西湖志","明代刻本","金石拓片"], ["西湖","之江","武林门"]),
                          lib_sents("广东", ["粤剧剧本","岭南文献","广府族谱","骑楼史料","潮州歌册","南音曲本"], ["珠江","越秀山","荔湾"])),
    "food":    ("美食",   food_sents("浙江", ["西湖醋鱼","东坡肉","龙井虾仁","宋嫂鱼羹","片儿川","定胜糕"]),
                          food_sents("广东", ["白切鸡","烧鹅","虾饺","艇仔粥","肠粉","叉烧"])),
}

# ---------------- 器 ----------------
MODEL_KW = dict(torch_dtype=torch.float32)
tok = AutoTokenizer.from_pretrained(MP)
model = AutoModelForCausalLM.from_pretrained(MP, **MODEL_KW).eval()
LAYER = len(model.transformer.h) // 2      # 冻式: 中层
print(f"[init] gpt2 ok | LAYER {LAYER}/{len(model.transformer.h)} | vocab {tok.vocab_size}", flush=True)

def make_idx_fn(word):
    def fn(text):
        enc = tok(text, return_offsets_mapping=True)
        offs = enc["offset_mapping"]
        st = text.index(word); en = st + len(word)
        idxs = [i for i, (a, b) in enumerate(offs) if a < en and b > st]
        if not idxs:
            raise ValueError(f"target {word!r} not found in {text!r}")
        return idxs[-1]                     # 目标词之末 token
    return fn

def acts_of(texts, idxfn, sv=None, alpha=0.0):
    """读出目标词 token 处之表示; 可带 sv 干预。"""
    samples = [(t, t) for t in texts]
    def _extract():
        pos, _ = extract_activations(model, tok, samples, layers=[LAYER], read_token_index=idxfn)
        return pos[LAYER]
    with torch.no_grad():
        if sv is not None and alpha != 0.0:
            with sv.apply(model, multiplier=alpha):
                out = _extract()
        else:
            out = _extract()
    return torch.cat([p.reshape(-1, p.shape[-1]) for p in out], 0)

def run_case(name, word, A, B, seed):
    rng = random.Random(seed)
    A2, B2 = A[:], B[:]; rng.shuffle(A2); rng.shuffle(B2)
    nA = min(len(A2)-1, max(2, int(round(len(A2)*0.7))))
    nB = min(len(B2)-1, max(2, int(round(len(B2)*0.7))))
    Atr, Ate, Btr, Bte = A2[:nA], A2[nA:], B2[:nB], B2[nB:]
    idxfn = make_idx_fn(word)
    sv = train_steering_vector(model, tok, list(zip(Btr, Atr)), layers=[LAYER],
                               read_token_index=idxfn, show_progress=False)
    v = sv.layer_activations[LAYER].reshape(-1)
    hAtr, hBtr = acts_of(Atr, idxfn), acts_of(Btr, idxfn)
    cA, cB = hAtr.mean(0), hBtr.mean(0)
    axis = (cB - cA); axis = axis / axis.norm()
    alpha_star = ((cB - cA).norm() / v.norm()).item()
    X = torch.cat([hAtr, hBtr]).numpy(); y = np.array([0]*len(Atr) + [1]*len(Btr))
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)).fit(X, y)
    probe_tr = float((clf.predict(X) == y).mean())
    # H-p5-0 轴移动 (单调)
    h0 = [float(((acts_of(Ate, idxfn, sv, a*alpha_star) - cA) @ axis).mean()) for a in ALPHAS]
    # H-p5-1 换义 (正/反)
    h1_fwd = float((clf.predict(acts_of(Ate, idxfn, sv,  1.0*alpha_star).numpy()) == 1).mean())
    h1_rev = float((clf.predict(acts_of(Bte, idxfn, sv, -1.0*alpha_star).numpy()) == 0).mean())
    # 器具自检: 随机 v 不得过 H-p5-1
    g = torch.Generator().manual_seed(seed + 100)
    rv = torch.randn(v.shape, generator=g); rv = rv / rv.norm() * v.norm()
    rsv = SteeringVector(layer_activations={LAYER: rv}, layer_type=sv.layer_type)
    h1_rand = float((clf.predict(acts_of(Ate, idxfn, rsv, 1.0*alpha_star).numpy()) == 1).mean())
    return dict(name=name, word=word, seed=seed, alpha_star=alpha_star, probe_train_acc=probe_tr,
                h0_projs=h0, h1_fwd=h1_fwd, h1_rev=h1_rev, h1_rand=h1_rand,
                _sv=sv, _clf=clf, _Ate=Ate, _Bte=Bte, _idxfn=idxfn, _cA=cA, _cB=cB)

def gen_eval(src, dst, alpha=None):
    """H-p5-2: src 之 v 施于 dst 之 held-out A, 用 dst 自己的探针判。"""
    a = alpha if alpha is not None else src["alpha_star"]
    h = acts_of(dst["_Ate"], dst["_idxfn"], src["_sv"], 1.0*a)
    return float((dst["_clf"].predict(h.numpy()) == 1).mean())

def agg(per, key):
    xs = [p[key] for p in per]
    return {"mean": float(np.mean(xs)), "std": float(np.std(xs)), "vals": xs}

def monotone(projs):
    return all(projs[i+1] >= projs[i] - 1e-9 for i in range(len(projs)-1)) and projs[-1] > projs[0]

def main():
    t0 = time.time()
    cases = {"library": DATA["library"], "food": DATA["food"]}
    cname, cword, cA, cB = build_control()
    cases[cname] = (cword, cA, cB)

    per_case = {}
    for cname_, (word, A, B) in cases.items():
        per = [run_case(cname_, word, A, B, s) for s in SEEDS]
        per_case[cname_] = per
        print(f"[case] {cname_:16s} fwd={agg(per,'h1_fwd')['mean']:.3f} "
              f"rand={agg(per,'h1_rand')['mean']:.3f} probe_tr={agg(per,'probe_train_acc')['mean']:.3f}", flush=True)

    # H-p5-2 泛化: library 之 v → food 之 held-out
    gen = [gen_eval(per_case["library"][i], per_case["food"][i]) for i in range(len(SEEDS))]

    lib = per_case["library"]; ctl = per_case[cname]
    verdict = {
        "H-p5-0_axis_monotone": {"pass": all(monotone(p["h0_projs"]) for p in lib)},
        "H-p5-1_change_meaning": {"acc": agg(lib, "h1_fwd"), "pass": sum(p["h1_fwd"] > FWD_PASS for p in lib) >= 2},
        "H-p5-1_reverse":        {"acc": agg(lib, "h1_rev")},
        "H-p5-2_generalize":     {"acc": {"mean": float(np.mean(gen)), "std": float(np.std(gen)), "vals": gen},
                                  "pass": sum(g > FWD_PASS for g in gen) >= 2},
        "H-p5-3_control_no_v":   {"acc": agg(ctl, "h1_fwd"), "pass": sum(p["h1_fwd"] < CTRL_MAX for p in ctl) >= 2},
        "instrument_random_v":   {"acc": agg(lib, "h1_rand"),
                                  "pass": sum(p["h1_rand"] < CTRL_MAX for p in lib) >= 2},
    }
    report = {
        "case": "P5-domain-switch", "prereg_sha256": PREREG_SHA, "model": "gpt2",
        "layer": LAYER, "seeds": SEEDS, "alphas": ALPHAS,
        "thresholds": {"fwd_pass": FWD_PASS, "ctrl_max": CTRL_MAX},
        "per_case": {k: [{kk: vv for kk, vv in p.items() if not kk.startswith("_")} for p in v] for k, v in per_case.items()},
        "verdict": verdict,
        "elapsed_s": round(time.time()-t0, 1),
    }
    out = HERE / "report_p5.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 判词 ===")
    for k, v in verdict.items():
        print(f"  {k:26s} {'PASS' if v.get('pass') else '—':4s} {json.dumps(v.get('acc', v.get('pass')), ensure_ascii=False)}")
    print(f"\n[out] {out} | {report['elapsed_s']}s", flush=True)
    print(f"[sha] {hashlib.sha256(out.read_bytes()).hexdigest()[:16]}", flush=True)
    print("P5-DONE", flush=True)

if __name__ == "__main__":
    main()
