# PB16-MAC · 三臂课程对决 (S 域序 / R 乱序 / B 旅制) —— B 机 (m1-16g, MPS) 执行仪
# 判据在册: PREREG_PB16_MAC_3ARM.md (先冻于任何一格训练之前)
# 仪之来源: exp11-kaggle/matrix_run.py 的几何管线 (dWov / k90 V-A) —— 此处把"臂对臂"换成"段对段"，
#           并以 tr((A2A1^T)(B1^TB2)) 恒等式精确算低秩 ΔW 内积，不落 1.4GB 稠密矩阵 (数学等价，省内存)。
# 断亦留档: 每臂每 seed 每 epoch 末 flush 一次 json；崩臂记 error+traceback 入匣，不许静默消失。
import os, sys, json, time, base64, hashlib, itertools, math, traceback
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from safetensors.torch import save_file

# ---------------------------------------------------------------- 冻结参数 (PREREG §0/§1)
MODEL = os.environ.get("PB16_MODEL",
    "/Users/lunarcheung/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B-Instruct/snapshots/master")
EMBED = "/Users/lunarcheung/Programming/code-2026/chora/experiments/exp11-kaggle/matrix_corpus_embed.py"
OUT   = os.environ.get("PB16_OUT",
    "/Users/lunarcheung/Programming/code-2026/chora/experiments/pb16-mac-brigade/out")
DATA  = "/tmp/pb16mac-corpus"
DOMAINS_ORDER = ["general", "code", "spring", "summer", "legal", "medical", "mid"]   # PB16 §0 冻结序
FILES = {d: f"corpus_{d}.jsonl" for d in DOMAINS_ORDER}
ARMS  = ["S", "R", "B"]
SPLIT_SEED = 20260923
HP     = dict(lr=1e-4, batch=7, accum=1, epochs=int(os.environ.get("PB16_EPOCHS", 4)),
              seeds=[int(x) for x in os.environ.get("PB16_SEEDS", "13,14").split(",")])
RECIPE = dict(r=16, lora_alpha=32, lora_dropout=0.05,
              target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
MODS = RECIPE["target_modules"]
os.makedirs(OUT, exist_ok=True); os.makedirs(DATA, exist_ok=True)
LOG = open(os.path.join(OUT, "run_log.txt"), "a", buffering=1)
def log(*a):
    s = " ".join(str(x) for x in a)
    print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True); LOG.write(s + "\n")

# ---------------------------------------------------------------- 弹药: 解包即验 (律二)
def unpack_corpus():
    src = open(EMBED).read()
    payload = json.loads(src[src.index("PAYLOAD=") + len("PAYLOAD="):])
    verify = {}
    for f, m in payload.items():
        raw = base64.b64decode(m["b64"]); h = hashlib.sha256(raw).hexdigest()
        if h != m["sha256"] or len(raw) != m["bytes"]:
            raise SystemExit(f"corpus drift: {f} {h[:12]} != {m['sha256'][:12]} —— 一字不符即停")
        p = os.path.join(DATA, f)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != h:
            open(p, "wb").write(raw)
        verify[f] = {"sha256": h, "bytes": len(raw)}
    return verify

def load_pairs(d):
    out = []
    for line in open(os.path.join(DATA, FILES[d])):
        if not line.strip(): continue
        ms = json.loads(line)["messages"]
        out.append((d, ms[0]["content"], ms[1]["content"]))
    return out

def split_all():
    rng = np.random.default_rng(SPLIT_SEED)
    train, held, ledger = [], [], {}
    for d in DOMAINS_ORDER:
        ps = load_pairs(d); idx = rng.permutation(len(ps)); nh = int(math.ceil(len(ps) / 4))
        held += [ps[i] for i in idx[:nh]]; train += [ps[i] for i in idx[nh:]]
        ledger[d] = {"n_total": len(ps), "n_held": nh, "n_train": len(ps) - nh}
    return train, held, ledger

_ENC = {}
def enc(tok, u, a):
    key = (u, a)
    if key in _ENC: return _ENC[key]
    msgs = [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
    p = tok.apply_chat_template(msgs[:1] + [{"role": "assistant", "content": ""}], tokenize=False, add_generation_prompt=True)
    full = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    fi = tok(full, add_special_tokens=False)["input_ids"]; pi = tok(p, add_special_tokens=False)["input_ids"]
    r = (fi, [-100] * len(pi) + fi[len(pi):]); _ENC[key] = r
    return r

def collate(fs, tok):
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    L = max(len(f[0]) for f in fs); ids, lab, at = [], [], []
    for i, l in fs:
        n = L - len(i); ids.append(i + [pad] * n); lab.append(l + [-100] * n); at.append([1] * len(i) + [0] * n)
    return torch.tensor(ids), torch.tensor(lab), torch.tensor(at)

# ---------------------------------------------------------------- 三臂之课程 (唯一变量)
def arm_order(arm, train, seed):
    by_dom = {d: [p for p in train if p[0] == d] for d in DOMAINS_ORDER}
    rng = np.random.default_rng(seed)
    if arm == "S":
        seq = []
        for d in DOMAINS_ORDER:
            ps = by_dom[d][:]; rng.shuffle(ps); seq += ps
    elif arm == "R":
        seq = train[:]; rng.shuffle(seq)
    elif arm == "B":
        q = {d: by_dom[d][:] for d in DOMAINS_ORDER}
        for d in q: rng.shuffle(q[d])
        seq = []
        while any(q.values()):
            for d in DOMAINS_ORDER:
                if q[d]: seq.append(q[d].pop(0))
    else: raise ValueError(arm)
    n = HP["batch"]
    return [seq[i:i + n] for i in range(0, len(seq), n)]

def segment_boundaries(nb, k=7):
    return [int(round(nb * (i + 1) / k)) for i in range(k)]

# ---------------------------------------------------------------- 几何仪 (低秩精确内积)
def keys_of(sd):
    out = {}
    for k, v in sd.items():
        for kind in ("A", "B"):
            if f".lora_{kind}.weight" in k:
                L = int(k.split(".layers.")[1].split(".")[0])
                m = k.split(f".layers.{L}.")[1].split(f".lora_{kind}.weight")[0].split(".")[-1]
                out.setdefault((L, m), {})[kind] = v
    return {tuple(km): (d["B"], d["A"]) for km, d in out.items()}

def snapshot(model):
    sd = {k: v.detach().float().cpu().numpy() for k, v in model.state_dict().items() if "lora_" in k}
    return keys_of(sd)

def seg_repr(prev, cur, key):
    """ΔW_seg = B_c A_c − B_p A_p = [B_c, -B_p] @ [[A_c],[A_p]]  (秩 ≤ 2r)。"""
    Bc, Ac = cur[key]; Bp, Ap = prev[key]
    return np.concatenate([Bc, -Bp], axis=1), np.concatenate([Ac, Ap], axis=0)

def ip(B1, A1, B2, A2):
    return float(np.trace((A2 @ A1.T) @ (B1.T @ B2)))

def k90(s):
    e = s ** 2 / (s ** 2).sum(); return int(np.searchsorted(np.cumsum(e), 0.90) + 1)

def _prep(prev, cur):
    """每段每模块: 内积所需 (Bt,At) + 右子空间 SVD 缓存。"""
    cache = {}
    for key in sorted(cur):
        Bt, At = seg_repr(prev, cur, key)
        _, s, Vh = np.linalg.svd(At, full_matrices=False)
        cache[key] = (Bt, At, s, Vh)
    return cache

def seg_analysis(prep, labels):
    """K1 段能量谱 + K2 段间 dWov / k90 重叠。"""
    energy = {}
    for lab in labels:
        tot = 0.0
        for key, (Bt, At, _, _) in prep[lab].items():
            tot += ip(Bt, At, Bt, At)
        energy[lab] = math.sqrt(max(tot, 0.0))
    geo = {}
    for a, b in itertools.combinations(labels, 2):
        num = na = nb2 = va = 0.0; nk = 0
        for key in sorted(prep[a]):
            B1, A1, s1, V1 = prep[a][key]; B2, A2, s2, V2 = prep[b][key]
            num += ip(B1, A1, B2, A2); na += ip(B1, A1, B1, A1); nb2 += ip(B2, A2, B2, A2)
            if s1.sum() > 0 and s2.sum() > 0 and (s2 ** 2).sum() > 0:
                k = k90(s1); va += float(np.linalg.norm(V1[:k] @ V2[:k].T, "fro")); nk += 1
        denom = math.sqrt(na) * math.sqrt(nb2)
        geo[f"{a}~{b}"] = {"dWov": round(num / denom, 4) if denom > 0 else None,
                           "V-A_k90": round(va / nk, 3) if nk else None}
    return energy, geo

# ---------------------------------------------------------------- 探针: 各域 held-out NLL (assistant 段)
def heldout_nll(model, tok, held, dev):
    model.eval(); acc = {d: [0.0, 0] for d in DOMAINS_ORDER}
    ce = torch.nn.functional.cross_entropy
    with torch.no_grad():
        for i in range(0, len(held), 8):
            chunk = held[i:i + 8]
            ids, lab, at = collate([enc(tok, u, a) for _, u, a in chunk], tok)
            o = model(input_ids=ids.to(dev), attention_mask=at.to(dev))
            logits = o.logits[:, :-1, :].float(); sl = lab[:, 1:]
            flat_l = sl.reshape(-1); flat_p = logits.reshape(-1, logits.shape[-1])
            losses = ce(flat_p, flat_l, ignore_index=-100, reduction="none").reshape(sl.shape)
            mask = (sl != -100).float()
            per = (losses * mask).sum(1).tolist(); cnt = mask.sum(1).tolist()
            for (d, _, _), lv, cv in zip(chunk, per, cnt):
                acc[d][0] += lv; acc[d][1] += cv
            del o, logits, losses
    model.train()
    return {d: (round(v[0] / v[1], 4) if v[1] else None) for d, v in acc.items()}

# ---------------------------------------------------------------- 主循环
def build(dev, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32)
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, **RECIPE, bias="none"))
    model.to(dev); model.train()
    return model

def run_arm(arm, seed, tok, train, held, dev, master):
    t0 = time.time()
    batches = arm_order(arm, train, seed); nb = len(batches); bounds = segment_boundaries(nb)
    labels = [f"s{k+1}" for k in range(len(bounds))]
    rec = {"arm": arm, "seed": seed, "steps_per_epoch": nb, "segment_bounds": bounds,
           "n_lora_params": None, "epochs": []}
    if arm == "B":
        rec["batches_full_brigade"] = sum(1 for b in batches if len({p[0] for p in b}) == len(DOMAINS_ORDER))
        rec["batches_depleted"] = nb - rec["batches_full_brigade"]
    model = build(dev, seed)
    rec["n_lora_params"] = sum(p.numel() for p in model.parameters() if p.requires_grad)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=HP["lr"])
    for e in range(1, HP["epochs"] + 1):
        ep_start = snapshot(model); prev = ep_start; snap_at = {}
        acc = 0.0; nstep = 0
        for si, batch in enumerate(batches, start=1):
            ids, lab, at = collate([enc(tok, u, a) for _, u, a in batch], tok)
            o = model(input_ids=ids.to(dev), attention_mask=at.to(dev), labels=lab.to(dev))
            (o.loss / HP["accum"]).backward(); acc += o.loss.item(); nstep += 1
            if HP["accum"] == 1 or nstep % HP["accum"] == 0: opt.step(); opt.zero_grad()
            if si in bounds: snap_at[si] = snapshot(model); prev = snap_at[si]
            if si % 20 == 0: log(f"  {arm}/s{seed}/ep{e} {si}/{nb} loss {acc/nstep:.3f} {time.time()-t0:.0f}s")
        prep = {}; prev = ep_start
        for k, b in enumerate(bounds):
            prep[labels[k]] = _prep(prev, snap_at[b]); prev = snap_at[b]
        energy, geo = seg_analysis(prep, labels)
        ev = [energy[l] for l in labels]
        cv = float(np.std(ev) / (np.mean(ev) + 1e-300))
        heg = [geo[f"{labels[0]}~{labels[j]}"]["dWov"] for j in range(1, len(labels))]
        off = [v["dWov"] for k, v in geo.items()]
        nll = heldout_nll(model, tok, held, dev)
        ck = os.path.join(OUT, f"ckpt_{arm}_seed{seed}_ep{e}.safetensors")
        save_file({k: v.detach().cpu().contiguous() for k, v in model.state_dict().items() if "lora_" in k}, ck)
        if os.path.getsize(ck) == 0: raise RuntimeError("0 字节 checkpoint —— 作废重跑 (律二)")
        sha = hashlib.sha256(open(ck, "rb").read()).hexdigest()
        rec["epochs"].append({"epoch": e, "loss_mean": round(acc / max(nstep, 1), 4),
                              "seg_energy": {l: round(x, 4) for l, x in zip(labels, ev)},
                              "seg_energy_CV": round(cv, 4), "E1_over_E7": round(ev[0] / ev[-1], 3),
                              "first_seg_hegemony_row": heg,
                              "mean_offdiag_dWov": round(float(np.mean([x for x in off if x is not None])), 4),
                              "seg_geometry": geo, "heldout_nll": nll,
                              "ckpt": os.path.basename(ck), "ckpt_sha256": sha, "bytes": os.path.getsize(ck),
                              "min": round((time.time() - t0) / 60, 2)})
        master["ts_update"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(master, open(os.path.join(OUT, "report_macb.json"), "w"), indent=1, ensure_ascii=False)
        log(f"== {arm}/s{seed} ep{e}: CV={cv:.3f} E1/E7={ev[0]/ev[-1]:.2f} meanNLL="
            f"{np.mean([v for v in nll.values() if v]):.3f} nll={nll} {rec['epochs'][-1]['min']}min")
        del prep
    rec["minutes"] = round((time.time() - t0) / 60, 2)
    del model
    return rec

def main():
    if not os.path.isdir(MODEL): raise SystemExit("底座不在盘上: " + MODEL)
    verify = unpack_corpus()
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    train, held, ledger = split_all()
    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "right"
    import transformers, peft
    arms = os.environ.get("PB16_ARMS", ",".join(ARMS)).split(",")
    master = {"run": "pb16-mac-3arm", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "run_on": "m1-16g (MacB)", "device": dev,
              "env": {"torch": torch.__version__, "transformers": transformers.__version__,
                      "peft": peft.__version__, "numpy": np.__version__, "python": sys.version.split()[0]},
              "model_path": MODEL, "corpus_verify": verify, "split_seed": SPLIT_SEED, "ledger": ledger,
              "n_train": len(train), "n_held": len(held),
              "hp": {**HP, "recipe": RECIPE, "domains_order": DOMAINS_ORDER},
              "arms": arms, "prereg": "experiments/pb16-mac-brigade/PREREG_PB16_MAC_3ARM.md",
              "results": []}
    json.dump(master, open(os.path.join(OUT, "report_macb.json"), "w"), indent=1, ensure_ascii=False)
    log(f"START arms={arms} epochs={HP['epochs']} dev={dev} n_train={len(train)} n_held={len(held)}")
    for arm in arms:
        for seed in HP["seeds"]:
            try:
                master["results"].append(run_arm(arm, seed, tok, train, held, dev, master))
                json.dump(master, open(os.path.join(OUT, "report_macb.json"), "w"), indent=1, ensure_ascii=False)
            except Exception as ex:
                master["results"].append({"arm": arm, "seed": seed, "FAILED": True,
                                          "error": type(ex).__name__ + ": " + str(ex)[:300],
                                          "traceback": traceback.format_exc()[-1500:]})
                json.dump(master, open(os.path.join(OUT, "report_macb.json"), "w"), indent=1, ensure_ascii=False)
                log(f"!! {arm}/s{seed} FAILED: {type(ex).__name__}: {str(ex)[:200]}")
    log("ALL DONE")

if __name__ == "__main__":
    main()
