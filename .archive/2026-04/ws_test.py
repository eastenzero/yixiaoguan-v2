import asyncio, json, websockets
async def test(token):
    async with websockets.connect(f"ws://localhost:8100/ws?token={token}") as ws:
        await ws.send(json.dumps({"type":"ping"}))
        resp = await asyncio.wait_for(ws.recv(), timeout=5)
        data = json.loads(resp)
        assert data["type"] == "pong", f"Expected pong, got {data}"
        print("WebSocket PASS: ping/pong works")
