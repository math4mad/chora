#!/usr/bin/env python3
"""chora/bin/onenote_graph.py — Microsoft OneNote via Graph API (device-code flow).

Owner's fourth screen (2026-09-19): 夜巡 digest → HTML → OneNote page.
App registration: client id c2834a1d-741f-4715-b4b0-1a4a8439ce92 (owner's own).
Token cache: ~/.chora/ms-onenote.tokens.json (0600), authority consumers (personal account).

usage: onenote_graph.py auth [scope ...]        # one-time device-code approval
                           | notebooks          # list sections/notebooks discovered
                           | ensure-section     # create 分区 Concept-Space (idempotent)
                           | post <digest.html|-> <title>   # push one page
                           | read              # quick state dump
"""
import json, os, sys, time
import urllib.request, urllib.error

CACHE = os.path.expanduser("~/.chora/ms-onenote.tokens.json")
AUTHORITY = os.environ.get("CHORA_M365_AUTHORITY", "https://login.microsoftonline.com/consumers")
CLIENT_ID = os.environ.get("CHORA_M365_CLIENT_ID", "c2834a1d-741f-4715-b4b0-1a4a8439ce92")
GRAPH = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPES = ["Notes.ReadWrite", "Tasks.ReadWrite"]
SECTION_NAME = "Concept-Space"


def _app(scopes):
    import msal
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE):
        cache.deserialize(open(CACHE).read())
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    return app, cache


def _save(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    changed = getattr(cache, "has_state_changed", None)
    if changed is None:
        changed = getattr(cache, "has_changed", True)
    if changed:
        with open(CACHE, "w") as f:
            f.write(cache.serialize())
        os.chmod(CACHE, 0o600)


def _token(scopes=None, interactive=True):
    scopes = scopes or DEFAULT_SCOPES
    app, cache = _app(scopes)
    acc = next(iter(app.get_accounts() or []), None)
    if acc:
        res = app.acquire_token_silent(scopes, account=acc)
        if res and "access_token" in res:
            _save(cache)
            return res["access_token"]
    if not interactive:
        sys.exit("无 token — 先跑 auth")
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        sys.exit(f"device flow 失败: {flow.get('error_description', flow)}")
    print("请点击或复制以下链接在浏览器中完成授权：", flush=True)
    print(flow["verification_uri"], " 一次性代码:", flow["user_code"], flush=True)
    res = app.acquire_token_by_device_flow(flow)   # blocks until owner approves
    _save(cache)
    if "access_token" not in res:
        sys.exit(f"授权失败: {res.get('error')} {res.get('error_description','')[:160]}")
    print("⚿ 已授权:", (res.get("id_token_claims") or {}).get("preferred_username"), flush=True)
    return res["access_token"]


def _clean(path):
    from urllib.parse import quote
    # URL 卫生: 空格/CJK 一律 percent-encode (Graph 查询串与 ?title= 皆安全)
    return quote(path, safe="/?&=$,:'()!~-")

def _req(path, method="GET", body=None, raw=None):
    path = _clean(path)
    tok = _token()
    data = body and json.dumps(body).encode() or (raw and raw.encode())
    req = urllib.request.Request(GRAPH + path, data=data, method=method, headers={
        "Authorization": "Bearer " + tok,
        "Content-Type": "application/json" if body else "text/html; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        txt = r.read().decode()
        return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "msg": e.read().decode()[:300]}


def _section_id():
    for _ in range(20):
        r = _req(f"/me/onenote/sections?$select=id,displayName&$top=200")
        for s in r.get("value", []):
            if s["displayName"] == SECTION_NAME:
                return s["id"]
        nb = r.get("__error__")
        if nb:
            sys.exit(f"读取分区失败 {nb}: {r.get('msg','')[:150]}")
        nxt = r.get("@odata.nextLink")
        if not nxt:
            break
        # paginate (simple: next link path)
        r2 = {"value": []}
        req = urllib.request.Request(nxt, headers={"Authorization": "Bearer " + _token()})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "auth":
        scopes = sys.argv[2:] or DEFAULT_SCOPES
        t = _token(scopes=scopes)
        print("⚿ token 已缓存（%d 字符）" % len(t))
        return
    if cmd == "notebooks":
        r = _req("/me/onenote/notebooks?$select=id,displayName,sectionGroupsUrl")
        print(json.dumps(r.get("value", r), ensure_ascii=False)[:900])
        return
    if cmd == "ensure-section":
        sid = _section_id()
        if sid:
            print("分区已在:", sid[:24]); return
        nb = _req("/me/onenote/notebooks?$select=id,displayName")
        nbs = nb.get("value", [])
        if not nbs:
            sys.exit("账户里没有笔记本 — 请主人先在 OneNote App 建一个 (任意名字) 再跑")
        r = _req(f"/me/onenote/notebooks/{nbs[0]['id']}/sections", method="POST",
                 body={"displayName": SECTION_NAME})
        print("分区已建 → 笔记本「%s」: %s" % (nbs[0]["displayName"], str(r.get("id", r))[:60]))
        return
    if cmd == "post":
        src, title = sys.argv[2], sys.argv[3]
        html = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
        sid = _section_id() or sys.exit("先 ensure-section")
        wrapped = ("<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
                   + html + "</body></html>")
        doc = wrapped.replace("<p></body></html>", "</body></html>")
        r = _req(f"/me/onenote/sections/{sid}/pages",
                 raw=doc, method="POST")
        print("页已落:", title, r.get("id", r))
        return
    if cmd == "read":
        r = _req("/me/onenote/pages?$select=title,createdDateTime&$top=5&$orderby=createdDateTime desc")
        print(json.dumps(r.get("value", r), ensure_ascii=False, indent=1)[:800])
        return
    print(__doc__)


if __name__ == "__main__":
    main()
