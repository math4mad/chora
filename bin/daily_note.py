#!/usr/bin/env python3
# daily_note.py — 夜巡第三屏: 把日报 digest 落进 Apple Notes「园区」夹 (iCloud → iPhone)
# 用法: daily_note.py <digest-file> <YYYY-MM-DD>
import sys, subprocess

dig_path, d = sys.argv[1], sys.argv[2]
body = open(dig_path, encoding="utf-8").read()
# AppleScript 字符串卫生: 转义反斜杠/引号, 掐换行 (Notes body 用 & return & 拼接更稳, 这里按行组装)
lines = [ln.replace("\\", "\\\\").replace('"', '\\"') for ln in body.splitlines()]
as_lines = ' & return & '.join(f'"{ln}"' for ln in lines if ln.strip()) or '"(空)"'
script = f'''tell application "Notes"
  tell account "iCloud"
    if not (exists folder "园区") then make new folder with properties {{name:"园区"}}
    tell folder "园区"
      repeat with n in (every note whose name is "园区日报 {d}") to delete n
      make new note with properties {{name:"园区日报 {d}", body:"{as_lines}"}}
    end tell
  end tell
end tell'''
r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print("notes:", (r.stdout or r.stderr).strip()[:100])
sys.exit(0 if r.returncode == 0 else 1)
