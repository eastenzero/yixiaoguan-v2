#!/bin/bash
# Directly call Dify v1/chat-messages with the RAG question + dump full SSE trace.
APP_KEY="app-0zqUgdeR2dQ1vJkPeoitneQ6"

curl -sS -N -X POST http://127.0.0.1:8088/v1/chat-messages \
  -H "Authorization: Bearer ${APP_KEY}" \
  -H 'Content-Type: application/json' \
  --max-time 30 \
  -d '{"inputs":{"college_name":"医药管理学院","campus":"泰安校区","class_name":"测试班"},"query":"宿舍电费怎么交？支付方式有哪些？","response_mode":"streaming","user":"trace-test","conversation_id":""}' \
  > /tmp/trace-stream.txt 2>&1

echo "=== FULL RAW STREAM ==="
cat /tmp/trace-stream.txt

echo
echo
echo "=== node lifecycle (started/finished/title) ==="
grep -oE '"event":"(node_started|node_finished|workflow_started|workflow_finished)"[^}]*"title":"[^"]*"[^}]*"node_type":"[^"]*"' /tmp/trace-stream.txt 2>/dev/null

echo
echo "=== retriever_resources ==="
grep -oE '"retriever_resources":\[[^]]*\]' /tmp/trace-stream.txt | head -c 2000

echo
echo "=== final answer ==="
grep -oE '"answer":"[^"]*"' /tmp/trace-stream.txt | tail -3
