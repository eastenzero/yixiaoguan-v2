#!/bin/bash
# RUN ON: tx-new (root)
# 阶段 A · 系统基础安装 + 创建 easten 用户
# 幂等:可重复执行,已装的包 apt 会跳过

set -euo pipefail

log()  { echo -e "\e[36m[A]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }

log "== 1. 系统信息快照 =="
lsb_release -a 2>/dev/null | grep -E 'Description|Release|Codename' || cat /etc/os-release | head -5
uname -m
free -h | head -2
df -h / | head -2

log "== 2. apt update + 核心包 =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
# Ubuntu 24.04 noble:docker compose plugin 的 apt 包名是 docker-compose-v2(不是 docker-compose-plugin)
apt-get install -y -q \
    docker.io docker-compose-v2 docker-buildx \
    nginx \
    certbot python3-certbot-nginx \
    postgresql-client-16 \
    redis-tools \
    python3.12 python3.12-venv python3-pip python3-full \
    build-essential git curl jq zstd rsync \
    ca-certificates
ok "apt 安装完成"

log "== 3. 启动 docker =="
systemctl enable --now docker
docker --version
ok "docker: $(docker info --format '{{.ServerVersion}}')"

log "== 4. 创建 easten 用户(如不存在) =="
if id easten >/dev/null 2>&1; then
  warn "easten 已存在,跳过创建"
else
  useradd -m -s /bin/bash -G sudo,docker easten
  # 无密码 sudo(与 165 一致,方便自动化)
  echo 'easten ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-easten
  chmod 0440 /etc/sudoers.d/90-easten
  ok "easten 已创建并加入 sudo + docker 组"
fi

log "== 5. 同步 ssh 密钥到 easten =="
mkdir -p /home/easten/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp -f /root/.ssh/authorized_keys /home/easten/.ssh/authorized_keys
fi
chown -R easten:easten /home/easten/.ssh
chmod 700 /home/easten/.ssh
chmod 600 /home/easten/.ssh/authorized_keys 2>/dev/null || true
ok "easten ssh 密钥就绪 (ssh easten@82.156.129.75 可通)"

log "== 6. 确保 docker 组对 easten 生效 =="
# 刚加组需要重新登录才生效;这里不强制,后续脚本用 sg/newgrp 或 sudo -u easten
groups easten | tr ' ' '\n' | grep -E '^(docker|sudo)$' || true

log "== 7. nvm + node 20(给前端构建用) =="
if [ ! -d /home/easten/.nvm ]; then
  sudo -u easten bash -c '
    curl -fsSL -o /tmp/nvm-install.sh https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh
    bash /tmp/nvm-install.sh
    export NVM_DIR="$HOME/.nvm"
    . "$NVM_DIR/nvm.sh"
    nvm install 20
    nvm alias default 20
  ' && ok "nvm + node 20 已安装" || warn "nvm 安装失败(可后续手动);不影响后端部署"
else
  ok "nvm 已存在,跳过"
fi

log "== 8. 创建工作目录 =="
sudo -u easten mkdir -p /home/easten/dev /home/easten/logs
ok "/home/easten/dev + /home/easten/logs 就绪"

log "== 9. 关闭 ufw(腾讯云用安全组) =="
if systemctl is-active --quiet ufw; then
  ufw disable || true
  ok "ufw 已停"
else
  ok "ufw 已停/未装"
fi

log "== 10. 停掉 nginx 默认站(但保留 nginx systemd) =="
if [ -L /etc/nginx/sites-enabled/default ]; then
  rm -f /etc/nginx/sites-enabled/default
  nginx -t && systemctl reload nginx || true
  ok "默认站已禁,nginx 空跑"
else
  ok "无默认站或已禁"
fi

log "== 11. 最终状态 =="
systemctl --no-pager is-active docker nginx || true
ss -tlnp 2>/dev/null | grep -E ':(22|80) ' | head

ok "阶段 A 完成"
echo ""
echo "下一步:"
echo "  1. 本地 PowerShell: ssh easten@82.156.129.75 验证免密登录"
echo "  2. 跑 02-docker-load.ps1 加载 docker 镜像"
