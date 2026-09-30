#!/usr/bin/env python3
"""ima 知识库 (wiki/v1) 上传器:
  check_repeated_names → create_media → COS Upload → add_knowledge
用法:
  ima_kb.py ls                          # 列我的知识库
  ima_kb.py upload <file> [--kb <名|id>] # 传文件到知识库(默认第一个)
"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ima  # noqa

SK = os.path.expanduser("~/.pi/agent/skills/ima-skill/knowledge-base/scripts")
COS, PREFLIGHT = os.path.join(SK, "cos-upload.cjs"), os.path.join(SK, "preflight-check.cjs")


def kb_list():
    return ima.api("openapi/wiki/v1/search_knowledge_base", {"query": "", "cursor": "", "limit": 20})


def _kbs(d):
    data = d.get("data") or {}
    return data.get("info_list") or data.get("knowledge_base_list") or data.get("list") or []


def find_kb(name_or_id):
    for kb in _kbs(kb_list()):
        kid = kb.get("kb_id") or kb.get("id") or kb.get("knowledge_base_id")
        nm = kb.get("kb_name") or kb.get("name") or kb.get("title")
        if name_or_id in (kid, nm) or (nm and name_or_id in nm):
            return kid, nm
    return None, None


def preflight(path):
    r = subprocess.run(["node", PREFLIGHT, "--file", path], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        sys.exit(f"preflight 失败: {r.stdout} {r.stderr}")


def upload(path, kb_id):
    pf = preflight(path)
    if pf.get("pass") is False:
        sys.exit(f"preflight 不过: {pf}")
    # 1) 重名检查
    ima.api("openapi/wiki/v1/check_repeated_names",
            {"params": [{"name": pf["file_name"], "media_type": pf["media_type"]}],
             "knowledge_base_id": kb_id})
    # 2) create_media
    cm = ima.api("openapi/wiki/v1/create_media",
                 {"file_name": pf["file_name"], "file_size": pf["file_size"],
                  "content_type": pf["content_type"], "knowledge_base_id": kb_id, "file_ext": pf["file_ext"]})
    data = cm.get("data") or {}
    mid, cred = data.get("media_id"), data.get("cos_credential") or {}
    if not mid:
        sys.exit(f"create_media 失败: {json.dumps(cm, ensure_ascii=False)[:300]}")
    # 3) COS 上传
    args = ["node", COS, "--file", path,
            "--secret-id", cred.get("secret_id", ""), "--secret-key", cred.get("secret_key", ""),
            "--token", cred.get("token", ""), "--bucket", cred.get("bucket_name", ""),
            "--region", cred.get("region", ""), "--cos-key", cred.get("cos_key", ""),
            "--content-type", pf["content_type"],
            "--start-time", str(cred.get("start_time", "")), "--expired-time", str(cred.get("expired_time", ""))]
    up = subprocess.run(args, capture_output=True, text=True)
    if up.returncode != 0:
        sys.exit(f"COS 上传失败: {up.stdout} {up.stderr}")
    # 4) add_knowledge
    ak = ima.api("openapi/wiki/v1/add_knowledge",
                 {"media_type": pf["media_type"], "media_id": mid, "title": pf["file_name"],
                  "knowledge_base_id": kb_id,
                  "file_info": {"cos_key": cred.get("cos_key", ""), "file_size": pf["file_size"], "file_name": pf["file_name"]}})
    return ak


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "ls":
        d = kb_list()
        print(json.dumps(d, ensure_ascii=False, indent=1)[:2000])
    elif a[0] == "upload":
        kb = a[a.index("--kb") + 1] if "--kb" in a else None
        kid, nm = (find_kb(kb) if kb else find_kb(""))
        if not kid and not kb:
            ks = _kbs(kb_list())
            if ks:
                kid = ks[0].get("kb_id") or ks[0].get("id") or ks[0].get("knowledge_base_id")
                nm = ks[0].get("kb_name") or ks[0].get("name") or ks[0].get("title")
        if not kid:
            sys.exit("未找到知识库 (用 ima_kb.py ls 看清单)")
        print(f"目标知识库: {nm} ({kid})")
        r = upload(a[1], kid)
        print(json.dumps(r, ensure_ascii=False)[:400])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
