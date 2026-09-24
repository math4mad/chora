"""G3·三年级模型 — 舱偏置注意力 (给定注意力) 核心件。
口谕(0924): "不要模型自己去注意, 我们给他注意力。"
实现: 标准 QKV softmax 保留; attn_logits += B[舱i,舱j] (设计者视野), 叠加因果掩码。
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


def make_bias(cab, adj, neg=-1e9):
    """cab: (T,) 舱号; adj: 已解锁邻舱对集合(无序)。返回 (T,T) 加性偏置。
    同舱=0, 已解锁邻舱=-2, 其余=-inf(neg)。"""
    same = cab[:, None] == cab[None, :]
    adjm = torch.zeros_like(same)
    for (i, j) in adj:
        adjm |= ((cab[:, None] == i) & (cab[None, :] == j)) | \
                 ((cab[:, None] == j) & (cab[None, :] == i))
    b = torch.full((cab.numel(), cab.numel()), neg, device=cab.device)
    b = torch.where(adjm, torch.full_like(b, -2.0), b)
    return torch.where(same, torch.zeros_like(b), b)


class CabinBlock(nn.Module):
    def __init__(self, d, h):
        super().__init__()
        self.h, self.d = h, d
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.proj = nn.Linear(d, d)
        self.n1, self.n2 = nn.RMSNorm(d), nn.RMSNorm(d)
        ff = int(8 / 3 * d) // 64 * 64
        self.gate = nn.Linear(d, ff)
        self.up = nn.Linear(d, ff)
        self.down = nn.Linear(ff, d)

    def attn(self, x, bias, cos, sin):
        B, T, d = x.shape
        q, k, v = self.qkv(x).split(d, dim=2)
        q, k, v = (t.view(B, T, self.h, d // self.h).transpose(1, 2) for t in (q, k, v))
        def rope(t):
            return t * cos + torch.cat((-t[..., t.size(-1) // 2:], t[..., :t.size(-1) // 2]), -1) * sin
        q, k = rope(q), rope(k)
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=bias)
        return self.proj(y.transpose(1, 2).reshape(B, T, d))

    def forward(self, x, bias, cos, sin):
        x = x + self.attn(self.n1(x), bias, cos, sin)
        h = self.n2(x)
        return x + self.down(F.silu(self.gate(h)) * self.up(h))


class G3Model(nn.Module):
    def __init__(self, vocab, d=192, layers=4, h=6, ctx=256):
        super().__init__()
        self.ctx = ctx
        self.emb = nn.Embedding(vocab, d)
        nn.init.normal_(self.emb.weight, std=0.02)
        self.blocks = nn.ModuleList([CabinBlock(d, h) for _ in range(layers)])
        self.head = nn.Linear(d, vocab, bias=False)
        self.head.weight = self.emb.weight  # tied
        dh = d // h
        p = torch.arange(ctx)
        f = 1.0 / (10000 ** (torch.arange(0, dh // 2).float() * 2 / dh))
        fr = torch.cat([p[:, None] * f[None, :]] * 2, dim=-1)  # (ctx, dh) rotate_half 配套
        self.register_buffer("cos", torch.cos(fr)[None, None])
        self.register_buffer("sin", torch.sin(fr)[None, None])

    def forward(self, idx, cab, bias):
        x = self.emb(idx)
        T = idx.size(1)
        for blk in self.blocks:
            x = blk(x, bias, self.cos[:, :, :T], self.sin[:, :, :T])
        return self.head(x)
