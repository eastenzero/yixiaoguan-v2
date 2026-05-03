#!/bin/bash
# 测试 WebSocket 连通性

# 1) 获取学生 token
TOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "token: ${TOKEN:0:20}..."

# 2) 测试直连 gateway ws（绕过 nginx）
echo ""
echo "=== Direct WS (127.0.0.1:8100) ==="
python3 -c "
import asyncio, websockets, json

async def test():
    uri = 'ws://127.0.0.1:8100/ws?token=$TOKEN'
    try:
        async with websockets.connect(uri, close_timeout=3) as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(resp)
            if msg.get('type') == 'pong':
                print('PASS: direct WS ping/pong OK')
            else:
                print(f'FAIL: unexpected response: {msg}')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>&1

# 3) 测试通过 nginx ws（学生端域名）
echo ""
echo "=== Nginx WS (yxg.130814.xyz) ==="
python3 -c "
import asyncio, websockets, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def test():
    uri = 'wss://yxg.130814.xyz/ws?token=$TOKEN'
    try:
        async with websockets.connect(uri, ssl=ctx, close_timeout=3) as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(resp)
            if msg.get('type') == 'pong':
                print('PASS: nginx WS ping/pong OK')
            else:
                print(f'FAIL: unexpected response: {msg}')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>&1

# 4) 测试教师端域名
echo ""
echo "=== Nginx WS (teacher.130814.xyz) ==="
TEACHER_TOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

python3 -c "
import asyncio, websockets, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def test():
    uri = 'wss://teacher.130814.xyz/ws?token=$TEACHER_TOKEN'
    try:
        async with websockets.connect(uri, ssl=ctx, close_timeout=3) as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(resp)
            if msg.get('type') == 'pong':
                print('PASS: teacher nginx WS ping/pong OK')
            else:
                print(f'FAIL: unexpected response: {msg}')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>&1
