#!/usr/bin/env python3
"""P5f 判据运行 — 非标记载域之跨词型正证
冻本: PREREG_P5f_nomarker_positive.md sha256 e4761936816573cb12474d0d4ec255e62f909bf59e3a1bc7d42f4353a47a0497

域轴: 古典↔现代 (无标记 token, 由多样内容词承载)。训词型=图书馆; 测=博物馆/档案馆。
正本输出 report_p5g_qwen15b.json。跑法: ../../.venv-g3/bin/python run_p5f.py
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
MP = "/Users/mac/Programming/code-2026/GrandFather/models/models/Qwen--Qwen2.5-1.5B/snapshots/master"
PREREG_SHA = "e4761936816573cb12474d0d4ec255e62f909bf59e3a1bc7d42f4353a47a0497"
SEEDS = [0, 1, 2]
ALPHAS = [0.0, 0.5, 1.0, 1.5, 2.0]
FWD = 0.80

CLASSICAL = ["古籍", "竹简", "碑刻", "宋版书", "拓片", "青铜器"]
MODERN = ["数字资源", "网络资料", "电子档案", "数据库", "手机导览", "扫码展签"]
TMPL = ["{O}是{W}最珍贵的收藏", "这批{O}一直存放在{W}里", "研究{O}的人都爱去{W}", "{O}让{W}远近闻名"]
WORD_TRAIN = "图书馆"
WORD_TEST = ["博物馆", "档案馆"]

def sents(W, objs):
    return [t.replace("{W}", W).replace("{O}", o) for t in TMPL for o in objs]

DATA = {W: (sents(W, CLASSICAL), sents(W, MODERN)) for W in [WORD_TRAIN] + WORD_TEST}

tok = AutoTokenizer.from_pretrained(MP, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MP, dtype=torch.float32, trust_remote_code=True).eval()
LAYER = len(model.model.layers) // 2
print(f"[init] Qwen0.5B local | n_layers {len(model.model.layers)} | LAYER {LAYER}", flush=True)

def _span_last(text, word):
    enc = tok(text, return_offsets_mapping=True); offs = enc["offset_mapping"]
    st = text.index(word); en = st + len(word)
    idx = [i for i, (a, b) in enumerate(offs) if a < en and b > st][-1]
    assert idx > 0, f"P5g 前置断言: 读出位不得为 token 0 ({text!r})"
    return idx

def word_idx(word):
    return lambda text: _span_last(text, word)

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

def probe(hA, hB):
    X = torch.cat([hA, hB]).numpy(); y = np.array([0]*len(hA) + [1]*len(hB))
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0)).fit(X, y)

def train_case(word, A, B, seed):
    idxfn = word_idx(word)
    rng = random.Random(seed)
    A2, B2 = A[:], B[:]; rng.shuffle(A2); rng.shuffle(B2)
    nA = int(round(len(A2)*0.7)); nB = int(round(len(B2)*0.7))
    Atr, Ate, Btr, Bte = A2[:nA], A2[nA:], B2[:nB], B2[nB:]
    sv = train_steering_vector(model, tok, list(zip(Btr, Atr)), layers=[LAYER], read_token_index=idxfn, show_progress=False)
    v = sv.layer_activations[LAYER].reshape(-1)
    hA, hB = acts(Atr, idxfn), acts(Btr, idxfn)
    cA, cB = hA.mean(0), hB.mean(0)
    axis = (cB - cA); axis = axis / axis.norm()
    as_ = ((cB - cA).norm() / v.norm()).item()
    clf = probe(hA, hB)
    projs = [float(((acts(Ate, idxfn, sv, a*as_) - cA) @ axis).mean()) for a in ALPHAS]
    fwd = float((clf.predict(acts(Ate, idxfn, sv, 1.0*as_).numpy()) == 1).mean())
    g = torch.Generator().manual_seed(seed + 100)
    rv = torch.randn(v.shape, generator=g); rv = rv / rv.norm() * v.norm()
    rsv = SteeringVector(layer_activations={LAYER: rv}, layer_type=sv.layer_type)
    rand = float((clf.predict(acts(Ate, idxfn, rsv, 1.0*as_).numpy()) == 1).mean())
    return dict(alpha_star=as_, projs=projs, fwd=fwd, rand=rand, _sv=sv, _clf=clf, _Ate=Ate, _idxfn=idxfn)

def gen_word(src, test_word, seed):
    """src 之 v 施于 test_word 之 classical 句, 用 test_word 自训探针判。"""
    A, B = DATA[test_word]
    idxfn = word_idx(test_word)
    rng = random.Random(seed)
    A2, B2 = A[:], B[:]; rng.shuffle(A2); rng.shuffle(B2)
    nA = int(round(len(A2)*0.7)); nB = int(round(len(B2)*0.7))
    Atr, Ate, Btr, Bte = A2[:nA], A2[nA:], B2[:nB], B2[nB:]
    clf = probe(acts(Atr, idxfn), acts(Btr, idxfn))
    h = acts(Ate, idxfn, src["_sv"], 1.0*src["alpha_star"])
    return float((clf.predict(h.numpy()) == 1).mean())

def monotone(ps):
    return all(ps[i+1] >= ps[i] - 1e-9 for i in range(len(ps)-1)) and ps[-1] > ps[0]

def main():
    t0 = time.time()
    per = [train_case(WORD_TRAIN, *DATA[WORD_TRAIN], s) for s in SEEDS]
    print(f"[train {WORD_TRAIN}] fwd={np.mean([p['fwd'] for p in per]):.3f} rand={np.mean([p['rand'] for p in per]):.3f}", flush=True)
    gen = {}
    for W in WORD_TEST:
        vals = [gen_word(per[i], W, SEEDS[i]) for i in range(len(SEEDS))]
        gen[W] = {"mean": float(np.mean(vals)), "vals": vals}
        print(f"[gen {W}] {np.mean(vals):.3f} {vals}", flush=True)

    verdict = {
        "H-p5g-0_axis_monotone": {"pass": all(monotone(p["projs"]) for p in per)},
        "H-p5g-1_change_meaning_train_word": {"acc": float(np.mean([p["fwd"] for p in per])),
                                              "pass": sum(p["fwd"] > FWD for p in per) >= 2},
        "H-p5g-2_generalize_museum": {"acc": gen["博物馆"],
                                      "pass": sum(g > FWD for g in gen["博物馆"]["vals"]) >= 2},
        "H-p5g-3_generalize_archive": {"acc": gen["档案馆"],
                                       "pass": sum(g > FWD for g in gen["档案馆"]["vals"]) >= 2},
        "instrument_random_v": {"acc": float(np.mean([p["rand"] for p in per])),
                                "pass": sum(p["rand"] < 0.50 for p in per) >= 2},
    }
    report = {"case": "P5g-nomarker-fixed", "prereg_sha256": PREREG_SHA, "model": "Qwen2.5-0.5B-local",
              "layer": LAYER, "seeds": SEEDS, "alphas": ALPHAS, "train_word": WORD_TRAIN, "test_words": WORD_TEST,
              "per_seed": [{k: v for k, v in p.items() if not k.startswith("_")} for p in per],
              "gen": gen, "verdict": verdict, "elapsed_s": round(time.time()-t0, 1)}
    p = HERE / "report_p5g_qwen15b.json"
    p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 判词 ===")
    for k, v in verdict.items():
        print(f"  {k:34s} {'PASS' if v.get('pass') else '—':4s} {json.dumps(v.get('acc', v.get('pass')), ensure_ascii=False)}")
    print(f"\n[out] {p} | {report['elapsed_s']}s", flush=True)
    print(f"[sha] {hashlib.sha256(p.read_bytes()).hexdigest()[:16]}", flush=True)
    print("P5G15-DONE", flush=True)

if __name__ == "__main__":
    main()
