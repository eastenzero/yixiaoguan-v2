#!/bin/bash
curl -s http://127.0.0.1:8100/openapi.json | python3 -c '
import sys, json
d = json.load(sys.stdin)
for path, ops in sorted(d.get("paths", {}).items()):
    methods = ", ".join(m.upper() for m in ops)
    print(f"{methods:10s} {path}")
'
