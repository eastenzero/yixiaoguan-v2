#!/bin/bash
echo "=== find .env ==="
find /home/easten -name '.env' 2>/dev/null

echo ""
echo "=== gateway env ==="
ENV_FILE=$(find /home/easten -name '.env' -path '*gateway*' 2>/dev/null | head -1)
if [ -z "$ENV_FILE" ]; then
  # fallback: check systemd unit for env location
  ENV_FILE=$(grep -r 'EnvironmentFile\|WorkingDirectory' /etc/systemd/system/yixiaoguan* 2>/dev/null | head -5)
  echo "No .env found, systemd hints: $ENV_FILE"
  # try to extract from running process
  GATEWAY_PID=$(pgrep -f 'uvicorn.*8100' | head -1)
  if [ -n "$GATEWAY_PID" ]; then
    echo "Gateway PID: $GATEWAY_PID"
    GW_CWD=$(readlink -f /proc/$GATEWAY_PID/cwd 2>/dev/null)
    echo "Gateway CWD: $GW_CWD"
    if [ -f "$GW_CWD/.env" ]; then
      ENV_FILE="$GW_CWD/.env"
    fi
  fi
fi

echo "ENV_FILE=$ENV_FILE"

if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | grep DIFY | xargs)
fi

echo "DIFY_API_URL=${DIFY_API_URL:-(not set)}"
echo "DIFY_API_KEY=${DIFY_API_KEY:0:15}..."

echo ""
echo "=== Test Dify SSE events ==="
if [ -n "$DIFY_API_KEY" ]; then
  timeout 30 curl -sN -X POST "${DIFY_API_URL}/chat-messages" \
    -H "Authorization: Bearer $DIFY_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"inputs":{},"query":"图书馆开放时间","response_mode":"streaming","user":"test-suggest"}' \
    2>/dev/null | while IFS= read -r line; do
      echo "$line"
    done | tail -5
else
  echo "SKIP: no DIFY_API_KEY"
fi
