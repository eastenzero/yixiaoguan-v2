You are on 165 server at ~/dev/yixiaoguan-v2. A datetime timezone bug was just fixed. Re-run the S2 smoke test.

Step 1: Setup
- pkill -f uvicorn || true
- cd ~/dev/yixiaoguan-v2/services/gateway
- source ~/dev/yixiaoguan-v2/venv/bin/activate
- Clean old test data: PYTHONPATH=. python3 -c 'import asyncio; from sqlalchemy import text; from app.database import async_engine; asyncio.run((async lambda: (await (c:=async_engine.begin()).__aenter__(), await c.execute(text(" DELETE FROM messages\)), await c.execute(text(\DELETE FROM conversations\)), await c.__aexit__(None,None,None)))())' || echo cleanup-skipped
- Start service: PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &
- sleep 3
- Verify: curl -s http://localhost:8100/health

Step 2: Run ALL 13 curl smoke test steps, saving JWT tokens and conv_id between steps:
1. Student login: POST /api/auth/login body={staff_id:2024010001,password:2024010001}
2. GET /api/auth/me with student token
3. POST /api/conversations body={title:test conv}
4. POST /api/conversations/{conv_id}/messages body={content:hello}
5. GET /api/conversations/{conv_id}/messages (expect 2 msgs)
6. POST /api/conversations/{conv_id}/escalate (expect pending_teacher)
7. Teacher login: POST /api/auth/login body={staff_id:T001,password:liangshufeng}
8. GET /api/conversations with teacher token
9. POST /api/conversations/{conv_id}/accept with teacher token
10. POST /api/conversations/{conv_id}/messages with teacher token body={content:answer}
11. POST /api/conversations/{conv_id}/resolve with teacher token
12. GET /api/conversations/{conv_id}/messages (expect 6+ msgs)
13. WebSocket test if wscat is available

You have continue authorization. Execute directly without asking. Report pass/fail for each step.
