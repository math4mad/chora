#!/usr/bin/env bash
# bin/guard-size.sh — 预提交尺寸闸 (0927 夜立, 学费=chora push 连败十二次)
# GitHub 单文件 100MB 硬限: 一枚巨物入库, 全仓 push 长跪不起。
# 律: 凡 >95MB 的暂存块一律斩于闸前; 大件走云灶 (Concept-Space-Sphere/bin/yunpan.sh put)
#     并在案目录 OVERSIZE-REGISTER.txt 留 sha 存目; 仓内只留指针, 不留bytes。
set -u
LIM=$((95 * 1024 * 1024))
bad=0
while IFS= read -r -d '' f; do
  [ -f "$f" ] || continue
  case "$f" in .git/*) continue;; esac
  sz=$(git cat-file -s ":$f" 2>/dev/null) || continue
  if [ "${sz:-0}" -gt "$LIM" ]; then
    printf '✘ 尺寸闸斩: %s  %sMB (>100MB GitHub 硬限)\n' "$f" "$((sz / 1024 / 1024))"
    bad=1
  fi
done < <(git diff --cached --name-only -z --diff-filter=ACM)
[ $bad -eq 0 ] && exit 0
cat <<'MSG'
  治法三条 (0927 除胀案在册):
    1) git rm --cached <件>            —— 本体检留盘, 不入册
    2) bin/yunpan.sh put <件> <云名>   —— 上云灶, sha 双向对撞
    3) 案目录 OVERSIZE-REGISTER.txt 补一行 (sha + 云端在架地址)
  若已误入历史且未推: filter-branch --index-filter 只重写未推范围 (先 refs/backup 留退路)。
MSG
exit 1
