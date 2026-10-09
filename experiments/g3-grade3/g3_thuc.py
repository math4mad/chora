#!/usr/bin/env python3
"""G3 自然语料复证 — THUCNews (10 主题 = 10 舱), 测「给定注意力」是否仍无优势。

与中炮之别: 语料由**模板**换为**自然中文新闻**(主题标注); 舱数 4→10; 判分由 G3-Paper 换为
**held-out 交叉熵** (scale-free, 不依赖探针)。
用法: ../../.venv-g3/bin/python g3_thuc.py --steps 800 --d 384 --layers 6
"""
import argparse, os, random, time
import torch, torch.nn.functional as F
from g3_model import G3Model, make_bias

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/tmp/thuc"          # train.txt / test.txt (fasttext: __label__N\ttokens)
PAD, BOS, EOS = 0, 1, 2


def load(fn):
    docs = []
    with open(os.path.join(SRC, fn), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if "\t" not in line:
                continue
            lab, txt = line.split("\t", 1)
            cab = int(lab.replace("__label__", ""))
            txt = "".join(txt.split())          # 去分词空格 → 连续中文
            if len(txt) >= 8:
                docs.append((txt, cab))
    return docs


class Tok:
    def __init__(self, docs):
        chars = sorted({c for t, _ in docs for c in t})
        self.itos = ["<pad>", "<bos>", "<eos>"] + chars
        self.stoi = {c: i for i, c in enumerate(self.itos)}
        self.vocab = len(self.itos)
    def encode(self, t):
        return [BOS] + [self.stoi[c] for c in t if c in self.stoi] + [EOS]


def causal(T, dev):
    return torch.full((T, T), -1e9, device=dev).triu(1)


def bias_for(arm, cb, table, seed, n_cab):
    if arm == "free":
        return torch.zeros(cb.size(0), cb.size(0), device=cb.device)
    if arm == "given":
        return make_bias(cb, set())
    if arm == "random":
        g = torch.Generator().manual_seed(seed)
        perm = torch.randperm(n_cab, generator=g).to(cb.device)
        return make_bias(perm[cb], set())
    if arm == "learned":
        return table[cb][:, cb]
    raise ValueError(arm)


def pack(docs, tok, ctx, seed):
    ds = docs[:]; random.Random(seed).shuffle(ds)
    toks, cabs = [], []
    for t, c in ds:
        e = tok.encode(t); toks += e; cabs += [c] * len(e)
    rows = max(1, (len(toks) - 1) // ctx)
    arr = torch.tensor(toks[:rows*ctx+1]); car = torch.tensor(cabs[:rows*ctx+1])
    return (arr[:rows*ctx].view(rows, ctx), car[:rows*ctx].view(rows, ctx), arr[1:rows*ctx+1].view(rows, ctx))


def evaluate(model, tok, docs, ctx, batch, dev, arm, n_cab):
    model.eval(); table = torch.zeros(n_cab, n_cab, device=dev)
    xs, cs, ys = pack(docs, tok, ctx, seed=999)
    tot, n = 0.0, 0
    with torch.no_grad():
        for i in range(0, xs.size(0), batch):
            xb, cb, yb = xs[i:i+batch].to(dev), cs[i:i+batch].to(dev), ys[i:i+batch].to(dev)
            bias = torch.stack([bias_for(arm, cb[b], table, 0, n_cab) + causal(cb.size(1), dev)
                                for b in range(cb.size(0))])[:, None]
            lg = model(xb, cb, bias)
            tot += F.cross_entropy(lg.view(-1, tok.vocab), yb.view(-1), ignore_index=PAD, reduction="sum").item()
            n += (yb != PAD).sum().item()
    model.train()
    return tot / max(1, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--d", type=int, default=384); ap.add_argument("--layers", type=int, default=6)
    ap.add_argument("--heads", type=int, default=6); ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--arms", nargs="*", default=["given", "random", "free", "learned"])
    a = ap.parse_args()
    dev = torch.device(a.device)
    tr, te = load("train.txt"), load("test.txt")
    tok = Tok(tr); n_cab = max(c for _, c in tr) + 1
    print(f"[thuc] train={len(tr)} test={len(te)} chars={sum(len(t) for t,_ in tr)} vocab={tok.vocab} cabins={n_cab} dev={dev}", flush=True)
    for arm in a.arms:
        m = G3Model(tok.vocab, d=a.d, layers=a.layers, h=a.heads, ctx=a.ctx).to(dev)
        table = torch.zeros(n_cab, n_cab, device=dev, requires_grad=(arm == "learned"))
        opt = torch.optim.AdamW(m.parameters(), lr=3e-4, weight_decay=0.1)
        if arm == "learned": opt.add_param_group({"params": [table]})
        t0 = time.time(); step = 0; losses = []
        while step < a.steps:
            xs, cs, ys = pack(tr, tok, a.ctx, seed=step)
            xs, cs, ys = xs.to(dev), cs.to(dev), ys.to(dev)
            for i in range(0, xs.size(0), a.batch):
                xb, cb, yb = xs[i:i+a.batch], cs[i:i+a.batch], ys[i:i+a.batch]
                bias = torch.stack([bias_for(arm, cb[b], table, step, n_cab) + causal(cb.size(1), dev)
                                    for b in range(cb.size(0))])[:, None]
                lg = m(xb, cb, bias)
                loss = F.cross_entropy(lg.view(-1, tok.vocab), yb.view(-1), ignore_index=PAD)
                opt.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
                losses.append(loss.item()); step += 1
                if step >= a.steps: break
        te_loss = evaluate(m, tok, te, a.ctx, a.batch, dev, arm, n_cab)
        print(f"  [{arm:8s}] train_avg {sum(losses[-50:])/len(losses[-50:]):.3f} | **test_loss {te_loss:.4f}** | {time.time()-t0:.0f}s", flush=True)
    print("THUC-DONE", flush=True)


if __name__ == "__main__":
    main()
