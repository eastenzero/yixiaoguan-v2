#!/bin/bash
# Test RAG pipeline end-to-end. Print streaming tokens + retriever_resources.
set -e
BASE=https://yxg.130814.xyz
STAFF_ID=4124150001
PASS=4124150001

echo "=== login ==="
TOKEN=$(curl -sk -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"staff_id\":\"$STAFF_ID\",\"password\":\"$PASS\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
[ -z "$TOKEN" ] && { echo "ERR: no token"; exit 1; }
echo "TOKEN=${TOKEN:0:30}..."

run_test() {
  local title="$1"
  local query="$2"
  echo
  echo "==================================================================="
  echo "= TEST: $title"
  echo "= query: $query"
  echo "==================================================================="

  CONV=$(curl -sk -X POST "$BASE/api/conversations" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"title\":\"e2e-rag-$title\"}")
  CONV_ID=$(echo "$CONV" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
  echo "CONV_ID=$CONV_ID"

  # Capture full SSE stream
  curl -sk -N -X POST "$BASE/api/chat/send" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    --max-time 35 \
    -d "{\"conv_id\":$CONV_ID,\"content\":\"$query\"}" \
    > /tmp/rag-stream-$CONV_ID.txt 2>&1

  echo
  echo "--- assembled answer ---"
  grep -E '^data:' /tmp/rag-stream-$CONV_ID.txt 2>/dev/null \
    | sed 's/^data: //' \
    | python3 -c '
import sys, json
tokens = []
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        if "token" in d:
            tokens.append(d["token"])
    except: pass
ans = "".join(tokens)
print(ans[:1500] + ("..." if len(ans) > 1500 else ""))
'

  echo
  echo "--- intent / retriever from raw stream ---"
  grep -oE '"intent":"[^"]*"' /tmp/rag-stream-$CONV_ID.txt | head -1
  # In dify, full retriever info is internal; we can also look at gateway analytics if any
}

run_test "greeting" "你好"
run_test "rag-jiangxuejin" "请问国家奖学金有哪些类型？金额多少？怎么申请？"
run_test "rag-xiaoyiyuan" "校医院在哪？开放时间？有哪些科室？"
run_test "rag-dianfei" "宿舍电费怎么交？支付方式有哪些？"
run_test "rag-shaoyou" "本科生毕业要求多少学分？毕业证什么时候发？"

echo
echo "=== done ==="
