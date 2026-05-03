#!/bin/bash
set -e
REPO=/opt/yxg-v2/repo
SVC=yxg-gateway

echo "====== 1. Deploy Gateway (R11 admin API) ======"
# Backup
cp "$REPO/services/gateway/app/main.py" /tmp/main.py.bak

# Copy updated backend files
cp /tmp/deploy-r11/admin_router.py "$REPO/services/gateway/app/routers/admin.py"
cp /tmp/deploy-r11/admin_schema.py "$REPO/services/gateway/app/schemas/admin.py"
cp /tmp/deploy-r11/main.py "$REPO/services/gateway/app/main.py"

echo "Gateway files updated"
systemctl restart $SVC
sleep 3
if systemctl is-active --quiet $SVC; then
  echo "Gateway: OK"
else
  echo "Gateway: FAILED"
  journalctl -u $SVC --no-pager -n 30
  exit 1
fi

echo ""
echo "====== 2. Deploy Teacher Frontend (R11 admin pages) ======"
# Copy updated frontend files
mkdir -p "$REPO/apps/teacher-app/src/pages/admin"
mkdir -p "$REPO/apps/teacher-app/src/api"
cp /tmp/deploy-r11/admin-api.ts "$REPO/apps/teacher-app/src/api/admin.ts"
cp /tmp/deploy-r11/admin-users.vue "$REPO/apps/teacher-app/src/pages/admin/users.vue"
cp /tmp/deploy-r11/admin-import.vue "$REPO/apps/teacher-app/src/pages/admin/import.vue"
cp /tmp/deploy-r11/pages.json "$REPO/apps/teacher-app/src/pages.json"
cp /tmp/deploy-r11/dashboard.vue "$REPO/apps/teacher-app/src/pages/dashboard/index.vue"

echo "Teacher frontend files updated"

cd "$REPO/apps/teacher-app"
export NODE_OPTIONS="--max-old-space-size=4096"

if [ ! -d "node_modules" ]; then
  echo "Installing deps..."
  npm install --legacy-peer-deps 2>&1 | tail -5
fi

echo "Building teacher app (H5)..."
npx uni build -p h5 2>&1 | tail -15

if [ -d "dist/build/h5" ]; then
  rm -rf /var/www/yxg-teacher/*
  cp -r dist/build/h5/* /var/www/yxg-teacher/
  echo "Teacher frontend deployed OK"
else
  echo "ERROR: build output missing"
  ls -la dist/ 2>/dev/null
  exit 1
fi

echo ""
echo "====== 3. Quick API test ======"
# Login as admin and test
TOKEN=$(curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"admin","password":"Admin@yxg2026"}' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  # Try alternate admin credentials
  TOKEN=$(curl -s http://127.0.0.1:8100/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"staff_id":"easten","password":"Easten@yxg2026"}' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
fi

if [ -n "$TOKEN" ]; then
  echo "Admin login: OK"
  echo "Testing GET /api/admin/users..."
  curl -s http://127.0.0.1:8100/api/admin/users?size=3 \
    -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  total={d[\"total\"]}, showing={len(d[\"items\"])} items')
for u in d['items']:
    print(f'  {u[\"staff_id\"]} | {u[\"name\"]} | {u[\"role\"]}')
" 2>/dev/null
else
  echo "WARN: No admin account found, skipping API test"
fi

echo ""
echo "====== DONE ======"
