# 由每個案例的 scaffold.sh source。在空的工作區裡建立：
#   - 工作區基本檔案（workspace/：TRUTH.md、tasks/、tools/，不含任何規則）
#   - .sim/：模擬器與這個案例的 sim.json
#   - bin/：kubectl、ssh、helm、scp 的包裝（呼叫模擬器）
#   - 案例自己的 files/（例如其他 session 的任務紀錄）
#   - $HOME/.kube/config：和模擬器相同的 current-context，讓 guard hook 看得到
# 任務紀錄裡的 {{NOW}}、{{AGO_20M}}、{{AGO_1D}} 會換成實際時間。

SHARED="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"

setup_workspace() {
  cp -R "$SHARED/workspace/." .
  mkdir -p .sim bin
  cp "$SHARED/fakecli.py" .sim/
  cp "$CASE_DIR/sim.json" .sim/
  local tool
  for tool in kubectl ssh helm scp; do
    printf '#!/usr/bin/env bash\nexec python3 "$(cd "$(dirname "$0")/.." && pwd)/.sim/fakecli.py" %s "$@"\n' "$tool" > "bin/$tool"
    chmod +x "bin/$tool"
  done
  if [[ -d "$CASE_DIR/files" ]]; then
    cp -R "$CASE_DIR/files/." .
  fi
  chmod +x tools/*.sh tools/*.py 2>/dev/null || true
  python3 - <<'PY'
import glob, json, os, time
fmt = "%Y-%m-%d %H:%M"
subs = {
    "{{NOW}}": time.strftime(fmt),
    "{{AGO_20M}}": time.strftime(fmt, time.localtime(time.time() - 20 * 60)),
    "{{AGO_1D}}": time.strftime(fmt, time.localtime(time.time() - 26 * 3600)),
}
for path in glob.glob("tasks/*.md") + glob.glob("notes/*.md"):
    text = open(path, encoding="utf-8").read()
    for k, v in subs.items():
        text = text.replace(k, v)
    open(path, "w", encoding="utf-8").write(text)
ctx = json.load(open(".sim/sim.json", encoding="utf-8")).get("current_context", "")
os.makedirs(os.path.expanduser("~/.kube"), exist_ok=True)
with open(os.path.expanduser("~/.kube/config"), "w") as f:
    f.write(f"apiVersion: v1\nkind: Config\ncurrent-context: {ctx}\n")
PY
}
