# G3 三年级模型 · Runbook

## 本地(金丝雀, M1 Pro 已验 2026-09-24)
```
cd chora && python3 -m venv .venv-g3 && .venv-g3/bin/pip install torch numpy
cd experiments/g3-grade3
../../.venv-g3/bin/python test_g3.py                       # 枪膛自检
../../.venv-g3/bin/python g3_train.py --arm given --steps 400 --device mps
../../.venv-g3/bin/python g3_probe.py --arm given          # 落架判分
```

## 主炮(5090, 一周末)
1. 装环境同上(CUDA torch)；`--d 768 --layers 12 --heads 12 --ctx 1024 --batch 16`(~130M)；
2. 语料升级：corpusgen 量产四舱快餐语料至 ~1B token（NBA 舱扩全部届次；三年级舱对课标）；
3. 四臂各跑：given / free / random / learned（同 token 预算，判据先冻不许改）；
4. G3-Paper **v1 修正**（金丝雀暴露）：①序敏/验收轴候选须掺跨舱干扰词，否则落架恒真；②字面/落架分轴出表；③及格线 主臂≥85% 对照≤65% 差≥20pt（候朱批后生效）。

## 消融臂(Kaggle 免费夜航)
去课程 / 去掩码 / 半量 token / 序打乱复训——kernel-metadata 格式照 exp11，双席位轮转，日志即幸存者，torchao 疫苗照打。

## 弹药现状
四舱语料: spring55+summer55(exp11 承库) + nba24 + grade3 32 = 166 docs / ~6k 字符（金丝雀口粮；主炮靠 corpusgen）。
