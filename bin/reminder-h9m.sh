#!/usr/bin/env bash
# CHORA — one-shot reminder, 2026-09-13 09:10 (+0800): the H9-M morning.
# Installed as ~/Library/LaunchAgents/com.chora.remind-h9m.plist (launchd StartCalendarInterval with
# an explicit Month+Day, so it fires once; a job missed during sleep runs on wake — hence the lateness
# check). macOS has no `at`; this is the native one-shot. Self-removes after firing.
set -uo pipefail
LOG=/tmp/chora-reminders.log

read -r -d '' MSG <<'TXT' || true
09:10 — MEF's answer on H9-M is due: adopt, amend, or refuse.

Then, in order: (1) the k=0 replicate band on ONE machine — Gate 6 is still open, and two seeds on two laptops confounds machine with seed, so it is not a band; (2) seed 15's ladder, ~30 min (base 742.5 s + 15 arms × 96.2 s); (3) R1 densification only if the slope exceeds the band.

Also queued for the room: H6a's fate after DEAD-BY-CURVE-CLAUSE (S = 7.880 — the dial reads rank, it is just not early) · D2 per-bench manifests · 3 stale pins (pretrain.log, season-1 outline, the spectra race).

Draft: benches/Kairos/docs/PREREG.md @ Kairos@ae6be01 · plan: letters/024 · ceiling ~1 h 20 m.
TXT

echo "$(date '+%Y-%m-%d %H:%M:%S %z')  FIRED  H9-M reminder" >> "$LOG"

# modal first: a dialog waits for you, a notification does not. Message arrives via argv so no
# AppleScript line-continuations are needed (that is how the first draft of this file broke).
/usr/bin/osascript - "$MSG" <<'OSA' >>"$LOG" 2>&1
on run argv
	try
		display dialog (item 1 of argv) with title "CHORA · 09:10 (you asked to be woken)" with icon caution buttons {"Snooze 20 min", "OK, filed"} default button 2 cancel button 1 giving up after 1200
	on error number -128
		return "dismissed-or-timed-out"
	end try
end run
OSA

/usr/bin/osascript -e 'display notification "H9-M morning: MEF answers the draft, then the band, then seed 15." with title "CHORA · 09:10 reminder" sound name "Glass"' >>"$LOG" 2>&1

# if the machine was asleep at 09:10 and this only ran late, say so rather than pretending
if [ "$(date +%H%M)" -ge 1010 ]; then
	/usr/bin/osascript -e 'display dialog "MISSED 09:10 — fired late, the machine was asleep. H9-M is still waiting on MEF.'"'"'s answer." with title "CHORA · late reminder" buttons {"OK"} default button 1' >>"$LOG" 2>&1
fi

launchctl bootout "gui/$(id -u)/com.chora.remind-h9m" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/com.chora.remind-h9m.plist"
echo "$(date '+%Y-%m-%d %H:%M:%S %z')  self-removed" >> "$LOG"
exit 0
