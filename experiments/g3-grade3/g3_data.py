"""G3 数据舱: 春节/夏天(承 exp11 弹药库) + NBA选秀(序即维度) + 三年级常识(自制)。
字符级词表; 文档打包成带舱标签 token 流; 课程门控按阶段放舱/解锁邻舱。"""
import json, os, random
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
EXP11 = os.path.join(HERE, "..", "exp11-kaggle", "corpus")
PAD, BOS, EOS = 0, 1, 2
CABINS = ["spring", "summer", "nba", "grade3"]

# (年份, 顺位, 球员, 球队) —— 真实史实, 顺序即语料之序
NBA_TRIPLES = [
    ("2003", "1", "勒布朗·詹姆斯", "骑士"), ("2003", "2", "卡梅隆·安东尼", "活塞"),
    ("2003", "3", "克里斯·波什", "猛龙"), ("2003", "4", "德维恩·韦德", "热火"),
    ("1997", "1", "蒂姆·邓肯", "马刺"), ("1997", "2", "基斯·范霍恩", "76人"),
    ("1997", "3", "昌西·比卢普斯", "凯尔特人"), ("1997", "4", "安东尼奥·麦克戴斯", "掘金"),
    ("1998", "1", "迈克·奥洛沃坎迪", "快船"), ("1998", "2", "迈克·毕比", "灰熊"),
    ("1998", "3", "拉夫·阿尔斯通", "独行侠"), ("1998", "4", "迈克尔·杜布里", "猛龙"),
]

GRADE3 = [
    "鲸不是鱼，它是哺乳动物，用肺呼吸。", "春天，燕子从南方飞回来，在屋檐下筑巢。",
    "水在标准大气压下到一百度就会沸腾。", "北京是我们国家的首都。",
    "零乘任何数都得零。", "植物生长需要阳光、水和空气。",
    "月亮本身不发光，它反射太阳的光。", "一年有四季：春、夏、秋、冬。",
    "身份证上的号码是唯一的，一人一号。", "红灯停，绿灯行，黄灯亮了等一等。",
    "蜜蜂跳圆圈舞告诉同伴花在哪里。", "长江是我国第一长河。",
    "固体有固定的形状，液体没有。", "我们看到的彩虹是阳光被水滴折射形成的。",
    "地图上通常上北下南，左西右东。", "在自然界中，动物按食性分为草食、肉食和杂食。",
]


def load_docs(seed=0):
    """返回 [(text, cabin_id), ...]"""
    docs = []
    for ci, fn in enumerate(["corpus_spring.jsonl", "corpus_summer.jsonl"]):
        with open(os.path.join(EXP11, fn), encoding="utf-8") as f:
            for line in f:
                m = json.loads(line)["messages"]
                for turn in m:
                    if turn["role"] == "assistant":
                        docs.append((turn["content"], ci))
    for y, r, p, t in NBA_TRIPLES:
        docs.append((f"{y}年NBA选秀第{r}顺位：{p}被{t}队选中。", 2))
        docs.append((f"{p}在{y}年选秀大会首轮第{r}顺位被{t}队摘下。", 2))
    for s in GRADE3:
        docs.append((s, 3))
        docs.append(("三年级科学课上，老师讲道：" + s, 3))
    random.Random(seed).shuffle(docs)
    return docs


class Tok:
    def __init__(self, docs):
        chars = sorted({c for t, _ in docs for c in t})
        self.itos = ["<pad>", "<bos>", "<eos>"] + chars
        self.stoi = {c: i for i, c in enumerate(self.itos)}
        self.vocab = len(self.itos)

    def encode(self, text):
        ids = [self.stoi[c] for c in text if c in self.stoi]
        return [BOS] + ids + [EOS]


def pack(docs, tok, ctx, batch, seed=0, cabins_filter=None):
    """打包成 (B,T) idx 与 cab; 舱过滤=课程门控的数据侧。"""
    ds = [d for d in docs if cabins_filter is None or d[1] in cabins_filter]
    random.Random(seed).shuffle(ds)
    toks, cabs = [], []
    for t, c in ds:
        e = tok.encode(t)
        toks += e; cabs += [c] * len(e)
    nb = max(1, (len(toks) - 1) // (ctx * batch))
    need = nb * batch * ctx + 1
    arr = torch.tensor(toks[:need])
    car = torch.tensor(cabs[:need])
    xs = arr[: nb * batch * ctx].view(nb * batch, ctx)
    cs = car[: nb * batch * ctx].view(nb * batch, ctx)
    ys = arr[1: nb * batch * ctx + 1].view(nb * batch, ctx)
    return xs, cs, ys


def stage_at(step, total):
    """课程门控: (允许舱集合, 已解锁邻舱对)。三阶段 one by one。"""
    if step < 0.4 * total:
        return {0, 1}, set()
    if step < 0.7 * total:
        return {0, 1, 2, 3}, {(0, 1)}
    return {0, 1, 2, 3}, {(0, 1), (2, 3)}
