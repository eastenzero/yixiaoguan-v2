#!/usr/bin/env bash
# Read prompt from /tmp/kimi-task.txt, run kimi at /home/easten/dev/yixiaoguan-v2
set -u
PROMPT="$(cat /tmp/kimi-task.txt)"
cd /home/easten/dev/yixiaoguan-v2
exec kimi --print --quiet --yolo -p "$PROMPT"
