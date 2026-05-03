#!/bin/bash
# Direct Dify API test on 165
DIFY_KEY="app-WyMuIbnBB351RxqitjbncX6A"
DIFY_URL="http://localhost:3000/v1"

echo "=== test dify /parameters ==="
curl -s "$DIFY_URL/parameters" -H "Authorization: Bearer $DIFY_KEY" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:500])'

echo
echo "=== test dify /chat-messages (greeting) ==="
curl -sN -X POST "$DIFY_URL/chat-messages" \
  -H "Authorization: Bearer $DIFY_KEY" \
  -H 'Content-Type: application/json' \
  --max-time 30 \
  -d '{"inputs":{},"query":"你好","response_mode":"streaming","user":"test-165"}' \
  > /tmp/dify165-greeting.txt 2>&1
head -20 /tmp/dify165-greeting.txt

echo
echo "=== test dify /chat-messages (dianfei) ==="
curl -sN -X POST "$DIFY_URL/chat-messages" \
  -H "Authorization: Bearer $DIFY_KEY" \
  -H 'Content-Type: application/json' \
  --max-time 60 \
  -d '{"inputs":{"college_name":"临床与基础医学院","campus":"济南校区","class_name":"临床2024-1班"},"query":"宿舍电费怎么交？支付方式有哪些？","response_mode":"streaming","user":"test-165"}' \
  > /tmp/dify165-dianfei.txt 2>&1

echo "--- raw dianfei ---"
head -30 /tmp/dify165-dianfei.txt

echo
echo "--- retriever + answer ---"
python3 -c "
import json, re
raw = open('/tmp/dify165-dianfei.txt').read()
# extract answer
answers = []
for line in raw.split('\n'):
    if line.startswith('data: '):
        try:
            d = json.loads(line[6:])
            if d.get('event') == 'message':
                answers.append(d.get('answer',''))
            if d.get('event') == 'message_end':
                md = d.get('metadata',{})
                rr = md.get('retriever_resources',[])
                if rr:
                    print('retriever_resources:')
                    for i,r in enumerate(rr,1):
                        print(f'  #{i} score={r.get(\"score\",0):.4f} doc={r.get(\"document_name\",\"?\")[:50]}')
                        print(f'      content={r.get(\"content\",\"\")[:120]}')
        except: pass
ans = answers[-1] if answers else '(empty)'
print(f'answer: {ans[:500]}')
"
