#!/bin/bash
set -e
REPO=/opt/yxg-v2/repo
SVC=yxg-gateway

echo "====== 1. Deploy Gateway (R10) ======"
cp "$REPO/services/gateway/app/services/dify_client.py" /tmp/dify_client.py.bak
cp "$REPO/services/gateway/app/routers/chat.py" /tmp/chat.py.bak
cp /tmp/deploy-r10/dify_client.py "$REPO/services/gateway/app/services/dify_client.py"
cp /tmp/deploy-r10/chat.py "$REPO/services/gateway/app/routers/chat.py"
echo "Gateway files updated"

systemctl restart $SVC
sleep 3
systemctl is-active $SVC && echo "Gateway: OK" || { echo "Gateway: FAILED"; journalctl -u $SVC --no-pager -n 20; exit 1; }

echo ""
echo "====== 2. Deploy Student Frontend (R10 UI) ======"
cp /tmp/deploy-r10/sse.ts "$REPO/apps/student-app/src/utils/sse.ts"
cp /tmp/deploy-r10/chat-index.vue "$REPO/apps/student-app/src/pages/chat/index.vue"
echo "Frontend source files updated"

cd "$REPO/apps/student-app"
export NODE_OPTIONS="--max-old-space-size=4096"

if [ ! -d "node_modules" ]; then
  echo "Installing deps..."
  npm install --legacy-peer-deps 2>&1 | tail -5
fi

echo "Building student app (H5)..."
npx uni build -p h5 2>&1 | tail -15

if [ -d "dist/build/h5" ]; then
  rm -rf /var/www/yxg-student/*
  cp -r dist/build/h5/* /var/www/yxg-student/
  echo "Student frontend deployed OK"
else
  echo "ERROR: build output missing"
  ls -la dist/ 2>/dev/null
  exit 1
fi

echo ""
echo "====== 3. Domain: 130814.xyz → xiaoguan.site ======"
python3 << 'PYEOF'
import os, shutil, datetime
ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
replacements = {
    "yxg.130814.xyz": "yxg.xiaoguan.site",
    "teacher.130814.xyz": "teacher.xiaoguan.site",
    "dify.130814.xyz": "dify.xiaoguan.site",
}
files = [
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
    "/etc/nginx/sites-enabled/yxg-dify-domain",
]
for f in files:
    if not os.path.isfile(f):
        print(f"SKIP: {f} not found")
        continue
    content = open(f).read()
    changed = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changed = True
    if changed:
        shutil.copy2(f, f"/tmp/{os.path.basename(f)}.bak-{ts}")
        open(f, "w").write(content)
        print(f"PATCHED: {f}")
    else:
        print(f"NO CHANGE: {f}")
PYEOF

echo ""
echo "--- Requesting SSL cert ---"
certbot certonly --nginx \
  -d yxg.xiaoguan.site \
  -d teacher.xiaoguan.site \
  -d dify.xiaoguan.site \
  --non-interactive --agree-tos \
  --email easten@xiaoguan.site \
  2>&1 | tail -15

echo ""
echo "--- Update cert paths ---"
python3 << 'PYEOF2'
import os
files = [
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
    "/etc/nginx/sites-enabled/yxg-dify-domain",
]
old_cert = "/etc/letsencrypt/live/yxg.130814.xyz"
# find new cert
new_cert = None
for candidate in ["/etc/letsencrypt/live/yxg.xiaoguan.site",
                  "/etc/letsencrypt/live/yxg.xiaoguan.site-0001"]:
    if os.path.isdir(candidate):
        new_cert = candidate
        break
if not new_cert:
    live = "/etc/letsencrypt/live/"
    avail = os.listdir(live) if os.path.isdir(live) else []
    print(f"WARNING: new cert not found. Available: {avail}")
else:
    print(f"New cert: {new_cert}")
    for f in files:
        if not os.path.isfile(f):
            continue
        content = open(f).read()
        if old_cert in content:
            content = content.replace(old_cert, new_cert)
            open(f, "w").write(content)
            print(f"Cert path updated: {f}")
PYEOF2

echo ""
echo "--- nginx test & reload ---"
nginx -t 2>&1
systemctl reload nginx
echo "nginx reloaded"

echo ""
echo "====== 4. Verify ======"
grep 'server_name' /etc/nginx/sites-enabled/yxg-*domain* 2>/dev/null
echo ""
for d in yxg.xiaoguan.site teacher.xiaoguan.site; do
  echo -n "$d → "
  curl -sk --max-time 5 "https://$d/" -o /dev/null -w "%{http_code}" 2>/dev/null
  echo ""
done
echo ""
curl -s http://127.0.0.1:8100/health 2>/dev/null | head -5
echo ""
echo "====== ALL DONE ======"
