#!/usr/bin/env bash
# Step C-prep: 装 node + 跑 npm install + build:h5
set -euo pipefail

# 1. install node 22 LTS via NodeSource
if ! command -v node >/dev/null; then
    echo "[*] installing node 22 LTS"
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
else
    echo "[*] node already installed: $(node --version)"
fi
node --version
npm --version

# 2. enable pnpm/corepack (faster install)
corepack enable 2>/dev/null || true

# 3. build student-app
echo ""
echo "==== building student-app ===="
cd /opt/yxg-v2/repo/apps/student-app
[[ -d node_modules ]] || npm install --no-audit --no-fund 2>&1 | tail -10
npm run build:h5 2>&1 | tail -15
ls -la dist/build/h5/ | head -10
echo "[*] student dist size: $(du -sh dist/build/h5/ | cut -f1)"

# 4. build teacher-app
echo ""
echo "==== building teacher-app ===="
cd /opt/yxg-v2/repo/apps/teacher-app
[[ -d node_modules ]] || npm install --no-audit --no-fund 2>&1 | tail -10
npm run build:h5 2>&1 | tail -15
ls -la dist/build/h5/ | head -10
echo "[*] teacher dist size: $(du -sh dist/build/h5/ | cut -f1)"

# 5. 部署 dist 到 /var/www
mkdir -p /var/www/yxg-student /var/www/yxg-teacher
rm -rf /var/www/yxg-student/* /var/www/yxg-teacher/*
cp -r /opt/yxg-v2/repo/apps/student-app/dist/build/h5/* /var/www/yxg-student/
cp -r /opt/yxg-v2/repo/apps/teacher-app/dist/build/h5/* /var/www/yxg-teacher/

ls -la /var/www/yxg-student/ | head -5
ls -la /var/www/yxg-teacher/ | head -5

echo ""
echo "[OK] Step C-prep complete (h5 built + deployed to /var/www/yxg-{student,teacher})"
