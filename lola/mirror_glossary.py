#!/usr/bin/env python3
"""mirror_glossary.py — 术语碑 → ima 笔记镜像（**保持最新**）。

幂等: 碑内容（渲染后四栏表）sha 未变 → 跳过; 变了 → 建新版本笔记
《术语碑 · Glossary of the Garden（vN）》并去信对岸。

版本号以**本地状态**（.glossary-mirror.state: 行1=vN, 行2=sha）为准，不依赖 ima 搜索。
用法: python3 mirror_glossary.py [--force]
挂点: cora-atlas/scripts/build-site.sh 末尾（best-effort, 失败不阻断建站）。
"""
import hashlib, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ima  # noqa

CORALI = os.path.expanduser("~/Programming/code-2026/cora-atlas")
SRC = os.path.join(CORALI, "site", "GLOSSARY.qmd")   # 渲染后（四栏 markdown 表）
STATE = os.path.join(HERE, ".glossary-mirror.state")
BASE_TITLE = "术语碑 · Glossary of the Garden"


def body():
    g = open(SRC, encoding="utf-8").read().splitlines()
    if g and g[0].startswith("# "):
        g = g[1:]
    return "\n".join(g).strip("\n")


def read_state():
    v, sha = 1, ""
    if os.path.exists(STATE):
        lines = [l.strip() for l in open(STATE) if l.strip()]
        for l in lines:
            if l.startswith("v"):
                try:
                    v = int(l[1:])
                except ValueError:
                    pass
            elif not sha:
                sha = l
    return v, sha


def write_state(v, sha):
    with open(STATE, "w", encoding="utf-8") as f:
        f.write(f"v{v}\n{sha}\n")


def main():
    force = "--force" in sys.argv
    b = body()
    h = hashlib.sha256(b.encode("utf-8")).hexdigest()[:16]
    v, last = read_state()
    if h == last and not force:
        print(f"[glossary-mirror] unchanged (v{v}, sha={h}); skip")
        return 0
    nv = v + 1
    title = f"{BASE_TITLE}（v{nv}）"
    note = (f"# {title}\n\n> v{nv} · {datetime.date.today()} · 凡例「术语｜EN｜一义｜**非此**｜账目」→ 渲染**四栏**（术语｜义｜非此／不包含｜账）。\n"
            f"> **碑不可判**：术语碑是地图，不是法律。\n> 旧版作废；**以最高 vN 为最新**。\n\n{b}\n")
    did = ima.make(title, note)
    write_state(nv, h)
    print(f"[glossary-mirror] created 《{title}》 doc_id={did} sha={h}")
    try:
        subprocess.run(["python3", os.path.join(HERE, "lola.py"), "--transport=ima", "push",
                        f"术语碑镜像已更新：**{title}** doc_id={did} sha={h}。碑变即镜像变；请以**最高 vN** 为最新。"],
                       timeout=120, check=False)
    except Exception as e:
        print("[glossary-mirror] outbox note failed:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
