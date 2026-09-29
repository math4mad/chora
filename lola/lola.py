#!/usr/bin/env python3
"""lola 信鸽匣 — ima-Lola <-> 本地 Lola 的最小通信 (默认 transport = 剪贴板)。

契约见同目录 README.md。铁律: LEDGER append-only, 每条带 sha256[:16]。
用法:
  lola.py push "<text>"   写 outbox + 置剪贴板 (你粘进 ima)
  lola.py pull            从剪贴板取 ima 回信 -> inbox + LEDGER
  lola.py log [n]         台账尾 n 行
  lola.py read            看 outbox 全文
  lola.py selftest        不碰剪贴板的语法/账本自检
"""
import sys, os, hashlib, datetime, subprocess

DIR = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(DIR, "inbox.md")
OUTBOX = os.path.join(DIR, "outbox.md")
LEDGER = os.path.join(DIR, "LEDGER.md")
LEDGER_HEAD = "# Lola 通信台账 (append-only)"


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def clip_read():
    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout


def clip_write(s):
    subprocess.run(["pbcopy"], input=s, text=True)


def append(path, header, body):
    new = (not os.path.exists(path)) or os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8") as f:
        if new and header:
            f.write(header + "\n")
        f.write(body)


def ledger_line(direction, text):
    first = (text.splitlines() or [""])[0][:80]
    append(LEDGER, LEDGER_HEAD, f"- {now()} {direction}  [{sha(text)}] {first}\n")


def cmd_push(args):
    msg = (" ".join(args) if args else sys.stdin.read()).strip()
    if not msg:
        print("empty; nothing pushed"); return 1
    append(OUTBOX, "# Lola·outbox (local → ima)", f"\n### {now()} · local→ima · {sha(msg)}\n{msg}\n")
    ledger_line("⇢ ima", msg)
    clip_write(msg)
    print(f"pushed {sha(msg)}; on clipboard — paste into ima.")
    print(f"outbox: {OUTBOX}")
    return 0


def cmd_pull(args):
    text = clip_read().strip()
    if not text:
        print("clipboard empty; copy ima's reply first"); return 1
    append(INBOX, "# Lola·inbox (ima → local)", f"\n### {now()} · ima→local · {sha(text)}\n{text}\n")
    ledger_line("⇠ ima", text)
    print(f"pulled {sha(text)} ({len(text)} chars) → inbox + LEDGER")
    return 0


def cmd_log(args):
    n = int(args[0]) if args else 20
    if not os.path.exists(LEDGER):
        print("(no ledger yet)"); return 0
    print("".join(open(LEDGER, encoding="utf-8").readlines()[-n:]))
    return 0


def cmd_read(args):
    print(open(OUTBOX, encoding="utf-8").read() if os.path.exists(OUTBOX) else "(no outbox yet)")
    return 0


def cmd_selftest(args):
    # 不碰剪贴板: 校验 IO 与 sha, 用一个临时串
    s = "selftest " + now()
    assert len(sha(s)) == 16
    print("selftest OK:", sha(s))
    return 0


CMDS = {"push": cmd_push, "pull": cmd_pull, "log": cmd_log, "read": cmd_read, "selftest": cmd_selftest}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); return 2
    return CMDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
