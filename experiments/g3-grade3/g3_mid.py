#!/usr/bin/env python3
"""G3 中炮 — corpus_big (3.4M 字符) × 四臂 + no-curr → G3-Paper 落架判分。

非冻本之 1B 主炮; 系**源受限之降格试射** (如实登)。
用法: ../../.venv-g3/bin/python g3_mid.py --steps 3000 --d 512 --layers 8 --device mps
"""
import argparse, json, os, time
import torch, torch.nn.functional as F
from g3_model import G3Model
import g3_data as D
from g3_train import arm_bias, causal_mask
from g3_paper_v1 import PROBES_V1 as PROBES

HERE = os.path.dirname(os.path.abspath(__file__))


def train_arm(docs, tok, arm, a, dev, curr=True):
    model = G3Model(tok.vocab, d=a.d, layers=a.layers, h=a.heads, ctx=a.ctx).to(dev)
    table = torch.zeros(len(D.CABINS), len(D.CABINS), device=dev, requires_grad=(arm == "learned"))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)
    if arm == "learned":
        opt.add_param_group({"params": [table]})
    steps = a.steps
    step, t0, losses = 0, time.time(), []
    while step < steps:
        cabins, adj = D.stage_at(step, steps) if curr else ({0, 1, 2, 3}, {(0, 1), (2, 3)})
        xs, cs, ys = D.pack(docs, tok, a.ctx, a.batch, seed=step, cabins_filter=cabins)
        xs, cs, ys = xs.to(dev), cs.to(dev), ys.to(dev)
        for i in range(0, xs.size(0), a.batch):
            xb, cb, yb = xs[i:i+a.batch], cs[i:i+a.batch], ys[i:i+a.batch]
            bias = torch.stack([arm_bias(arm, cb[b], adj, table) + causal_mask(cb.size(1), dev)
                                for b in range(cb.size(0))])[:, None]
            logits = model(xb, cb, bias)
            loss = F.cross_entropy(logits.view(-1, tok.vocab), yb.view(-1), ignore_index=D.PAD)
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
            losses.append(loss.item()); step += 1
            if step % 200 == 0 or step == 1:
                print(f"  [{arm}{'' if curr else '_nocurr'}] {step:4d} loss {loss.item():.3f} "
                      f"avg {sum(losses[-50:])/len(losses[-50:]):.3f} {time.time()-t0:.0f}s", flush=True)
            if step >= steps:
                break
    model.eval()
    return model, round(time.time()-t0, 1)


def paper(model, tok, dev, arm):
    zeros = torch.zeros(len(D.CABINS), len(D.CABINS), device=dev)
    def lp(text):
        ids = tok.encode(text)
        x = torch.tensor([ids], device=dev); cab = torch.tensor([[0]*len(ids)], device=dev)
        bias = arm_bias(arm, cab[0], set(), zeros) + causal_mask(len(ids), dev)
        with torch.no_grad():
            lg = model(x, cab, bias[None, None])[:, :-1].log_softmax(-1)
        t = torch.tensor(ids[1:], device=dev)
        return lg.gather(-1, t.view(1, -1, 1)).sum().item()
    strict = shelf = 0; rows = []
    for prompt, cands, gold, axis in PROBES:
        base = lp(prompt); w, wc = max(cands, key=lambda c: lp(prompt + c[0]) - base)
        gc = next(c for g, c in cands if g == gold)
        s, h = w == gold, wc == gc
        strict += s; shelf += h
        rows.append([axis, prompt, w, wc, gold, gc, bool(s), bool(h)])
    return strict, shelf, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--d", type=int, default=512); ap.add_argument("--layers", type=int, default=8)
    ap.add_argument("--heads", type=int, default=8); ap.add_argument("--ctx", type=int, default=512)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--corpus", default="corpus_big")
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--arms", nargs="*", default=["given", "free", "random", "learned"])
    a = ap.parse_args()
    dev = torch.device(a.device)
    docs = D.load_docs_big(a.corpus); tok = D.Tok(docs)
    print(f"[mid] corpus={a.corpus} docs={len(docs)} chars={sum(len(t) for t,_ in docs)} "
          f"vocab={tok.vocab} dev={dev} cfg=d{a.d}/L{a.layers}/h{a.heads}/ctx{a.ctx} steps={a.steps}", flush=True)
    report = {"paper": "v1", "paper_sha": "de0c87e6391f8d7a037b6c115dc841fe2c7eabff9a262dd7d1ce7f623471f34c",
              "config": vars(a), "n_docs": len(docs), "n_chars": sum(len(t) for t, _ in docs),
              "vocab": tok.vocab, "arms": {}}
    for arm in a.arms:
        print(f"\n=== arm {arm} ===", flush=True)
        m, wall = train_arm(docs, tok, arm, a, dev, curr=True)
        st, sh, rows = paper(m, tok, dev, arm)
        report["arms"][arm] = {"strict": st, "shelf": sh, "n": len(PROBES), "wall_s": wall, "rows": rows}
        print(f"  G3-Paper[{arm}] 字面 {st}/{len(PROBES)} 落架 {sh}/{len(PROBES)} wall {wall:.0f}s", flush=True)
    if "given" in a.arms:
        print("\n=== arm given (no-curr) ===", flush=True)
        m, wall = train_arm(docs, tok, "given", a, dev, curr=False)
        st, sh, rows = paper(m, tok, dev, "given")
        report["arms"]["given_nocurr"] = {"strict": st, "shelf": sh, "n": len(PROBES), "wall_s": wall, "rows": rows}
        print(f"  G3-Paper[given_nocurr] 字面 {st}/{len(PROBES)} 落架 {sh}/{len(PROBES)} wall {wall:.0f}s", flush=True)
    out = os.path.join(HERE, "report_g3_mid.json")
    json.dump(report, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"\n[out] {out}", flush=True)
    print("G3MID-DONE", flush=True)


if __name__ == "__main__":
    main()
