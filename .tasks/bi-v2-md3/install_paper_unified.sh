#!/usr/bin/env bash
# 米色画报风一统两处:
#   - 删除 V2 MD3 残留: yxg-bi-tokens.css, yxg-bi.css
#   - 删除 wall/+layout@.svelte (回归 +layout.svelte)
#   - 上传新 yxg-theme.css (V2 升级版米色画报 token + 画报章节样式)
#   - 上传新 yxg-wall.css (米色画报头版式大屏)
#   - 上传新 pages: index.md, wall/index.md, +layout.svelte, wall/+layout.svelte
#   - build + rsync + 验证
set -euo pipefail

P=/home/easten/dev/yixiaoguan-v2/services/bi-evidence
STASH=/tmp/yxg-stash

chmod 644 $STASH/yxg-theme.css $STASH/yxg-wall.css $STASH/index.md $STASH/root-layout.svelte $STASH/wall-layout.svelte $STASH/wall-index.md

# ── 删除 V2 MD3 残留 ──
sudo -u easten rm -f $P/static/yxg-bi-tokens.css
sudo -u easten rm -f $P/static/yxg-bi.css
# 删除可能残留的 wall/+layout@.svelte (上一版尝试过的 reset layout 文件名)
sudo -u easten rm -f "$P/pages/wall/+layout@.svelte"

# ── 上传新文件 ──
sudo -u easten cp $STASH/yxg-theme.css $P/static/yxg-theme.css
sudo -u easten cp $STASH/yxg-wall.css  $P/static/yxg-wall.css
sudo -u easten cp $STASH/index.md      $P/pages/index.md
sudo -u easten cp $STASH/wall-index.md $P/pages/wall/index.md
sudo -u easten cp $STASH/root-layout.svelte $P/pages/+layout.svelte
sudo -u easten cp $STASH/wall-layout.svelte $P/pages/wall/+layout.svelte

echo "── pages/ ──"
ls -la $P/pages/
echo ""
echo "── pages/wall/ ──"
ls -la $P/pages/wall/
echo ""
echo "── static/ ──"
ls -la $P/static/

echo ""
echo "── build ──"
sudo -u easten bash -c "cd $P && npm run build" > /tmp/build.log 2>&1 || true
tail -10 /tmp/build.log

if [ -d $P/build/_app ] && [ -f $P/build/wall/index.html ] && [ -f $P/build/index.html ]; then
  rsync -a --delete $P/build/ /var/www/yixiaoguan/bi/
  chown -R www-data:www-data /var/www/yixiaoguan/bi
  echo ""
  echo "── deployed (HTTP / size) ──"
  for u in /bi/ /bi/wall/ /bi-v1/ /bi-v1/wall/; do
    printf "%-15s " "$u"
    curl -sLk -o /dev/null -w "HTTP %{http_code} %{size_download}b\n" "https://yxg.xiaoguan.site$u"
  done
  echo ""
  echo "── /bi/wall/ html: aside count + css refs ──"
  H=$(curl -sLk https://yxg.xiaoguan.site/bi/wall/)
  echo "$H" | grep -oE '<aside' | wc -l | xargs -I{} echo "<aside count: {}"
  echo "$H" | grep -oE '(yxg-theme|yxg-wall)\.css\?v=[a-z0-9]+' | sort -u
else
  echo "── BUILD FAILED ──"
  exit 1
fi
