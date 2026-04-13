#!/bin/bash
set -e
BASE=http://localhost:8100

echo '=== Step 1: Student login ==='
STU_RESP=$(curl -s -X POST $BASE/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"2024010001","password":"2024010001"}')
echo "$STU_RESP"
STU_TOKEN=$(echo "$STU_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "TOKEN: ${STU_TOKEN:0:30}..."

echo ''
echo '=== Step 2: GET /api/auth/me ==='
curl -s $BASE/api/auth/me -H "Authorization: Bearer $STU_TOKEN"
echo ''

echo ''
echo '=== Step 2b: Wrong password => 401 ==='
curl -s -o /dev/null -w 'HTTP %{http_code}' -X POST $BASE/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"2024010001","password":"wrongpwd"}'
echo ''

echo ''
echo '=== Step 3: Create conversation ==='
CONV_RESP=$(curl -s -X POST $BASE/api/conversations \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"S2验收测试"}')
echo "$CONV_RESP"
CONV_ID=$(echo "$CONV_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "CONV_ID: $CONV_ID"

echo ''
echo '=== Step 4: Student send message ==='
curl -s -X POST $BASE/api/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content":"你好，请问怎么办理校园卡？"}'
echo ''

echo ''
echo '=== Step 5: GET messages (expect 2) ==='
curl -s "$BASE/api/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $STU_TOKEN" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print('total:', data['total'])
for m in data['items']:
    print('  [%s] %s' % (m['sender_type'], m['content'][:40]))
"

echo ''
echo '=== Step 6: Escalate ==='
curl -s -X POST $BASE/api/conversations/$CONV_ID/escalate \
  -H "Authorization: Bearer $STU_TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print('status:', d['status'])
"

echo ''
echo '=== Step 7: Teacher login ==='
TCH_RESP=$(curl -s -X POST $BASE/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"T001","password":"liangshufeng"}')
TCH_TOKEN=$(echo "$TCH_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "TEACHER TOKEN: ${TCH_TOKEN:0:30}..."

echo ''
echo '=== Step 8: Teacher list conversations ==='
curl -s "$BASE/api/conversations" \
  -H "Authorization: Bearer $TCH_TOKEN" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print('total:', data['total'])
for c in data['items']:
    print('  conv_id=%s status=%s title=%s' % (c['id'], c['status'], c['title']))
"

echo ''
echo '=== Step 9: Teacher accept ==='
curl -s -X POST $BASE/api/conversations/$CONV_ID/accept \
  -H "Authorization: Bearer $TCH_TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print('status:', d['status'], 'teacher_id:', d.get('teacher_id'))
"

echo ''
echo '=== Step 10: Teacher send message ==='
curl -s -X POST $BASE/api/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $TCH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content":"你好，校园卡在行政楼一楼办理"}' | python3 -c "
import sys,json
d = json.load(sys.stdin)
print('sender_type:', d['sender_type'], 'content:', d['content'][:30])
"

echo ''
echo '=== Step 11: Teacher resolve ==='
curl -s -X POST $BASE/api/conversations/$CONV_ID/resolve \
  -H "Authorization: Bearer $TCH_TOKEN" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print('status:', d['status'], 'resolved_at:', d.get('resolved_at'))
"

echo ''
echo '=== Step 12: Final messages (expect 6) ==='
curl -s "$BASE/api/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $STU_TOKEN" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print('total:', data['total'])
for i, m in enumerate(data['items'], 1):
    print('  %d. [%s] %s' % (i, m['sender_type'], m['content'][:50]))
"

echo ''
echo '=== Step 13: Invalid transition (escalate from resolved => 409) ==='
curl -s -o /dev/null -w 'HTTP %{http_code}' -X POST $BASE/api/conversations/$CONV_ID/escalate \
  -H "Authorization: Bearer $STU_TOKEN"
echo ''

echo ''
echo '=== DONE ==='
