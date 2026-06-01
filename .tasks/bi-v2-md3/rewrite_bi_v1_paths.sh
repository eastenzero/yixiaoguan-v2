#!/usr/bin/env bash
# 把 /var/www/yixiaoguan/bi-v1/ 下所有 HTML/JS/JSON 里的 /bi/ 引用改成 /bi-v1/，
# 让旧版备份独立于新 /bi/ 的资源。
set -euo pipefail

ROOT=/var/www/yixiaoguan/bi-v1
[ -d "$ROOT" ] || { echo "missing $ROOT" >&2; exit 1; }

echo "── before ──"
grep -roE '"/bi/[a-zA-Z_./-]+' "$ROOT" | wc -l

# 只改文本类文件；二进制 (png/woff) 跳过
find "$ROOT" -type f \( -name '*.html' -o -name '*.js' -o -name '*.css' -o -name '*.json' -o -name '*.txt' -o -name '*.svg' -o -name '*.xml' \) \
  -exec sed -i \
    -e 's|"/bi/|"/bi-v1/|g' \
    -e "s|'/bi/|'/bi-v1/|g" \
    -e 's|=/bi/|=/bi-v1/|g' \
    -e 's|(/bi/|(/bi-v1/|g' \
    {} +

echo "── after ──"
grep -roE '"/bi/[a-zA-Z_./-]+' "$ROOT" | wc -l
echo "── /bi-v1/ count after ──"
grep -roE '"/bi-v1/[a-zA-Z_./-]+' "$ROOT" | wc -l
