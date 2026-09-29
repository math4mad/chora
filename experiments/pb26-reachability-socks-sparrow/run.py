#!/usr/bin/env python3
# PB26 — 可达几何基准 · 袜对与麻雀
# 判据冻本: chora commit 32ffd7a / PREREG sha256 f659d06d53219e916363f26ce08cccfc5dfc9b4940d98020ce69351da98740b2
# 先冻后用: 本脚本只执行冻册 §1 之判据, 不改准则。
# 零 GPU · 纯 numpy · 三 seed (嵌入构造) 复跑 ≥3 次 (冻册裁决器)。
import json, os, sys, time, hashlib
import numpy as np

SEEDS        = [13, 14, 15]
N_PER        = 100          # 每分量节点数 → N = 200 ≥ 200
D            = 32
DECOY_COS    = 0.92         # 诱饵目标余弦 (冻册: 须真"面对面" ≥0.9)
N_DECOY      = 40           # 跨割诱饵对
N_POS        = 500          # 正例 (同分量可达) 采样对
N_NEG_NAT    = 500          # 自然负例 (跨割, 非诱饵)
N_WALL_CAND  = 12           # 玻璃候选边 (墙候选)
N_WALL_BLOCK = 9            # 其中真阻断 (玻璃) 数; 余 3 为真通门
OBS_FRAC     = 0.8          # 观测覆盖率 (无观测者按"阻断"先验)
OUTDIR       = os.path.dirname(os.path.abspath(__file__))

# ---------- 世界图 ----------
def build_component(n, rng):
    adj = [[] for _ in range(n)]
    for i in range(1, n):                       # 随机生成树 → 连通
        j = int(rng.integers(0, i)); adj[i].append(j); adj[j].append(i)
    for _ in range(int(0.5 * n)):               # 加边 → 有环, 路不止一条
        i, j = map(int, rng.integers(0, n, 2))
        if i != j and j not in adj[i]:
            adj[i].append(j); adj[j].append(i)
    return adj

def graph_dist(adj, src):
    n = len(adj); dist = [-1] * n; dist[src] = 0; q = [src]
    while q:
        u = q.pop(0)
        for v in adj[u]:
            if dist[v] < 0:
                dist[v] = dist[u] + 1; q.append(v)
    return np.array(dist)

def kernel_coords(adj, k, tau=2.0):
    """图距离核 MDS: S=exp(-hops/tau) 特征分解 → cos ≈ S, 相似随跳距衰减。"""
    n = len(adj)
    Dg = np.zeros((n, n))
    for i in range(n):
        Dg[i] = graph_dist(adj, i)
    S = np.exp(-Dg / tau)
    w, V = np.linalg.eigh(S)
    idx = np.argsort(w)[::-1][:k]
    vals = np.clip(w[idx], 0, None)
    return V[:, idx] * np.sqrt(vals)

# ---------- 嵌入 (可复现: seed 决定一切) ----------
def make_world(seed):
    rng = np.random.default_rng(seed)
    adj = [build_component(N_PER, rng), build_component(N_PER, rng)]
    e = np.zeros((2 * N_PER, D))
    KH = 16
    for comp in (0, 1):
        coords = kernel_coords(adj[comp], KH, tau=2.0)
        base = comp * KH                    # 两分量各占互斥谱子空间 → 跨割普通对真远
        for i in range(N_PER):
            idx = comp * N_PER + i
            spec = np.zeros(D); spec[base:base + KH] = coords[i]
            e[idx] = spec + rng.normal(scale=0.03, size=D)
    e = e / np.linalg.norm(e, axis=1, keepdims=True)

    # 跨割诱饵: 让 C2 的 m 与 C1 的 s "面对面" (高相似) 但隔玻璃
    # 关键: 取不重复节点, 否则后对覆盖前对 → 裁决器失效
    decoys = []
    s_pool = rng.choice(N_PER, size=N_DECOY, replace=False)
    m_pool = rng.choice(np.arange(N_PER, 2 * N_PER), size=N_DECOY, replace=False)
    for s, m in zip(s_pool, m_pool):
        s, m = int(s), int(m)
        tgt = DECOY_COS
        # 取与 e[s] 正交的**单位**噪声 → cos(vec, e[s]) = tgt (噪声未归一曾致 cos≈0.38, 仪器 bug)
        n = rng.normal(size=D)
        n = n - (n @ e[s]) * e[s]
        n = n / (np.linalg.norm(n) + 1e-12)
        vec = tgt * e[s] + np.sqrt(max(1 - tgt**2, 0)) * n
        vec = vec / np.linalg.norm(vec)
        e[m] = vec
        decoys.append((s, m))
    return adj, e, decoys, rng

# ---------- 采样 ----------
def sample_pairs(rng, adj, e, decoys):
    S = e @ e.T
    # 正例: 同分量, 跳距 1..6
    pos = []
    while len(pos) < N_POS:
        comp = int(rng.integers(0, 2)); off = comp * N_PER
        a = int(rng.integers(0, N_PER)); b = int(rng.integers(0, N_PER))
        if a == b: continue
        d = graph_dist(adj[comp], a)[b]
        if 1 <= d <= 6:
            pos.append((off + a, off + b))
    # 自然负例: 跨割, 非诱饵
    decoy_set = set((min(s, m), max(s, m)) for s, m in decoys)
    nat = []
    while len(nat) < N_NEG_NAT:
        a = int(rng.integers(0, N_PER)); b = int(rng.integers(N_PER, 2 * N_PER))
        if (min(a, b), max(a, b)) in decoy_set: continue
        nat.append((a, b))
    dec = [(s, m) for s, m in decoys]
    return S, pos, nat, dec

# ---------- 代理 ----------
def fit_similarity_threshold(S, pairs_pos, pairs_neg):
    """纯相似代理: 一维阈值, 在 train(正例+自然负例, 无诱饵) 上取最优。"""
    sim = np.array([S[a, b] for a, b in pairs_pos] + [S[a, b] for a, b in pairs_neg])
    lab = np.array([1] * len(pairs_pos) + [0] * len(pairs_neg))
    order = np.argsort(sim)
    best_tau, best_err = 0.0, 1e9
    for i in range(len(sim) + 1):
        tau = sim[order[i]] if i < len(sim) else 1.1
        pred = (sim >= tau).astype(int)
        err = int((pred != lab).sum())
        if err < best_err:
            best_err, best_tau = err, tau
    # 平滑: 取最优 err 的 tau 中点
    return float(best_tau), best_err / len(sim)

def sim_agent(S, tau, pairs):
    return np.array([1 if S[a, b] >= tau else 0 for a, b in pairs])

# ---------- 单 seed ----------
def run_seed(seed):
    adj, e, decoys, rng = make_world(seed)
    S, pos, nat, dec = sample_pairs(rng, adj, e, decoys)

    # 裁决器: 诱饵须真"面对面"
    decoy_cos = [float(S[s, m]) for s, m in dec]
    if min(decoy_cos) < 0.9:
        return {"seed": seed, "void": True, "min_decoy_cos": min(decoy_cos)}

    # 训练相似阈值 (无诱饵泄漏)
    tau, train_err = fit_similarity_threshold(S, pos, nat)

    # 测试 = 正例 + 自然负例 + 诱饵负例
    p_pos = sim_agent(S, tau, pos)
    p_nat = sim_agent(S, tau, nat)
    p_dec = sim_agent(S, tau, dec)
    pos_err = float((p_pos != 1).mean())
    nat_err = float((p_nat != 0).mean())
    decoy_err = float((p_dec != 0).mean())          # H-r1 读数
    overall_err = float((np.concatenate([p_pos, p_nat, p_dec]) !=
                         np.concatenate([np.ones(len(pos)), np.zeros(len(nat)), np.zeros(len(dec))])).mean())

    # 可达代理 (oracle 世界图): 同分量可达, 跨割 ∞
    def reach(a, b):
        return (a < N_PER) == (b < N_PER)
    r_err = float(np.mean([reach(a, b) != 1 for a, b in pos] +
                          [reach(a, b) != 0 for a, b in nat] +
                          [reach(a, b) != 0 for a, b in dec]))

    # 学墙臂:  N_WALL_CAND 条跨割候选边 (前 N_WALL_BLOCK 为玻璃/阻断, 余为真通门)
    wp = []
    for _ in range(N_WALL_CAND):
        i = int(rng.integers(0, N_PER)); j = int(rng.integers(N_PER, 2 * N_PER))
        wp.append((i, j))
    blocked_true = set(wp[:N_WALL_BLOCK])
    obs = {}
    for pair in wp:
        if rng.random() < OBS_FRAC:
            obs[pair] = pair not in blocked_true        # True=通, False=阻断
    pred_blocked = [pair for pair in wp if (obs.get(pair) is False) or (pair not in obs)]
    tp = len(set(pred_blocked) & blocked_true)
    fp = len(set(pred_blocked) - blocked_true)
    fn = len(blocked_true - set(pred_blocked))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0

    # 诚实诊断 (exploratory, 不占判据格): 相似分布与 AUC
    sim_pos = np.array([S[a, b] for a, b in pos])
    sim_nat = np.array([S[a, b] for a, b in nat])
    sim_dec = np.array([S[a, b] for a, b in dec])
    def auc(ps, ns):
        allv = np.concatenate([ps, ns]); lab = np.concatenate([np.ones(len(ps)), np.zeros(len(ns))])
        order = np.argsort(allv); ranks = np.empty_like(order); ranks[order] = np.arange(1, len(allv) + 1)
        n1, n0 = len(ps), len(ns)
        return float((ranks[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    diag = {"sim_pos_mean": float(sim_pos.mean()), "sim_pos_std": float(sim_pos.std()),
            "sim_nat_mean": float(sim_nat.mean()), "sim_nat_std": float(sim_nat.std()),
            "sim_dec_mean": float(sim_dec.mean()),
            "auc_pos_vs_nat": auc(sim_pos, sim_nat),
            "auc_pos_vs_all": auc(sim_pos, np.concatenate([sim_nat, sim_dec])),
            "frac_nat_ge_decoy_min": float((sim_nat >= sim_dec.min()).mean())}

    return {"seed": seed, "void": False, "tau": tau, "train_err": train_err,
            "min_decoy_cos": min(decoy_cos), "mean_decoy_cos": float(np.mean(decoy_cos)),
            "pos_err": pos_err, "nat_err": nat_err, "decoy_err": decoy_err,
            "overall_err": overall_err, "reach_err": r_err, "wall_f1": f1,
            "diag": diag}

# ---------- 主 ----------
def main():
    print("PB26 reachability benchmark — 冻册 §1 判据执行")
    print("判据冻本 sha256 f659d06d53219e916363f26ce08cccfc5dfc9b4940d98020ce69351da98740b2")
    results = []
    out = open(os.path.join(OUTDIR, "report_pb26.jsonl"), "w")
    for s in SEEDS:
        r = run_seed(s)
        out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush()   # 即算即落盘
        results.append(r)
        print("seed", s, r)
    out.close()
    ok = [r for r in results if not r.get("void")]
    if not ok:
        raise SystemExit("PB26: 三 seed 皆 void (裁决器未过) — 构造失败, 判仪器案")
    agg = {
        "seeds": SEEDS, "n_seeds_ok": len(ok),
        "decoy_err_mean": float(np.mean([r["decoy_err"] for r in ok])),
        "pos_err_mean": float(np.mean([r["pos_err"] for r in ok])),
        "nat_err_mean": float(np.mean([r["nat_err"] for r in ok])),
        "reach_err_mean": float(np.mean([r["reach_err"] for r in ok])),
        "wall_f1_mean": float(np.mean([r["wall_f1"] for r in ok])),
        "min_decoy_cos": float(min(r["min_decoy_cos"] for r in ok)),
    }
    H_r1 = agg["decoy_err_mean"] >= 0.8
    H_r2 = agg["reach_err_mean"] == 0.0
    H_r3 = agg["wall_f1_mean"] >= 0.8
    verdict = {"H-r1_similarity_fails": bool(H_r1),
               "H-r2_reachability_oracle": bool(H_r2),
               "H-r3_wall_learnable": bool(H_r3)}
    report = {"agg": agg, "judgement": verdict, "per_seed": results}
    with open(os.path.join(OUTDIR, "report_pb26.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n=== AGG ===", json.dumps(agg, ensure_ascii=False))
    print("=== JUDGEMENT ===", json.dumps(verdict, ensure_ascii=False))
    line = json.dumps({"agg": agg, "judgement": verdict}, ensure_ascii=False)
    import base64
    b = base64.b64encode(line.encode()).decode()
    print("REPORT_LINE_PB26 " + b[:120] + "...")
    with open(os.path.join(OUTDIR, "REPORT_LINE.txt"), "w") as f:
        f.write(b + "\n")
    print("PB26-DONE")

if __name__ == "__main__":
    main()
