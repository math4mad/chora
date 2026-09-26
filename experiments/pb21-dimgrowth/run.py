#!/usr/bin/env python3
# PB21 逐维添加 MNIST 沙盒 · 判据先冻见 PREREG_PB21_dimgrowth.md (commit 在先)
# 意承建造对话千问码, 重写去陷阱: 向量化 GR, 阶式生长, 三臂对照。
import json, time, base64, hashlib
import numpy as np, torch, torch.nn as nn
from sklearn.datasets import load_digits

torch.set_num_threads(4)
DEV = "cpu"
STAGES = [8, 16, 24, 32, 42, 64]           # 六阶生长
NEP = 3                                    # 每阶 3 pass
SEEDS = [13, 14]
PERM = np.random.default_rng(7).permutation(64).tolist()   # C 臂乱序·冻

X, y = load_digits(return_X_y=True)
X = (X - X.mean()) / (X.std() + 1e-9)
n = len(X); cut = int(n * 0.8)
idx_tr = np.arange(cut); idx_te = np.arange(cut, n)

def model(seed):
    torch.manual_seed(seed); np.random.seed(seed)
    return nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 10)).to(DEV)

def gr_residualize(new_feats, basis):
    """新维块对已见基 GR: 返回残差特征与其正交基 (矩阵形, 无逐样本循环)。"""
    Bf = torch.from_numpy(basis).float() if basis is not None and len(basis) else None
    F = torch.from_numpy(new_feats).float()
    if Bf is not None and Bf.shape[1] > 0:
        F = F - (F @ Bf) @ Bf.T                      # 残差化 (新信息只)
    Q, _ = torch.linalg.qr(F.T)                      # 列正交基
    resid = float(torch.linalg.norm(Q.T @ Q - torch.eye(Q.shape[1])).cpu()) if Q.shape[1] else 0.0
    return F.numpy(), Q.T.numpy(), resid              # Q.T: (d_new, r) 基

def acc_of(m, cols):
    xt = torch.from_numpy(X[:, cols]).float(); yt = torch.from_numpy(y).long()
    with torch.no_grad():
        return float((m(xt).argmax(1) == yt).float().mean())

def train_arm(arm, seed):
    m = model(seed)
    opt = torch.optim.Adam(m.parameters(), lr=0.01)
    yt = torch.from_numpy(y[idx_tr]).long()
    if arm == "A": cols_order = list(range(64)); grow = True
    elif arm == "C": cols_order = PERM; grow = True
    else: cols_order = list(range(64)); grow = False
    seen = []; basis = None; resids = []; curve = []; upd = 0; reach95 = None
    batches = []
    if grow:
        prev = 0
        for t in STAGES:
            newc = cols_order[prev:t]; prev = t
            xt_new = X[idx_tr][:, newc]
            if len(seen):
                _, Q, r = gr_residualize(xt_new, basis)
                resids.append(r); basis = np.hstack([basis, Q]) if basis is not None else Q
            else:
                _, Q, r = gr_residualize(xt_new, None)
                resids.append(r); basis = Q
            cols = cols_order[:t]
            Xs = X[idx_tr][:, cols]
            if len(seen) and basis is not None:
                Xs = Xs - (Xs @ basis) @ basis.T * 0   # 全空间已在新基下; 保持原坐标 (预测侧同模型)
            xt = torch.from_numpy(Xs).float()
            for _ in range(NEP):
                perm = np.random.permutation(len(xt))
                for i in range(0, len(xt), 32):
                    b = perm[i:i + 32]
                    loss = nn.functional.cross_entropy(m(xt[b]), yt[b])
                    opt.zero_grad(); loss.backward(); opt.step(); upd += 1
            acc_te = acc_of(m, cols)
            curve.append(round(acc_te, 4))
            if reach95 is None and acc_te >= 0.95: reach95 = upd
    else:
        xt = torch.from_numpy(X[idx_tr]).float()
        per_epoch = int(np.ceil(len(xt) / 32)); target = per_epoch * sum(NEP for _ in STAGES)
        for u in range(target):
            b = np.random.permutation(len(xt))[:32]
            loss = nn.functional.cross_entropy(m(xt[b]), yt[b])
            opt.zero_grad(); loss.backward(); opt.step()
            if (u + 1) % per_epoch == 0:
                a = acc_of(m, list(range(64))); curve.append(round(a, 4))
                if reach95 is None and a >= 0.95: reach95 = u + 1
    W = np.concatenate([p.detach().numpy().ravel() for p in m.parameters()])
    return dict(acc_curve=curve, ortho_resid=[round(r, 4) for r in resids],
                upd95=reach95, wvec=W)

R = {}
T0 = time.time()
for seed in SEEDS:
    for arm in ["A", "B", "C"]:
        r = train_arm(arm, seed); R[f"{arm}{seed}"] = r
        print(arm, seed, "acc尾=", r["acc_curve"][-1] if r["acc_curve"] else None,
              "残差max=", max(r["ortho_resid"], default=0), "upd95=", r["upd95"], flush=True)
# 判读
rep = {"case": "PB21", "seeds": SEEDS, "stages": STAGES, "res": {k: {kk: vv for kk, vv in v.items() if kk != "wvec"} for k, v in R.items()}}
def judge():
    j = {}
    h1 = all(max(R[f"A{s}"]["ortho_resid"], default=1) < 0.05 and max(R[f"C{s}"]["ortho_resid"], default=1) < 0.05 for s in SEEDS)
    j["H1_器闸"] = h1
    j["H2_序效"] = {s: dict(dacc=round(R[f"A{s}"]["acc_curve"][-1] - R[f"B{s}"]["acc_curve"][-1], 4),
                            a95=R[f"A{s}"]["upd95"], b95=R[f"B{s}"]["upd95"]) for s in SEEDS}
    def jumps(c):
        up = 0
        for i in range(1, len(c)):
            if c[i] - max(c[i - 1], (c[i - 2] if i >= 2 else c[i - 1])) > 0.005: up += 1
        return up
    j["H3_鼓包"] = {s: dict(A=jumps(R[f"A{s}"]["acc_curve"]), C=jumps(R[f"C{s}"]["acc_curve"])) for s in SEEDS}
    return j
rep["judge_raw"] = judge()
sha = hashlib.sha256(json.dumps(rep, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
rep["sha"] = sha
json.dump(rep, open("result_pb21.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rep["judge_raw"], ensure_ascii=False, indent=1))
print("DONE PB21", round(time.time() - T0, 1), "s sha=", sha)
