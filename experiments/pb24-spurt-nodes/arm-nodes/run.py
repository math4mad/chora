#!/usr/bin/env python3
# PB24-spurt-nodes — 命名爆炸假说机 (合成流+义素引擎; 判据见 PREREG_PB24.md, 先冻后用)
# v2 (0928 试射修三疵): GB 剖面重写; 池 4000 防饱和截顶; pending FIFO 600 防积滞。
# 舱律: 即算即落盘 (逐格 append jsonl + REPORT_LINE b64)。CPU 舱免席位; 无 torch 无疫苗。
import numpy as np, json, base64, hashlib, os, time
from collections import deque

T = 3000; D = 64; K_SPARSE = 8; POOL = 4000; GAMMA = 3.0; CHECK = 5; MAXP = 600
RATES = [0.5, 1.0, 2.0]; KAPPAS = [0.0, 1.5, 3.0]; SEEDS = [11, 22, 33]
OUT = '/kaggle/working' if os.path.isdir('/kaggle/working') else os.path.dirname(os.path.abspath(__file__))
RPT = os.path.join(OUT, 'report_pb24.jsonl')

def make_lexicon(seed):
    rng = np.random.default_rng(seed)
    W = np.zeros((POOL, D))
    for i in range(POOL):
        idx = rng.choice(D, K_SPARSE, replace=False)
        W[i, idx] = rng.normal(size=K_SPARSE)
    W /= np.linalg.norm(W, axis=1, keepdims=True)
    Q = rng.normal(size=(256, D)); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    sha = hashlib.sha256(W.tobytes()).hexdigest()[:16]
    return W, Q, sha

def simulate(r, kap, seed):
    rng = np.random.default_rng(seed * 1000 + int(r * 10) + int(kap * 10))
    W, Q, sha = make_lexicon(seed)
    learned = np.zeros(POOL, bool); L = np.zeros((0, D))
    pend = deque()
    V = np.zeros(T + 1); Sarr = np.zeros(T + 1)
    order = rng.permutation(POOL); optr = 0
    for t in range(1, T + 1):
        for _ in range(rng.poisson(r)):
            if optr < POOL:
                w = order[optr]; optr += 1
                if not learned[w]:
                    pend.append(w)
                    if len(pend) > MAXP: pend.popleft()   # FIFO: 过期即弃 (真实时效窗)
        if pend and (t % CHECK == 0 or len(L) == 0):
            P = np.array(pend)
            if len(L) == 0:
                cost = np.ones(len(P))
                S = 0.0
            else:
                sim = W[P] @ L.T
                cost = 1.0 - sim.max(axis=1)
                S = float(np.maximum(Q @ L.T, 0).max(axis=1).mean())
            h = np.clip(np.exp(kap * S - GAMMA * cost), 0, 1)
            hit = rng.random(len(P)) < (1 - (1 - h) ** CHECK)
            if hit.any():
                add = P[hit]
                learned[add] = True
                L = np.vstack([L, W[add]])
                pend = deque(P[~hit].tolist())
            Sarr[t] = S
        V[t] = learned.sum()
    return V, sha

def metrics(V):
    sm = np.convolve(V, np.ones(51) / 51, mode='valid')
    dV = np.gradient(sm)
    base = np.median(dV[:len(dV) // 4]) + 1e-9
    ratio = float(dV.max() / base)
    tp = int(np.argmax(dV))
    return ratio, tp, int(V[tp])

def gb_pair(runs_V):
    """龄对齐峰 vs 量对齐峰 (Ganger&Brent 伪影复测)。返回 (peak_age, peak_size)。"""
    dA = np.stack([np.gradient(np.convolve(V, np.ones(31) / 31, 'valid')) for V in runs_V])
    age = dA.mean(0)
    base_a = np.median(age[:len(age) // 4]) + 1e-9
    pk_age = float(age.max() / base_a)
    # 量对齐: 每 run 把 dV/dt 重采样到共同词量格
    gmax = min(V[-1] for V in runs_V); grid = np.linspace(1, gmax, 200)
    prof = []
    for V in runs_V:
        dV = np.gradient(V)
        idx = np.arange(len(V))
        vq = np.maximum.accumulate(V)                     # 单调化
        prof.append(np.interp(grid, vq[1:], dV[1:]))
    pr = np.mean(prof, 0)
    pk_size = float(pr.max() / (np.median(pr[:50]) + 1e-9))
    return round(pk_age, 3), round(pk_size, 3)

def fl(obj):
    with open(RPT, 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
    print('REPORT_LINE ' + base64.b64encode(json.dumps(obj).encode()).decode(), flush=True)

if __name__ == '__main__':
    t0 = time.time()
    open(RPT, 'w').close()
    results = {}
    for r in RATES:
        for kap in KAPPAS:
            runs_V, rows = [], []
            for sd in SEEDS:
                V, sha = simulate(r, kap, sd)
                ratio, tp, vpk = metrics(V)
                row = {'cell': f'r{r}_k{kap}', 'seed': sd, 'V_end': int(V[-1]),
                       'spurt_ratio': round(ratio, 3), 't_peak': tp, 'V_peak': vpk, 'lex_sha': sha}
                fl(row); rows.append(row); runs_V.append(V)
                del V
            a, b = gb_pair(runs_V)
            fl({'cell': f'r{r}_k{kap}', 'type': 'cell_summary',
                'V_peak_mean': round(float(np.mean([x['V_peak'] for x in rows])), 1),
                't_peak_mean': round(float(np.mean([x['t_peak'] for x in rows])), 1),
                'gb_age_peak': a, 'gb_size_peak': b})
            results[f'{r}_{kap}'] = rows
    for kap in KAPPAS:
        vp = [np.mean([x['V_peak'] for x in results[f'{r}_{kap}']]) for r in RATES]
        tp = [np.mean([x['t_peak'] for x in results[f'{r}_{kap}']]) for r in RATES]
        cv = lambda a: float(np.std(a) / (np.mean(a) + 1e-9))
        lock = cv(vp) / (cv(tp) + 1e-9)
        fl({'type': 'verdict', 'kappa': kap, 'CV_Vpeak': round(cv(vp), 3),
            'CV_tpeak': round(cv(tp), 3), 'lock_state_ratio': round(lock, 3),
            'ruling': '锁量' if lock < 0.5 else ('锁龄' if lock > 2 else '中间态')})
    print('PB24-NODES-DONE elapsed=%.1fs' % (time.time() - t0), flush=True)
