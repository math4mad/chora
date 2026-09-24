"""G3-Paper v0 · 落架判分: 概念空间进, 概念空间出。
每题: prompt + 候选(词,舱) + 金标词 + 金标舱。
判两档: 字面中(词=金标词) 与 落架中(候选词所属舱=金标舱)。"""
import argparse, os
import torch
from g3_model import G3Model
import g3_data as D
from g3_train import arm_bias, causal_mask

HERE = os.path.dirname(os.path.abspath(__file__))

# (prompt, [(词,舱)...], 金标词, 轴)
PROBES = [
    ("除夕夜，全家围坐吃年夜饭，饭后开始", [("守岁", 0), ("烧烤", 1), ("选秀", 2), ("彩虹", 3)], "守岁", "空间判别"),
    ("夏天晚上，院子里摆开小桌，喝冰啤酒吃", [("饺子", 0), ("烧烤", 1), ("红包", 0), ("燕巢", 3)], "烧烤", "空间判别"),
    ("我们给长辈发", [("红包", 0), ("球票", 2), ("烤串", 1), ("字典", 3)], "红包", "锚点"),
    ("2003年选秀第1顺位是", [("蒂姆·邓肯", 2), ("勒布朗·詹姆斯", 2), ("迈克·毕比", 2), ("昌西·比卢普斯", 2)], "勒布朗·詹姆斯", "序敏"),
    ("2003年选秀第3顺位是", [("卡梅隆·安东尼", 2), ("德维恩·韦德", 2), ("克里斯·波什", 2), ("蒂姆·邓肯", 2)], "克里斯·波什", "序敏"),
    ("1997年选秀第1顺位是", [("蒂姆·邓肯", 2), ("迈克·奥洛沃坎迪", 2), ("勒布朗·詹姆斯", 2), ("昌西·比卢普斯", 2)], "蒂姆·邓肯", "序敏"),
    ("鲸不是鱼，它是", [("哺乳动物", 3), ("爬行动物", 3), ("鱼类", 3), ("鸟类", 3)], "哺乳动物", "三年级验收"),
    ("零乘任何数都", [("得零", 3), ("得原数", 3), ("得一", 3), ("无意义", 3)], "得零", "三年级验收"),
    ("春天来了，从南方飞回来的是", [("燕子", 3), ("蝙蝠", 3), ("喜鹊", 3), ("蜻蜓", 3)], "燕子", "三年级验收"),
]


def make_scorer(model, tok, dev, arm):
    def logprob(text):
        ids = tok.encode(text)
        x = torch.tensor([ids], device=dev)
        cab = torch.tensor([[0] * len(ids)], device=dev)
        bias = arm_bias(arm, cab[0], set()) + causal_mask(len(ids), dev)
        with torch.no_grad():
            lg = model(x, cab, bias[None, None])[:, :-1].log_softmax(-1)
        t = torch.tensor(ids[1:], device=dev)
        return lg.gather(-1, t.view(1, -1, 1)).sum().item()
    return logprob


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--arm", default="given")
    p.add_argument("--ckpt", default=None)
    a = p.parse_args()
    docs = D.load_docs(); tok = D.Tok(docs)
    ck = torch.load(a.ckpt or os.path.join(HERE, f"out/g3_{a.arm}.pt"), map_location="cpu")
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    m = G3Model(tok.vocab, d=ck["args"]["d"], layers=ck["args"]["layers"],
                h=ck["args"]["heads"], ctx=ck["args"]["ctx"]).to(dev)
    m.load_state_dict(ck["model"]); m.eval()
    lp = make_scorer(m, tok, dev, a.arm)
    strict = shelf = 0; axes = {}
    for prompt, cands, gold, axis in PROBES:
        base = lp(prompt)
        w, wc = max(cands, key=lambda c: lp(prompt + c[0]) - base)
        gc = next(c for g, c in [(x[0], x[1]) for x in cands] if g == gold)
        s, h = w == gold, wc == gc
        strict += s; shelf += h
        axes.setdefault(axis, [0, 0]); axes[axis][0] += s; axes[axis][1] += h
        print(f"[{axis}] {prompt}… → {w}(舱{wc}) 金标 {gold}(舱{gc}) 字面{'✓' if s else '✗'} 落架{'✓' if h else '✗'}")
    n = len(PROBES)
    print(f"\nG3-Paper: 字面 {strict}/{n}={strict/n:.0%} · 落架 {shelf}/{n}={shelf/n:.0%} · 分轴(字面/落架) {axes}")


if __name__ == "__main__":
    main()
