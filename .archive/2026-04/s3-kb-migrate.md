You are on 165 server. Run the KB migration script to import 731 KB entries from v1 into Dify knowledge base and PG kb_entries table.

## Steps

1. cd ~/dev/yixiaoguan-v2
2. source venv/bin/activate
3. Check if v1 KB entries exist: ls ~/dev/yixiaoguan/knowledge-base/entries/KB-*.md | wc -l
4. Run migration:
   PYTHONPATH=services/gateway python scripts/migrate_kb.py \
     --entries-dir ~/dev/yixiaoguan/knowledge-base/entries \
     --dataset-id ec072e85-ebb3-4f2a-a966-a21566b88995 \
     --api-key dataset-XcnM3rGW1vBpBk9yQxXC5jCo \
     --api-url http://localhost:3000/v1 \
     --output migrate_result.csv
5. After completion, check results:
   - tail -5 migrate_result.csv
   - grep -c "ok" migrate_result.csv
   - grep -c "error" migrate_result.csv
   - Check PG: psql -U yxg -d yixiaoguan_v2 -c "SELECT count(*) FROM kb_entries;"
   - Check non-null original_source: psql -U yxg -d yixiaoguan_v2 -c "SELECT count(*) FROM kb_entries WHERE original_source IS NOT NULL;"

6. Also restart uvicorn with the schema fix:
   pkill -f uvicorn || true
   cd services/gateway
   PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &

7. Verify schema fix: curl the conversation detail and check dify_conversation_id is in response

Report: total KB files, success count, error count, PG kb_entries count, original_source non-null rate.
You have continue authorization. Execute directly.
