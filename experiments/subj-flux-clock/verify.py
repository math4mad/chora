#!/usr/bin/env python3
"""主观流逝率律 the subj-flux law · 事件驱动验证。
物理钟照走; 主观流逝 = ∫ r(t) dt, r = ω(事件), 事件=可感知状态变化。
睡眠(无事件)→r≈0→主观时间停走; 清醒(有事件)→r=1→恢复; 起床对表=相位重锚。
输出: out/subj-flux.png (+ 相位差打印)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Songti SC", "PingFang SC", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

GOLD, DIM, INK = "#b8860b", "#8d8a80", "#1a1a1a"


class SubjectiveClock:
    def __init__(self, r_active=1.0, r_sleep=0.0):
        self.r_active, self.r_sleep = r_active, r_sleep
        self.t_subj = 0.0
        self.t_phys = 0.0
        self.s_prev = None
        self.hist = []            # (t_phys, t_subj, r)

    def tick(self, dt, s_new):
        event = 1.0 if (self.s_prev is not None and s_new != self.s_prev) else 0.0
        r = event * self.r_active + (1 - event) * self.r_sleep
        self.t_subj += r * dt
        self.t_phys += dt
        self.s_prev = s_new
        self.hist.append((self.t_phys, self.t_subj, r))
        return self.t_subj

    def resync(self):
        """对表: 把主观钟重锚到外部钟相位 (数值积分的重设初值)。"""
        self.t_subj = self.t_phys
        return self.t_subj


def run(sleep=2 * 3600, active=1 * 3600, resync=True):
    c = SubjectiveClock()
    for _ in range(sleep):                       # 睡: 状态恒 'zzz' → 无事件
        c.tick(1.0, "zzz")
    gap_before = c.t_phys - c.t_subj             # 睡眠累积相位差 Δ
    if resync:
        c.resync()
    for i in range(active):                      # 醒: 事件频繁
        c.tick(1.0, f"act-{i % 17}")
    gap_after = c.t_phys - c.t_subj
    return c, gap_before, gap_after


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)

    c, gap_before, gap_after = run(resync=True)
    c2, gap2, _ = run(resync=False)
    print(f"睡眠 {2}h 后相位差 Δ = {gap_before:.0f} s (={gap_before/3600:.1f} h)")
    print(f"  对表后 Δ = {gap_after:.0f} s  | 不对表 Δ 继承 = {gap2:.0f} s (={gap2/3600:.1f} h)")

    xs = [h[0] / 3600 for h in c.hist]
    ys = [h[1] / 3600 for h in c.hist]
    xs2 = [h[0] / 3600 for h in c2.hist]
    ys2 = [h[1] / 3600 for h in c2.hist]

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=200)
    ax.plot(xs, ys, color=GOLD, lw=2.6, label="主观时间 $t_{subj}$ (对表)")
    ax.plot(xs2, ys2, color=GOLD, lw=1.4, ls=":", label="主观时间 (不对表·相位漂移)")
    ax.plot([0, xs[-1]], [0, xs[-1]], color=DIM, lw=1.2, ls="--", label="物理时间 $t_{phys}$ (r=1·钟)")
    ax.axvspan(0, 2, color="#888", alpha=0.07)
    ax.text(1.0, 0.35, "睡眠（无事件 → r≈0）\n主观时间停走", ha="center", va="bottom", color=DIM, fontsize=11)
    ax.annotate("", xy=(2, 2), xytext=(2, 0), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.3))
    ax.text(2.08, 1.0, f"相位差 Δ≈{gap_before/3600:.0f}h\n（对表即抹平）", color=INK, fontsize=10)
    ax.text(2.6, 2.6, "清醒（事件频繁 → r=1）\n主观时间恢复走动", color=DIM, fontsize=11)
    ax.set_xlabel("物理时间 t (h)"); ax.set_ylabel("主观时间 $t_{subj}$ (h)")
    ax.set_title("主观流逝率律 · 事件驱动：睡眠停走、醒则涨、对表复位", color=INK)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "subj-flux.png"), facecolor="white")
    print("✔", os.path.join(out, "subj-flux.png"))


if __name__ == "__main__":
    main()
