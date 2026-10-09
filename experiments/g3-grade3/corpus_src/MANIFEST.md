# 语料源 · Corpus Sources（先 pin 后动 token）

| 源 | 文件 | 行/条 | sha256 | 来处 |
|---|---|---|---|---|
| NBA 选秀真史实 | `nbaplayersdraft.csv` | 1922 行 (1989–2021) | `9cedeccc384220f3464e1fea535a046b1124004077fe4ca2cfa9ed437e2ce018` | Kaggle `mattop/nba-draft-basketball-player-data-19892021` |
| 春节/夏天 (exp11) | `../exp11-kaggle/corpus/corpus_{spring,summer}.jsonl` | 各 55 篇 | (见 exp11) | 早期 LLM 产 |
| 三年级常识 | `g3_data.GRADE3` | 16 条 | — | 自编, **候人工审** |

纪律: 史实不编 (NBA 用真 CSV); 舱界由互斥词表保证。
