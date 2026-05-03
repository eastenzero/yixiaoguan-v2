#!/usr/bin/env bash
# Step B2: systemd unit + start gateway + 验证监听 + health
set -euo pipefail

mkdir -p /opt/yxg-v2/logs

cat > /etc/systemd/system/yxg-gateway.service <<'UNIT'
[Unit]
Description=Yixiaoguan v2 Gateway (FastAPI) — HK pilot
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/yxg-v2/repo/services/gateway
EnvironmentFile=/opt/yxg-v2/repo/services/gateway/.env
ExecStart=/opt/yxg-v2/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 2
Restart=on-failure
RestartSec=5
StandardOutput=append:/opt/yxg-v2/logs/yxg-gateway.log
StandardError=append:/opt/yxg-v2/logs/yxg-gateway.err.log
# 禁止外部直接访问 8100，nginx 反代
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now yxg-gateway
sleep 3

echo "=== systemd status ==="
systemctl is-active yxg-gateway
systemctl status yxg-gateway --no-pager -l | head -20

echo ""
echo "=== port :8100 ==="
ss -tlnp | grep :8100 || echo "[!] :8100 not listening"

echo ""
echo "=== last 20 lines of log ==="
tail -20 /opt/yxg-v2/logs/yxg-gateway.log 2>/dev/null || echo "(no stdout log yet)"

echo ""
echo "=== last 20 lines of err.log ==="
tail -20 /opt/yxg-v2/logs/yxg-gateway.err.log 2>/dev/null || echo "(no err log yet)"

echo ""
echo "=== curl /docs (sanity check) ==="
curl -sS -o /dev/null -w "http_code=%{http_code} time=%{time_total}s\n" http://127.0.0.1:8100/docs || true

echo ""
echo "=== curl /api/v1/auth/login (should 422 on empty) ==="
curl -sS -X POST http://127.0.0.1:8100/api/v1/auth/login -H 'Content-Type: application/json' -d '{}' -w "\nhttp_code=%{http_code}\n" || true

echo ""
echo "[OK] Step B2 complete (gateway listening on 127.0.0.1:8100)"
