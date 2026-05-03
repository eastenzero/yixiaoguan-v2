#!/bin/bash
source /home/easten/dev/yixiaoguan-v2/services/gateway/.env 2>/dev/null

DIFY_URL="${DIFY_API_URL:-http://127.0.0.1:8101/v1}"
DIFY_KEY="${DIFY_API_KEY}"

# 打印所有 SSE 事件（不过滤），但超时 30s
timeout 30 curl -sN -X POST "$DIFY_URL/chat-messages" \
  -H "Authorization: Bearer $DIFY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"college_name": "医药管理学院", "campus": "", "class_name": "公共事业管理2025-1班"},
    "query": "奖学金怎么申请",
    "response_mode": "streaming",
    "user": "test-suggestion-check"
  }' 2>/dev/null | grep -o '"event":"[^"]*"' | sort | uniq -c | sort -rn

echo ""
echo "--- full message_end event ---"
timeout 30 curl -sN -X POST "$DIFY_URL/chat-messages" \
  -H "Authorization: Bearer $DIFY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"college_name": "医药管理学院", "campus": "", "class_name": "公共事业管理2025-1班"},
    "query": "图书馆开放时间",
    "response_mode": "streaming",
    "user": "test-suggestion-check-2"
  }' 2>/dev/null | grep 'message_end' | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('data:'):
        line = line[5:].strip()
    try:
        d = json.loads(line)
        print(json.dumps(d, indent=2, ensure_ascii=False))
    except:
        print(line)
" 2>/dev/null
