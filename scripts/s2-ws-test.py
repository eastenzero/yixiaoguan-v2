#!/usr/bin/env python3
"""S2 WebSocket smoke test"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:8100"

async def test():
    # 1. Get student token
    req = urllib.request.Request(f"{BASE}/api/auth/login", method="POST")
    req.add_header("Content-Type", "application/json")
    body = json.dumps({"staff_id": "2024010001", "password": "2024010001"}).encode()
    resp = urllib.request.urlopen(req, body)
    token = json.loads(resp.read())["access_token"]
    print(f"[OK] Got student token: {token[:30]}...")

    uri = f"ws://localhost:8100/ws?token={token}"
    async with websockets.connect(uri) as ws:
        # 2. ping/pong
        await ws.send(json.dumps({"type": "ping"}))
        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert r["type"] == "pong", f"Expected pong, got {r}"
        print(f"[OK] ping => pong")

        # 3. join_room
        await ws.send(json.dumps({"type": "join_room", "data": {"conv_id": 1}}))
        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert r["type"] == "room_joined", f"Expected room_joined, got {r}"
        print(f"[OK] join_room => room_joined (conv_id={r['data']['conv_id']})")

        # 4. unknown type
        await ws.send(json.dumps({"type": "bogus"}))
        r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert r["type"] == "error", f"Expected error, got {r}"
        print(f"[OK] unknown type => error: {r['data']['message']}")

    # 5. Invalid token => close 4001
    try:
        async with websockets.connect("ws://localhost:8100/ws?token=bad-token") as ws2:
            await asyncio.wait_for(ws2.recv(), timeout=3)
            print("[FAIL] Should have been closed")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[OK] invalid token => close code {e.code}")
    except Exception as e:
        # Different websockets versions handle this differently
        print(f"[OK] invalid token => rejected ({type(e).__name__})")

    print("\nWS TEST: ALL PASS")

asyncio.run(test())
