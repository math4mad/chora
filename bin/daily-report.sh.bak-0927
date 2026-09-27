#!/usr/bin/env bash
# daily-report.sh — 园区日报双巡 (morning 08:00 任务上表 · evening 21:00 战果投邮)
# 依主人 2026-09-19 钦定分工: 批复走提醒最短路径, 报告走邮件读物路径, 存档走 git/网页不变介质。
#   morning : 看板未决 + 提醒未勾 → 逐条挂进「Concept-Space」(去重), 勾掉即批复
#   evening : 今日两园 commits + ☑批复 + Kaggle 矩阵收获 → CMS 邮 theoros@chora.dev
#             + 追加 GRAPHIA notes/daily-log.md (周末网页沉淀的原料)
# 排程: ~/Library/LaunchAgents/com.lethe.daily-report.plist (08:00/21:00 两时点)
set -uo pipefail
R=~/Programming/code-2026
CHORA=$R/chora; LETHE=$R/Concept-Space-Sphere; GRAPHIA=$R/GRAPHIA
REMIND=$LETHE/bin/remind.sh
LOG=/tmp/daily-report.log
mode="${1:-$( [ $(date +%H) -lt 12 ] && echo morning || echo evening )}"
echo "$(date '+%F %T') mode=$mode" >> $LOG

if [ "$mode" = "morning" ]; then
  # 1) 看板未决 (lane 未至 announced/closed 的行, 取 id + next 首句)
  /opt/miniconda3/envs/default/bin/python - <<'PY' >> $LOG 2>&1
import json, subprocess, datetime, os
rows=json.load(open("/Users/mac/Programming/code-2026/chora/docs/experiments.json"))["rows"]
open_rows=[r for r in rows if r.get("claim") not in ("announced","closed","scored") or True]
# 晨报只挑: 未 announced 的 experiment 行, 每行一条, 上限 6
pick=[r for r in rows if r.get("kind","experiment")=="experiment" and r.get("claim") not in ("announced","closed")][:6]
import subprocess, os
have=subprocess.run(["osascript","-e",'tell application "Reminders" to tell list "Concept-Space" to get name of reminders whose completed is false'],capture_output=True,text=True).stdout
for r in pick:
    title=f"📌 {r['id']}: " + (r.get("next") or r.get("title") or "")[:70]
    if title[:24] not in have:
        subprocess.run(["osascript","-e",f'''tell application "Reminders" to tell list "Concept-Space" to make new reminder with properties {{name:"{title}",body:"看板行 {r['id']} · claim={r.get('claim','?')}"}}'''])
        print("morning add:", title[:60])
        # MS To Do 通道: 经 Mac 的 Exchange 账户直写「Concept-Space」专单 (服务器同步 ~5s, 零注册零授权)
        esc=title.replace('"','\\"')
        subprocess.run(["osascript","-e",f'''tell application "Reminders" to tell list "Concept-Space" of account "Exchange" to make new reminder with properties {{name:"{esc}",body:"看板镜像 · 勾掉两端同效"}}'''])
PY
  # 2) 昨日遗留 ☐ 不重挂 (本体就是提醒), 只推一条"晨圈"聚合提醒若无
  if ! /opt/miniconda3/envs/default/bin/python -c "
import subprocess
out=subprocess.run(['osascript','-e','tell application \"Reminders\" to tell list \"园区·GRAPHIA\" to get name of reminders whose completed is false'],capture_output=True,text=True).stdout
import datetime; print('晨圈' in out and datetime.date.today().isoformat()[5:] in out)" | grep -q True; then
    bash $REMIND add "☀️ 晨圈 $(date +%m-%d)：勾掉=点菜/批复" "来源: 看板未决行 + Kaggle 矩阵昨夜战果 (详见 evening 日报邮件)" "$(date +%Y-%m-%d) 08:30" >> $LOG 2>&1
  fi
else
  D=$(date +%F)
  DIG=$(mktemp)
  { echo "# 园区日报 $D · 夜巡"
    echo
    echo "## 今日 commits (chora / LETHE / GRAPHIA)"
    for repo in chora Concept-Space-Sphere GRAPHIA; do
      lg=$(git -C $R/$repo log --since="$D 00:00" --invert-grep --grep='status snapshot' --pretty=format:'- `%h` %s' 2>/dev/null | cut -c1-160)
      autos=$(git -C $R/$repo log --since="$D 00:00" --grep='status snapshot' --oneline 2>/dev/null | wc -l | tr -d ' ')
      [ -n "$lg" ] && { echo "### $repo"; echo "$lg"; [ "${autos:-0}" != "0" ] && echo "- (+$autos 条自动快照，略)"; echo; }
    done
    echo "## 今日批复 (Apple ☑ + MS To Do ☑ 并集)"
    osascript -e 'tell application "Reminders" to tell list "Concept-Space" to get "• " & (name of every reminder whose completed is true)' 2>/dev/null | tr ',' '\n' | tail -8
    osascript -e 'tell application "Reminders" to tell list "Concept-Space" of account "Exchange" to get name of (reminders whose completed is true)' 2>/dev/null | tr ',' '\n' | sed 's/^/☑MS /' | tail -6
    echo
    echo "## 外界哨位"
    curl -s --max-time 15 https://api.github.com/repos/redux-saga/redux-saga/issues/2784 2>/dev/null | /usr/local/bin/python3 -c "
import json,sys
try: d=json.load(sys.stdin); print('· redux-saga RFC #2784 → 评论', d.get('comments'), '| 状态', d.get('state'))
except Exception: print('· RFC #2784 哨兵暂哑 (网络)')" 2>/dev/null
  echo "## Kaggle 矩阵近况"
    tail -6 /tmp/kag_night.log 2>/dev/null || tail -4 /tmp/kag_marshal.log 2>/dev/null
    ls $CHORA/experiments/exp11-kaggle/matrix_out/*.done 2>/dev/null | sed 's/^/完成: /'
    echo
    echo "_dispatched by bin/daily-report.sh · 回执请 reply_"
  } > $DIG
  cd $CHORA && bash bin/mail.sh send --from lola --to theoros --subject "Concept-Space 日报 $D" --body "$DIG" 2>&1 | tee -a $LOG
  mkdir -p $GRAPHIA/notes && { echo; sed "s/^# 园区日报/## 园区日报/" $DIG; } >> $GRAPHIA/notes/daily-log.md
  cd $GRAPHIA && git add notes/daily-log.md 2>/dev/null && git commit -q -m "daily digest $D (evening patrol, machine-written)" 2>/dev/null && echo "graphia daily-log appended" >> $LOG
  /opt/miniconda3/envs/default/bin/python "/Users/mac/Programming/code-2026/chora/bin/daily_note.py" "$DIG" "$D" >> $LOG 2>&1 || echo "notes channel failed (不阻断邮件与图档)" >> $LOG
  /opt/miniconda3/envs/default/bin/python "/Users/mac/Programming/code-2026/chora/bin/daily_onenote.py" "$DIG" "$D" >> $LOG 2>&1 || echo "onenote channel failed (不阻断前三屏)" >> $LOG
  rm -f $DIG
fi
echo "$(date '+%F %T') done" >> $LOG

# ③ 园报进袋 (飞书, 无配置静默跳)
POCKET=$HOME/Programming/code-2026/Concept-Space-Sphere/bin/pocket.sh
[ -x "$POCKET" ] && [ -f ~/.config/pocket/feishu.env ] && grep -q "FEISHU_WEBHOOK=http" ~/.config/pocket/feishu.env \
  && "$POCKET" "$(head -6 /tmp/daily_report.txt 2>/dev/null | head -c 900 || echo 园报已生成,见提醒事项)"
