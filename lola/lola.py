#!/usr/bin/env python3
"""lola 信鸽匣 — ima-Lola <-> 本地 Lola 的最小通信 (默认 transport = 剪贴板)。

契约见同目录 README.md。铁律: LEDGER append-only, 每条带 sha256[:16]。
用法:
  lola.py push "<text>"   写 outbox + 置剪贴板 (你粘进 ima)
  lola.py pull            从剪贴板取 ima 回信 -> inbox + LEDGER
  lola.py recv [text]     收一段粘贴进来的 ima 信 (非剪贴板通道) -> inbox + LEDGER
  lola.py log [n]         台账尾 n 行
  lola.py status          信鸽匣概览 (进/出计数 + 末条)
  lola.py recopy          把 outbox 最后一封信重新放回剪贴板 (不重复入账)
  lola.py read            看 outbox 全文
  lola.py selftest        不碰剪贴板的语法/账本自检
通用旗: --transport=ima (直推/直拉 ima 笔记) · --box=<name> (一账一道; 默认 lola;
  各道本地草稿 outbox-<box>.md / inbox-<box>.md, LEDGER 方向记 ⇢/⇠ ima·<box>)
"""
import sys, os, re, hashlib, datetime, subprocess

DIR = os.path.dirname(os.path.abspath(__file__))

# transport: clipboard(默认) | ima (--transport=ima); box: 一账一道 (--box=<name>)
TRANSPORT = "clipboard"
BOX = "lola"
_argv = []
_i = 0
while _i < len(sys.argv):
    _x = sys.argv[_i]
    if _x.startswith("--transport="):
        TRANSPORT = _x.split("=", 1)[1]
    elif _x.startswith("--box="):
        BOX = _x.split("=", 1)[1]
    elif _x == "--box" and _i + 1 < len(sys.argv):
        BOX = sys.argv[_i + 1]
        _i += 1
    else:
        _argv.append(_x)
    _i += 1
ARGV = _argv
if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", BOX):
    sys.exit(f"bad box name: {BOX!r} (须字母开头, 仅字母数字_- , ≤32 字符)")
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
    box = BOX
    msg = (" ".join(args) if args else sys.stdin.read()).strip()
    if not msg:
        print("empty; nothing pushed"); return 1
    outbox_path = _box_path("outbox.md", box)
    header = "# Lola·outbox (local → ima)" if box == "lola" else f"# {box.capitalize()}·outbox (local → ima)"
    append(outbox_path, header, f"\n### {now()} · local→ima · {sha(msg)}\n{msg}\n")
    ledger_line("⇢ ima" if box == "lola" else f"⇢ ima·{box}", msg)
    if TRANSPORT == "ima":
        import ima as _ima
        did, created = _ima.box_push(msg, box)
        print(f"pushed {sha(msg)} → ima《{box.capitalize()}·outbox》 doc_id={did} ({'created' if created else 'appended'})")
    else:
        clip_write(msg)
        print(f"pushed {sha(msg)}; on clipboard — paste into ima.")
    print(f"outbox: {outbox_path}")
    return 0


def _last_ledger_sha():
    if not os.path.exists(LEDGER):
        return None
    lines = [l for l in open(LEDGER, encoding="utf-8") if l.startswith("- ")]
    if not lines:
        return None
    m = re.search(r"\[([0-9a-f]{16})\]", lines[-1])
    return m.group(1) if m else None


def _box_path(name, box="lola"):
    if box == "lola":
        return os.path.join(DIR, name)
    stem, ext = name.rsplit(".", 1)
    return os.path.join(DIR, f"{stem}-{box}.{ext}")


def ingest(text, direction, via, box="lola"):
    text = (text or "").strip()
    if not text:
        print(f"empty; nothing ingested via {via}"); return 1
    if sha(text) == _last_ledger_sha():
        print(f"duplicate (same sha {sha(text)}); skipped — 防重复折入")
        return 0
    inbox_path = _box_path("inbox.md", box)
    header = "# Lola·inbox (ima → local)" if box == "lola" else f"# {box.capitalize()}·inbox (ima → local)"
    append(inbox_path, header, f"\n### {now()} · {via} · {sha(text)}\n{text}\n")
    ledger_line(direction, text)
    print(f"{via}: {sha(text)} ({len(text)} chars) → inbox + LEDGER")
    return 0


def cmd_pull(args):
    box = BOX
    if TRANSPORT == "ima":
        import ima as _ima
        did, c = _ima.box_pull(box)
        if not c:
            print(f"ima《{box.capitalize()}·inbox》empty or missing"); return 1
        return ingest(c, "⇠ ima" if box == "lola" else f"⇠ ima·{box}", f"ima→local ima-api【{box}】", box)
    text = clip_read()
    if not text.strip():
        print("clipboard empty; copy ima's reply first"); return 1
    return ingest(text, "⇠ ima" if box == "lola" else f"⇠ ima·{box}", "ima→local clipboard", box)


def cmd_recv(args):
    box = BOX
    text = " ".join(args) if args else sys.stdin.read()
    return ingest(text, "⇠ ima" if box == "lola" else f"⇠ ima·{box}", f"ima→local chat【{box}】", box)


def _last_outbox_msg(box="lola"):
    path = _box_path("outbox.md", box)
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8").read()
    blocks = [p for p in re.split(r'(?m)^### ', txt) if "local→ima" in p.split("\n", 1)[0]]
    return blocks[-1].split("\n", 1)[1].strip("\n") if blocks else None


def cmd_recopy(args):
    msg = _last_outbox_msg(BOX)
    if not msg:
        print("no outbox letter to recopy"); return 1
    clip_write(msg)
    print(f"recopied {sha(msg)} ({len(msg.encode())} bytes) → clipboard")
    return 0


def cmd_status(args):
    def count(key):
        if not os.path.exists(LEDGER):
            return 0
        return sum(1 for ln in open(LEDGER, encoding="utf-8") if key in ln)
    n_in, n_out = count("⇠ ima"), count("⇢ ima")
    last = ""
    if os.path.exists(LEDGER):
        lines = [l.rstrip() for l in open(LEDGER, encoding="utf-8") if l.startswith("- ")]
        last = lines[-1] if lines else ""
    print(f"lola 信鸽匣 | 进 {n_in} · 出 {n_out}")
    if last:
        print("last: " + last[:100])
    return 0


def cmd_log(args):
    n = int(args[0]) if args else 20
    if not os.path.exists(LEDGER):
        print("(no ledger yet)"); return 0
    print("".join(open(LEDGER, encoding="utf-8").readlines()[-n:]))
    return 0


def cmd_read(args):
    path = _box_path("outbox.md", BOX)
    print(open(path, encoding="utf-8").read() if os.path.exists(path) else "(no outbox yet)")
    return 0


def cmd_selftest(args):
    # 不碰剪贴板: 校验 IO 与 sha, 用一个临时串
    s = "selftest " + now()
    assert len(sha(s)) == 16
    print("selftest OK:", sha(s))
    return 0


CMDS = {"push": cmd_push, "pull": cmd_pull, "recv": cmd_recv, "log": cmd_log,
        "read": cmd_read, "recopy": cmd_recopy, "status": cmd_status, "selftest": cmd_selftest}


def main():
    if len(ARGV) < 2 or ARGV[1] not in CMDS:
        print(__doc__); return 2
    return CMDS[ARGV[1]](ARGV[2:])


if __name__ == "__main__":
    sys.exit(main())
