#!/usr/bin/env bash
# LADDER-2b 回收哨: 完赛三验 → scp 报告 → sha 立户 → 射后关机止血
set -u
H="root@connect.bjb1.seetacloud.com"; P=47810
OUT="$(cd "$(dirname "$0")/.." && pwd)/out"
L=$(ssh -p $P -o BatchMode=yes -o ConnectTimeout=10 "$H" 'tail -c 400 /root/autodl-tmp/ladder2b-run.log | grep -c "DONE ladder2b_ok"' 2>/dev/null | tr -dc "01")
if [ "$L" != "1" ]; then
  ERR=$(ssh -p $P -o BatchMode=yes "$H" 'grep -c "\"error\"" /root/autodl-tmp/report_ladder2b.json 2>/dev/null; tail -2 /root/autodl-tmp/ladder2b-run.log | grep -c Traceback' 2>/dev/null)
  echo "在途/未验: $L errflag=$ERR"; exit 1
fi
scp -q -P $P -o BatchMode=yes "$H:/root/autodl-tmp/report_ladder2b.json" "$OUT/report_ladder2b.json" || { echo "scp 失败"; exit 1; }
grep -q ladder2b_ok "$OUT/report_ladder2b.json" || { echo "假收货: 无 sentinel"; exit 1; }
shasum -a 256 "$OUT/report_ladder2b.json" | tee "$OUT/report_ladder2b.sha256"
ssh -p $P -o BatchMode=yes "$H" 'echo GARDEN_COLLECTED; /usr/bin/shutdown' 2>/dev/null | tail -1
echo "收讫+关机令已发"; exit 0
