---
id: "r07-1-exec-teacher-send"
parent: "R07-1"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "medium"
foundation: false

scope:
  - "services/gateway/app/routers/conversations.py"
  - "services/gateway/app/schemas/conversation.py"
  - "services/gateway/app/services/conversation_service.py"
  - "services/gateway/tests/test_teacher_send.py"
  - ".tasks/reports/r07-1-exec-teacher-send_report.md"

out_of_scope:
  - "services/gateway/app/routers/chat.py"           # 不改学生直连 AI 主链路
  - "services/gateway/app/routers/actions.py"        # 不改接单/解决状态机
  - "services/gateway/app/services/state_machine.py"
  - "apps/**"                                        # 不改前端 UI
  - "Dify Chatflow / dify_client"
  - "短信、邮件、站内信等额外通知渠道"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R02-师生对话与主动运营.md"
  - "services/gateway/app/models/conversation.py"
  - "services/gateway/app/routers/conversations.py"
  - "services/gateway/app/services/conversation_service.py"
  - "services/gateway/app/services/ws_manager.py"

done_criteria:
  L0: "教师在会话状态为 teacher_serving 且自己是接单教师时，可通过 HTTP 接口发送消息；消息写入 messages 表，sender_type=teacher，且立即通过 WS 向 conv:{id} 房间广播 new_message"
  L1: "pytest services/gateway/tests/test_teacher_send.py 通过；覆盖未接单教师、非 teacher_serving 状态、空内容/非法请求等拒绝路径；ruff / mypy 通过"
  L2: "手工用教师 token 调用发送接口后，GET /api/conversations/{conv_id}/messages 可看到该条 teacher 消息；学生端已连接的 WS 能实时收到 sender_type=teacher 的广播"
  L3: "完成一次完整人工插话链路：student escalate -> teacher accept -> teacher HTTP 发消息 -> student 端实时看到真人老师消息且消息顺序、created_at、sender_id 均正确"

depends_on: []
created_at: "2026-04-21"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-21 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R07-1 Executor · 教师在 `teacher_serving` 下通过 HTTP 发消息

> 目标状态：教师接单后，不需要额外的 WebSocket 反向写接口，只通过 HTTP 即可完成“写库 + WS 广播”闭环，让学生端在同一会话流里实时看到真人老师插入的消息。

## 背景

`services/gateway/app/routers/conversations.py` 当前已经有 `POST /api/conversations/{conv_id}/messages`，并且具备：

- 学生/教师共用的消息入库逻辑
- 教师仅在 `teacher_serving` 且 `conv.teacher_id == current_user.id` 时可回复
- 写库后向 `conv:{conv_id}` 房间广播 `new_message`

这说明 D1 的骨架已存在；本任务不是从零造轮子，而是把它补成 **R02 需求 1 可验收的“教师实时插入对话”能力**：

- 契约清晰（teacher 发送是正式能力，不只是 S2 临时实现）
- 权限严格（只有接单教师可发）
- 广播字段稳定（学生端能明确识别真人老师消息）
- 测试覆盖到位（防止后续重构打断闭环）

## 必读上下文

1. `docs/requirements/R02-师生对话与主动运营.md` § 需求 1
2. `services/gateway/app/routers/conversations.py`
3. `services/gateway/app/models/conversation.py`
4. `services/gateway/app/services/ws_manager.py`

## 执行重点

### 1. 明确 HTTP 契约

确认并固化教师发消息使用的正式入口：

- `POST /api/conversations/{conv_id}/messages`
- 请求体：沿用 `SendMessageRequest`
- 响应体：返回落库后的 `MessageResponse`

若当前响应字段不足以让前端区分真人老师身份，可在 **不破坏学生发消息兼容性** 的前提下补字段；否则保持最小改动。

### 2. 权限与状态守卫

至少保证：

- 只有 `teacher` / `admin` 可走教师发送路径
- 普通教师必须是 `conv.teacher_id` 对应的接单教师
- 会话状态必须是 `teacher_serving`
- `resolved / closed / pending_teacher / ai_serving` 下教师发送一律拒绝

### 3. WS 广播格式稳定

广播消息仍使用：

- `type = new_message`
- `data.sender_type = teacher`
- `data.sender_id = current_user.id`
- `data.content / created_at / conv_id` 完整

若 teacher 端前端需要额外展示字段，优先补在 `data` 中，避免另开新事件类型。

### 4. 补齐自动化测试

当前 `services/gateway/tests/` 几乎没有对会话路由的覆盖。至少新增一个独立测试文件，验证：

- 接单教师发送成功
- 非接单教师发送 403
- 非 `teacher_serving` 状态发送 403
- 成功后消息确实落库且广播函数被调用

## 已知陷阱

- `conversations.py` 现有注释还停留在 “S2 阶段只写库，不调 Dify”，容易让后续开发误以为教师发消息仍是临时能力；本任务需要把语义升级为正式闭环的一部分。
- 若直接新增“teacher 专用发送接口”，会和现有 `/messages` 形成双入口，增加维护成本；除非 TX 明确要求，否则不要扩出第二套接口。
- 广播里如果缺 `sender_type=teacher`，学生端无法稳定区分 AI 与真人老师。
- 不要在本任务中引入 Dify 或 AI 逻辑；教师消息必须是纯人工发送。

## 回滚方案

- Git revert 本次改动即可
- 若新增了测试文件，回滚时一并删除对应测试与报告
- 若修改了响应体字段导致前端不兼容，优先回滚到原有 `MessageResponse` 契约
