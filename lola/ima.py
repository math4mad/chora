#!/usr/bin/env python3
"""ima OpenAPI 客户端 — 笔记读写 ＋ 信鸽匣 transport=ima-api 之桥。
凭据: env IMA_OPENAPI_CLIENTID/APIKEY → ~/.config/ima/{client_id,api_key} → ~/.zshrc
用法:
  ima.py folders | list [folder_id] | search <q> | read <doc_id> | find <title>
  ima.py make <title> <md_file> | append <doc_id> <md_file>
  ima.py box-push <md_file>   # 追加到《Lola·outbox》(无则建)
  ima.py box-pull             # 读《Lola·inbox》正文
"""
import os, re, sys, json, ssl, urllib.request

BASE = "https://ima.qq.com"
OUTBOX_TITLE = "Lola·outbox"
INBOX_TITLE = "Lola·inbox"

_SSLCTX = None
for _c in ["/etc/ssl/cert.pem", "/usr/local/etc/openssl@3/cert.pem", "/opt/homebrew/etc/openssl@3/cert.pem"]:
    if os.path.exists(_c):
        try:
            _SSLCTX = ssl.create_default_context(cafile=_c); break
        except Exception:
            pass
if _SSLCTX is None:
    try:
        import certifi; _SSLCTX = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        _SSLCTX = ssl.create_default_context()


def cred(name, env):
    v = os.environ.get(env)
    if v:
        return v.strip()
    p = os.path.expanduser(f"~/.config/ima/{name}")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    z = os.path.expanduser("~/.zshrc")
    if os.path.exists(z):
        for ln in open(z, encoding="utf-8"):
            m = re.match(rf"export {env}=(.*)", ln.strip())
            if m:
                return m.group(1).strip().strip('"\'')
    return None


def api(path, body):
    cid = cred("client_id", "IMA_OPENAPI_CLIENTID")
    key = cred("api_key", "IMA_OPENAPI_APIKEY")
    if not cid or not key:
        sys.exit("缺 IMA 凭证 (IMA_OPENAPI_CLIENTID/APIKEY)")
    req = urllib.request.Request(
        f"{BASE}/{path}", data=json.dumps(body).encode("utf-8"),
        headers={"ima-openapi-clientid": cid, "ima-openapi-apikey": key,
                 "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=40, context=_SSLCTX) as r:
        return json.load(r)


# ---------- 笔记原语 ----------
def folders():
    return api("openapi/note/v1/list_note_folder_by_cursor", {"cursor": "0", "limit": 50})


def list_notes(folder_id=None, limit=20):
    b = {"cursor": "", "limit": limit}
    if folder_id:
        b["folder_id"] = folder_id
    return api("openapi/note/v1/list_note_by_folder_id", b)


def search(q, by_body=False):
    return api("openapi/note/v1/search_note_book",
               {"search_type": 1 if by_body else 0,
                "query_info": ({"content": q} if by_body else {"title": q}),
                "start": 0, "end": 20})


def read(doc_id, fmt=0):
    return api("openapi/note/v1/get_doc_content", {"doc_id": doc_id, "target_content_format": fmt})


def make(title, content, folder_id=None):
    b = {"content": content, "content_format": 1, "title": title}
    if folder_id:
        b["folder_id"] = folder_id
    r = api("openapi/note/v1/import_doc", b)
    return _find_key(r, ("note_id", "doc_id", "docid"))


def append(doc_id, content):
    return api("openapi/note/v1/append_doc", {"doc_id": doc_id, "content": content, "content_format": 1})


def _find_key(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, str) and v:
                return v
        for v in obj.values():
            r = _find_key(v, keys)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, keys)
            if r:
                return r
    return None


def _docs(d):
    return (d.get("data") or {}).get("docs") or (d.get("data") or {}).get("note_book_list") or []


def find(title):
    """按标题找 doc_id (精确匹配 title)。"""
    for doc in _docs(search(title, by_body=False)):
        t = _find_key(doc, ("title",))
        did = _find_key(doc, ("docid", "doc_id", "note_id"))
        if t and t.strip() == title.strip() and did:
            return did
    return None


def ensure(title):
    did = find(title)
    if did:
        return did, False
    r = make(title, f"# {title}\n")
    return r, True


# ---------- 信鸽匣 ----------
def box_push(text):
    did, created = ensure(OUTBOX_TITLE)
    append(did, text)
    return did, created


def box_pull():
    did = find(INBOX_TITLE)
    if not did:
        return None, None
    d = read(did, 0)
    return did, (d.get("data") or {}).get("content", "")


def _main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == "folders":
        print(json.dumps(folders(), ensure_ascii=False))
    elif cmd == "list":
        print(json.dumps(list_notes(a[1] if len(a) > 1 else None), ensure_ascii=False))
    elif cmd == "search":
        print(json.dumps(search(a[1], by_body=("--body" in a)), ensure_ascii=False))
    elif cmd == "read":
        print(json.dumps(read(a[1]), ensure_ascii=False))
    elif cmd == "find":
        print(find(a[1]) or "(none)")
    elif cmd == "make":
        print(json.dumps(make(a[1], open(a[2], encoding="utf-8").read()), ensure_ascii=False))
    elif cmd == "append":
        print(json.dumps(append(a[1], open(a[2], encoding="utf-8").read()), ensure_ascii=False))
    elif cmd == "box-push":
        did, created = box_push(open(a[1], encoding="utf-8").read())
        print(f"{'created' if created else 'appended'} {OUTBOX_TITLE} doc_id={did}")
    elif cmd == "box-pull":
        did, c = box_pull()
        print(f"# {INBOX_TITLE} doc_id={did}\n{c}" if did else "(no inbox note)")
    else:
        print(__doc__)


if __name__ == "__main__":
    _main()
