"""G3 单元自检: 视野接管是否真的接管了注意力。跑法: python test_g3.py"""
import torch
import torch.nn.functional as F
from g3_model import G3Model, make_bias
import g3_data as D


def test_bias_values():
    cab = torch.tensor([0, 0, 1, 2])
    b = make_bias(cab, {(0, 1)})
    assert b[0, 1] == 0 and b[2, 0] == -2, "同舱0/邻舱-2"
    assert b[0, 3] < -1e8 and b[3, 0] < -1e8, "远舱应不可见"
    print("✓ bias 值: 同舱0 邻舱-2 远舱-∞")


def test_attention_mass():
    """给定视野下, 跨舱注意力质量必须≈0。"""
    torch.manual_seed(0)
    cab = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    bias = make_bias(cab, set()) + torch.full((8, 8), -1e9).triu(1)  # 未解锁邻舱阶段: 跨舱一律-∞
    q, k = torch.randn(8, 16), torch.randn(8, 16)
    w = F.softmax(q @ k.T / 4 + bias, dim=-1)
    cross = w[cab[:, None] != cab[None, :]].sum()
    assert cross < 1e-6, f"跨舱质量 {cross}"
    print(f"✓ 跨舱注意力质量 = {cross:.2e} ≈ 0 —— 视野确被接管")
    bias2 = make_bias(cab, {(0, 1)}) + torch.full((8, 8), -1e9).triu(1)
    w2 = F.softmax(q @ k.T / 4 + bias2, dim=-1)
    hard = w2[(cab[:, None] != cab[None, :]) & ~((cab[:, None] <= 1) & (cab[None, :] <= 1))].sum()
    assert hard < 1e-6, f"硬隔质量 {hard}"
    soft = w2[(cab[:, None] == 0) & (cab[None, :] == 1)].sum()
    print(f"✓ 解锁后: 硬隔质量 {hard:.2e}≈0, 邻舱软视野质量 {soft:.3f}(可见但受抑)")


def test_forward_and_loss_drop():
    docs = D.load_docs(); tok = D.Tok(docs)
    m = G3Model(tok.vocab, d=96, layers=2, h=4, ctx=128)
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
    xs, cs, ys = D.pack(docs, tok, 128, 8, cabins_filter={0, 1})
    first = last = None
    for i in range(60):
        bias = torch.stack([make_bias(cs[b], set()) + torch.full((128, 128), -1e9).triu(1)
                            for b in range(cs.size(0))])[:, None]
        loss = F.cross_entropy(m(xs, cs, bias).view(-1, tok.vocab), ys.view(-1), ignore_index=D.PAD)
        opt.zero_grad(); loss.backward(); opt.step()
        if i == 0: first = loss.item()
        if i == 59: last = loss.item()
    assert last < first, f"loss 未降 {first}->{last}"
    print(f"✓ 60步 loss {first:.2f} → {last:.2f} (vocab {tok.vocab})")


if __name__ == "__main__":
    test_bias_values(); test_attention_mass(); test_forward_and_loss_drop()
    print("\n全部自检通过 —— 枪膛干净")
