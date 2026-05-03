import urllib.request
import json

API_KEY = "SuP3pEzTw638IOl0JNCycTTWQsgXnNSgw1xa8GPFvZc="
URL = "http://127.0.0.1:8000/api/publish"

body = json.dumps({"channel": "test", "data": {"hello": "world"}}).encode()
req = urllib.request.Request(URL, data=body, headers={
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
})
try:
    resp = urllib.request.urlopen(req)
    print(f"STATUS: {resp.status}")
    print(f"BODY: {resp.read().decode()}")
except Exception as e:
    print(f"ERROR: {e}")
    if hasattr(e, 'read'):
        print(f"RESPONSE: {e.read().decode()}")
