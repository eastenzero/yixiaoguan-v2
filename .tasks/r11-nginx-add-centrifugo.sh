#!/bin/bash
# 把 /centrifugo/ location 块插入到 yixiaoguan nginx 配置的两个 server block 中
# 使用 Python 改文件确保幂等

set -euo pipefail

NGINX_CONF=/etc/nginx/sites-enabled/yixiaoguan
BACKUP=/tmp/yixiaoguan-nginx.bak.$(date +%s)

sudo -n cp "$NGINX_CONF" "$BACKUP"
echo "[OK] backup at $BACKUP"

sudo -n python3 <<'PY'
import re

PATH = "/etc/nginx/sites-enabled/yixiaoguan"
with open(PATH, "r") as f:
    content = f.read()

# 如果已包含 centrifugo location，跳过
if "/centrifugo/" in content:
    print("[SKIP] /centrifugo/ already present, no changes")
    raise SystemExit(0)

CENTRIFUGO_BLOCK = """
    # Centrifugo WebSocket reverse proxy (R11)
    location /centrifugo/ {
        proxy_pass http://127.0.0.1:8000/;
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

# 把 CENTRIFUGO_BLOCK 插入到每个 location /ws/ {} 块的下一行（保留缩进结构）
# 策略：找到 location /ws/ 后的第一个 } （server block 末尾）的前一行
# 用 regex 找 "    location /ws/ { ... }" 整块（multi-line），然后在它后插入 centrifugo

# 简单做法：每个 "    location /ws/ {" 之后，找到对应的 "    }"（4 空格 + } + 换行），
# 在那个 } 后追加 CENTRIFUGO_BLOCK

pattern = re.compile(r'(    location /ws/ \{[\s\S]*?\n    \}\n)', re.MULTILINE)
matches = pattern.findall(content)
if len(matches) < 2:
    print(f"[ERROR] expected >=2 /ws/ blocks, found {len(matches)}; abort")
    raise SystemExit(1)

new_content = pattern.sub(r'\1' + CENTRIFUGO_BLOCK, content)
with open(PATH, "w") as f:
    f.write(new_content)
print(f"[OK] inserted {len(matches)} centrifugo location blocks")
PY

echo "---nginx -t---"
sudo -n nginx -t 2>&1
echo "---reload---"
sudo -n systemctl reload nginx
echo "[OK] nginx reloaded"
echo "---verify centrifugo ws path returns 400 (centrifugo expects WS upgrade)---"
curl -s -o /dev/null -w "port 80 /centrifugo/ HTTP %{http_code}\n" http://localhost/centrifugo/connection/websocket
curl -s -o /dev/null -w "port 81 /centrifugo/ HTTP %{http_code}\n" http://localhost:81/centrifugo/connection/websocket
