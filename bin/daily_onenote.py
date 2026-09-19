#!/usr/bin/env python3
# daily_onenote.py — 夜巡第四屏: digest(md) → 装裱 HTML → Graph POST 落 OneNote「Concept-Space」分区
import sys, os, re, html, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import onenote_graph as OG

CSS = ("<style>body{font-family:-apple-system,'PingFang SC',sans-serif;color:#333;line-height:1.75}"
       "h1{color:#7a5c1e}h2{color:#b3762a;border-bottom:2px solid #e5d9c3;padding-bottom:2px}"
       "h3{color:#555;margin:8px 0 2px}b{color:#444;font-family:Menlo,monospace;font-size:.92em}"
       "li{margin-left:1.1em}</style>")

def md2html(md: str) -> str:
    out = []
    for ln in md.splitlines():
        e = html.escape(ln.strip())
        code = lambda t: re.sub(r"`([^`]+)`", r"<b>\1</b>", t)
        if ln.startswith("# "):   out.append(f"<h1>🗺 {e[2:]}</h1>")
        elif ln.startswith("## "): out.append(f"<h2>{e[3:]}</h2>")
        elif ln.startswith("### "): out.append(f"<h3>◆ {e[4:]}</h3>")
        elif ln.startswith("- "):  out.append(f"<li>{code(e[2:])}</li>")
        elif e:                    out.append(f"<p>{code(e)}</p>")
    return "<br>".join(out)

def main():
    dig, d = sys.argv[1], sys.argv[2]
    body = open(dig, encoding="utf-8").read().split("---", 1)[-1]
    doc = "<html><head><meta charset='utf-8'>" + CSS + "</head><body>" + md2html(body) + "</body></html>"
    open("/tmp/_daily_onenote.html", "w").write(doc)
    sid = OG._section_id()
    if not sid:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "onenote_graph.py"), "ensure-section"])
        sid = OG._section_id()
        if not sid: sys.exit("onenote: 无分区 (token 或失效, 重跑 auth)")
    title = f"Concept-Space 日报 {d}"
    # 覆帖如覆备忘录: 同名旧页先删 (一日一页)
    old = OG._req(f"/me/onenote/sections/{sid}/pages?$select=id,title&$top=200")
    for pg in old.get("value", []):
        if pg.get("title") == title:
            OG._req(f"/me/onenote/pages/{pg['id']}", method="DELETE")
    r = OG._req(f"/me/onenote/sections/{sid}/pages?title={title}", method="POST",
                raw=doc)
    print("onenote:", "页已落 " + str(r.get("id", r))[:50] if "id" in r else r)

if __name__ == "__main__":
    main()
