#!/bin/bash
# Temporarily add debug logging to auth login to see what's received
ROUTER=/opt/yxg-v2/repo/services/gateway/app/routers/auth.py

# Backup
cp "$ROUTER" /tmp/auth.py.bak

# Add logging import and debug print
python3 << 'PATCH'
import re

with open("/opt/yxg-v2/repo/services/gateway/app/routers/auth.py", "r") as f:
    content = f.read()

# Add logging import if not present
if "import logging" not in content:
    content = "import logging\n_log = logging.getLogger(__name__)\n" + content

# Add debug line after the login function def
old = '    user = await authenticate_user(db, body.staff_id, body.password)'
new = '    _log.warning("LOGIN_DEBUG staff_id=%r password_len=%d first3=%r", body.staff_id, len(body.password), body.password[:3])\n    user = await authenticate_user(db, body.staff_id, body.password)'

content = content.replace(old, new)

with open("/opt/yxg-v2/repo/services/gateway/app/routers/auth.py", "w") as f:
    f.write(content)

print("Patched auth.py with debug logging")
PATCH

systemctl restart yxg-gateway
sleep 2
echo "Gateway restarted. Now try to login from browser, then run: journalctl -u yxg-gateway --since '1 min ago' --no-pager | grep LOGIN_DEBUG"
