#!/usr/bin/env python3
"""事件密度谱律 the event-density-spectrum law · 验证。
r 不是布尔开关, 而是事件密度 Ṅ 的函数: r(t)=ω(Ṅ(t)) (ω 单调, ω(0)=0).
三段: 睡(密度0)→r=0; 清醒(密度1)→r=1; 心流(密度4→capped 2)→r=2。
输出: out/subj-flux-density.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

GOLD, DIM, INK, RED, GREEN = "#b8860b", "#8d8a80", "#1a1a1a", "#b46a5a", "#4f6f4a"


class DensityClock:
    """事件密度驱动的时钟: r = ω(滑窗事件密度)。"""
    def __init__(self, ref=1.0, r_max=2.0, window=30.0):
        self.t_subj = 0.0; self.t_phys = 0.0
        self.ref, self.r_max, self.window = ref, r_max, window
        self.events = []
        self.hist = []   # (t_phys, t_subj, r, dens)

    def tick(self, dt, event):
        self.t_phys += dt
        if event:
            self.events.append(self.t_phys)
        t0 = self.t_phys - self.window
        n = sum(1 for e in self.events if e >= t0)
        dens = n / self.window
        r = min(self.r_max, dens / self.ref)      # ω: 线性截顶
        self.t_subj += r * dt
        self.hist.append((self.t_phys, self.t_subj, r, dens))


def segment(clk, dur, period, dt=0.25):
    """跑 dur 秒; period=事件周期秒 (None=无事件)。"""
    i = 0
    while clk.t_phys < dur0 + dur - 1e-9:
        ev = (period is not None) and (abs((clk.t_phys - (dur0)) % period) < dt / 2)
        clk.tick(dt, bool(ev)); i += 1


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    global dur0
    clk = DensityClock(ref=1.0, r_max=2.0, window=30.0)
    dt = 0.25
    # 睡 600s: 无事件
    dur0 = 0.0
    while clk.t_phys < 600: clk.tick(dt, False)
    # 清醒 600s: 事件周期 1s → 密度1 → r=1
    dur0 = 600.0
    while clk.t_phys < 1200:
        ev = abs((clk.t_phys - 600.0) % 1.0) < dt / 2
        clk.tick(dt, bool(ev))
    # 心流 600s: 事件周期 0.25s → 密度4 → r=capped 2
    dur0 = 1200.0
    while clk.t_phys < 1800:
        ev = abs((clk.t_phys - 1200.0) % 0.25) < dt / 2
        clk.tick(dt, bool(ev))

    xs = [h[0] / 60 for h in clk.hist]
    ys = [h[1] / 60 for h in clk.hist]
    fig, ax = plt.subplots(figsize=(9.6, 5.2), dpi=200)
    ax.plot(xs, ys, color=GOLD, lw=2.6, label="主观时间 $t_{subj}$ (密度驱动)")
    ax.plot([0, xs[-1]], [0, xs[-1]], color=DIM, lw=1.2, ls="--", label="物理时间 t (钟)")
    for x0, x1, lab, col in [(0, 600, "睡 · 密度0 → r=0\n（停走）", DIM), (600, 1200, "清醒 · 密度1 → r=1\n（常速）", INK), (1200, 1800, "心流 · 密度4 → r=2\n（飞逝）", RED)]:
        ax.axvspan(x0 / 60, x1 / 60, color=col, alpha=0.05)
        ax.text((x0 + x1) / 120, max(ys) * 0.30, lab, ha="center", color=col, fontsize=10.5)
    for x1, x2 in [(600, 1200), (1200, 1800)]:
        ax.plot([x1 / 60, x2 / 60], [y1of(clk, x1), y1of(clk, x2)], color=GOLD, lw=0.8, alpha=0.4)
    ax.set_xlabel("物理时间 t (min)"); ax.set_ylabel("主观时间 $t_{subj}$ (min)")
    ax.set_title("事件密度谱律 · 流速是事件密度的函数：睡停 / 醒常 / 心流飞", color=INK)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.15); fig.tight_layout()
    fig.savefig(os.path.join(out, "subj-flux-density.png"), facecolor="white")
    # 打印三段的 r 中位
    def rmed(a, b):
        rs = [h[2] for h in clk.hist if a <= h[0] <= b]
        return sorted(rs)[len(rs) // 2] if rs else 0
    print(f"r 中位: 睡={rmed(0,600):.2f}  清醒={rmed(600,1200):.2f}  心流={rmed(1200,1800):.2f}")
    print(f"主观总时 / 物理总时 = {clk.t_subj:.0f} / {clk.t_phys:.0f} s")
    print("✔", os.path.join(out, "subj-flux-density.png"))


def y1of(clk, t):
    ys = [h[1] for h in clk.hist if h[0] <= t]
    return ys[-1] / 60 if ys else 0.0


if __name__ == "__main__":
    main()
