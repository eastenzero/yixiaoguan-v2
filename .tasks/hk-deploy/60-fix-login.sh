#!/bin/bash
set -e

echo "=== 1. Restore auth.py (remove debug log) ==="
cp /tmp/auth.py.bak /opt/yxg-v2/repo/services/gateway/app/routers/auth.py
systemctl restart yxg-gateway
sleep 2
systemctl is-active yxg-gateway && echo "Gateway OK"

echo ""
echo "=== 2. Deploy fixed login page ==="
cp /tmp/deploy-r11/login.vue /opt/yxg-v2/repo/apps/teacher-app/src/pages/login/index.vue

cd /opt/yxg-v2/repo/apps/teacher-app
export NODE_OPTIONS="--max-old-space-size=4096"
npx uni build -p h5 2>&1 | tail -5

if [ -d "dist/build/h5" ]; then
  rm -rf /var/www/yxg-teacher/*
  cp -r dist/build/h5/* /var/www/yxg-teacher/
  echo "Teacher frontend deployed OK"
else
  echo "BUILD FAILED"
  exit 1
fi
