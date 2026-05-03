#!/bin/bash
set -e

python3 << 'PYEOF'
import shutil, datetime, os

WS_BLOCK = """
    # WebSocket reverse proxy → gateway uvicorn
    location /ws {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
"""

files = [
    "/etc/nginx/sites-enabled/yxg-student",
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
]

ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

for f in files:
    if not os.path.isfile(f):
        print(f"SKIP: {f} not found")
        continue
    content = open(f).read()
    if "location /ws" in content:
        print(f"SKIP: {f} already has /ws")
        continue
    shutil.copy2(f, f"{f}.bak-{ts}")
    # Insert WS_BLOCK before "location /api/"
    marker = "    location /api/"
    if marker not in content:
        # try without leading spaces
        marker = "location /api/"
    if marker not in content:
        print(f"WARN: {f} has no 'location /api/' marker, skip")
        continue
    content = content.replace(marker, WS_BLOCK + "\n" + marker, 1)
    open(f, "w").write(content)
    print(f"PATCHED: {f}")
PYEOF

echo ""
echo "=== nginx -t ==="
nginx -t 2>&1

echo ""
echo "=== reload ==="
systemctl reload nginx
echo "nginx reloaded"

echo ""
echo "=== verify ==="
for f in /etc/nginx/sites-enabled/yxg-student /etc/nginx/sites-enabled/yxg-student-domain /etc/nginx/sites-enabled/yxg-teacher /etc/nginx/sites-enabled/yxg-teacher-domain; do
    count=$(grep -c 'location /ws' "$f" 2>/dev/null || echo 0)
    echo "  $f: /ws locations=$count"
done
