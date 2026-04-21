---
id: "r07-2-exec-ai-pause-resume"
parent: "R07-2"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "high"
foundation: false

scope:
  - "services/gateway/app/routers/chat.py"
  - "services/gateway/app/routers/actions.py"
  - "services/gateway/app/services/state_machine.py"
  - "services/gateway/tests/test_ai_pause_resume.py"
  - ".tasks/reports/r07-2-exec-ai-pause-resume_report.md"

out_of_scope:
  - "services/gateway/app/routers/conversations.py"    # 教师发消息能力属于 D1
  - "services/gateway/app/services/ws_manager.py"      # 仅复用现有广播，不重构连接层
  - "apps/**"                                          # 不改前端交互文案
  - "Dify Chatflow / prompt"
  - "超时派单、轮询派单、自动回收工单"
  - "短信/邮件/企业微信通知"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R02-师生对话与主动运营.md"
  - "services/gateway/app/models/conversation.py"
  - "services/gateway/app/routers/chat.py"
  - "services/gateway/app/routers/actions.py"
  - "services/gateway/app/services/state_machine.py"

done_criteria:
  L0: "教师 accept 后，会话进入 teacher_serving；此后学生继续调用 /api/chat/send 时只写库并广播给房间，不触发 Dify；教师 resolve 后，AI 能按约定恢复可用"
  L1: "pytest services/gateway/tests/test_ai_pause_resume.py 通过；覆盖 accept/resolve/reactivate 主链路、teacher_serving 下禁止 Dify、非法状态转换等场景；ruff / mypy 通过"
  L2: "手工验证完整链路：student escalate -> teacher accept -> student 发一条消息只收到 JSON 不收到 SSE，且 gateway 日志无新的 Dify 请求；teacher resolve 后，student 再发一条消息可重新得到 AI 的 SSE 回复"
  L3: "同一会话在 WS 时间线上可观察到 pending_teacher -> teacher_serving -> resolved -> ai_serving（或等效恢复策略）的完整状态流，且 AI 在人工介入期间 0 次回复、恢复后仅回复 1 次"

depends_on:
  - "r07-1-exec-teacher-send"
created_at: "2026-04-21"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-21 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R07-2 Executor · AI 暂停 / 恢复策略补齐

> 目标状态：真实教师一旦接入会话，AI 立即停止继续抢答；人工处理完成后，学生继续提问时 AI 可以重新接管，形成清晰、可预期的多角色协作策略。

## 背景

当前网关里已经有一部分 D2 骨架：

- `actions.py` 的 `accept` 会把状态切到 `teacher_serving`
- `chat.py` 在 `teacher_serving` 下对学生消息只做“写库 + WS 广播 + 返回 JSON”，不会走 SSE/Dify
- `resolve` 会把状态切到 `resolved`
- 学生在 `resolved` 下再次发送消息时，`chat.py` 会先 `reactivate -> ai_serving`，然后重新走 AI SSE

也就是说，**“AI 暂停”基本已有，“AI 恢复”已有半闭环，但还缺显式任务化与测试化**。本任务的重点是把这套策略固化为正式行为，而不是在状态机里随意增加新状态。

## 策略约定（本任务默认方案）

除非 TX 明确要求“resolve 即刻回到 ai_serving”，本任务默认沿用并固化以下策略：

1. `accept`：`pending_teacher -> teacher_serving`
2. `teacher_serving` 期间：学生消息只写库 + WS 广播，**绝不调 Dify**
3. `resolve`：`teacher_serving -> resolved`
4. 学生后续再发消息：`resolved -> reactivate -> ai_serving`，然后恢复 AI 回复

这个方案的好处：

- `resolved` 保留为可审计状态，教师已解决的动作可见
- AI 恢复时机明确，由学生下一次提问触发，避免教师刚点 resolve 就被 AI 插话
- 兼容当前代码骨架，改动面最小

## 必读上下文

1. `docs/requirements/R02-师生对话与主动运营.md` § 需求 1
2. `services/gateway/app/routers/chat.py`
3. `services/gateway/app/routers/actions.py`
4. `services/gateway/app/services/state_machine.py`

## 执行重点

### 1. 明确“暂停”的唯一判定条件

暂停 AI 的 authoritative source 必须是会话状态，而不是前端本地标记。

- `teacher_serving` = AI 暂停
- `ai_serving` = AI 可答
- `resolved` = 等待学生下一次提问触发恢复

### 2. 明确“恢复”的链路

执行时需要确认以下行为在代码和测试里都可见：

- `resolve` 后广播 `status_changed: resolved`
- 学生再次发消息时，先广播 `status_changed: ai_serving`
- 之后才进入 Dify SSE 流

若顺序不稳定，要在 `chat.py` 内补强，避免前端先收到 AI 回答、后收到恢复状态。

### 3. 防止 teacher_serving 期间误调 Dify

建议在测试中直接 mock `dify_client.chat_stream`，断言：

- `ai_serving` 时会调用
- `teacher_serving` 时不会调用
- `resolved` 被 `reactivate` 后会再次调用

### 4. 报告中写清楚恢复语义

在执行报告里必须明确写：

- “恢复”是 `resolve` 后立即恢复，还是“学生下一条消息触发恢复”
- 当前代码最终采用的是哪种语义
- 前端应监听哪些 `status_changed` 事件来切换 AI/教师输入提示

## 已知陷阱

- 若把 `resolve` 直接改成 `ai_serving`，虽然看起来更直观，但会丢掉“教师已解决”的显式审计状态；如要这么做，必须经 TX 明确确认。
- `chat.py` 里 `resolved` 分支和普通状态校验的先后顺序不能乱，否则会出现学生在 `resolved` 下被 403 拒绝的问题。
- 若只靠前端隐藏 AI 输入框，而后端仍允许调 Dify，就会出现“看似暂停、实际抢答”的假闭环。
- `teacher_serving` 期间学生消息仍然要写库和广播，否则教师看不到学生的补充信息。

## 回滚方案

- Git revert 本次改动即可
- 若状态机被改坏，优先恢复到当前的 `accept -> teacher_serving -> resolve -> resolved -> reactivate -> ai_serving` 既有链路
- 若新增测试依赖 mock 结构较复杂，回滚时一并删除测试文件和报告文件
