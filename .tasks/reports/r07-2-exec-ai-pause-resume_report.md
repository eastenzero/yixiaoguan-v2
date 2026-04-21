# R07-2 Executor Report · AI 暂停 / 恢复 + 学生消息状态守卫

## 改动文件

- `services/gateway/app/routers/conversations.py`
- `services/gateway/app/services/state_machine.py`
- `services/gateway/tests/test_ai_pause_resume.py`
- `.tasks/reports/r07-2-exec-ai-pause-resume_report.md`

## 已审阅但未改的文件

- `services/gateway/app/routers/chat.py`
  - 已核对当前实现，已满足本任务默认立场：
    - `resolved` 时先 `reactivate`
    - 先广播 `status_changed: ai_serving`
    - 再写学生消息
    - 仅 `ai_serving` 时进入 Dify SSE
  - 因此本次 **不做代码改动**，只通过补测把语义固化。
- `services/gateway/app/routers/actions.py`
  - 本轮不改，避免越界到 `r07-3` 已锁定文件。
- `services/gateway/tests/test_teacher_send.py`
  - 本轮不改，仅做回归执行，确认 `r07-1` 不回退。

## 核心 diff 摘要

### 1. `chat.py` 恢复语义复核结论

本次没有修改 `chat.py` 主逻辑，但已确认它当前行为与 T0 默认立场一致：

- `teacher_serving` / `pending_teacher` 下，学生调用 `POST /api/chat/send`
  - 只写库
  - 只广播
  - 返回 JSON
  - **不调用 Dify**
- `resolved` 下，学生再次调用 `POST /api/chat/send`
  - 先 `reactivate -> ai_serving`
  - 先广播 `status_changed: ai_serving`
  - 再恢复 Dify SSE

也就是说，**恢复语义 = 学生下次消息触发**，不是 `resolve` 时立即恢复。

### 2. `conversations.py` 补学生分支状态守卫

在 `POST /api/conversations/{conv_id}/messages` 中，仅补了学生分支：

- `closed`
  - 返回 `403`
  - 错误文案：`会话已关闭，无法发送消息`
- `resolved`
  - 先调用 `transition(db, conv, "reactivate", actor=current_user)`
  - 再广播：
    - `type = status_changed`
    - `data.status = ai_serving`
    - `data.previous_status = resolved`
  - 然后继续走 `/messages` 既有 JSON 路径：写库 + `new_message` 广播 + 返回 `MessageResponse`
- `ai_serving` / `pending_teacher` / `teacher_serving`
  - 保持学生可发消息
  - `/messages` 不接 Dify，只做写库与广播

### 3. `state_machine.py` 未改转换表

本次 **没有修改 `TRANSITIONS`**，只清理了一个 scope 内遗留 lint：

- 删除未使用的 `UserRole` import

状态机仍保持：

- `teacher_serving -> resolve -> resolved`
- `resolved -> reactivate -> ai_serving`

没有新增状态，也没有改变转换语义。

### 4. `test_ai_pause_resume.py` 补齐覆盖

新增 / 扩展覆盖如下：

- `ai_serving` 下学生发消息会调用 Dify
- `pending_teacher` 下学生发消息不调用 Dify
- `teacher_serving` 下学生发消息不调用 Dify
- `resolved` 下学生发消息会先 `reactivate`，再调 Dify
- `conversations.py` 在 `ai_serving / pending_teacher / teacher_serving` 下允许学生发消息
- `conversations.py` 在 `resolved` 下会先恢复再写库广播
- `conversations.py` 在 `closed` 下直接 `403`

## 本地校验输出

### pytest · `test_ai_pause_resume.py`

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_ai_pause_resume.py -q
.........                                                                   [100%]
========================================================================================= warnings summary =========================================================================================
app\schemas\conversation.py:10
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
app\schemas\conversation.py:38
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:38: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
9 passed, 2 warnings in 0.82s
```

### pytest · `test_teacher_send.py` 回归

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_teacher_send.py -q
.........                                                                     [100%]
========================================================================================= warnings summary =========================================================================================
app\schemas\conversation.py:10
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
app\schemas\conversation.py:38(BaseModel):
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:38: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
9 passed, 2 warnings in 0.68s
```

### ruff

```text
All checks passed!
```

### mypy

```text
Success: no issues found in 4 source files
```

## L0-L3 自检结论

### L0

- **本地已验证 AI 暂停 / 恢复的核心契约**
- 已验证：
  - `ai_serving` 时学生消息会触发 Dify
  - `pending_teacher` / `teacher_serving` 时学生消息不触发 Dify
  - `resolved` 时不是立刻恢复，而是由学生下一次消息触发 `reactivate -> ai_serving`
  - `/api/conversations/{conv_id}/messages` 的学生分支已补上 `closed` 与 `resolved` 守卫

### L1

- **本地已完成**
- `pytest services/gateway/tests/test_ai_pause_resume.py` 通过
- `pytest services/gateway/tests/test_teacher_send.py` 回归通过
- `ruff`（scope 文件集合）通过
- `mypy`（scope 文件集合）通过

### L2

- **需 TX / T2 在远端 165 手工验**
- 目标：
  - `pending_teacher` / `teacher_serving` 下学生发消息只返回 JSON，不返回 SSE
  - Gateway 日志无新增 Dify 请求
  - `resolved` 下学生发下一条时先看到 `status_changed: ai_serving`，再收到 AI SSE
  - `closed` 下学生消息被 `403` 拒绝

### L3

- **需 TX / T2 在远端 165 手工验**
- 目标链路：
  - `pending_teacher -> teacher_serving -> resolved -> ai_serving`
  - 人工介入期间 AI 0 次回复
  - 恢复后 AI 仅按学生下一次提问回复 1 次
  - `/messages` 端点始终保持 JSON 返回，不参与 SSE

## 给前端的一行说明

前端应监听 `status_changed` 的 `pending_teacher`、`teacher_serving`、`resolved`、`ai_serving` 4 种状态，并据此切换“等待老师 / 老师处理中 / 已解决待再次提问 / AI 已恢复”的输入提示；其中 `ai_serving` 恢复事件来自**学生下一次消息触发的 reactivate**，不是老师点击 `resolve` 的瞬间。

## 远端 165 冒烟步骤（给 TX / T2）

基址：`http://192.168.100.165:8100`

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

记为：

- `STUDENT_TOKEN`
- `TEACHER_TOKEN`

### 2. 学生创建会话

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"r07-2 ai pause resume smoke"}'
```

记录返回中的 `id` 为 `CONV_ID`。

### 3. 先验证 `ai_serving` 行为

学生直接走 `/api/chat/send`：

```bash
curl -N -X POST "http://192.168.100.165:8100/api/chat/send" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conv_id":CONV_ID,"content":"AI 在吗？"}'
```

期望：

- 返回 `text/event-stream`
- 可看到 AI 流式返回
- 证明 `ai_serving` 会调 Dify

### 4. 进入 `pending_teacher`，验证学生消息不调 Dify

#### 4.1 学生呼叫老师

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/escalate" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

期望：

- `status = pending_teacher`

#### 4.2 学生在 `pending_teacher` 下发消息

```bash
curl -s -X POST "http://192.168.100.165:8100/api/chat/send" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conv_id":CONV_ID,"content":"老师接单前我再补充一点"}'
```

期望：

- 返回 JSON
- **不是** SSE
- Gateway 无新 Dify 请求

### 5. 进入 `teacher_serving`，验证学生消息仍不调 Dify

#### 5.1 教师接单

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/accept" \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

期望：

- `status = teacher_serving`

#### 5.2 学生在 `teacher_serving` 下发消息

```bash
curl -s -X POST "http://192.168.100.165:8100/api/chat/send" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conv_id":CONV_ID,"content":"老师处理中时我补充一下"}'
```

期望：

- 返回 JSON
- **不是** SSE
- Gateway 无新 Dify 请求

### 6. 进入 `resolved`，验证“学生下一次消息触发恢复”

#### 6.1 教师标记解决

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/resolve" \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

期望：

- `status = resolved`

#### 6.2 建立学生 WS 观察状态恢复

连接：

```text
ws://192.168.100.165:8100/ws?token=STUDENT_TOKEN
```

发送：

```json
{"type":"join_room","data":{"conv_id":CONV_ID}}
```

#### 6.3 学生再次发消息触发恢复

```bash
curl -N -X POST "http://192.168.100.165:8100/api/chat/send" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conv_id":CONV_ID,"content":"我还有后续问题"}'
```

期望顺序：

- WS 先收到：

```json
{
  "type": "status_changed",
  "data": {
    "conv_id": CONV_ID,
    "status": "ai_serving",
    "previous_status": "resolved"
  }
}
```

- 之后才看到 AI 流式响应
- 这证明 **恢复不是 resolve 立即发生，而是学生下一次消息触发**

### 7. 验证 `/messages` 在 `resolved` 下也会先恢复，但仍只返回 JSON

先让老师再次接单并再次 `resolve`，使会话回到 `resolved` 后，再执行：

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/messages" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"resolved 状态下通过 messages 发消息"}'
```

期望：

- HTTP `201`
- 返回 JSON `MessageResponse`
- **不会**返回 SSE
- 学生 WS 先收到 `status_changed: ai_serving`
- 再收到 `new_message`

### 8. 验证 `closed` 下学生被拒绝

#### 8.1 关闭会话

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/close" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

期望：

- `status = closed`

#### 8.2 学生通过 `/messages` 再发消息

```bash
curl -i -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/messages" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"closed 后继续发送"}'
```

期望：

- HTTP `403`
- body 中包含：`会话已关闭，无法发送消息`

## 交付结论

- `r07-2` 已在 scope 内完成代码、测试与报告
- 没有改 `TRANSITIONS` 表
- 没有改 `actions.py / ws_manager.py / test_teacher_send.py`
- 可交回 TX / T0 审阅

## 新发现的错误模式

- **现象**：在 Windows PowerShell 下并行执行 `ruff / mypy` 时，带相对路径参数的命令偶发出现路径解析抖动，导致误报“cannot read file / 系统找不到指定路径”。
- **正确做法**：若并行批量检查出现明显与代码无关的路径错误，应立即用同一工作目录下的**单条命令重跑一次**，以区分工具/壳层抖动与真实代码问题。
