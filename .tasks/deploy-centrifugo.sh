#!/bin/bash
set -e

echo "=== 1. Add Centrifugo location to Nginx vhosts ==="
for VHOST in /etc/nginx/sites-enabled/yxg-student-domain /etc/nginx/sites-enabled/yxg-teacher-domain; do
    if grep -q "centrifugo" "$VHOST"; then
        echo "  $VHOST: already has centrifugo block, skipping"
    else
        # Insert centrifugo location before the "location /api/" block
        sed -i '/location \/api\//i \
    # Centrifugo WebSocket reverse proxy\
    location /connection/websocket {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 3600s;\
        proxy_send_timeout 3600s;\
    }\
' "$VHOST"
        echo "  $VHOST: added centrifugo location"
    fi
done

echo "=== 2. Test Nginx config ==="
nginx -t

echo "=== 3. Reload Nginx ==="
systemctl reload nginx

echo "=== 4. Deploy frontend static files ==="
# Student app
rm -rf /var/www/yxg-student/*
cp -r /opt/yxg-v2/repo/apps/student-app/dist/build/h5/* /var/www/yxg-student/
echo "  Student app deployed"

# Teacher app
rm -rf /var/www/yxg-teacher/*
cp -r /opt/yxg-v2/repo/apps/teacher-app/dist/build/h5/* /var/www/yxg-teacher/
echo "  Teacher app deployed"

echo "=== 5. Install Python deps & restart gateway ==="
cd /opt/yxg-v2/repo/services/gateway
source venv/bin/activate
pip install httpx PyJWT -q 2>&1 | tail -3
deactivate
systemctl restart yxg-gateway
sleep 2
systemctl is-active yxg-gateway

echo "=== DONE ==="
