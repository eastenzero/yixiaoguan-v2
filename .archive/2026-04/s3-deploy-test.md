You are on 165 server. Deploy S3 changes and run smoke test.

## Task 1: Install dependencies and configure .env

1. cd ~/dev/yixiaoguan-v2/services/gateway
2. source ~/dev/yixiaoguan-v2/venv/bin/activate
3. pip install httpx-sse pyyaml
4. Update .env - append these 3 lines (use echo >> to append):
   dify_api_key=app-WyMuIbnBB351RxqitjbncX6A
   dify_global_dataset_id=ec072e85-ebb3-4f2a-a966-a21566b88995
   dify_dataset_api_key=dataset-XcnM3rGW1vBpBk9yQxXC5jCo
5. Verify: cat .env and confirm dify_api_key is set

## Task 2: Alembic migration for kb_entries table

1. cd ~/dev/yixiaoguan-v2/services/gateway
2. PYTHONPATH=. alembic revision --autogenerate -m "add kb_entries table"
3. PYTHONPATH=. alembic upgrade head
4. Verify: psql -U yxg -d yixiaoguan_v2 -c "SELECT column_name FROM information_schema.columns WHERE table_name='kb_entries';"

## Task 3: Restart service

1. pkill -f uvicorn || true
2. Clean old test data: PYTHONPATH=. python3 -c "import asyncio; from sqlalchemy import text; from app.database import async_engine; asyncio.run((lambda e: e.begin().__aenter__().then(None))())" || echo skip
3. cd ~/dev/yixiaoguan-v2/services/gateway
4. PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &
5. sleep 3
6. curl -s http://localhost:8100/health

## Task 4: Smoke test (10 steps)

Run ALL steps in order. Save tokens/IDs between steps.

Step 1: Health check
  curl -s http://localhost:8100/health
  Expect: dify check = ok (or at least not error about bearer)

Step 2: Student login
  curl -s -X POST http://localhost:8100/api/auth/login -H "Content-Type: application/json" -d '{"staff_id":"2024010001","password":"2024010001"}'
  Save the access_token as STUDENT_TOKEN

Step 3: Create conversation
  curl -s -X POST http://localhost:8100/api/conversations -H "Authorization: Bearer $STUDENT_TOKEN" -H "Content-Type: application/json" -d '{"title":"AI chat test"}'
  Save the conversation id as CONV_ID

Step 4: Send message to AI (SSE stream) - THIS IS THE KEY TEST
  curl -N -X POST http://localhost:8100/api/chat/send -H "Authorization: Bearer $STUDENT_TOKEN" -H "Content-Type: application/json" -d "{\"conv_id\":$CONV_ID,\"content\":\"hello\"}"
  Expect: SSE stream with event:message tokens, event:message_end, event:done

Step 5: Verify AI message saved in DB
  curl -s http://localhost:8100/api/conversations/$CONV_ID/messages -H "Authorization: Bearer $STUDENT_TOKEN"
  Expect: at least 3 messages (system + student + ai)

Step 6: Verify dify_conversation_id saved
  curl -s http://localhost:8100/api/conversations/$CONV_ID -H "Authorization: Bearer $STUDENT_TOKEN"
  Expect: dify_conversation_id field is non-empty

Step 7: Multi-turn conversation
  curl -N -X POST http://localhost:8100/api/chat/send -H "Authorization: Bearer $STUDENT_TOKEN" -H "Content-Type: application/json" -d "{\"conv_id\":$CONV_ID,\"content\":\"thanks\"}"
  Expect: AI responds with context awareness

Step 8: Test chitchat (new conv)
  Create new conv, then send: "who are you"
  Expect: AI mentions something about itself

Step 9: Test transfer to human
  Create new conv, then send: "transfer to human"

Step 10: Teacher serving path
  Use the first conv: escalate it, then teacher login (T001/liangshufeng), accept it.
  Then student sends via /api/chat/send - expect JSON response (not SSE)

Report each step: PASS/FAIL with key response data.
You have continue authorization. Execute directly.
