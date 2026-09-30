#!/usr/bin/env python3
"""sync-2-ima: 园 → ima 笔记同步 (经 ima OpenAPI)。
用法:
  sync_ima.py file <path> [--append]   推一 markdown 文件为 ima 笔记 (--append 则并入同名笔记)
  sync_ima.py text "<标题>" <md_file>   以指定标题新建
  sync_ima.py digest                    推「园·digest」= 信鸽匣 digest.md + 台账尾
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ima  # noqa


def _title_of(path, content):
    for ln in content.splitlines():
        if ln.startswith("# "):
            return ln[2:].strip()
    return os.path.basename(path)


def sync_file(path, append=False):
    content = open(path, encoding="utf-8").read()
    title = _title_of(path, content)
    did = ima.find(title)
    if append and did:
        ima.append(did, "\n\n---\n\n" + content)
        return f"appended 《{title}》 doc_id={did}"
    if did:
        # 同名已存：建带日期后缀的新篇，避免覆写
        title = f"{title} · {__import__('datetime').date.today()}"
    did = ima.make(title, content)
    return f"created 《{title}》 doc_id={did}"


def sync_text(title, path):
    content = open(path, encoding="utf-8").read()
    did = ima.make(title, content)
    return f"created 《{title}》 doc_id={did}"


def sync_digest():
    parts = []
    dg = os.path.join(HERE, "digest.md")
    if os.path.exists(dg):
        parts.append(open(dg, encoding="utf-8").read())
    lg = os.path.join(HERE, "LEDGER.md")
    if os.path.exists(lg):
        tail = open(lg, encoding="utf-8").read().splitlines()[-8:]
        parts.append("## 信鸽匣台账（尾）\n\n" + "\n".join(tail))
    content = "\n\n".join(parts) or "# 园·digest\n(空)"
    did = ima.find("园·digest")
    if did:
        ima.append(did, "\n\n---\n\n" + content)
        return f"appended 《园·digest》 doc_id={did}"
    did = ima.make("园·digest", content)
    return f"created 《园·digest》 doc_id={did}"


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "file":
        print(sync_file(a[1], append=("--append" in a)))
    elif a[0] == "text":
        print(sync_text(a[1], a[2]))
    elif a[0] == "digest":
        print(sync_digest())
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
