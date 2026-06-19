#!/usr/bin/env bash
# OPTCG 組牌造價 — 啟動本機網站並開啟瀏覽器
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${OPTCG_DECK_PORT:-8765}"
HOST="${OPTCG_DECK_HOST:-127.0.0.1}"
URL="http://${HOST}:${PORT}/"

cd "$DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "找不到 python3，請先安裝 Python 3。"
  exit 1
fi

# 若埠號被佔用，嘗試關閉舊的造價伺服器
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  OLD_PID="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -1 || true)"
  if [[ -n "$OLD_PID" ]]; then
    PROC="$(ps -p "$OLD_PID" -o command= 2>/dev/null || true)"
    if [[ "$PROC" == *"deck-pricing/server.py"* ]] || [[ "$PROC" == *"server.py --port $PORT"* ]]; then
      echo "關閉舊的造價伺服器 (PID $OLD_PID)…"
      kill "$OLD_PID" 2>/dev/null || true
      sleep 0.5
    else
      echo "埠 $PORT 已被其他程式佔用，請關閉後再試，或設定 OPTCG_DECK_PORT。"
      exit 1
    fi
  fi
fi

echo "啟動 OPTCG 組牌造價：$URL"
python3 server.py --host "$HOST" --port "$PORT" --open &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 等待伺服器就緒
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "$URL" 2>/dev/null; then
    break
  fi
  sleep 0.2
done

wait "$SERVER_PID"
