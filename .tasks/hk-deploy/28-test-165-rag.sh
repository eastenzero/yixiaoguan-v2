#!/bin/bash
# Test RAG on 165 server for comparison with HK 64
set -e
BASE=http://192.168.100.165:8100
STAFF_ID=2024010001
PASS=2024010001

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
    -d "{\"title\":\"test-165-$title\"}")
  CONV_ID=$(echo "$CONV" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
  echo "CONV_ID=$CONV_ID"

  # Capture full SSE stream
  TMPF="/tmp/rag165-$title.txt"
  curl -sk -N -X POST "$BASE/api/chat/send" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    --max-time 60 \
    -d "{\"conv_id\":$CONV_ID,\"content\":\"$query\"}" \
    > "$TMPF" 2>&1

  echo
  echo "--- assembled answer ---"
  grep -E '^data:' "$TMPF" 2>/dev/null \
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
print(ans[:2000] + ("..." if len(ans) > 2000 else ""))
'

  echo
  echo "--- retriever_resources (doc names + scores) ---"
  python3 -c "
import sys, json, re
raw = open('$TMPF').read()
m = re.search(r'\"retriever_resources\":\s*(\[.*?\])', raw)
if m:
    rr = json.loads(m.group(1))
    for i, r in enumerate(rr, 1):
        print(f'  #{i} score={r.get(\"score\",0):.4f} doc={r.get(\"document_name\",\"?\")[:50]}')
        print(f'      content={r.get(\"content\",\"\")[:100]}')
else:
    print('  (no retriever_resources found)')
"
}

run_test "dianfei" "宿舍电费怎么交？支付方式有哪些？"
run_test "jiangxuejin" "请问国家奖学金有哪些类型？金额多少？怎么申请？"
run_test "xiaoyiyuan" "校医院在哪？开放时间？有哪些科室？"

echo
echo "=== done ==="
