#!/bin/bash
set -e

echo "====== 1. 域名现状 ======"
echo "--- nginx server_name ---"
grep -r 'server_name' /etc/nginx/sites-enabled/yxg-* 2>/dev/null
echo ""
echo "--- SSL cert domains ---"
for f in /etc/nginx/sites-enabled/yxg-*domain*; do
  echo "$f:"
  grep 'ssl_certificate\b' "$f" | head -1
  cert=$(grep 'ssl_certificate\b' "$f" | head -1 | awk '{print $2}' | tr -d ';')
  if [ -f "$cert" ]; then
    openssl x509 -in "$cert" -noout -subject -dates 2>/dev/null | head -3
  fi
done

echo ""
echo "====== 2. Git pull (deploy R10 code) ======"
cd /opt/yxg-v2/repo
git status --short | head -5
echo "current branch: $(git branch --show-current)"
echo "current commit: $(git log -1 --oneline)"
