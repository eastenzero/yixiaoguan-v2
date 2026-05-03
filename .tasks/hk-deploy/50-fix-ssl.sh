#!/bin/bash
set -e

echo "=== Step 1: Revert cert paths to old cert (still valid) ==="
# Domain names already updated to xiaoguan.site, just fix cert paths back to old
python3 << 'PYEOF'
import os
files = [
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
    "/etc/nginx/sites-enabled/yxg-dify-domain",
]
# The new domain is already in server_name, but cert path was wrongly updated
# Ensure cert path points to existing old cert
for f in files:
    if not os.path.isfile(f):
        continue
    content = open(f).read()
    # Make sure cert path is the old one that exists
    if "yxg.xiaoguan.site/fullchain" in content:
        content = content.replace("yxg.xiaoguan.site/fullchain", "yxg.130814.xyz/fullchain")
        content = content.replace("yxg.xiaoguan.site/privkey", "yxg.130814.xyz/privkey")
        open(f, "w").write(content)
        print(f"Reverted cert path: {f}")
    else:
        print(f"OK (already using old cert): {f}")
PYEOF

echo ""
echo "=== Step 2: Test and reload nginx ==="
nginx -t 2>&1
systemctl reload nginx
echo "nginx reloaded with old cert + new domain names"

echo ""
echo "=== Step 3: Request new SSL cert via certbot ==="
certbot certonly --nginx \
  -d yxg.xiaoguan.site \
  -d teacher.xiaoguan.site \
  -d dify.xiaoguan.site \
  --non-interactive --agree-tos \
  --email easten@xiaoguan.site \
  2>&1 | tail -15

echo ""
echo "=== Step 4: Update nginx to use new cert ==="
python3 << 'PYEOF2'
import os
files = [
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
    "/etc/nginx/sites-enabled/yxg-dify-domain",
]
# find new cert
new_cert = None
for c in ["/etc/letsencrypt/live/yxg.xiaoguan.site",
          "/etc/letsencrypt/live/yxg.xiaoguan.site-0001",
          "/etc/letsencrypt/live/xiaoguan.site"]:
    if os.path.isdir(c):
        new_cert = c
        break

if not new_cert:
    live = "/etc/letsencrypt/live/"
    avail = os.listdir(live) if os.path.isdir(live) else []
    print(f"FAIL: No new cert found. Available: {avail}")
    print("Keeping old cert (still works, just domain mismatch warning)")
else:
    print(f"New cert: {new_cert}")
    for f in files:
        if not os.path.isfile(f):
            continue
        content = open(f).read()
        if "/etc/letsencrypt/live/yxg.130814.xyz" in content:
            content = content.replace("/etc/letsencrypt/live/yxg.130814.xyz", new_cert)
            open(f, "w").write(content)
            print(f"Updated: {f}")

PYEOF2

echo ""
echo "=== Step 5: Final nginx test & reload ==="
nginx -t 2>&1
systemctl reload nginx
echo "DONE"

echo ""
echo "=== Verify ==="
grep 'server_name\|ssl_certificate ' /etc/nginx/sites-enabled/yxg-*domain* 2>/dev/null
echo ""
for d in yxg.xiaoguan.site teacher.xiaoguan.site; do
  echo -n "https://$d → "
  CODE=$(curl -sk --max-time 5 -o /dev/null -w "%{http_code}" "https://$d/" 2>/dev/null)
  echo "$CODE"
done
