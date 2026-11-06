#!/usr/bin/env bash
# 把 template/ 複製到你的工作區（infra repo 或你在 Claude 開啟的資料夾）。
# 用法：./install.sh <工作區路徑> [--force]
#   預設不覆蓋已存在的檔案；--force 會覆蓋（tasks/ 裡的任務紀錄永遠不會被覆蓋）。
# 不會修改 ~/.claude 或任何全域設定。
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="${1:?用法：./install.sh <工作區路徑> [--force]}"
force=0
[[ "${2:-}" == "--force" ]] && force=1
mkdir -p "$target"
target="$(cd "$target" && pwd)"

copied=0 skipped=0
while IFS= read -r -d '' src; do
  rel="${src#"$KIT/template/"}"
  dst="$target/$rel"
  if [[ -e "$dst" ]] && { ((!force)) || [[ "$rel" == tasks/T-* ]]; }; then
    echo "  略過（已存在）：$rel"
    skipped=$((skipped + 1))
    continue
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  copied=$((copied + 1))
done < <(find "$KIT/template" -type f -print0)

chmod +x "$target/tools/"*.sh "$target/tools/"*.py
echo "已複製 $copied 個檔案，略過 $skipped 個 → $target"
python3 "$target/tools/check_kit.py" || true

cat <<EOF

接下來：
  1. 編輯 $target/TRUTH.md 的「環境」表：哪些 context／主機是 prod（guard hook 依這張表判斷 R3）
  2. 編輯 $target/AGENTS.md 開頭「這個工作區」那段
  3. 在 Claude 開啟 $target（桌面版：選這個資料夾），開新 session
  4. 改完任何規則後：python3 tools/check_kit.py
EOF
