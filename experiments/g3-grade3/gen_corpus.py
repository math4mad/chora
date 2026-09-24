"""corpusgen 产线: SpaceBunny 弹药库 → 四舱快餐语料(exp11 jsonl 同构)。
枪口纪律: 只产非敏感活(舱语料), 钥匙走 env 不落盘不落屏。
用法: ../../.venv-g3/bin/python gen_corpus.py --cabin spring --n 5
NBA 舱为确定性模板扩增(史实序不许 LLM 编); grade3 舱产物候人工审。"""
import argparse, json, os, random, re, subprocess, sys
import urllib.request
try:
    import ssl, certifi
    _SSLCTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSLCTX = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus")
API = "https://api.tokenbargain.dev/v1/chat/completions"
MODEL = os.environ.get("TB_MODEL", "SpaceBunny")

PROMPTS = {
    "spring": ("你在写春节概念空间的短文档。要求:只写春节/年货/团圆/鞭炮/饺子/红包/庙会/元宵这一舱的物事,"
               "不出现夏天/海滩/烧烤词;口吻生活化,60-90字,一段到底。只输出正文,每行一条,共{n}条,不要编号。"),
    "summer": ("你在写夏天概念空间的短文档。要求:只写夏夜/海滩/游泳/蝉鸣/西瓜/啤酒/烧烤/凉席这一舱的物事,"
               "不出现春节/饺子/红包词;口吻生活化,60-90字,一段到底。只输出正文,每行一条,共{n}条,不要编号。"),
    "grade3": ("你在编三年级科学/数学/社会常识短句(陈述句,事实正确,像课本)。要求:一条一句,30-60字,"
               "话题分散(动物/植物/天气/数字/地理/安全)。每行一条,共{n}条,不要编号。"),
}


def get_key():
    k = os.environ.get("TOKENBARGAIN_API_KEY")
    if k:
        return k.strip()
    with open(os.path.expanduser("~/.zshrc")) as f:
        for line in f:
            if line.startswith("export TOKENBARGAIN_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"\'')
    sys.exit("无钥匙")


def ask(key, prompt):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 6000, "temperature": 0.9}).encode()
    req = urllib.request.Request(API, data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(req, timeout=60, context=_SSLCTX) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def nba_docs():
    from g3_data import NBA_TRIPLES
    out = []
    T = ["{y}年NBA选秀第{r}顺位：{p}被{t}队选中。",
         "在{y}年的选秀大会上，{p}于首轮第{r}顺位被{t}队摘下。",
         "{y}年第{r}顺位属于{p}，{t}队用这个签位选了他。"]
    for y, r, p, t in NBA_TRIPLES:
        for f in T:
            out.append(f.format(y=y, r=r, p=p, t=t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cabin", default="spring", choices=["spring", "summer", "grade3", "nba"])
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.cabin == "nba":
        docs = nba_docs()
    else:
        txt = ask(get_key(), PROMPTS[a.cabin].format(n=a.n))
        docs = [l.strip() for l in txt.splitlines() if len(l.strip()) >= 20]
    fn = os.path.join(OUT, f"gen_{a.cabin}.jsonl")
    with open(fn, "a", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"messages": [{"role": "user", "content": "写一条。"},
                                             {"role": "assistant", "content": d}],
                                "cabin": a.cabin}, ensure_ascii=False) + "\n")
    print(f"{a.cabin}: +{len(docs)} 条 → {fn}")


if __name__ == "__main__":
    main()
