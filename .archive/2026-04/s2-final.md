You are on 165 server. Two fixes were applied to yixiaoguan-v2:
1. datetime timezone: now uses datetime.now() (local time) matching PG func.now()
2. WebSocket test was skipped last time

Your tasks:

Task A: Restart service and verify timezone fix
- pkill -f uvicorn || true
- cd ~/dev/yixiaoguan-v2/services/gateway
- source ~/dev/yixiaoguan-v2/venv/bin/activate
- Clean old test data with this Python script:
  PYTHONPATH=. python3 -c "import asyncio; from sqlalchemy import text; from app.database import async_engine; asyncio.run((lambda: (async_engine.begin().__aenter__().then(lambda c: c.execute(text('DELETE FROM messages')).then(lambda _: c.execute(text('DELETE FROM conversations'))))))())" || echo cleanup-skipped
- Start: PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &
- sleep 3
- Verify health: curl -s http://localhost:8100/health

Then run a quick 3-step test to verify timezone consistency:
1. Login student: POST /api/auth/login with body {"staff_id":"2024010001","password":"2024010001"}
2. Create conv: POST /api/conversations with body {"title":"tz-test"}
3. Send a message, then escalate, then GET /api/conversations/{id} - verify created_at and updated_at are in the SAME timezone (both should show similar hour values, no 8-hour gap)

Task B: WebSocket ping/pong test
- Install websockets in the venv: pip install websockets
- Write a Python test file ~/dev/yixiaoguan-v2/ws_test.py with content:
```python
import asyncio, json, websockets
async def test(token):
    async with websockets.connect(f"ws://localhost:8100/ws?token={token}") as ws:
        await ws.send(json.dumps({"type":"ping"}))
        resp = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(resp)
        assert data["type"] == "pong", f"Expected pong, got {data}"
        print("WebSocket PASS: ping/pong works")
```
- Get the student token from Task A step 1, then run: PYTHONPATH=services/gateway python3 -c "import asyncio; from ws_test import test; asyncio.run(test('TOKEN_HERE'))"

Report results for both tasks. You have continue authorization. Execute directly.
