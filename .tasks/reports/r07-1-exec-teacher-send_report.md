# R07-1 Executor Report · 教师在 `teacher_serving` 下通过 HTTP 发消息

## 改动文件

- `services/gateway/app/routers/conversations.py`
- `services/gateway/app/schemas/conversation.py`
- `services/gateway/tests/test_teacher_send.py`
- `.tasks/reports/r07-1-exec-teacher-send_report.md`

## 未改文件

- `services/gateway/app/services/conversation_service.py`
  - 已复核 `build_message_broadcast_event`，现有广播字段已满足本任务要求：`type=new_message`、`data.conv_id`、`data.sender_type`、`data.sender_id`、`data.content`、`data.created_at`。
  - 因此本次不做行为改动，仅通过路由与测试把契约固化。

## 核心 diff 摘要

### 1. `SendMessageRequest` 正式拒绝空白内容

- 为 `content` 增加 `Field(min_length=1)`
- 增加 `field_validator("content")`
- 请求内容会先 `strip()`，全空白直接报错 `content must not be empty`
- 这样教师和学生走同一入口时，都会遵守一致的 HTTP 契约

### 2. `POST /api/conversations/{conv_id}/messages` 教师分支补强

- 明确将 `teacher` 和 `admin` 统一纳入“教师发送路径”
- 当角色为 `teacher` 或 `admin` 时：
  - 只有 `teacher_serving` 状态允许发送
  - 普通教师必须满足 `conv.teacher_id == current_user.id`
- `teacher` / `admin` 成功发送时，统一落库为：
  - `sender_type = teacher`
  - `sender_id = current_user.id`
- 保持原有广播事件类型不变，仍走：
  - `type = new_message`
  - `data = build_message_broadcast_event(...)`

### 3. 补齐 `test_teacher_send.py`

覆盖了以下场景：

- 接单教师发送成功，且会落库并广播
- 广播中包含 `sender_type=teacher`、`sender_id`、`conv_id`、`content`、`created_at`
- 管理员在 `teacher_serving` 下发送时，也走 `teacher` 语义
- 非接单教师发送返回 `403`
- 非 `teacher_serving` 状态发送返回 `403`
- 会话不存在时返回 `404`
- 空白内容在 schema 层被拒绝

## 本地校验输出

### pytest

```text
.........                                                                                                                                                                                     [100%]
========================================================================================= warnings summary =========================================================================================
app\schemas\conversation.py:10
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated 
in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
app\schemas\conversation.py:38(BaseModel):
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:38: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated 
in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
9 passed, 2 warnings in 0.59s
```

### ruff

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> ruff check app/routers/conversations.py app/schemas/conversation.py app/services/conversation_service.py tests/test_teacher_send.py
All checks passed!
```

### mypy

```text
Success: no issues found in 4 source files
```

## 关于全仓 `ruff / mypy`

首次直接对整个 `services/gateway` 运行时，发现多个 **scope 外遗留问题**，包括：

- 其他路由的 unused import / style 问题
- `python-jose` / `passlib` 的 typing stub 缺失
- 若干与本任务无关的模型类型标注问题

按照 T3 任务红线，本次 **没有越界修改** 这些文件；最终采用“仅检查本任务 scope 文件集合”的方式完成 `ruff / mypy` 自检，并已通过。

## L0-L3 自检结论

### L0

- **本地可部分验证，已通过单测覆盖关键行为**
- 已验证：
  - 接单教师在 `teacher_serving` 下可通过 HTTP 发送
  - 发送后会调用写库逻辑
  - 会调用 `broadcast_to_room("conv:{id}", payload)`
  - 广播中包含 `new_message` 与 `sender_type=teacher`
- 未做本地真实 DB + WS 集成联调，因为本轮按约束不启动本地 V2 后端

### L1

- **本地已完成**
- `pytest services/gateway/tests/test_teacher_send.py` 通过
- `ruff`（scope 文件）通过
- `mypy`（scope 文件）通过

### L2

- **需 TX / T2 在远端 165 手工验**
- 目标：
  - 教师 token 调用发送接口成功
  - `GET /api/conversations/{conv_id}/messages` 能看到 `sender_type=teacher`
  - 已连接学生端 WS 能实时收到 `new_message`

### L3

- **需 TX / T2 在远端 165 完整手工验**
- 目标链路：
  - `student escalate`
  - `teacher accept`
  - `teacher HTTP send`
  - 学生端实时看到真人老师消息
  - 核对 `sender_id`、`created_at`、消息顺序

## 给 T2 / TX 的远端 165 冒烟步骤

以下命令按远端 `http://192.168.100.165:8100` 编写。

### 1. 登录拿 token

#### 学生 token

```bash
curl -s -X POST "http://192.168.100.165:8100/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"staff_id":"2024010001","password":"2024010001"}'
```

#### 教师 token

```bash
curl -s -X POST "http://192.168.100.165:8100/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"staff_id":"T001","password":"liangshufeng"}'
```

把返回里的 `access_token` 分别记为：

- `STUDENT_TOKEN`
- `TEACHER_TOKEN`

### 2. 学生创建会话

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"r07 teacher send smoke"}'
```

从返回中记录 `id` 为 `CONV_ID`。

### 3. 学生升级为待教师处理

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/escalate" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

期望返回中 `status = pending_teacher`。

### 4. 教师接单

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/accept" \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

期望返回中：

- `status = teacher_serving`
- `teacher_id` 为当前教师 ID

### 5. 教师通过 HTTP 发送消息

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/messages" \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"同学你好，这个问题我来人工跟进。"}'
```

期望返回：

- HTTP `201`
- `sender_type = teacher`
- `sender_id` 为当前教师 ID
- `content` 为发送内容

### 6. 拉取消息列表核对落库

```bash
curl -s "http://192.168.100.165:8100/api/conversations/CONV_ID/messages" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

期望能看到教师刚发的消息，且：

- `sender_type = teacher`
- `sender_id` 正确
- `created_at` 存在
- 顺序符合会话时间线

### 7. WS 手工观察（L2 / L3）

WS 地址：

```text
ws://192.168.100.165:8100/ws?token=STUDENT_TOKEN
```

建立连接后，先发送：

```json
{"type":"join_room","data":{"conv_id":CONV_ID}}
```

教师执行第 5 步后，学生侧应收到类似事件：

```json
{
  "type": "new_message",
  "data": {
    "conv_id": CONV_ID,
    "sender_type": "teacher",
    "sender_id": TEACHER_ID,
    "content": "同学你好，这个问题我来人工跟进。",
    "created_at": "2026-..."
  }
}
```

## 交付结论

- 本任务已在 **scope 内完成代码补强 + 自动化测试 + 报告**
- 未越界修改 `chat.py / actions.py / state_machine.py / apps/** / dify_client`
- 可交回 TX / T0 审阅，再决定是否派发下一任（`r07-2` 或 `r07-3`）

## 新发现的错误模式

- 暂无新增
