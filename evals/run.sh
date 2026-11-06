#!/usr/bin/env bash
# 跑實驗：建置各 arm → 逐一用 `claude plugin eval` 評估 → 產生比較報告
#
# 用法：evals/run.sh [選項]
#   --arms a1,a2,a3        要比較的組別（預設 a1,a2,a3）
#   --ablate K2,K4g|all    a3 的消融組（all = K1…K10 各一組，外加 K4g）
#   --runs 3               每個案例每組跑幾次（預設 3）
#   --case 'c0*'           只跑符合的案例
#   --model sonnet         受測模型（建議固定，避免模型更新被誤認為規則的效果）
#   --judge-model sonnet   llm grader 用的模型
#   --max-cost-usd 20      每一組的費用上限
#   -j 2                   同時執行數（1–8）
#   --quick                等於 --arms a1,a3 --runs 1
#
# 需求：Claude Code（有 `claude plugin eval`）、已登入；Linux 需要 bubblewrap 與 socat（Bash 沙盒）。
# 第一組會加跑「不裝任何規則」的基準（A0），其他組只跑自己。
set -euo pipefail

EVALS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
arms="a1,a2,a3" ablate="" runs=3 case_glob="" model="" judge="" cost="" conc=1

while (($#)); do
  case "$1" in
    --arms) arms="$2"; shift ;;
    --ablate) ablate="$2"; shift ;;
    --runs) runs="$2"; shift ;;
    --case) case_glob="$2"; shift ;;
    --model) model="$2"; shift ;;
    --judge-model) judge="$2"; shift ;;
    --max-cost-usd) cost="$2"; shift ;;
    -j|--concurrency) conc="$2"; shift ;;
    --quick) arms="a1,a3"; runs=1 ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知選項：$1" >&2; exit 1 ;;
  esac
  shift
done

command -v claude >/dev/null || { echo "找不到 claude 指令" >&2; exit 1; }
if [[ "$(uname)" == "Linux" ]] && ! { command -v bwrap >/dev/null && command -v socat >/dev/null; }; then
  echo "Linux 上評估需要 Bash 沙盒：請先安裝 bubblewrap 與 socat（例如 sudo apt install bubblewrap socat）" >&2
  exit 1
fi

python3 "$EVALS/selftest.py" >/dev/null || { echo "selftest 沒過，先執行 python3 $EVALS/selftest.py 看哪個案例有問題" >&2; exit 1; }

build_args=(--arms "$arms")
[[ -n "$ablate" ]] && build_args+=(--ablate "$ablate")
python3 "$EVALS/build_arms.py" "${build_args[@]}" >/dev/null

stamp="$(date +%Y%m%d-%H%M%S)"
out="$EVALS/results/$stamp"
mkdir -p "$out"
echo "結果目錄：$out"

first=1
for dir in "$EVALS"/build/*/; do
  arm="$(basename "$dir")"
  ablation=none
  if ((first)); then ablation=with-without; fi
  first=0
  cmd=(claude plugin eval "$dir" --scaffold --trust-plugin --no-publish
       --runs "$runs" --ablation "$ablation" -j "$conc" --threshold 0
       --json "$out/$arm.json")
  [[ -n "$case_glob" ]] && cmd+=(--case "$case_glob")
  [[ -n "$model" ]] && cmd+=(--model "$model")
  [[ -n "$judge" ]] && cmd+=(--judge-model "$judge")
  [[ -n "$cost" ]] && cmd+=(--max-cost-usd "$cost")
  cmd+=(--allow-tools Bash Write Edit)
  echo "▶ $arm（ablation=$ablation）"
  "${cmd[@]}" || echo "  ⚠ $arm 結束代碼 $?（看 $out/$arm.json 的 partial／error）"
done

python3 "$EVALS/compare.py" "$out"
