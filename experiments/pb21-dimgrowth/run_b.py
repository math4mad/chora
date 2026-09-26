# PB21b 因果链维序 · 判据 PREREG_PB21b_causalchain.md 先冻
import json,numpy as np,torch,torch.nn as nn
rho=0.95; n=2880
rng=np.random.default_rng(11); e=rng.normal(size=(n,64))
X=np.zeros((n,64)); X[:,0]=rng.normal(size=n)
for k in range(1,64): X[:,k]=rho*X[:,k-1]+np.sqrt(1-rho**2)*e[:,k]
q=np.quantile(X[:,0],[.25,.5,.75]); y=np.searchsorted(q,X[:,0])
X=(X-X.mean())/X.std(); cut=int(n*.8); ytr=torch.from_numpy(y[:cut]).long(); yall=torch.from_numpy(y).long()
STAGES=[8,16,24,32,42,64]; NEP=3; SEEDS=[13,14]
def model(s):
    torch.manual_seed(s); np.random.seed(s)
    return nn.Sequential(nn.Linear(64,32),nn.ReLU(),nn.Linear(32,4))
def gr(newmat,basis):
    F=torch.from_numpy(newmat).float()
    if basis is not None and basis.shape[1]:
        B=torch.from_numpy(basis).float(); F=F-(F@B)@B.T
    Q,_=torch.linalg.qr(F.T)
    r=float(torch.linalg.norm(Q.T@Q-torch.eye(Q.shape[1]))) if Q.shape[1] else 0.0
    return Q.numpy(),r
def run(arm,seed):
    m=model(seed); opt=torch.optim.Adam(m.parameters(),lr=0.01)
    order=list(range(64)) if arm!="D" else list(range(63,-1,-1))
    grow=arm!="B"; usegr=arm in "AD"
    basis=None; resids=[]; curve=[]; upd=0; u95=None
    if grow:
        prev=0
        for t in STAGES:
            newc=order[prev:t]; prev=t
            if usegr:
                nm=np.zeros((n,64)); nm[:,newc]=X[:,newc]; Qn,r=gr(nm,basis); resids.append(r)
                basis=Qn if basis is None else np.hstack([basis,Qn])
                Xtr=X[:cut]-((X[:cut]@basis)@basis.T); Xev=X-((X@basis)@basis.T)
            else:
                Z=np.zeros((n,64)); Z[:,order[:t]]=X[:,order[:t]]
                Xtr=Z[:cut]; Xev=Z
            xt=torch.from_numpy(Xtr).float()
            for _ in range(NEP):
                p=np.random.permutation(cut)
                for i in range(0,cut,32):
                    b=p[i:i+32]; loss=nn.functional.cross_entropy(m(xt[b]),ytr[b])
                    opt.zero_grad(); loss.backward(); opt.step(); upd+=1
            a=float((m(torch.from_numpy(Xev).float()).argmax(1)==yall).float().mean())
            curve.append(round(a,4))
            if u95 is None and a>=0.95: u95=upd
    else:
        xt=torch.from_numpy(X[:cut]).float(); pe=int(np.ceil(cut/32))
        for u in range(pe*18):
            b=np.random.permutation(cut)[:32]; loss=nn.functional.cross_entropy(m(xt[b]),ytr[b])
            opt.zero_grad(); loss.backward(); opt.step()
            if (u+1)%pe==0:
                a=float((m(torch.from_numpy(X).float()).argmax(1)==yall).float().mean())
                curve.append(round(a,4))
                if u95 is None and a>=0.95: u95=u+1
    return dict(curve=curve,resid=[round(r,4) for r in resids],upd95=u95)
R={}
for s in SEEDS:
    for arm in ["A","E","D","B"]: R[f"{arm}{s}"]=run(arm,s)
out=dict(case="PB21b",rho=rho,res=R,
  judge=dict(
    H_b1=all(max(R[f"{a}{s}"]["resid"] or [0])<0.05 for a in "AD" for s in SEEDS),
    H_b2={s:dict(dA_D=round(R[f"A{s}"]["curve"][-1]-R[f"D{s}"]["curve"][-1],4),
                 A95=R[f"A{s}"]["upd95"],D95=R[f"D{s}"]["upd95"]) for s in SEEDS},
    H_b3={s:round(R[f"A{s}"]["curve"][-1]-R[f"E{s}"]["curve"][-1],4) for s in SEEDS}))
json.dump(out,open("result_pb21b.json","w"),ensure_ascii=False)
print(json.dumps(out["judge"],ensure_ascii=False))
for k,v in R.items(): print(k,v["curve"],"u95=",v["upd95"])
