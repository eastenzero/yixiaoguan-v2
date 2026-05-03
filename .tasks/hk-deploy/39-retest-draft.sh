#!/bin/bash
BASE="http://127.0.0.1:8100/api"

# Login as teacher
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "teacher_token: ${TOKEN:0:20}..."

# Get unanswered-top to find an ID
UNANSWERED=$(curl -s "$BASE/v1/knowledge/unanswered-top?limit=3" \
  -H "Authorization: Bearer $TOKEN")
echo ""
echo "unanswered-top:"
echo "$UNANSWERED" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for item in d.get('items', [])[:3]:
    print(f'  id={item[\"id\"]} q={item[\"question_text\"][:50]} hits={item[\"hit_count\"]}')
if not d.get('items'):
    print('  (empty)')
"

# Get first unanswered ID
UQ_ID=$(echo "$UNANSWERED" | python3 -c "
import sys, json
items = json.load(sys.stdin).get('items', [])
print(items[0]['id'] if items else '')
")

if [ -z "$UQ_ID" ]; then
    echo "No unanswered questions found. Creating a test conversation first..."
    # Create a conversation to generate an unanswered question
    STUDENT_TOKEN=$(curl -s -X POST "$BASE/auth/login" \
      -H 'Content-Type: application/json' \
      -d '{"staff_id":"4125150001","password":"4125150001"}' \
      | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
    
    CONV=$(curl -s -X POST "$BASE/conversations" \
      -H "Authorization: Bearer $STUDENT_TOKEN" \
      -H 'Content-Type: application/json' \
      -d '{"title":"smoke-draft-test"}')
    CONV_ID=$(echo "$CONV" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
    echo "created conv: $CONV_ID"
    
    # Send a question that might generate unanswered
    curl -s -X POST "$BASE/chat/send" \
      -H "Authorization: Bearer $STUDENT_TOKEN" \
      -H 'Content-Type: application/json' \
      -d "{\"conv_id\":$CONV_ID,\"content\":\"实验室安全培训什么时候开始？\"}" > /dev/null 2>&1
    sleep 5
    
    # Check unanswered again
    UNANSWERED=$(curl -s "$BASE/v1/knowledge/unanswered-top?limit=3" \
      -H "Authorization: Bearer $TOKEN")
    UQ_ID=$(echo "$UNANSWERED" | python3 -c "
import sys, json
items = json.load(sys.stdin).get('items', [])
print(items[0]['id'] if items else '')
")
fi

if [ -n "$UQ_ID" ]; then
    echo ""
    echo "=== Testing draft submission with unanswered_question_id=$UQ_ID ==="
    RESULT=$(curl -s -w "\n%{http_code}" -X POST "$BASE/v1/knowledge/drafts" \
      -H "Authorization: Bearer $TOKEN" \
      -H 'Content-Type: application/json' \
      -d "{\"unanswered_question_id\":$UQ_ID,\"raw_answer\":\"smoke-test: 实验室安全培训每学期初举行\",\"scope\":\"college\"}")
    
    HTTP_CODE=$(echo "$RESULT" | tail -1)
    BODY=$(echo "$RESULT" | sed '$d')
    
    echo "HTTP: $HTTP_CODE"
    echo "Response: $(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, ensure_ascii=False)[:500])" 2>/dev/null || echo "$BODY")"
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✅ PASS: Knowledge draft created"
    else
        echo "❌ FAIL: HTTP $HTTP_CODE"
    fi
else
    echo "⚠️ No unanswered question available. Cannot test draft."
fi
