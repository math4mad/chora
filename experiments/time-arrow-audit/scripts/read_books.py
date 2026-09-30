#!/usr/bin/env python3
"""时间之箭审计 · 跑器: 公开书 → 切块 → token 口 SpaceBunny 抽取 → 解剖册。
枪口纪律: 只送公开书; 钥匙不落盘不落屏。
用法: python3 scripts/read_books.py --book roberts [--limit-chunks N]
"""
import argparse, json, os, re, sys, time, zipfile, glob
import urllib.request, urllib.error

try:
    import ssl
    _CA = None
    try:
        import certifi
        _CA = certifi.where()
    except Exception:
        pass
    _SSLCTX = None
    for _c in ([_CA] if _CA else []) + ["/etc/ssl/cert.pem", "/usr/local/etc/openssl@3/cert.pem", "/opt/homebrew/etc/openssl@3/cert.pem"]:
        if _c and os.path.exists(_c):
            try:
                _SSLCTX = ssl.create_default_context(cafile=_c); break
            except Exception:
                pass
    if _SSLCTX is None:
        _SSLCTX = ssl.create_default_context()
except Exception:
    _SSLCTX = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "dissection")
SRC = os.path.expanduser("~/Downloads/DownLoad_Temp/time-space-concept-space")
API = "https://api.tokenbargain.dev/v1/chat/completions"
MODEL = os.environ.get("TB_MODEL", "SpaceBunny")
CHUNK = 28000  # 字符/块 (SpaceBunny context 32768)

BOOKS = {
    "roberts":   "*Roberts*.pdf",
    "price":     "*Price*.epub",
    "zuchowski": "*Zuchowski*.pdf",
    "davies":    "*Complexity and the arrow*.pdf",
    "lopez":     "*Arrow of Time_ From Local*.pdf",
    "gould":     "*Gould*.pdf",
}

PROMPT = """你在做一次严格的**文献解剖**（只依据所给文本，不得引入文本外知识）。
下面是一部学术著作的第 {pages} 页文本。请抽取与以下主题相关的**主张**：

T1 时间箭头之真假：某箭头（热力学/宇宙学/心理学/量子/因果）是否为真·时间不对称
T2 时间反转(time reversal)之定义；"representation view"（把时间反转当作表征/对称问题）
T3 热力学/熵箭头之地位：真 / 假 / 派生 / 条件
T4 时间之箭与"结构/表征"之关系：箭头住在时间本身的结构，还是物质能量之偶然事实？
T5 熵与信息 / 统计涌现

**输出**：每行一条 JSON，不要任何围栏或解说；查无则只输出 []：
{{"topic":"T3","claim":"<一句话主张>","quote":"<逐字原句>","page":"{pages}"}}
规则：quote 必须**逐字**（禁转述/禁翻译）；不得编造；无相关主张就输出 []。

--- 文本开始 ---
{text}
--- 文本结束 ---"""

TOPIC_NAMES = {"T1": "箭头真假", "T2": "时间反转·representation", "T3": "热力学/熵箭头地位", "T4": "箭头与结构/表征", "T5": "熵·信息·涌现"}


def get_key():
    k = os.environ.get("TOKENBARGAIN_API_KEY")
    if k:
        return k.strip()
    for p in ("~/.zshrc", "~/.zprofile", "~/.bashrc"):
        try:
            with open(os.path.expanduser(p)) as f:
                for line in f:
                    if line.startswith("export TOKENBARGAIN_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'')
        except FileNotFoundError:
            pass
    sys.exit("无钥匙 (TOKENBARGAIN_API_KEY)")


def extract_pdf(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    return [(i + 1, r.pages[i].extract_text() or "") for i in range(len(r.pages))]


def extract_epub(path):
    import html
    out = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        for n in sorted(names):
            raw = z.read(n).decode("utf-8", "replace")
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
            txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                out.append((n.split("/")[-1], txt))
    # 分页标签: 用序号（epub 无固定页码）
    return [(i + 1, t) for i, (_, t) in enumerate(out)]


def chunk_items(items):
    """items: [(label,text)] → [(pages_label, text)] 合并到 ~CHUNK 字符。"""
    chunks, buf, lab0, lab1, size = [], [], None, None, 0
    for lab, txt in items:
        if not txt.strip():
            continue
        if size and size + len(txt) > CHUNK:
            chunks.append((f"{lab0}-{lab1}", "\n".join(buf))); buf, size, lab0 = [], 0, None
        if lab0 is None:
            lab0 = lab
        buf.append(txt); size += len(txt); lab1 = lab
    if buf:
        chunks.append((f"{lab0}-{lab1}", "\n".join(buf)))
    return chunks


def ask(key, prompt, tries=4):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 8000, "temperature": 0.2}).encode()
    for t in range(tries):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"})
            with urllib.request.urlopen(req, timeout=120, context=_SSLCTX) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and t < tries - 1:
                time.sleep(5 * (t + 1)); continue
            raise
        except Exception as e:
            if t < tries - 1:
                time.sleep(4 * (t + 1)); continue
            raise
    raise RuntimeError("ask failed")


def parse_lines(txt):
    rows = []
    for ln in txt.splitlines():
        ln = ln.strip().lstrip("`").strip()
        if not ln.startswith("{"):
            continue
        try:
            o = json.loads(ln)
            if o.get("claim"):
                rows.append(o)
        except Exception:
            pass
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True, choices=list(BOOKS))
    ap.add_argument("--limit-chunks", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    g = glob.glob(os.path.join(SRC, BOOKS[a.book]))
    if not g:
        sys.exit(f"未找到书: {BOOKS[a.book]}")
    path = g[0]
    items = extract_pdf(path) if path.lower().endswith(".pdf") else extract_epub(path)
    chunks = chunk_items(items)
    if a.limit_chunks:
        chunks = chunks[:a.limit_chunks]
    print(f"书={os.path.basename(path)} 页/章={len(items)} 块={len(chunks)}")
    key = get_key()
    jl = os.path.join(OUT, f"{a.book}_chunks.jsonl")
    done = set()
    if os.path.exists(jl):
        for ln in open(jl, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["pages"])
            except Exception:
                pass
    with open(jl, "a", encoding="utf-8") as f:
        for i, (pages, text) in enumerate(chunks):
            if pages in done:
                print(f"  跳过(已跑) {pages}"); continue
            try:
                out = ask(key, PROMPT.format(pages=pages, text=text))
                rows = parse_lines(out)
            except Exception as e:
                rows = []
                print(f"  ✘ {pages}: {e}")
            f.write(json.dumps({"book": a.book, "pages": pages, "rows": rows}, ensure_ascii=False) + "\n"); f.flush()
            print(f"  ✔ {pages}: {len(rows)} 条")
    aggregate(a.book)


def aggregate(book):
    jl = os.path.join(OUT, f"{book}_chunks.jsonl")
    if not os.path.exists(jl):
        return
    by = {}
    for ln in open(jl, encoding="utf-8"):
        try:
            o = json.loads(ln)
        except Exception:
            continue
        for r in o.get("rows", []):
            by.setdefault(r.get("topic", "?"), []).append(r)
    lines = [f"# 文献解剖册 · {book}（token 口 SpaceBunny 抽取 · 本地汇总）\n"]
    for t in ["T1", "T2", "T3", "T4", "T5"]:
        rows = by.get(t, [])
        lines.append(f"\n## {t} · {TOPIC_NAMES[t]}（{len(rows)} 条）\n")
        for r in rows:
            lines.append(f"- **{r.get('claim','')}**")
            lines.append(f"  > {r.get('quote','')}  \n  〔p.{r.get('page','?')}〕")
    open(os.path.join(OUT, f"DISSECTION_{book}.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"✔ 解剖册: {OUT}/DISSECTION_{book}.md")


if __name__ == "__main__":
    main()
