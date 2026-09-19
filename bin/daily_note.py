#!/usr/bin/env python3
# daily_note.py — 夜巡第三屏: digest 落 Apple Notes「园区」夹 (iCloud → iPhone)
# 用法: daily_note.py <digest-file> <YYYY-MM-DD>
# 字符串政策 (两役教训): AppleScript 双引号定界内 → 反斜杠翻倍; 直双引号摘除;
# 弯引号归正为直引号再摘; 其余 Unicode 原样放行 (osascript -e UTF-8 无恙)。
import sys, subprocess

def sanitize(line: str) -> str:
    return (line.replace("\\", "\\\\")
                .replace("\u201c", "\u201d").replace("\u201d", "\u201d")
                .replace('"', "").replace("\u201c", "").replace("\u201d", ""))

def main():
    dig_path, d = sys.argv[1], sys.argv[2]
    body = open(dig_path, encoding="utf-8").read()
    lines = [sanitize(ln) for ln in body.splitlines() if ln.strip()]
    joined = " & return & ".join(f'"{ln}"' for ln in lines) or '"(空)"'
    script = f'''tell application "Notes"
  tell account "iCloud"
    if not (exists folder "园区") then make new folder with properties {{name:"园区"}}
    tell folder "园区"
      set oldList to (every note whose name is "园区日报 {d}")
      repeat with n in oldList
        delete n
      end repeat
      make new note with properties {{name:"园区日报 {d}", body:{joined}}}
    end tell
  end tell
end tell'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    ok = r.returncode == 0
    print(("notes: 帖已落 " if ok else "notes 失败: ") + (r.stdout + r.stderr).strip()[:120])
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
