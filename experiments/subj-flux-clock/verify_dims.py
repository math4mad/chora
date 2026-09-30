#!/usr/bin/env python3
"""感知维数-流速律 · 验证: 可感维数 D 越多 → 事件密度越高 → r 越高。
状态 = D 维比特; 每 tick 每维以 p 翻转; 事件 = 任一维变。
输出: out/subj-flux-dims.png
"""
import os, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

GOLD, DIM, INK, GREEN, RED = "#b8860b", "#8d8a80", "#1a1a1a", "#4f6f4a", "#b46a5a"


def measure(D, p=0.03, T=40000, seed=0):
    rng = random.Random(seed)
    st = [0] * D
    events = 0
    for _ in range(T):
        ch = False
        for i in range(D):
            if rng.random() < p:
                st[i] ^= 1; ch = True
        if ch:
            events += 1
    return events / T


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    Ds = [1, 2, 4, 8, 16]
    dens = [measure(D) for D in Ds]
    ref = dens[0]
    rs = [min(2.0, d / ref) for d in dens]

    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=200)
    ax.bar([str(D) for D in Ds], dens, color=GOLD, alpha=0.85, width=0.55, label="实测事件密度 $\\dot N$")
    ax.plot([str(D) for D in Ds], [D * 0.03 for D in Ds], color=RED, lw=1.5, ls="--", marker="o",
            ms=4, label="理想 ∝ $D$  (稍不如一元)")
    ax.set_xlabel("可感维数 D（能区分的差分类型数）")
    ax.set_ylabel("事件密度 $\\dot N$")
    ax.set_title("感知维数-流速律 · 可感维数越多 → 事件密度越高 → 主观流速越快", color=INK)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.15, axis="y"); fig.tight_layout()
    fig.savefig(os.path.join(out, "subj-flux-dims.png"), facecolor="white")
    for D, d, r in zip(Ds, dens, rs):
        print(f"D={D:2d}  事件密度={d:.4f}  r={r:.2f}")
    print("✔", os.path.join(out, "subj-flux-dims.png"))


if __name__ == "__main__":
    main()
