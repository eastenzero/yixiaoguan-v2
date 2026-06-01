#!/usr/bin/env bash
# 把 /tmp/yxg-stash 里的 V2 文件覆盖到 bi-evidence 项目并 build + rsync
set -euo pipefail

P=/home/easten/dev/yixiaoguan-v2/services/bi-evidence
STASH=/tmp/yxg-stash

chmod 644 $STASH/*

# static
sudo -u easten cp $STASH/yxg-bi-tokens.css $P/static/yxg-bi-tokens.css
sudo -u easten cp $STASH/yxg-bi.css        $P/static/yxg-bi.css
sudo -u easten cp $STASH/yxg-wall.css      $P/static/yxg-wall.css

# pages
sudo -u easten cp $STASH/root-layout.svelte $P/pages/+layout.svelte
sudo -u easten cp $STASH/wall-layout.svelte $P/pages/wall/+layout.svelte
sudo -u easten cp $STASH/wall-index.md      $P/pages/wall/index.md
sudo -u easten cp $STASH/index.md           $P/pages/index.md

echo "── files in static ──"
ls -la $P/static/
echo ""
echo "── files in pages ──"
ls -la $P/pages/

echo ""
echo "── build ──"
sudo -u easten bash -c "cd $P && npm run build" > /tmp/build.log 2>&1 || true
tail -15 /tmp/build.log

if [ -d $P/build/_app ] && [ -f $P/build/wall/index.html ]; then
  rsync -a --delete $P/build/ /var/www/yixiaoguan/bi/
  chown -R www-data:www-data /var/www/yixiaoguan/bi
  echo ""
  echo "── deployed ──"
  for u in /bi/ /bi/wall/ /bi-v1/ /bi-v1/wall/; do
    printf "%-15s " "$u"
    curl -sLk -o /dev/null -w "HTTP %{http_code} %{size_download}b\n" "https://yxg.xiaoguan.site$u"
  done
else
  echo "── build failed ──"
  exit 1
fi
