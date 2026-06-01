#!/bin/bash
# 只读探查 TX-NEW 当前状态
set +e

echo '=== INSTALLED PACKAGES ==='
for p in docker.io docker-ce nginx postgresql postgresql-16 redis-server certbot zstd jq; do
  printf '%-20s ' "$p"
  v=$(dpkg-query -W -f='${Version}\n' "$p" 2>/dev/null)
  if [ -n "$v" ]; then echo "$v"; else echo MISSING; fi
done

echo
echo '=== DOCKER ==='
which docker && docker --version 2>/dev/null
docker ps 2>/dev/null && echo "docker ok" || echo "no docker daemon"

echo
echo '=== LISTEN PORTS ==='
ss -tlnp 2>/dev/null | head -30

echo
echo '=== UFW ==='
ufw status 2>/dev/null | head -15

echo
echo '=== /opt /home /var/www listing ==='
ls -la /opt /home /var/www 2>/dev/null

echo
echo '=== ENABLED units (top 40) ==='
systemctl list-unit-files --state=enabled --no-pager 2>/dev/null | head -40

echo
echo '=== running services ==='
systemctl list-units --type=service --state=running --no-pager 2>/dev/null | head -30

echo
echo '=== nginx sites ==='
ls -la /etc/nginx/sites-enabled 2>/dev/null

echo
echo '=== existing certificates ==='
certbot certificates 2>/dev/null | grep -E 'Domains|Expiry' | head -20

echo
echo '=== SSH keys ==='
wc -l /root/.ssh/authorized_keys 2>/dev/null

echo
echo '=== git ==='
which git && git --version

echo
echo '=== node/npm ==='
which node && node --version
which npm && npm --version

echo
echo '=== python ==='
which python3 && python3 --version

echo
echo '=== /etc/hosts public IP hint ==='
hostname -I

echo
echo '=== firewall iptables snapshot ==='
iptables -L INPUT -n 2>/dev/null | head -20
