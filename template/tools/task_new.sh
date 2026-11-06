#!/usr/bin/env bash
# 建立任務紀錄（K1）
# 用法：tools/task_new.sh <slug> [incident|change|investigation|script|learning]
# 輸出：新紀錄的路徑。ID 格式 T-YYYYMMDD-NN，同一天自動遞增。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
slug="${1:?用法：tools/task_new.sh <slug> [incident|change|investigation|script|learning]}"
type="${2:-change}"

[[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "slug 只能用小寫英數字與 -：$slug" >&2; exit 1; }
case "$type" in incident|change|investigation|script|learning) ;; *) echo "未知的 type：$type" >&2; exit 1 ;; esac
[[ -f "$ROOT/tasks/TEMPLATE.md" ]] || { echo "找不到 $ROOT/tasks/TEMPLATE.md" >&2; exit 1; }

day="$(date +%Y%m%d)"
now="$(date '+%Y-%m-%d %H:%M')"
n=1
while compgen -G "$ROOT/tasks/T-$day-$(printf %02d "$n")-*.md" >/dev/null \
   || compgen -G "$ROOT/tasks/archive/T-$day-$(printf %02d "$n")-*.md" >/dev/null; do
  n=$((n + 1))
done
id="T-$day-$(printf %02d "$n")"
path="$ROOT/tasks/$id-$slug.md"

sed -e "1s/.*/# $id $slug/" \
    -e "s/^type: .*/type: $type/" \
    -e "s/YYYY-MM-DD HH:MM/$now/g" \
    -e '/^- HH:MM /d' \
    "$ROOT/tasks/TEMPLATE.md" > "$path"
echo "$path"
