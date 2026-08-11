#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2/kb-governance-ui-20260809-221900"
REPO_ROOT="/home/easten/dev/yixiaoguan-v2"
WEB_ROOT="/var/www/yixiaoguan"

test -f "$BACKUP_ROOT/gateway-files.before.tgz"
test -f "$BACKUP_ROOT/student.before.tgz"
test -f "$BACKUP_ROOT/teacher.before.tgz"

tar -xzf "$BACKUP_ROOT/gateway-files.before.tgz" -C "$REPO_ROOT"

sudo -n mv "$WEB_ROOT/student" "$WEB_ROOT/student.failed-20260809-221900"
sudo -n mv "$WEB_ROOT/teacher" "$WEB_ROOT/teacher.failed-20260809-221900"
sudo -n tar -xzf "$BACKUP_ROOT/student.before.tgz" -C "$WEB_ROOT"
sudo -n tar -xzf "$BACKUP_ROOT/teacher.before.tgz" -C "$WEB_ROOT"
sudo -n systemctl restart yixiaoguan-gateway.service
sudo -n systemctl is-active --quiet yixiaoguan-gateway.service

echo "Rollback complete: $BACKUP_ROOT"
