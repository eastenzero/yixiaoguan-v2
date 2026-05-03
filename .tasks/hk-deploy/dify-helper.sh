#!/bin/bash
# Dify console API helper, run on hk server
# Login + cache token, then expose acall() to do authenticated console requests
set -e
DIFY=https://dify.130814.xyz/console/api
COOK=/tmp/dify-cookie.txt
EMAIL=easten_zero@qq.com
PASS_B64=WmhhWWVGYW4wNS4wNy4xNA==

dify_login() {
  rm -f "$COOK"
  curl -sk -c "$COOK" -X POST "$DIFY/login" \
    -H 'Content-Type: application/json' \
    --data-raw "{\"email\":\"$EMAIL\",\"password\":\"$PASS_B64\",\"language\":\"zh-Hans\",\"remember_me\":true}" \
    -o /dev/null
  ACCESS=$(awk '/access_token/{print $NF}' "$COOK" | tail -1)
  CSRF=$(awk '/csrf_token/{print $NF}' "$COOK" | tail -1)
  REFRESH=$(awk '/refresh_token/{print $NF}' "$COOK" | tail -1)
  if [ -z "$ACCESS" ]; then echo "ERR: no access_token in cookie file"; cat "$COOK"; exit 1; fi
  echo "[login OK] access=${ACCESS:0:24}..."
  export ACCESS CSRF REFRESH
}

# acall METHOD PATH [extra curl args]
dify_acall() {
  local METHOD=$1
  local URLPATH=$2
  shift 2
  curl -sk -b "$COOK" -X "$METHOD" "$DIFY$URLPATH" \
    -H "Authorization: Bearer $ACCESS" \
    -H "X-Csrf-Token: $CSRF" \
    "$@"
}

# Smoke test
case "${1:-smoke}" in
  smoke)
    dify_login
    echo
    echo "=== GET /workspaces/current ==="
    dify_acall GET /workspaces/current -w '\nhttp=%{http_code}\n' | head -30
    echo
    echo "=== GET /apps?page=1&limit=5 ==="
    dify_acall GET '/apps?page=1&limit=5' -w '\nhttp=%{http_code}\n' | head -20
    echo
    echo "=== GET /datasets?page=1&limit=5 ==="
    dify_acall GET '/datasets?page=1&limit=5' -w '\nhttp=%{http_code}\n' | head -20
    ;;
  source)
    # Source mode: caller can do `. dify-helper.sh source` then dify_login + dify_acall
    dify_login
    ;;
  *)
    echo "usage: $0 [smoke|source]"
    exit 1
    ;;
esac
