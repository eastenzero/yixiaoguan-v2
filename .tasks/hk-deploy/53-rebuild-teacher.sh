#!/bin/bash
set -e
REPO=/opt/yxg-v2/repo

echo "=== Copy fixed dashboard ==="
cp /tmp/deploy-r11/dashboard.vue "$REPO/apps/teacher-app/src/pages/dashboard/index.vue"

echo "=== Rebuild teacher app ==="
cd "$REPO/apps/teacher-app"
export NODE_OPTIONS="--max-old-space-size=4096"
npx uni build -p h5 2>&1 | tail -15

if [ -d "dist/build/h5" ]; then
  rm -rf /var/www/yxg-teacher/*
  cp -r dist/build/h5/* /var/www/yxg-teacher/
  echo "Teacher frontend deployed OK"
else
  echo "BUILD FAILED"
  exit 1
fi

echo ""
echo "=== Verify ==="
curl -sk --max-time 5 -o /dev/null -w "teacher.xiaoguan.site → %{http_code}\n" https://teacher.xiaoguan.site/
