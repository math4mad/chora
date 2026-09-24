"""G3 训练器: 四臂(given/free/random/learned) × 课程门控。
用法: python g3_train.py --arm given --steps 300 [--device mps]"""
import argparse, math, os, time, random
import torch
import torch.nn.functional as F
from g3_model import G3Model, make_bias
import g3_data as D

CAUSAL_CACHE = {}


def causal_mask(T, device):
    key = (T, str(device))
    if key not in CAUSAL_CACHE:
        m = torch.full((T, T), -1e9, device=device).triu(1)
        CAUSAL_CACHE[key] = m
    return CAUSAL_CACHE[key]


def arm_bias(arm, cs_row, adj, table=None, seed=0):
    """(T,) 舱号 -> (T,T) 加性视野偏置(不含因果)。"""
    if arm == "free":                      # 麻辣烫: 全通
        return torch.zeros_like(cs_row, dtype=torch.float)[None, :].repeat(len(cs_row), 1) * 0
    if arm == "given":                     # 主臂: 设计者视野
        return make_bias(cs_row, adj)
    if arm == "random":                    # 安慰剂: 同稀疏度, 乱划
        g = torch.Generator().manual_seed(seed)
        perm = torch.randperm(len(D.CABINS), generator=g)
        return make_bias(perm[cs_row], adj)
    if arm == "learned":                   # 模型自己去注意: 可学舱表
        return table[cs_row][:, cs_row]
    raise ValueError(arm)


def run(args):
    dev = torch.device(args.device)
    docs = D.load_docs()
    tok = D.Tok(docs)
    print(f"vocab={tok.vocab} docs={len(docs)}")
    model = G3Model(tok.vocab, d=args.d, layers=args.layers, h=args.heads, ctx=args.ctx).to(dev)
    nparam = sum(p.numel() for p in model.parameters()) - tok.vocab * args.d  # tied
    print(f"params≈{nparam/1e6:.1f}M arm={args.arm}")
    table = torch.zeros(len(D.CABINS), len(D.CABINS), device=dev, requires_grad=(args.arm == "learned"))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)
    if args.arm == "learned":
        opt.add_param_group({"params": [table]})
    step, t0, losses = 0, time.time(), []
    while step < args.steps:
        cabins, adj = D.stage_at(step, args.steps)
        xs, cs, ys = D.pack(docs, tok, args.ctx, args.batch, seed=step, cabins_filter=cabins)
        xs, cs, ys = xs.to(dev), cs.to(dev), ys.to(dev)
        for i in range(0, xs.size(0), args.batch):
            xb, cb, yb = xs[i:i + args.batch], cs[i:i + args.batch], ys[i:i + args.batch]
            bias = torch.stack([arm_bias(args.arm, cb[b], adj, table) + causal_mask(cb.size(1), dev)
                                for b in range(cb.size(0))])[:, None]  # (B,1,T,T) 广播到各头
            logits = model(xb, cb, bias)
            loss = F.cross_entropy(logits.view(-1, tok.vocab), yb.view(-1), ignore_index=D.PAD)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            losses.append(loss.item()); step += 1
            if step % 50 == 0 or step == 1:
                print(f"step {step:4d} stage|{len(cabins)},{len(adj)} loss {loss.item():.3f} "
                      f"avg50 {sum(losses[-50:])/len(losses[-50:]):.3f} {time.time()-t0:.0f}s")
            if step >= args.steps:
                break
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"), exist_ok=True)
    torch.save({"model": model.state_dict(), "tok": tok.itos, "args": vars(args)},
               os.path.join(os.path.dirname(os.path.abspath(__file__)), f"out/g3_{args.arm}.pt"))
    print("saved ckpt, wall", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--arm", default="given", choices=["given", "free", "random", "learned"])
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    p.add_argument("--d", type=int, default=192); p.add_argument("--layers", type=int, default=4)
    p.add_argument("--heads", type=int, default=6); p.add_argument("--ctx", type=int, default=256)
    p.add_argument("--batch", type=int, default=8)
    run(p.parse_args())
