#!/usr/bin/env python3
"""chora/bin/todo_graph.py — Microsoft To Do via Graph API (device-code flow).

Park protocol mirrors bin/remind.sh (Apple Reminders): ☑=批复, body=回复.
One-time: `auth` prints a URL+code → owner approves at microsoft.com/devicelogin.
Token cache: ~/.chora/ms-todo.tokens.json (0600). List used: 「园区·CHORA」.

usage: todo_graph.py auth | ensure-list | add "标题" ["正文" ["YYYY-MM-DD HH:MM"]]
                           | read | done 片段 | purge 片段
"""
import json, os, sys, time, datetime

CACHE = os.path.expanduser("~/.chora/ms-todo.tokens.json")
AUTHORITY = os.environ.get("CHORA_M365_TENANT", "https://login.microsoftonline.com/consumers")
CLIENT_ID = os.environ.get("CHORA_M365_CLIENT_ID", "d3590ed6-52b1-4102-aeff-aad2292ab01c")  # Microsoft-known public client (Office); overridable once the owner registers their own app
SCOPES = ["Tasks.Read", "Tasks.ReadWrite"]  # msal 禁公户显式要 offline_access；MSA 端点照发 refresh
GRAPH = "https://graph.microsoft.com/v1.0"
LIST_NAME = "Concept-Space"


def _msal_app():
    import msal
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE):
        cache.deserialize(open(CACHE).read())
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    return app, cache


def _save(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    if cache.has_changed:
        with open(CACHE, "w") as f:
            f.write(cache.serialize())
        os.chmod(CACHE, 0o600)


def _token(interactive_hint=True):
    app, cache = _msal_app()
    acc = next(iter(app.get_accounts() or []), None)
    if acc:
        res = app.acquire_token_silent(SCOPES, account=acc)
        if res and "access_token" in res:
            _save(cache); return res["access_token"]
    if not interactive_hint:
        sys.exit("无 token — 先跑 auth")
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        sys.exit(f"device flow 失败: {flow.get('error_description', flow)}")
    print("请点击或复制以下链接在浏览器中完成授权：", flush=True)
    print()
    print(flow["verification_uri"], flush=True)
    print("一次性代码:", flow["user_code"], flush=True)
    print("(建议浏览器先登录您的个人 Microsoft 账户)", flush=True)
    res = app.acquire_token_by_device_flow(flow)  # blocks until owner approves
    _save(cache)
    if "access_token" not in res:
        sys.exit(f"授权失败: {res.get('error')} {res.get('error_description','')}")
    print("⚿ 已授权:", (res.get("id_token_claims") or {}).get("preferred_username") or res.get("username"), flush=True)
    return res["access_token"]


def _req(path, method="GET", body=None):
    import urllib.request
    req = urllib.request.Request(GRAPH + path,
        data=json.dumps(body).encode() if body else None, method=method,
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=40).read() or b'{"ok":true}')
    except Exception as e:
        try:
            e_body = e.read().decode()[:220]
        except Exception:
            e_body = ""
        sys.exit(f"Graph {method} {path} 失败: {e} {e_body}")


def _lists():
    return _req("/me/todo/lists")["value"]


def _list_id():
    for l in _lists():
        if l["displayName"] == LIST_NAME:
            return l["id"]
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "auth":
        _token(); return
    if cmd == "ensure-list":
        if _list_id():
            print("列表已在:", LIST_NAME); return
        _req("/me/todo/lists", "POST", {"displayName": LIST_NAME})
        print("列表已建:", LIST_NAME); return
    lid = _list_id() or (sys.exit("先 ensure-list"))
    if cmd == "add":
        title = sys.argv[2]
        body = sys.argv[3] if len(sys.argv) > 3 else ""
        due = sys.argv[4] if len(sys.argv) > 4 else ""
        task = {"title": title, "categories": ["园区"]}
        if body:
            task["body"] = {"content": body, "contentType": "text"}
        if due:
            dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M")
            task["dueDateTime"] = {"dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "China Standard Time"}
        r = _req(f"/me/todo/lists/{lid}/tasks", "POST", task)
        print("⏰ 已挂 To Do:", r["title"], f"(id {r['id'][-8:]})")
    elif cmd == "read":
        vs = _req(f"/me/todo/lists/{lid}/tasks?$top=50&$orderby=createdDateTime desc")["value"]
        open_t = [t for t in vs if t["status"] == "notStarted"]
        done = [t for t in vs if t["status"] == "completed"]
        print("── 未决 open ──")
        for t in open_t:
            due = (t.get("dueDateTime") or {}).get("dateTime", "")
            body = (t.get("body") or {}).get("content", "")
            print(f"◻ {t['title']}" + (f"  ⟪{body}⟫" if body else "") + (f"  ⏱{due[:16]}" if due else ""))
        print("── 已办 done (批复) ──")
        for t in done[:12]:
            print(f"☑ {t['title']}  ⌚{t.get('completedDateTime',{}).get('dateTime','')[:16]}")
    elif cmd == "done":
        pat = sys.argv[2]
        ts = [t for t in _req(f"/me/todo/lists/{lid}/tasks?$top=100")["value"] if pat in t["title"]]
        if not ts:
            sys.exit(f"无题含「{pat}」")
        t = ts[0]
        _req(f"/me/todo/lists/{lid}/tasks/{t['id']}", "PATCH", {"status": "completed"})
        print(f"☑ 已销账: {t['title']}")
    elif cmd == "purge":
        pat = sys.argv[2]
        ts = [t for t in _req(f"/me/todo/lists/{lid}/tasks?$top=100")["value"] if pat in t["title"]]
        for t in ts:
            _req(f"/me/todo/lists/{lid}/tasks/{t['id']}", "DELETE")
        print(f"✖ 删 {len(ts)} 条: {pat}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
