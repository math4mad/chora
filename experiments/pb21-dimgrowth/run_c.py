# PB21c 五臂三籽 · 判据先冻见 PREREG_PB21c_fivearms.md (整卷净本: 修刃 GR=新块残差嵌入64维原座)
import json, numpy as np, torch, torch.nn as nn
rho=.95; n=2880; SEEDS=[13,14,15]; STAGES=[8,16,24,32,42,64]; NEP=3
rng=np.random.default_rng(11); X=np.zeros((n,64)); X[:,0]=rng.normal(size=n)
for k in range(1,64): X[:,k]=rho*X[:,k-1]+np.sqrt(1-rho**2)*rng.normal(size=n)
q=np.quantile(X[:,0],[.25,.5,.75]); y=np.searchsorted(q,X[:,0]); X=(X-X.mean())/X.std()
cut=int(n*.8); ytr=torch.from_numpy(y[:cut]).long(); yall=torch.from_numpy(y).long()
PERM=np.random.default_rng(7).permutation(64).tolist()
def model(s):
    torch.manual_seed(s); np.random.seed(s)
    return nn.Sequential(nn.Linear(64,32),nn.ReLU(),nn.Linear(32,4))
def acc(m,Z): return float((m(torch.from_numpy(Z).float()).argmax(1)==yall).float().mean())
def run(arm,seed):
    m=model(seed); opt=torch.optim.Adam(m.parameters(),lr=.01)
    order={"E":list(range(64)),"A":list(range(64)),"D":list(range(63,-1,-1)),"C":PERM}.get(arm)
    grow=arm!="B"; gr=arm=="A"
    basis=None; resids=[]; curve=[]; upd=0; u95=None
    Ztr=np.zeros((cut,64)); Zev=np.zeros((n,64))
    if grow:
        prev=0
        for t in STAGES:
            newc=order[prev:t]; prev=t
            if gr:
                Nm=np.zeros((n,64)); Nm[:,newc]=X[:,newc]
                if basis is not None and basis.shape[1]:
                    B=torch.from_numpy(basis).float(); F64=torch.from_numpy(Nm).float()
                    R64=(F64-(F64@B)@B.T).numpy()
                else: R64=Nm
                Fb=torch.from_numpy(R64[:,newc]).float()
                Q,_=torch.linalg.qr(Fb.T)
                resids.append(float(torch.norm(Q.T@Q-torch.eye(Q.shape[1]))))
                Kb=np.zeros((64,Q.shape[1])); Kb[np.array(newc),:]=Q.numpy()
                basis=Kb if basis is None else np.hstack([basis,Kb])
                Ztr[:,newc]=R64[:cut,newc]; Zev[:,newc]=R64[:,newc]
            else:
                Ztr[:,newc]=X[:cut][:,newc]; Zev[:,newc]=X[:,newc]
            xt=torch.from_numpy(Ztr).float()
            for _ in range(NEP):
                p=np.random.permutation(cut)
                for i in range(0,cut,32):
                    b=p[i:i+32]; loss=nn.functional.cross_entropy(m(xt[b]),ytr[b])
                    opt.zero_grad(); loss.backward(); opt.step(); upd+=1
            a=acc(m,Zev); curve.append(round(a,4))
            if u95 is None and a>=.95: u95=upd
    else:
        xt=torch.from_numpy(X[:cut]).float(); pe=int(np.ceil(cut/32))
        for u in range(pe*18):
            b=np.random.permutation(cut)[:32]; loss=nn.functional.cross_entropy(m(xt[b]),ytr[b])
            opt.zero_grad(); loss.backward(); opt.step()
            if (u+1)%pe==0:
                a=acc(m,X); curve.append(round(a,4))
                if u95 is None and a>=.95: u95=u+1
    return dict(curve=curve,resid=[round(r,4) for r in resids],upd95=u95)
R={}
for s in SEEDS:
    for arm in "BEDCA":
        R[f"{arm}{s}"]=run(arm,s)
        print(arm,s,"尾acc=",R[f"{arm}{s}"]['curve'][-1],"u95=",R[f"{arm}{s}"]['upd95'],flush=True)
J=dict(
 H_c1=all(max(R[f"A{s}"]['resid'] or [1])<.05 for s in SEEDS),
 H_c2={s:(R[f"E{s}"]['upd95'] is not None and R[f"B{s}"]['upd95'] is not None
          and R[f"E{s}"]['upd95']<=.5*R[f"B{s}"]['upd95']) for s in SEEDS},
 H_c3={s:dict(E=R[f"E{s}"]['upd95'],D=R[f"D{s}"]['upd95'],C=R[f"C{s}"]['upd95']) for s in SEEDS},
 H_c4={s:round(R[f"A{s}"]['curve'][-1]-R[f"E{s}"]['curve'][-1],4) for s in SEEDS})
json.dump(dict(case="PB21c",res=R,judge=J),open("result_pb21c.json","w"),ensure_ascii=False)
print("JUDGE:",json.dumps(J,ensure_ascii=False))
