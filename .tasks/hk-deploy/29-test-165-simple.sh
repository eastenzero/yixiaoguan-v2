#!/bin/bash
# Simple 165 RAG test - also test greeting + raw dump
set -e
BASE=http://127.0.0.1:8100

TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"2024010001","password":"2024010001"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "TOKEN=${TOKEN:0:30}..."

test_q() {
  local label="$1"
  local query="$2"
  echo
  echo "=== $label ==="
  CONV=$(curl -s -X POST "$BASE/api/conversations" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"title\":\"t-$label\"}")
  CID=$(echo "$CONV" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
  echo "conv=$CID"

  curl -sN -X POST "$BASE/api/chat/send" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    --max-time 60 \
    -d "{\"conv_id\":$CID,\"content\":\"$query\"}" \
    > /tmp/raw165-$label.txt 2>&1

  echo "--- raw output ---"
  cat /tmp/raw165-$label.txt
  echo
}

test_q "greeting" "你好"
test_q "dianfei" "宿舍电费怎么交？支付方式有哪些？"
test_q "jiangxuejin" "请问国家奖学金有哪些类型？"

echo "=== done ==="
