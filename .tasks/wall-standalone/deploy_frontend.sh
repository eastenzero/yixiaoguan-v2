#!/usr/bin/env bash
# 把 wall-standalone/ 静态资源部署到 /var/www/yixiaoguan/wall/
# 注意: 不动 data.json (timer 在持续写入)
set -euo pipefail

SRC=/tmp/yxg-stash/wall-standalone
DST=/var/www/yixiaoguan/wall

[ -d "$SRC" ] || { echo "$SRC missing" >&2; exit 1; }
mkdir -p "$DST/assets"

# 复制前端文件 (不删 data.json)
cp -v "$SRC/index.html"         "$DST/index.html"
cp -v "$SRC/assets/wall-tokens.css" "$DST/assets/wall-tokens.css"
cp -v "$SRC/assets/wall.css"    "$DST/assets/wall.css"
cp -v "$SRC/assets/wall.js"     "$DST/assets/wall.js"

chown -R www-data:www-data "$DST/index.html" "$DST/assets"

echo ""
echo "── /var/www/yixiaoguan/wall/ ──"
ls -la "$DST" "$DST/assets"

echo ""
echo "── nginx location 加 /wall/ (检查是否已有) ──"
if grep -q 'location /wall/' /etc/nginx/sites-enabled/yixiaoguan; then
  echo "已有 /wall/ location, 跳过"
else
  python3 - <<'PY'
import pathlib
p = pathlib.Path('/etc/nginx/sites-enabled/yixiaoguan')
t = p.read_text()
old = '''    location /bi/ {'''
new = '''    location /wall/ {
        alias /var/www/yixiaoguan/wall/;
        try_files $uri $uri/ /wall/index.html;
    }

    location /bi/ {'''
if 'location /wall/' not in t:
    cnt = t.count(old)
    if cnt != 1:
        raise SystemExit(f'unexpected /bi/ count: {cnt}')
    p.write_text(t.replace(old, new))
    print('injected /wall/ before /bi/')
else:
    print('skip')
PY
fi

echo ""
echo "── nginx -t ──"
nginx -t 2>&1 | tail -3

echo ""
echo "── reload + curl ──"
systemctl reload nginx
sleep 1
for u in /wall/ /wall/data.json /wall/assets/wall.css /wall/assets/wall.js; do
  printf "%-32s " "$u"
  curl -sLk -o /dev/null -w "HTTP %{http_code} %{size_download}b %{content_type}\n" "https://yxg.xiaoguan.site$u"
done
