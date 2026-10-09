#!/usr/bin/env python3
"""corpusgen 扩产 (确定性模板 × 大槽位) — 四舱快餐语料 → exp11 同构 jsonl。

纪律:
  · 确定性模板律 — 不编史实 (NBA 只用既有真 triples; grade3 只用既有真事实);
  · 舱界由 **互斥词表** 保证 (spring/summer 词表不相交);
  · 可扩: --target-chars 控每舱字符量, 组合空间巨大。

用法:
  ../../.venv-g3/bin/python gen_corpus_big.py --cabins spring summer --target-chars 200000
  ../../.venv-g3/bin/python gen_corpus_big.py --all --target-chars 1000000 --out corpus_big
"""
import argparse, json, os, random, itertools

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- 词表 (舱间互斥) ----------------
SPRING = {
    "who":  ["一家人", "爷爷", "奶奶", "爸爸", "妈妈", "孩子们", "邻居们", "亲戚们", "外婆", "表哥", "叔叔", "婶婶"],
    "obj":  ["春联", "福字", "红包", "饺子", "汤圆", "年糕", "腊肉", "鞭炮", "烟花", "灯笼", "年货", "压岁钱", "窗花", "糖瓜"],
    "place":["家门口", "院子里", "庙会上", "厨房里", "客厅里", "村口", "街上", "集市上", "祠堂前", "老屋门口"],
    "act":  ["贴", "挂", "包", "煮", "放", "拜", "收", "买", "看", "吃", "蒸", "送"],
    "mood": ["热热闹闹", "喜气洋洋", "红红火火", "团团圆圆", "忙忙碌碌", "和和美美"],
}
SUMMER = {
    "who":  ["孩子们", "老王", "邻居", "朋友们", "一家人", "小狗", "大爷", "大妈", "表哥", "同学们"],
    "obj":  ["西瓜", "冰棍", "啤酒", "凉席", "蒲扇", "泳圈", "烧烤", "汽水", "草帽", "冰粉", "绿豆汤", "凉面"],
    "place":["院子里", "海边", "河边", "大树下", "阳台上", "夜市里", "泳池边", "沙滩上", "空调房里", "桥头"],
    "act":  ["吃", "喝", "摇", "铺", "游", "烤", "乘凉", "吹", "泡", "赏"],
    "mood": ["凉快", "舒服", "惬意", "热闹", "悠闲", "自在"],
}
TMPL = {
    "spring": [
        "{who}在{place}{act}{obj}，{mood}。",
        "过春节的时候，{who}在{place}{act}{obj}，一家人{mood}。",
        "{place}，{who}{act}{obj}，年味很浓，{mood}。",
        "腊月里，{who}忙着{act}{obj}，{place}一片{mood}。",
        "除夕这天，{who}在{place}{act}{obj}，心里{mood}。",
        "{who}说，过年就得在{place}{act}{obj}，才够{mood}。",
    ],
    "summer": [
        "{who}在{place}{act}{obj}，{mood}。",
        "夏天的傍晚，{who}在{place}{act}{obj}，{mood}极了。",
        "{place}，{who}{act}{obj}，蝉还在树上叫着，{mood}。",
        "天一热，{who}就在{place}{act}{obj}，{mood}。",
        "三伏天里，{who}在{place}{act}{obj}，{mood}得很。",
        "{who}说，夏天最开心的就是在{place}{act}{obj}，{mood}。",
    ],
}


def gen_cabin(cabin, target_chars, rng):
    V, T = (SPRING, TMPL["spring"]) if cabin == "spring" else (SUMMER, TMPL["summer"])
    combos = list(itertools.product(V["who"], V["place"], V["act"], V["obj"], V["mood"]))
    rng.shuffle(combos)
    docs, total = [], 0
    for who, place, act, obj, mood in combos:
        t = T[len(docs) % len(T)].format(who=who, place=place, act=act, obj=obj, mood=mood)
        docs.append(t); total += len(t)
        if total >= target_chars:
            break
    return docs


def gen_nba():
    """确定性模板 × **真 CSV** (1922 条, 1989–2021; 不编史实)。"""
    import csv
    p = os.path.join(HERE, "corpus_src", "nbaplayersdraft.csv")
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    T = ["{y}年NBA选秀第{r}顺位：{p}被{t}队选中。",
         "在{y}年的选秀大会上，{p}于首轮第{r}顺位被{t}队摘下。",
         "{y}年第{r}顺位属于{p}，{t}队用这个签位选了他。",
         "{p}在{y}年选秀大会首轮第{r}顺位被{t}队摘下。",
         "{y}年，{t}队在第{r}顺位选中{p}。",
         "第{r}顺位，{t}队把{h}的{p}带进了联盟。"]
    out = []
    for r in rows:
        for f in T:
            out.append(f.format(y=r["year"], r=r["rank"], p=r["player"],
                                t=r["team"], h=r.get("college", "") or "大学"))
    return out


def gen_grade3():
    from g3_data import GRADE3
    pre = ["", "三年级科学课上，老师讲道：", "课本里写着：", "老师告诉我们：", "书上说，"]
    out = []
    for s in GRADE3:
        for p in pre:
            out.append(p + s)
    return out


def write_jsonl(path, cabin, docs):
    with open(path, "a", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"messages": [{"role": "user", "content": "写一条。"},
                                             {"role": "assistant", "content": d}],
                                "cabin": cabin}, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cabins", nargs="*", default=["spring", "summer"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--target-chars", type=int, default=200_000)
    ap.add_argument("--out", default="corpus_big")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    outdir = os.path.join(HERE, a.out); os.makedirs(outdir, exist_ok=True)
    cabins = ["spring", "summer", "nba", "grade3"] if a.all else a.cabins
    for c in cabins:
        fn = os.path.join(outdir, f"gen_{c}.jsonl")
        if os.path.exists(fn):
            os.remove(fn)
        if c in ("spring", "summer"):
            docs = gen_cabin(c, a.target_chars, rng)
        elif c == "nba":
            docs = gen_nba()
        elif c == "grade3":
            docs = gen_grade3()
        else:
            continue
        write_jsonl(fn, c, docs)
        chars = sum(len(d) for d in docs)
        print(f"{c:7s}: {len(docs):>7} 条 / {chars:>9} 字符 → {a.out}/{os.path.basename(fn)}")


if __name__ == "__main__":
    main()
