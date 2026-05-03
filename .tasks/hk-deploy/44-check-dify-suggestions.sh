#!/bin/bash
# 检查 Dify 回答后是否返回 suggested_questions (message_end_chat 事件)
source /home/easten/dev/yixiaoguan-v2/services/gateway/.env 2>/dev/null

DIFY_URL="${DIFY_API_URL:-http://127.0.0.1:8101/v1}"
DIFY_KEY="${DIFY_API_KEY}"

echo "Dify URL: $DIFY_URL"
echo "Dify Key: ${DIFY_KEY:0:10}..."
echo ""

# 发送一个测试问题，看返回的 SSE 事件
curl -sN -X POST "$DIFY_URL/chat-messages" \
  -H "Authorization: Bearer $DIFY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"college_name": "医药管理学院", "campus": "", "class_name": "公共事业管理2025-1班"},
    "query": "奖学金怎么申请？",
    "response_mode": "streaming",
    "user": "test-suggestion-check"
  }' 2>/dev/null | while IFS= read -r line; do
    # 只打印含 suggested 或 message_end 的事件
    if echo "$line" | grep -q 'message_end\|suggested\|message_end_chat'; then
      echo "$line"
    fi
  done | head -20

echo ""
echo "=== done ==="
