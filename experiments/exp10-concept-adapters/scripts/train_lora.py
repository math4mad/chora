#!/usr/bin/env python3
# exp10 · train_lora.py — Step 0: mint the two discrete adapters (and later, the mid one)
# Recipe is ONE shared block for all arms (law: comparability), only the corpus path differs.
import argparse, json, os, sys, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType

BASE = os.path.expanduser("~/Programming/code-2026/chora/models/models/Qwen--Qwen2.5-0.5B/snapshots/master")
RECIPE = dict(r=16, lora_alpha=32, lora_dropout=0.05,
              target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                              "gate_proj", "up_proj", "down_proj"])
HP = dict(lr=1e-4, epochs=6, batch=2, accum=4, seed=13)   # small corpus → more epochs, fixed seed


def encode_pair(tok, user, assistant):
    msgs = [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
    prompt = tok.apply_chat_template(msgs[:1] + [{"role": "assistant", "content": ""}],
                                     tokenize=False, add_generation_prompt=True)
    full = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    ids_full = tok(full, add_special_tokens=False)["input_ids"]
    ids_pr = tok(prompt, add_special_tokens=False)["input_ids"]
    labels = [-100] * len(ids_pr) + ids_full[len(ids_pr):]
    return ids_full, labels


def collate(feats, tok):
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    L = max(len(f[0]) for f in feats)
    ids, lab, att = [], [], []
    for i, l in feats:
        p = L - len(i)
        ids.append(i + [pad] * p); lab.append(l + [-100] * p); att.append([1] * len(i) + [0] * p)
    return torch.tensor(ids), torch.tensor(lab), torch.tensor(att)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--epochs", type=int, default=None,
                    help="override epochs (used by the mid arm to match samples-seen)")
    ap.add_argument("--seed", type=int, default=None, help="override HP.seed")
    a = ap.parse_args()
    hp = dict(HP)
    if a.epochs:
        hp["epochs"] = a.epochs
    if a.seed:
        hp["seed"] = a.seed

    torch.manual_seed(hp["seed"])
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32)
    cfg = LoraConfig(task_type=TaskType.CAUSAL_LM, **RECIPE, bias="none")
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    model.to(dev)

    feats = []
    for line in open(a.corpus):
        m = json.loads(line)["messages"]
        feats.append(encode_pair(tok, m[0]["content"], m[1]["content"]))
    print(f"[{a.tag}] {len(feats)} pairs on {dev}", flush=True)

    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=hp["lr"])
    steps = (len(feats) // hp["batch"] + 1) * hp["epochs"]
    seen = 0
    t0 = time.time()
    for ep in range(hp["epochs"]):
        perm = torch.randperm(len(feats))
        acc, nb = 0.0, 0
        for b in range(0, len(feats), hp["batch"]):
            batch = [feats[i] for i in perm[b:b + hp["batch"]].tolist()]
            ids, lab, att = collate(batch, tok)
            if dev == "cuda": ids, lab, att = ids.cuda(), lab.cuda(), att.cuda()
            if dev == "mps": ids, lab, att = ids.to(dev), lab.to(dev), att.to(dev)
            out = model(input_ids=ids, attention_mask=att, labels=lab)
            (out.loss / hp["accum"]).backward()
            acc += out.loss.item(); nb += 1
            if nb % hp["accum"] == 0:
                opt.step(); opt.zero_grad()
        seen += len(feats)
        print(f"  ep{ep+1}/{hp['epochs']} loss {acc/nb:.3f}  {time.time()-t0:.0f}s", flush=True)
    model.save_pretrained(a.out)
    tok.save_pretrained(a.out)
    json.dump({"tag": a.tag, "corpus": a.corpus, "recipe": RECIPE, "hp": hp,
               "base": BASE, "dev": dev, "epochs_ran": hp["epochs"],
               "final_loss": acc / nb, "seconds": round(time.time() - t0, 1)},
              open(os.path.join(a.out, "train_receipt.json"), "w"), ensure_ascii=False, indent=1)
    print(f"[{a.tag}] saved → {a.out}", flush=True)


if __name__ == "__main__":
    main()
