#!/usr/bin/env bash
# Read-only health probe for the 165 server. Safe to run repeatedly.
set -u

PSQL_BIN="$(command -v psql || ls /usr/lib/postgresql/*/bin/psql 2>/dev/null | head -1)"
PSQL_CMD="PGPASSWORD=yxg_v2_pass ${PSQL_BIN:-psql} -h localhost -U yxg -d yixiaoguan_v2 -t -A"

section() { echo; echo "===$1==="; }

section HEALTH
curl -s -m 3 http://localhost:8100/health || echo "(curl failed)"
echo

section PORTS
ss -ltn | awk 'NR==1 || /:(8100|3000|5001|5432|6379)\b/'

section UVICORN
ps -ef | grep -E 'uvicorn|app.main' | grep -v grep | head -5 || echo "(no uvicorn)"

section DIFY-DOCKERS
if command -v docker >/dev/null 2>&1; then
    docker ps -a --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1 | head -30
else
    echo "(docker not in PATH; trying sudo)"
    sudo -n docker ps -a --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1 | head -30 || echo "(sudo docker also unavailable)"
fi
echo "--- dify compose dir ---"
ls -la /home/easten/dev/yixiaoguan-v2/deploy/dify 2>/dev/null | head -10 || echo "(no dify compose dir)"
ls -la /home/easten/dev/dify 2>/dev/null | head -5 || true

section ALEMBIC
if [ -d /home/easten/dev/yixiaoguan-v2/services/gateway ]; then
    cd /home/easten/dev/yixiaoguan-v2/services/gateway
    if [ -x ../../venv/bin/alembic ]; then
        PYTHONPATH=. ../../venv/bin/alembic current 2>&1 | head -5
    else
        echo "(no venv alembic)"
    fi
else
    echo "(gateway dir missing)"
fi

section ENV-KEYS
if [ -f /home/easten/dev/yixiaoguan-v2/services/gateway/.env ]; then
    awk -F= '/^(database_url|redis_url|dify_api_url|dify_api_key|dify_global_dataset_id|dify_dataset_api_key|jwt_secret)=/{print $1}' /home/easten/dev/yixiaoguan-v2/services/gateway/.env
else
    echo "(.env missing)"
fi

section KB-COUNT
eval "$PSQL_CMD -c \"select count(*) from kb_entries;\"" 2>&1 | head -3

section KB-SUGGESTIONS
eval "$PSQL_CMD -c \"select status, scope, count(*) from kb_suggestions group by 1,2 order by 1,2;\"" 2>&1 | head -20

section CHAT-ANALYTICS
eval "$PSQL_CMD -c \"select count(*) as total, count(*) filter (where used_kb=false) as no_kb_hit, max(created_at) as last_event from chat_analytics;\"" 2>&1 | head -5

section CONVERSATIONS
eval "$PSQL_CMD -c \"select status, count(*) from conversations group by 1 order by 1;\"" 2>&1 | head -10

section USERS
eval "$PSQL_CMD -c \"select role, count(*) from users group by 1 order by 1;\"" 2>&1 | head -10

section GATEWAY-LOG-TAIL
if [ -f /tmp/gw.log ]; then
    echo "size=$(wc -c </tmp/gw.log) bytes, last_modified=$(stat -c %y /tmp/gw.log 2>/dev/null || stat -f %Sm /tmp/gw.log)"
    tail -40 /tmp/gw.log
else
    echo "(no /tmp/gw.log)"
fi

section GIT
if [ -d /home/easten/dev/yixiaoguan-v2 ]; then
    cd /home/easten/dev/yixiaoguan-v2
    git log --oneline -n 8
    echo "--- status ---"
    git status -s | head -20
    echo "--- branch ---"
    git branch --show-current
else
    echo "(repo missing)"
fi

section DONE
