#!/usr/bin/env bash
# Step C: nginx vhost yxg-stu (:8080) + yxg-tea (:8081)
set -euo pipefail

# 先看现有 nginx 是否已有 map $http_upgrade（WebSocket support）
HAS_UPGRADE_MAP=$(grep -rh 'connection_upgrade' /etc/nginx/conf.d/ 2>/dev/null | head -1 || true)
if [[ -z "$HAS_UPGRADE_MAP" ]]; then
    echo "[*] adding connection-upgrade map"
    cat > /etc/nginx/conf.d/connection-upgrade.conf <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
EOF
fi

cat > /etc/nginx/sites-available/yxg-student <<'EOF'
server {
    listen 8080;
    server_name _;
    root /var/www/yxg-student;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static asset cache
    location ~* \.(?:js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|ico)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # API + WebSocket reverse proxy → gateway uvicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    # 学生端不暴露 dify-api 直访（仅 gateway 调用）

    access_log /var/log/nginx/yxg-student.access.log;
    error_log  /var/log/nginx/yxg-student.error.log;
}
EOF

cat > /etc/nginx/sites-available/yxg-teacher <<'EOF'
server {
    listen 8081;
    server_name _;
    root /var/www/yxg-teacher;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(?:js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|ico)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    access_log /var/log/nginx/yxg-teacher.access.log;
    error_log  /var/log/nginx/yxg-teacher.error.log;
}
EOF

# 启用 vhost
ln -sf /etc/nginx/sites-available/yxg-student /etc/nginx/sites-enabled/yxg-student
ln -sf /etc/nginx/sites-available/yxg-teacher /etc/nginx/sites-enabled/yxg-teacher

# 测试 + reload
echo ""
echo "=== nginx -t ==="
nginx -t

echo ""
echo "=== reload nginx ==="
systemctl reload nginx

# 验证端口监听
echo ""
echo "=== port 8080 / 8081 listening ==="
ss -tlnp | grep -E ':8080|:8081' || echo "[!] not listening"

# 验证响应
echo ""
echo "=== curl :8080/index.html ==="
curl -sS -o /dev/null -w "http_code=%{http_code} size=%{size_download}\n" http://127.0.0.1:8080/

echo "=== curl :8080/api/v1/... (gateway via nginx) ==="
curl -sS -o /dev/null -w "http_code=%{http_code}\n" http://127.0.0.1:8080/api/v1/users/me

echo "=== curl :8081/ (teacher) ==="
curl -sS -o /dev/null -w "http_code=%{http_code} size=%{size_download}\n" http://127.0.0.1:8081/

echo ""
echo "[OK] Step C complete"
echo "学生端 H5 → http://64.90.13.65:8080/"
echo "教师端 H5 → http://64.90.13.65:8081/"
