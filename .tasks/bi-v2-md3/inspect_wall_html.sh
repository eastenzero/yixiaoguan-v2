#!/usr/bin/env bash
# 打印 /bi/wall/ 的 aside 结构, 看 Evidence 的 sidebar 长什么样
URL="https://yxg.xiaoguan.site/bi/wall/"
HTML=$(curl -sLk "$URL")

echo "── aside snippet ──"
echo "$HTML" | python3 -c "
import sys
h = sys.stdin.read()
i = h.find('<aside')
print(h[i:i+600] if i >= 0 else 'no aside')
"
echo ""
echo "── classes containing sidebar/aside/nav/header ──"
echo "$HTML" | grep -oE 'class=\"[^\"]*(sidebar|aside|nav|header|menu|drawer)[^\"]*\"' | sort -u | head -10
