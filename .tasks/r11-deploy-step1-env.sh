#!/bin/bash
# R11 deploy step 1: 生成 secret + 追加到 gateway .env + 创建 deploy/.env
# 在 165 上执行：bash ~/dev/yixiaoguan-v2/.tasks/r11-deploy-step1-env.sh

set -euo pipefail

cd ~/dev/yixiaoguan-v2

# 防止重复执行：检查是否已有 pilot_mode_enabled
if grep -q "^pilot_mode_enabled=" services/gateway/.env 2>/dev/null; then
  echo "[SKIP] gateway .env 已含 pilot_mode_enabled，不重复追加"
else
  PROXY_SECRET=$(openssl rand -hex 16)
  CENT_SECRET=$(openssl rand -hex 16)
  CENT_API=$(openssl rand -hex 16)

  cat >> services/gateway/.env <<EOF

# R11 pilot mode + centrifugo proxy (added by deploy)
pilot_mode_enabled=true
centrifugo_proxy_secret=${PROXY_SECRET}
centrifugo_secret=${CENT_SECRET}
centrifugo_api_key=${CENT_API}
EOF
  echo "[OK] gateway .env 已追加 4 行"

  # 创建 deploy/.env（centrifugo compose 用）
  cat > deploy/.env <<EOF
DIFY_API_KEY=not-used-here
JWT_SECRET=not-used-by-centrifugo-compose
CENTRIFUGO_SECRET=${CENT_SECRET}
CENTRIFUGO_API_KEY=${CENT_API}
CENTRIFUGO_PROXY_STATIC_HTTP_HEADERS={"X-Auth": "${PROXY_SECRET}"}
EOF
  chmod 600 deploy/.env
  echo "[OK] deploy/.env 已创建（mode 600）"
fi

echo ""
echo "--- gateway .env keys (REDACTED) ---"
sed 's/=.*$/=<REDACTED>/' services/gateway/.env
echo ""
echo "--- deploy/.env keys (REDACTED) ---"
sed 's/=.*$/=<REDACTED>/' deploy/.env
