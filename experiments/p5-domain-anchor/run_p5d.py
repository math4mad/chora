#!/usr/bin/env python3
"""P5d 判据运行 — 未见标记迁移 (破 P5b 循环之嫌)
冻本: PREREG_P5d_unseen_marker.md sha256 6f07f759686bf1262bf35bdc3e9a0a83c8a1996dae3b38fdee586e1604c7e995

方向轴: 北方→南方。训标记={黑龙江,吉林}→{广东,广西}; 测标记(未见)={辽宁}→{海南}。
正本输出 report_p5d.json。跑法: ../../.venv-g3/bin/python run_p5d.py
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
PREREG_SHA = "6f07f759686bf1262bf35bdc3e9a0a83c8a1996dae3b38fdee586e1604c7e995"
SEEDS = [0, 1, 2]
ALPHAS = [0.0, 0.5, 1.0, 1.5, 2.0]
FWD = 0.80

NORTH, SOUTH = ["黑龙江", "吉林"], ["广东", "广西"]
NORTH_T, SOUTH_T = ["辽宁"], ["海南"]
ALL_PROV = NORTH + SOUTH + NORTH_T + SOUTH_T

LIB_TMPL = ["{P}的图书馆开放时间是早上八点", "{P}的图书馆藏书非常丰富", "他常去{P}的图书馆看书",
            "{P}的图书馆周末人很多", "{P}的图书馆新馆刚建成", "{P}的图书馆有很多读者",
            "{P}的图书馆坐落在市中心", "{P}的图书馆借书很方便", "{P}的图书馆冬天很暖和",
            "{P}的图书馆管理员很热情"]
FOOD_TMPL = ["{P}的美食很有名", "来{P}一定要尝尝当地美食", "{P}的美食街上人很多",
             "他最爱吃{P}的美食", "{P}的美食吸引了很多游客", "{P}的美食种类丰富",
             "每到晚上{P}的美食摊就摆开了", "{P}的美食让人流连忘返", "{P}的美食价格实惠",
             "他推荐了{P}的几道美食"]

def lib_sents(P):  return [t.replace("{P}", P) for t in LIB_TMPL]
def food_sents(P): return [t.replace("{P}", P) for t in FOOD_TMPL]

tok = AutoTokenizer.from_pretrained(MP)
model = AutoModelForCausalLM.from_pretrained(MP, dtype=torch.float32).eval()
LAYER = len(model.transformer.h) // 2
print(f"[init] gpt2 ok | LAYER {LAYER}", flush=True)

def _span_last(text, word):
    enc = tok(text, return_offsets_mapping=True); offs = enc["offset_mapping"]
    st = text.index(word); en = st + len(word)
    return [i for i, (a, b) in enumerate(offs) if a < en and b > st][-1]

def marker_idx(text):
    for p in ALL_PROV:
        if p in text:
            return _span_last(text, p)
    raise ValueError(f"no province marker in {text!r}")

def acts(texts, sv=None, alpha=0.0):
    samples = [(t, t) for t in texts]
    def _ex():
        pos, _ = extract_activations(model, tok, samples, layers=[LAYER], read_token_index=marker_idx)
        return pos[LAYER]
    with torch.no_grad():
        if sv is not None and alpha != 0.0:
            with sv.apply(model, multiplier=alpha):
                out = _ex()
        else:
            out = _ex()
    return torch.cat([p.reshape(-1, p.shape[-1]) for p in out], 0)

def probe(hA, hB):
    X = torch.cat([hA, hB]).numpy(); y = np.array([0]*len(hA) + [1]*len(hB))
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0)).fit(X, y)

def main():
    t0 = time.time()
    all_pairs = []
    for np_ in NORTH:
        for sp in SOUTH:
            l, r = lib_sents(np_), lib_sents(sp)
            all_pairs += list(zip(r, l))        # positive=南, negative=北

    per_seed = []
    for seed in SEEDS:
        rng = random.Random(seed)
        pairs = [all_pairs[i] for i in rng.sample(range(len(all_pairs)), int(len(all_pairs)*0.7))]
        sv = train_steering_vector(model, tok, pairs, layers=[LAYER], read_token_index=marker_idx, show_progress=False)
        v = sv.layer_activations[LAYER].reshape(-1)

        # 训练标记 probe
        hN = acts([s for p in NORTH for s in lib_sents(p)])
        hS = acts([s for p in SOUTH for s in lib_sents(p)])
        clf_tr = probe(hN, hS)
        cN, cS = hN.mean(0), hS.mean(0)
        axis = (cS - cN); axis = axis / axis.norm()
        as_ = ((cS - cN).norm() / v.norm()).item()
        # H-p5d-1 换义@训练标记
        fwd_tr = float((clf_tr.predict(acts([s for p in NORTH for s in lib_sents(p)], sv, 1.0*as_).numpy()) == 1).mean())
        projs = [float(((acts([s for p in NORTH for s in lib_sents(p)], sv, a*as_) - cN) @ axis).mean()) for a in ALPHAS]

        # H-p5d-2 未见标记 (lib): probe(辽宁 vs 海南), v 施于 辽宁
        hNt = acts([s for p in NORTH_T for s in lib_sents(p)])
        hSt = acts([s for p in SOUTH_T for s in lib_sents(p)])
        clf_t = probe(hNt, hSt)
        cNt, cSt = hNt.mean(0), hSt.mean(0)
        fwd_unseen = float((clf_t.predict(acts([s for p in NORTH_T for s in lib_sents(p)], sv, 1.0*as_).numpy()) == 1).mean())
        cos_before = float(torch.nn.functional.cosine_similarity(hNt.mean(0).unsqueeze(0), cSt.unsqueeze(0)).item())
        h_steer = acts([s for p in NORTH_T for s in lib_sents(p)], sv, 1.0*as_)
        cos_after = float(torch.nn.functional.cosine_similarity(h_steer.mean(0).unsqueeze(0), cSt.unsqueeze(0)).item())

        # H-p5d-3 未见标记 + 未见词型 (food)
        hNf = acts([s for p in NORTH_T for s in food_sents(p)])
        hSf = acts([s for p in SOUTH_T for s in food_sents(p)])
        clf_f = probe(hNf, hSf)
        fwd_food = float((clf_f.predict(acts([s for p in NORTH_T for s in food_sents(p)], sv, 1.0*as_).numpy()) == 1).mean())

        # 器具自检
        g = torch.Generator().manual_seed(seed + 100)
        rv = torch.randn(v.shape, generator=g); rv = rv / rv.norm() * v.norm()
        rsv = SteeringVector(layer_activations={LAYER: rv}, layer_type=sv.layer_type)
        rand = float((clf_tr.predict(acts([s for p in NORTH for s in lib_sents(p)], rsv, 1.0*as_).numpy()) == 1).mean())

        per_seed.append(dict(seed=seed, alpha_star=as_, fwd_train_marker=fwd_tr, projs=projs,
                             fwd_unseen_marker=fwd_unseen, cos_south_before=cos_before, cos_south_after=cos_after,
                             fwd_unseen_marker_food=fwd_food, rand=rand))
        print(f"[seed {seed}] train_fwd={fwd_tr:.3f} unseen={fwd_unseen:.3f} "
              f"unseen_food={fwd_food:.3f} cos(south) {cos_before:+.3f}→{cos_after:+.3f} rand={rand:.3f}", flush=True)

    def m(k): return float(np.mean([p[k] for p in per_seed]))
    verdict = {
        "H-p5d-0_axis_monotone": {"pass": all(all(p["projs"][i+1] >= p["projs"][i]-1e-9 for i in range(len(p["projs"])-1))
                                              and p["projs"][-1] > p["projs"][0] for p in per_seed)},
        "H-p5d-1_change_meaning_train_marker": {"acc": m("fwd_train_marker"),
                                                "pass": sum(p["fwd_train_marker"] > FWD for p in per_seed) >= 2},
        "H-p5d-2_generalize_unseen_marker": {"acc": m("fwd_unseen_marker"),
                                             "pass": sum(p["fwd_unseen_marker"] > FWD for p in per_seed) >= 2,
                                             "cos_south_before": m("cos_south_before"),
                                             "cos_south_after": m("cos_south_after")},
        "H-p5d-3_generalize_unseen_marker_food": {"acc": m("fwd_unseen_marker_food"),
                                                  "pass": sum(p["fwd_unseen_marker_food"] > FWD for p in per_seed) >= 2},
        "instrument_random_v": {"acc": m("rand"), "pass": sum(p["rand"] < 0.50 for p in per_seed) >= 2},
    }
    report = {"case": "P5d-unseen-marker", "prereg_sha256": PREREG_SHA, "model": "gpt2", "layer": LAYER,
              "seeds": SEEDS, "alphas": ALPHAS, "train_markers": {"north": NORTH, "south": SOUTH},
              "test_markers": {"north": NORTH_T, "south": SOUTH_T},
              "per_seed": per_seed, "verdict": verdict, "elapsed_s": round(time.time()-t0, 1)}
    p = HERE / "report_p5d.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 判词 ===")
    for k, v in verdict.items():
        print(f"  {k:40s} {'PASS' if v.get('pass') else '—':4s} {json.dumps(v.get('acc', v.get('pass')), ensure_ascii=False)}")
    print(f"\n[out] {p} | {report['elapsed_s']}s", flush=True)
    print(f"[sha] {hashlib.sha256(p.read_bytes()).hexdigest()[:16]}", flush=True)
    print("P5D-DONE", flush=True)

if __name__ == "__main__":
    main()
