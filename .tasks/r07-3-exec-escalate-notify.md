---
id: "r07-3-exec-escalate-notify"
parent: "R07-3"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "medium"
foundation: false

scope:
  - "services/gateway/app/routers/actions.py"
  - "services/gateway/app/services/ws_manager.py"
  - "services/gateway/tests/test_escalate_notify.py"
  - ".tasks/reports/r07-3-exec-escalate-notify_report.md"

out_of_scope:
  - "services/gateway/app/routers/conversations.py"    # 教师发消息能力属于 D1
  - "services/gateway/app/routers/chat.py"             # AI 暂停/恢复属于 D2
  - "apps/**"                                          # 不改教师端工单 UI
  - "短信/邮件/企业微信/电话等外部通知渠道"
  - "跨学院抢单或负载均衡派单策略"
  - "教师离线消息补投递"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R02-师生对话与主动运营.md"
  - "services/gateway/app/models/conversation.py"
  - "services/gateway/app/models/user.py"
  - "services/gateway/app/routers/actions.py"
  - "services/gateway/app/services/ws_manager.py"

done_criteria:
  L0: "学生执行 escalate 时，会话从 ai_serving 转为 pending_teacher，并通过 broadcast_to_college_teachers 向同学院在线教师广播 escalation_notify 工单通知"
  L1: "pytest services/gateway/tests/test_escalate_notify.py 通过；覆盖同学院教师收到、跨学院教师收不到、学院无在线教师时不报错等场景；ruff / mypy 通过"
  L2: "手工建立至少 3 个教师连接（同学院 2 个、其他学院 1 个）后触发 escalate，只有同学院在线教师收到包含 conv_id / student_id / title / status / created_at 的通知 payload"
  L3: "收到通知的教师可直接基于 payload 中的 conv_id 发起 accept，并在会话房间中看到状态切到 teacher_serving，证明 'escalate -> 通知 -> 接单' 工单链路闭环"

depends_on: []
created_at: "2026-04-21"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-21 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R07-3 Executor · `escalate` 时广播学院教师工单通知

> 目标状态：学生呼叫人工后，不只是把会话状态改成 `pending_teacher`，还要把“有新工单待接”这件事主动推给对应学院的在线教师，避免教师必须靠轮询列表页发现新单。

## 背景

当前 `services/gateway/app/routers/actions.py` 已经有 `_notify_college_teachers()`：

- 根据学生 `college_id` 查询同学院激活教师
- 调用 `manager.broadcast_to_college_teachers(...)`
- 发送 `type = escalation_notify` 的 payload

说明 D3 的主干同样已存在；本任务的重点是：

- 把现有能力补成可验收的正式工单通知
- 明确通知对象、payload 和失败容错
- 用测试锁住“只通知本学院教师”的边界

## 必读上下文

1. `docs/requirements/R02-师生对话与主动运营.md` § 需求 1 / 需求 4
2. `services/gateway/app/routers/actions.py`
3. `services/gateway/app/services/ws_manager.py`
4. `services/gateway/app/models/user.py`

## 执行重点

### 1. 固化通知时机

通知只在学生 `POST /api/actions/{conv_id}/escalate` 成功后发送。

至少保证顺序上：

1. 状态转换成功（`ai_serving -> pending_teacher`）
2. 生成学院教师通知
3. 向会话房间广播 `status_changed = pending_teacher`

若通知失败会影响主流程，需要在报告里说明是否容错；默认建议：**不因个别教师 WS 发送失败而回滚整个 escalate**。

### 2. 固化通知对象

通知对象必须满足：

- `role == teacher`
- `college_id == current_user.college_id`
- `is_active == True`
- 当前在线（由 `ws_manager.send_to_user` 是否有连接决定）

跨学院教师、学生本人、管理员是否接收，必须在任务中写清楚。默认：**仅同学院教师接收**。

### 3. 固化 payload

现有 payload 字段已经比较接近可用，至少保留：

- `conv_id`
- `student_id`
- `title`
- `status`
- `created_at`

若教师端列表页还需要更多上下文，优先在 `data` 下补字段，而不是新开第二种通知事件。

### 4. 增加自动化测试

至少验证：

- `broadcast_to_college_teachers` 被调用一次
- `teacher_ids` 只包含同学院教师
- payload 中 `type == escalation_notify`
- 学院下无教师 / 无在线教师时，escalate 仍成功返回

## 已知陷阱

- `broadcast_to_college_teachers()` 当前实现只是遍历 `teacher_ids -> send_to_user`，`college_id` 参数本身未参与筛选；真正的筛选逻辑在 `actions.py` 查询语句，测试必须锁住这一点。
- 若把管理员也混入广播对象，可能会造成权限边界变模糊；除非 TX 明确要求，默认不广播给 admin。
- 如果 payload 不带 `conv_id`，教师端即使收到通知也无法直接接单。
- 不要在本任务里扩成外部渠道通知系统；先把站内 WS 工单通知闭环做稳。

## 回滚方案

- Git revert 本次改动即可
- 若通知逻辑引发 escalate 主链路不稳定，优先回滚到“仅状态切换、不广播教师工单”的稳定版本
- 若新增测试或辅助函数，回滚时同步删除对应测试与报告
