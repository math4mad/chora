#!/usr/bin/env python3
# daily_note.py — 夜巡第三屏: Concept-Space 日报帖 (Apple Notes → iCloud → iPhone)
# 版式: 展示机风 —— 大标题 / ━ 分隔 / emoji 图标行 / 短行留白 (owner 目录之点缀法)
# 用法: daily_note.py <digest-file> <YYYY-MM-DD>
# 字符串政策 (两役教训): 反斜杠翻倍; 直双引号摘除 (弯引保留为文气, AppleScript 定界安全)
import sys, subprocess, re

FOLDER = "Concept-Space"

def sanitize(line: str) -> str:
    return line.replace("\\", "\\\\").replace('"', "")

def reflow(digest: str, d: str):
    """把 CMS 版 markdown digest 重排成展示机 notes 版。"""
    out_actions = []; out_approve = ["✅ 批复与回执", ""]; out_front = ["⚔️ 战线", ""]
    sec = None; snap = ""
    keep = {"chora": [], "LETHE": [], "GRAPHIA": []}; noise = {"chora": 0, "LETHE": 0, "GRAPHIA": 0}
    cur = "chora"
    for ln in (l.rstrip() for l in digest.splitlines()):
        t = ln.strip()
        if not t or t.startswith("# 园区日报"): continue
        if t.startswith("## 今日 commits"): sec = "commits"; continue
        if t.startswith("## 今日批复"): sec = "approvals"; continue
        if t.startswith("## Kaggle") or t.startswith("## 战线"): sec = "front"; continue
        if t.startswith("_dispatched") or t.startswith("## 刷新"): continue
        if sec == "commits":
            m = re.match(r"### (chora|Concept-Space-Sphere|GRAPHIA)", t)
            if m:
                cur = {"Concept-Space-Sphere": "LETHE", "chora": "chora", "GRAPHIA": "GRAPHIA"}[m.group(1)]
                continue
            m = re.match(r"- `(\w+)` (.+)", t)
            if m:
                sha, msg = m.groups()
                if msg.startswith("mail:") or msg.startswith("status snapshot") or "daily digest" in msg:
                    noise[cur] += 1; continue
                if len(keep[cur]) < 6: keep[cur].append(f"   · `{sha}` {msg[:64]}{'…' if len(msg) > 64 else ''}")
                else: noise[cur] += 1
                continue
            m = re.match(r"- \(\+(\d+) 条自动快照，略\)", t)
            if m: snap = f"   (另有 {m.group(1)} 枚自动快照, 略)"; continue
        elif sec == "approvals":
            t = t.replace("☑MS", "🟦 MS·").replace("•", "").strip()
            if t: out_approve.append(f"   {t[:80]}")
        elif sec == "front":
            t = re.sub(r"^[\d:]+\s*", "", t).strip()
            if t and not t.startswith("pushed"): out_front.append(f"   · {t[:76]}")
    out = [f"🗺 Concept-Space · 日报 {d}", "━━━━━━━━━━━━━━", "🚀 今日动作", ""]
    titles = {"chora": "◆ chora · 主园", "LETHE": "◆ LETHE · 概念空间球", "GRAPHIA": "◆ GRAPHIA · 案头V"}
    for repo in ("chora", "LETHE", "GRAPHIA"):
        if keep[repo] or noise[repo]:
            out.append(titles[repo])
            out += keep[repo]
            if noise[repo]: out.append(f"   …另 {noise[repo]} 枚（信件/快照/例行, 略）")
            out.append("")
    out += [x for x in out_approve]
    seen = set(); dedup_front = []
    for x in out_front[1:]:
        if x not in seen: dedup_front.append(x); seen.add(x)
    out += ["", "⚔️ 战线"] + dedup_front[-6:]
    out += ["", "━━━━━━━━━━━━━━", "📮 详版: CMS 邮 theoros@chora.dev · 图档 math4mad.github.io/GRAPHIA", "⚓ 一稿三面: 提醒=批复 · 邮件=读物 · 此帖=回看"]
    return out

def main():
    dig_path, d = sys.argv[1], sys.argv[2]
    body = open(dig_path, encoding="utf-8").read()
    lines = [sanitize(ln) for ln in reflow(body, d)]
    joined = " & return & ".join(f'"{ln}"' for ln in lines) or '"(空)"'
    script = f'''tell application "Notes"
  tell account "iCloud"
    if not (exists folder "{FOLDER}") then
      if exists folder "园区" then
        set name of folder "园区" to "{FOLDER}"
      else
        make new folder with properties {{name:"{FOLDER}"}}
      end if
    end if
    tell folder "{FOLDER}"
      set oldList to (every note whose name is "Concept-Space 日报 {d}")
      repeat with n in oldList
        delete n
      end repeat
      make new note with properties {{name:"Concept-Space 日报 {d}", body:{joined}}}
    end tell
  end tell
end tell'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    ok = r.returncode == 0
    print(("notes: 帖已落 " if ok else "notes 失败: ") + (r.stdout + r.stderr).strip()[:120])
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
