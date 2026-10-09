#!/usr/bin/env python3
"""P5 系探路诊断 (exploratory, 不入冻判)
A) 层扫描: 省名位 cos(v_lib,v_food) 与泛化 acc 随层深
B) OOD 诊: 干预后表示是否被推出流形
跑法: ../../.venv-g3/bin/python diag_p5.py
"""
import sys, torch, numpy as np
sys.path.insert(0, ".")
import run_p5b as R
from steering_vectors import train_steering_vector, extract_activations
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

LAYERS = list(range(len(R.model.transformer.h)))

def acts_at(texts, idxfn, L, sv=None, alpha=0.0):
    samples = [(t, t) for t in texts]
    def _ex():
        pos, _ = extract_activations(R.model, R.tok, samples, layers=[L], read_token_index=idxfn)
        return pos[L]
    with torch.no_grad():
        if sv is not None and alpha != 0.0:
            with sv.apply(R.model, multiplier=alpha):
                out = _ex()
        else:
            out = _ex()
    return torch.cat([p.reshape(-1, p.shape[-1]) for p in out], 0)

def probe(hA, hB):
    X = torch.cat([hA, hB]).numpy(); y = np.array([0]*len(hA) + [1]*len(hB))
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)).fit(X, y)

def main():
    data = R.DATA
    lw, lA, lB = data["library"]; fw, fA, fB = data["food"]
    ilib, ifood = R.prov_idx(), R.prov_idx()
    print("=== A) 层扫描 (省名位) ===", flush=True)
    print(f"{'L':>3} {'cos(v_lib,v_food)':>18} {'gen(lib→food)':>14} {'lib_fwd':>8}", flush=True)
    rows = []
    for L in LAYERS:
        svl = train_steering_vector(R.model, R.tok, list(zip(lB, lA)), layers=[L], read_token_index=ilib, show_progress=False)
        svf = train_steering_vector(R.model, R.tok, list(zip(fB, fA)), layers=[L], read_token_index=ifood, show_progress=False)
        vl = svl.layer_activations[L].reshape(-1); vf = svf.layer_activations[L].reshape(-1)
        cos = float(torch.nn.functional.cosine_similarity(vl.unsqueeze(0), vf.unsqueeze(0)).item())
        hAl, hBl = acts_at(lA, ilib, L), acts_at(lB, ilib, L)
        clf_l = probe(hAl, hBl)
        hAf, hBf = acts_at(fA, ifood, L), acts_at(fB, ifood, L)
        clf_f = probe(hAf, hBf)
        cAl, cBl = hAl.mean(0), hBl.mean(0)
        as_ = ((cBl - cAl).norm() / vl.norm()).item()
        libfwd = float((clf_l.predict(acts_at(lA, ilib, L, svl, 1.0*as_).numpy()) == 1).mean())
        cAf, cBf = hAf.mean(0), hBf.mean(0)
        asf_ = ((cBf - cAf).norm() / vf.norm()).item()
        hs = acts_at(fA, ifood, L, svl, asf_)          # library 之 v 施于 food
        gen = float((clf_f.predict(hs.numpy()) == 1).mean())
        rows.append((L, cos, gen, libfwd))
        print(f"{L:>3} {cos:>+18.3f} {gen:>14.3f} {libfwd:>8.3f}", flush=True)

    print("\n=== B) OOD 诊 (layer 6, 省名位) ===", flush=True)
    L = len(LAYERS)//2
    svl = train_steering_vector(R.model, R.tok, list(zip(lB, lA)), layers=[L], read_token_index=ilib, show_progress=False)
    vl = svl.layer_activations[L].reshape(-1)
    hAl, hBl = acts_at(lA, ilib, L), acts_at(lB, ilib, L)
    allreal = torch.cat([hAl, hBl], 0)
    cAl, cBl = hAl.mean(0), hBl.mean(0)
    as_ = ((cBl - cAl).norm() / vl.norm()).item()
    steered = acts_at(lA, ilib, L, svl, 1.0*as_)
    def nn_cos(X):
        # 每个 X 与所有真实表示的最大余弦
        Xn = X / X.norm(dim=1, keepdim=True)
        Rn = allreal / allreal.norm(dim=1, keepdim=True)
        return (Xn @ Rn.T).max(dim=1).values.mean().item()
    print(f"  真A 之最近真表示余弦:   {nn_cos(hAl):+.4f}", flush=True)
    print(f"  真B 之最近真表示余弦:   {nn_cos(hBl):+.4f}", flush=True)
    print(f"  干预A 之最近真表示余弦: {nn_cos(steered):+.4f}", flush=True)
    print(f"  范数比 ‖steered‖/‖orig‖: {(steered.norm(dim=1)/hAl.norm(dim=1)).mean().item():.3f}", flush=True)
    print("DIAG-DONE", flush=True)

if __name__ == "__main__":
    main()
