#!/usr/bin/env bash
# mail.sh — the Chora Mail System (CMS) v1: the city's internal post, built ON the
# letters protocol, never beside it. Numbered letters (001-…) remain diplomatic
# dispatches between benches; CMS mail is local traffic: reports, questions, orders.
#
#   Email == Markdown == Git Commit          (the docx promise, kept with two repairs:)
#   · delivery takes bin/writelock.sh first  (law 3: a commit is a sequence, not a gesture)
#   · read-state never touches git           (an inbox is a cursor, history stays the record)
#
# usage:
#   bin/mail.sh send  --from cora --to theoros --subject "exp #404 failed" [--body FILE|-]
#   bin/mail.sh check [who] [--read]            (who defaults to $CHORA_MAILBOX)
#   bin/mail.sh reply <mail-file> -m "text"     (sender = $CHORA_MAILBOX)
#   bin/mail.sh show  <mail-file>
#   bin/mail.sh status
#
# layout:  letters/mail/<ISO>-<from>-<to>-<slug>.md   the delivered city post (git-tracked)
#          .mail/outbox/                             composed, awaiting a free lock (ignored)
#          .mail/cursors/<who>                       last-read filename per recipient (ignored)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAILDIR="$ROOT/letters/mail"; OUTBOX="$ROOT/.mail/outbox"; CURSORS="$ROOT/.mail/cursors"
DOMAIN="chora.dev"
mkdir -p "$MAILDIR" "$OUTBOX" "$CURSORS"

die(){ echo "[mail] $*" >&2; exit 1; }
slug(){ echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-40; }
nowname(){ date +%Y-%m-%d-%H%M%S; }
rfcdate(){ date '+%a, %d %b %Y %H:%M:%S %z'; }
addr(){ case "$1" in *@*) echo "$1";; *) echo "$1@$DOMAIN";; esac; }
tok(){ echo "$1" | sed 's/@.*//' | tr -cd 'a-zA-Z0-9'; }
gitshort(){ git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo "???????"; }

new_mail(){ # new_mail FROM TO SUBJECT BODYFILE [IN_REPLY_TO]
  local from="$1" to="$2" subject="$3" body="$4" irt="${5:-}"
  local name
  while :; do
    name="$(nowname)-$(tok "$from")-$(tok "$to")-$(slug "$subject").md"
    { [ -e "$OUTBOX/$name" ] || [ -e "$MAILDIR/$name" ]; } || break
    sleep 1
  done
  {
    echo "From: $(addr "$from")"
    echo "To: $(addr "$to")"
    echo "Date: $(rfcdate)"
    echo "Subject: $subject"
    [ -n "$irt" ] && echo "In-Reply-To: $irt"
    echo "Message-Id: <$name@cms.chora>"
    echo "X-CMS: chora mail.sh v1 @ $(gitshort)"
    echo "---"
    cat "$body"
    echo ""
    echo "— $(tok "$from"), mailed from chora@$(gitshort)"
  } > "$OUTBOX/$name"
  echo "$name"
}

deliver(){ # deliver NAME — lock, move, commit; leaves the draft in outbox on lock conflict
  local name="$1" st holder took=0
  st=$(bash "$ROOT/bin/writelock.sh" status 2>/dev/null || true)
  holder=$(printf '%s' "$st" | sed -n 's/.*holder=\([^ ]*\).*/\1/p')
  if printf '%s' "$st" | grep -q HELD && [ "$holder" != "mail.sh" ]; then
    echo "[mail] lock held by '$holder' — mailed to outbox instead; run: bin/mail.sh flush" >&2
    return 1
  fi
  if ! printf '%s' "$st" | grep -q HELD; then
    bash "$ROOT/bin/writelock.sh" acquire "mail.sh" >/dev/null 2>&1 && took=1 \
      || { echo "[mail] could not take the lock — left in outbox" >&2; return 1; }
  fi
  mv "$OUTBOX/$name" "$MAILDIR/$name"
  git -C "$ROOT" add "$MAILDIR/$name"
  local from to subj
  from=$(sed -n 's/^From: \([^ <]*\).*/\1/p' "$MAILDIR/$name" | head -1)
  to=$(sed -n 's/^To: \([^ <]*\).*/\1/p' "$MAILDIR/$name" | head -1)
  subj=$(sed -n 's/^Subject: //p' "$MAILDIR/$name" | head -1)
  if ! git -C "$ROOT" commit -q --author="$(tok "$from") <$from>" -m "mail: $subj ($from → $to)"; then
    echo "[mail] COMMIT FAILED — $name left staged; fix and git commit, or re-send" >&2
    [ "$took" = 1 ] && bash "$ROOT/bin/writelock.sh" release >/dev/null
    return 1
  fi
  echo "[mail] delivered → $to : $subj  ($name)"
  [ "$took" = 1 ] && bash "$ROOT/bin/writelock.sh" release >/dev/null
  return 0
}

unread(){ # unread WHO — files addressed to WHO after the cursor, oldest first (bash 3.2: no mapfile)
  # filename grammar: YYYY-MM-DD-HHMMSS-from-to-slug… → the recipient is dash-field 6, exactly
  local who cur=""
  who="$(tok "$1")"
  [ -f "$CURSORS/$who" ] && cur="$(cat "$CURSORS/$who")"
  local all=()
  while IFS= read -r f; do all+=("$f"); done \
    < <(ls "$MAILDIR" 2>/dev/null | awk -F- -v w="$who" '$6==w' | sort)
  [ ${#all[@]} -gt 0 ] || return 0
  if [ -n "$cur" ]; then
    local out=() seen=0 f
    for f in "${all[@]}"; do
      if [ "$seen" = 1 ]; then out+=("$f"); fi
      [ "$f" = "$cur" ] && seen=1
    done
    # an unknown cursor (renamed history) must never swallow the whole inbox — show all then
    if [ "$seen" = 1 ]; then
      [ ${#out[@]} -gt 0 ] && printf '%s\n' "${out[@]}"
      return 0
    fi
  fi
  printf '%s\n' "${all[@]}"
}

cmd="${1:-status}"; shift || true
case "$cmd" in
  send)
    from="" to="" subject="" body=""
    while [ $# -gt 0 ]; do case "$1" in
      --from) from="$2"; shift 2;; --to) to="$2"; shift 2;; --subject|-s) subject="$2"; shift 2;;
      --body) body="$2"; shift 2;; *) die "unknown flag: $1";;
    esac; done
    [ -n "$from" ] && [ -n "$to" ] && [ -n "$subject" ] || die "send needs --from --to --subject"
    bf="$(mktemp)"
    if [ "$body" = "-" ] || [ -z "$body" ]; then cat > "$bf"; else cp "$body" "$bf"; fi
    name="$(new_mail "$from" "$to" "$subject" "$bf")"; rm -f "$bf"
    deliver "$name" || true
    ;;
  flush)
    shopt -s nullglob; n=0
    for f in "$OUTBOX"/*.md; do deliver "$(basename "$f")" && n=$((n+1)); done
    echo "[mail] flushed $n outbox letter(s)"
    ;;
  check)
    who="${1:-${CHORA_MAILBOX:-}}"
    [ -n "$who" ] || die "check needs a mailbox (arg or \$CHORA_MAILBOX)"
    mark="${2:-}"
    list=()
    while IFS= read -r f; do [ -n "$f" ] && list+=("$f"); done < <(unread "$who")
    if [ ${#list[@]} -eq 0 ]; then echo "[mail] $who: no unread"; exit 0; fi
    printf '[mail] %s: %d unread\n' "$who" "${#list[@]}"
    for f in "${list[@]}"; do
      printf '  %s\n    %s\n' "$f" "$(sed -n 's/^Subject: //p' "$MAILDIR/$f" | head -1)"
    done
    if [ "$mark" = "--read" ]; then
      echo "${list[${#list[@]}-1]}" > "$CURSORS/$who"
      echo "[mail] $who: cursor → ${list[${#list[@]}-1]}"
    fi
    ;;
  reply)
    file="$MAILDIR/${1:-}"; [ -f "$file" ] || file="$1"
    [ -f "$file" ] || die "reply: no such mail: $1"
    msgbox="${CHORA_MAILBOX:-}"; [ -n "$msgbox" ] || die "reply needs \$CHORA_MAILBOX set"
    shift
    text=""
    while [ $# -gt 0 ]; do case "$1" in -m) text="$2"; shift 2;; *) shift;; esac; done
    [ -n "$text" ] || die "reply needs -m \"text\""
    orig_from="$(sed -n 's/^From: \([^ <]*\).*/\1/p' "$file" | head -1)"
    subj="$(sed -n 's/^Subject: //p' "$file" | head -1)"
    case "$subj" in Re:*) ;; *) subj="Re: $subj";; esac
    bf="$(mktemp)"; printf '%s\n' "$text" > "$bf"
    name="$(new_mail "$msgbox" "$(tok "$orig_from")" "$subj" "$bf" "$(basename "$file")")"
    rm -f "$bf"; deliver "$name" || true
    ;;
  show) f="$MAILDIR/${1:-}"; [ -f "$f" ] || f="$1"; [ -f "$f" ] || die "show: no such mail"
    cat "$f";;
  status)
    printf '[mail] delivered: %s · outbox: %s · mailboxes with cursors: %s\n' \
      "$(ls "$MAILDIR" 2>/dev/null | wc -l | tr -d ' ')" \
      "$(ls "$OUTBOX" 2>/dev/null | wc -l | tr -d ' ')" \
      "$(ls "$CURSORS" 2>/dev/null | wc -l | tr -d ' ')"
    ;;
  *) die "unknown command: $cmd (send|flush|check|reply|show|status)";;
esac
