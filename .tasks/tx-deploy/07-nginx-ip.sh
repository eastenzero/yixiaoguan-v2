#!/bin/bash
# RUN ON: tx-new (as easten with sudo,或 root)
# 阶段 G · nginx IP 模式(先用 80=学生 / 81=教师,后期 DNS 切换后再配 443)
# 前置:阶段 E/F 已完成,gateway :8100 和 centrifugo :8000 都在跑
#
# 构建静态文件需要本地先 build 好 dist/,这个脚本假设:
#   本地 PowerShell 运行:
#     cd apps\student-app && npm run build:h5
#     cd apps\teacher-app && npm run build:h5
#     scp -r apps\student-app\dist\build\h5\* tx-new:/tmp/student/
#     scp -r apps\teacher-app\dist\build\h5\*  tx-new:/tmp/teacher/
#   然后 ssh tx-new 跑本脚本

set -euo pipefail
log()  { echo -e "\e[36m[G]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }

REPO=/home/easten/dev/yixiaoguan-v2
PUB_IP=82.156.129.75

log "== 1. 准备 /var/www/yixiaoguan =="
sudo mkdir -p /var/www/yixiaoguan/{student,teacher}
if [ -d /tmp/student ] && [ "$(ls -A /tmp/student 2>/dev/null)" ]; then
  sudo rsync -a --delete /tmp/student/ /var/www/yixiaoguan/student/
  ok "学生端静态已发布"
else
  warn "/tmp/student 空或不存在; 请先在本地 build h5 并 scp 到 tx-new:/tmp/student/"
fi
if [ -d /tmp/teacher ] && [ "$(ls -A /tmp/teacher 2>/dev/null)" ]; then
  sudo rsync -a --delete /tmp/teacher/ /var/www/yixiaoguan/teacher/
  ok "教师端静态已发布"
else
  warn "/tmp/teacher 空或不存在"
fi
sudo chown -R www-data:www-data /var/www/yixiaoguan

log "== 2. 写 nginx 站点(IP 模式) =="
# 先用仓库 deploy/nginx/gateway.conf 作基础(它已经是 80/81,但 server_name 有 192.168.100.165)
# 我们生成 tx-new 专用,server_name 用公网 IP + _
sudo tee /etc/nginx/sites-available/yixiaoguan > /dev/null <<'NGINX'
# Yixiaoguan v2 — TX-NEW IP 模式
# 学生端 :80 / 教师端 :81 / 后期 443 由 certbot --nginx 添加

# --- Student-app on port 80 ---
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name 82.156.129.75 _;

    root /var/www/yixiaoguan/student;
    index index.html;
    client_max_body_size 50m;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location /centrifugo/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}

# --- Teacher-app on port 81 ---
server {
    listen 81;
    listen [::]:81;
    server_name 82.156.129.75 _;

    root /var/www/yixiaoguan/teacher;
    index index.html;
    client_max_body_size 50m;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location /centrifugo/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
NGINX

sudo ln -sf ../sites-available/yixiaoguan /etc/nginx/sites-enabled/yixiaoguan
sudo rm -f /etc/nginx/sites-enabled/default

log "== 3. centrifugo config 允许 IP 模式访问 =="
# 需要把 http://82.156.129.75 加入 allowed_origins
cd "$REPO/deploy"
python3 - <<'PY'
import json
p = "/home/easten/dev/yixiaoguan-v2/deploy/centrifugo-config.json"
with open(p) as f:
    cfg = json.load(f)
origins = cfg.setdefault("client", {}).setdefault("allowed_origins", [])
NEW = ["http://82.156.129.75", "http://82.156.129.75:81"]
changed = False
for o in NEW:
    if o not in origins:
        origins.append(o)
        changed = True
if changed:
    with open(p, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("[OK] allowed_origins 已加入 IP:", NEW)
else:
    print("[OK] allowed_origins 已含 IP,无改动")
PY

# 改动了 config.json,要 restart centrifugo 容器
docker compose -f docker-compose.centrifugo.yml restart
sleep 2

log "== 4. nginx -t + reload =="
sudo nginx -t
sudo systemctl reload nginx
ok "nginx reload OK"

log "== 5. 自测 =="
curl -sI -m 5 http://127.0.0.1/ | head -5
curl -s -m 5 http://127.0.0.1/api/colleges | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'colleges={len(d)}')" || warn "/api/colleges 失败"
curl -sI -m 5 http://127.0.0.1:81/ | head -3

ok "阶段 G 完成"
echo ""
echo "下一步: 本地浏览器打开 http://82.156.129.75/ 实测"
echo "      再跑 08-verify.sh 做端到端验证"
