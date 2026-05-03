#!/bin/bash
echo "=== HK Service Status ==="
echo "gateway: $(curl -so /dev/null -w '%{http_code}' http://127.0.0.1:8100/docs)"
echo "dify-api: $(curl -so /dev/null -w '%{http_code}' -H 'Authorization: Bearer app-0zqUgdeR2dQ1vJkPeoitneQ6' http://127.0.0.1:8088/v1/parameters)"
echo "student-h5: $(curl -sko /dev/null -w '%{http_code}' https://yxg.130814.xyz/)"
echo "teacher-h5: $(curl -sko /dev/null -w '%{http_code}' https://teacher.130814.xyz/)"
echo "dify-console: $(curl -sko /dev/null -w '%{http_code}' https://dify.130814.xyz/)"
echo "gateway-systemd: $(systemctl is-active yxg-gateway 2>/dev/null || echo unknown)"
echo "dify-containers: $(docker ps --format '{{.Names}}' 2>/dev/null | grep -cE 'api|worker|web|nginx')"
echo "db-backup-files: $(find /var/backups /root/backups /opt -maxdepth 3 -name '*.sql.gz' 2>/dev/null | wc -l)"
echo "backup-cron: $(crontab -l 2>/dev/null | grep -c backup)"

echo ""
echo "=== Quick RAG Test ==="
RESULT=$(curl -s -X POST 'http://127.0.0.1:8088/v1/chat-messages' \
  -H 'Authorization: Bearer app-0zqUgdeR2dQ1vJkPeoitneQ6' \
  -H 'Content-Type: application/json' \
  --max-time 60 \
  -d '{"inputs":{"college_name":"临床与基础医学院","campus":"济南校区","class_name":"临床2024-1班"},"query":"图书馆开放时间？","response_mode":"blocking","user":"status-check"}')

ANSWER=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer','')[:300])" 2>/dev/null)
SCORE=$(echo "$RESULT" | python3 -c "import sys,json; rr=json.load(sys.stdin).get('metadata',{}).get('retriever_resources',[]); print(f'{rr[0][\"score\"]:.4f} {rr[0][\"document_name\"][:50]}') if rr else print('no-retrieval')" 2>/dev/null)
echo "answer: $ANSWER"
echo "top-doc: $SCORE"
