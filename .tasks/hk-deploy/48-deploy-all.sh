#!/bin/bash
set -e
REPO=/opt/yxg-v2/repo

echo "====== 1. Deploy Gateway (R10 + WS fix) ======"

# Backup current files
cp "$REPO/services/gateway/app/services/dify_client.py" /tmp/dify_client.py.bak
cp "$REPO/services/gateway/app/routers/chat.py" /tmp/chat.py.bak

# Copy updated files
cp /tmp/deploy-r10/dify_client.py "$REPO/services/gateway/app/services/dify_client.py"
cp /tmp/deploy-r10/chat.py "$REPO/services/gateway/app/routers/chat.py"

echo "Gateway files updated"

# Restart gateway
systemctl restart yixiaoguan-gateway
sleep 3
systemctl is-active yixiaoguan-gateway && echo "Gateway: OK" || echo "Gateway: FAILED"

echo ""
echo "====== 2. Deploy Student Frontend (R10 UI) ======"

# Copy updated frontend files
cp /tmp/deploy-r10/sse.ts "$REPO/apps/student-app/src/utils/sse.ts"
cp /tmp/deploy-r10/chat-index.vue "$REPO/apps/student-app/src/pages/chat/index.vue"

echo "Frontend source updated in repo"

# Build student app
cd "$REPO/apps/student-app"
export NODE_OPTIONS="--max-old-space-size=4096"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install --legacy-peer-deps 2>&1 | tail -3
fi

echo "Building student app..."
npx uni build -p h5 2>&1 | tail -10

# Deploy built files
if [ -d "dist/build/h5" ]; then
  rm -rf /var/www/yxg-student/*
  cp -r dist/build/h5/* /var/www/yxg-student/
  echo "Student frontend deployed to /var/www/yxg-student/"
else
  echo "ERROR: Build output not found at dist/build/h5"
  ls -la dist/ 2>/dev/null || echo "No dist/ directory"
fi

echo ""
echo "====== 3. Domain migration: 130814.xyz → xiaoguan.site ======"

# Update nginx server_name in domain configs
python3 << 'PYEOF'
import os, datetime

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

ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

for f in files:
    if not os.path.isfile(f):
        print(f"SKIP: {f}")
        continue
    content = open(f).read()
    changed = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changed = True
    if changed:
        # Don't put backup in sites-enabled!
        import shutil
        shutil.copy2(f, f"/tmp/{os.path.basename(f)}.bak-{ts}")
        open(f, "w").write(content)
        print(f"PATCHED: {f}")
    else:
        print(f"NO CHANGE: {f}")
PYEOF

echo ""
echo "--- Requesting SSL cert for new domains ---"
# Request new Let's Encrypt cert for all three domains
certbot certonly --nginx \
  -d yxg.xiaoguan.site \
  -d teacher.xiaoguan.site \
  -d dify.xiaoguan.site \
  --non-interactive --agree-tos \
  --email easten@xiaoguan.site \
  2>&1 | tail -10

echo ""
echo "--- Update SSL cert paths in nginx ---"
python3 << 'PYEOF2'
import os

files = [
    "/etc/nginx/sites-enabled/yxg-student-domain",
    "/etc/nginx/sites-enabled/yxg-teacher-domain",
    "/etc/nginx/sites-enabled/yxg-dify-domain",
]

old_cert_path = "/etc/letsencrypt/live/yxg.130814.xyz"
# Check what certbot created
new_candidates = [
    "/etc/letsencrypt/live/yxg.xiaoguan.site",
    "/etc/letsencrypt/live/yxg.xiaoguan.site-0001",
]
new_cert_path = None
for p in new_candidates:
    if os.path.isdir(p):
        new_cert_path = p
        break

if not new_cert_path:
    print(f"WARNING: new cert dir not found, keeping old path")
    print(f"Checked: {new_candidates}")
    # list what's available
    live_dir = "/etc/letsencrypt/live/"
    if os.path.isdir(live_dir):
        print(f"Available: {os.listdir(live_dir)}")
else:
    print(f"New cert path: {new_cert_path}")
    for f in files:
        if not os.path.isfile(f):
            continue
        content = open(f).read()
        if old_cert_path in content:
            content = content.replace(old_cert_path, new_cert_path)
            open(f, "w").write(content)
            print(f"Updated cert path in: {f}")
PYEOF2

echo ""
echo "--- nginx test & reload ---"
nginx -t 2>&1
systemctl reload nginx
echo "nginx reloaded"

echo ""
echo "====== 4. Verify ======"
echo "--- server_name ---"
grep 'server_name' /etc/nginx/sites-enabled/yxg-*domain* 2>/dev/null

echo ""
echo "--- SSL cert ---"
for d in yxg.xiaoguan.site teacher.xiaoguan.site; do
  echo -n "$d: "
  curl -sk --max-time 5 "https://$d/health" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "unreachable"
done

echo ""
echo "--- Gateway health ---"
curl -s http://127.0.0.1:8100/health | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null

echo ""
echo "====== DONE ======"
