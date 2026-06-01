#!/usr/bin/env bash
# 修复 wall layout 嵌套 + cache bust + 视觉收紧
set -euo pipefail

P=/home/easten/dev/yixiaoguan-v2/services/bi-evidence
STASH=/tmp/yxg-stash

chmod 644 $STASH/yxg-wall.css "$STASH/+layout@.svelte"

# 替换 wall.css
sudo -u easten cp $STASH/yxg-wall.css $P/static/yxg-wall.css

# 删旧 wall/+layout.svelte，放新 wall/+layout@.svelte
sudo -u easten rm -f $P/pages/wall/+layout.svelte
sudo -u easten cp "$STASH/+layout@.svelte" "$P/pages/wall/+layout@.svelte"

echo "── pages/wall ──"
ls -la $P/pages/wall/

echo ""
echo "── build ──"
sudo -u easten bash -c "cd $P && npm run build" > /tmp/build.log 2>&1 || true
tail -10 /tmp/build.log

if [ -d $P/build/_app ] && [ -f $P/build/wall/index.html ]; then
  rsync -a --delete $P/build/ /var/www/yixiaoguan/bi/
  chown -R www-data:www-data /var/www/yixiaoguan/bi
  echo ""
  echo "── deployed ──"
  for u in /bi/wall/ /bi-v1/wall/; do
    printf "%-15s " "$u"
    curl -sLk -o /dev/null -w "HTTP %{http_code} %{size_download}b\n" "https://yxg.xiaoguan.site$u"
  done
  echo ""
  echo "── /bi/wall/ html sample (sidebar / aside / yxg-wall.css?v=) ──"
  curl -sLk https://yxg.xiaoguan.site/bi/wall/ | grep -oE '(yxg-wall\.css\?v=[^"]+|<aside|class="wall-root)' | sort -u
else
  echo "── BUILD FAILED ──"
  exit 1
fi
