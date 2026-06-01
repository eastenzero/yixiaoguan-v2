#!/usr/bin/env bash
# 安装 yxg-wall-export 的 systemd unit + timer
set -euo pipefail

echo "── 1. 准备目录 + 权限 ──"
mkdir -p /var/www/yixiaoguan/wall
chown easten:easten /var/www/yixiaoguan/wall   # 让 service 用户 easten 能写

echo "── 2. 复制 unit 文件 ──"
cp /tmp/yxg-stash/yxg-wall-export.service /etc/systemd/system/yxg-wall-export.service
cp /tmp/yxg-stash/yxg-wall-export.timer   /etc/systemd/system/yxg-wall-export.timer
chmod 644 /etc/systemd/system/yxg-wall-export.{service,timer}

echo "── 3. systemctl daemon-reload + 启用 timer ──"
systemctl daemon-reload
systemctl enable --now yxg-wall-export.timer

echo "── 4. 立即跑一次 service 看效果 ──"
systemctl start yxg-wall-export.service
sleep 2

echo "── 5. timer 状态 ──"
systemctl status yxg-wall-export.timer --no-pager | head -15
echo ""
echo "── 6. service 最近一次输出 ──"
journalctl -u yxg-wall-export.service -n 5 --no-pager
echo ""
echo "── 7. data.json 检查 ──"
if [ -f /var/www/yixiaoguan/wall/data.json ]; then
  ls -la /var/www/yixiaoguan/wall/data.json
  echo "── 内容前 30 行 ──"
  head -30 /var/www/yixiaoguan/wall/data.json
  echo "── nginx 可读? (chmod 644) ──"
  stat -c '%a %U:%G' /var/www/yixiaoguan/wall/data.json
else
  echo "ERROR: data.json 未生成"
  exit 1
fi
echo ""
echo "── 8. timer 下次触发时间 ──"
systemctl list-timers yxg-wall-export.timer --no-pager
