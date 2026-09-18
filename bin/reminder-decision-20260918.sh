#!/usr/bin/env bash
# one-shot 14:00 (+08) 2026-09-18: the owner's experiment-decision reminder.
# Pattern per bin/reminder-h9m.sh's three lessons: self-remove BEFORE the UI, message via argv,
# admit lateness; label keeps the park's voice.
set -uo pipefail
LOG=/tmp/chora-reminders.log
read -r -d '' MSG <<'TXT' || true
14:00 — 主人午安，短账在等圈点。

候补实验清单：chora/experiments/DECISION-LIST-2026-09-18.md
A1 种子加固已自走完成（结果将附在 report_10b 旁）；A3 写信十五分钟可让看板转 announced；
A2 全序列 KL / C3 先验指针呼吸 各约一小时；B 组旧账各归其 bench；C1 冷冻速率当下午茶。

请圈一个号，Lola 即刻开工。
TXT
launchctl bootout "gui/$(id -u)/com.chora.remind-decision-0918" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.chora.remind-decision-0918.plist" || true
echo "$(date '+%Y-%m-%d %H:%M:%S %z')  decision-reminder self-removed" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S %z')  FIRED  decision-list 14:00" >> "$LOG"
/usr/bin/osascript - "$MSG" <<'OSA' >>"$LOG" 2>&1
on run argv
	try
		display dialog (item 1 of argv) with title "LETHE · 14:00 (Lola 的提醒)" with icon caution buttons {"Snooze 20 min", "OK, filed"} default button 2 cancel button 1 giving up after 1200
	on error number -128
		return "dismissed-or-timed-out"
	end try
end run
OSA
/usr/bin/osascript -e 'display notification "短账在 experiments/DECISION-LIST-2026-09-18.md —— 圈一个号即开工。" with title "LETHE · 14:00" sound name "Glass"' >>"$LOG" 2>&1
if [ "$(date +%H%M)" -ge 1500 ]; then
	/usr/bin/osascript -e 'display dialog "MISSED 14:00 — fired late, the machine was asleep. 短账仍在等圈点。" with title "LETHE · late reminder" buttons {"OK"} default button 1' >>"$LOG" 2>&1
fi
exit 0
