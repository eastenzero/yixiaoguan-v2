# R07-3 Executor Report · `escalate` 时广播学院教师工单通知

## 改动文件

- `services/gateway/app/routers/actions.py`
- `services/gateway/app/services/ws_manager.py`
- `services/gateway/tests/test_escalate_notify.py`
- `.tasks/reports/r07-3-exec-escalate-notify_report.md`

## 核心 diff 摘要

### 1. `escalate` 通知失败不阻塞主流程

在 `actions.py` 的 `escalate()` 中补了通知容错：

- 状态转换 `ai_serving -> pending_teacher` 成功后
- 调用 `_notify_college_teachers()` 时若抛异常
- 仅记 `warning log`
- **不会回滚会话状态，也不会阻断后续 `status_changed` 广播**

这与本批次默认立场保持一致：**通知失败不阻塞 escalate**。

### 2. 同学院 teacher 过滤语义被测试锁住

`_notify_college_teachers()` 本身仍通过 SQL 查询筛选：

- `User.role == teacher`
- `User.college_id == current_user.college_id`
- `User.is_active`

测试中不再只断言最终 `teacher_ids`，还直接检查 `db.execute()` 收到的查询语句，锁住这 3 个过滤条件，避免后续把筛选责任错误地下沉到 `broadcast_to_college_teachers()`。

### 3. `broadcast_to_college_teachers()` 行为保持最小

`ws_manager.py` 本次没有改业务逻辑，只清理了 scope 内 lint：

- 拆分多重 import
- 删除未使用的 `json`

广播行为仍是：

- 接收 `teacher_ids`
- 逐个 `send_to_user()`
- **college_id 参数不参与再次筛选**

这与任务文件和 T0 审阅结论一致。

### 4. 测试覆盖补齐

`test_escalate_notify.py` 现在覆盖：

- 同学院教师收到 `escalation_notify`
- 查询语句确实只筛选同学院 `teacher`
- 学院下没有教师时不报错
- `broadcast_to_college_teachers()` 只向传入的 `teacher_ids` 发送
- `escalate` 成功后会广播 `status_changed = pending_teacher`
- `_notify_college_teachers()` 失败时，`escalate` 仍成功返回

## 本地校验输出

### pytest

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_escalate_notify.py -q
.....                                                                       [100%]
========================================================================================= warnings summary =========================================================================================
app\schemas\conversation.py:10
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:10: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
app\schemas\conversation.py:38(BaseModel):
  C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway\app\schemas\conversation.py:38: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
5 passed, 2 warnings in 0.67s
```

### ruff

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> ruff check app/routers/actions.py app/services/ws_manager.py tests/test_escalate_notify.py
All checks passed!
```

### mypy

```text
app\services\ws_manager.py:21: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
app\services\ws_manager.py:22: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
app\services\ws_manager.py:23: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
Success: no issues found in 3 source files
```

## L0-L3 自检结论

### L0

- **本地已通过单测验证主链路语义**
- 已验证：
  - `escalate` 触发状态从 `ai_serving` 进入 `pending_teacher`
  - 调用学院教师通知
  - 再向会话房间广播 `status_changed`
  - 通知失败不阻塞主流程

### L1

- **本地已完成**
- `pytest services/gateway/tests/test_escalate_notify.py` 通过
- `ruff`（scope 文件集合）通过
- `mypy`（scope 文件集合）通过

### L2

- **需 TX / T2 在远端 165 手工验**
- 目标：
  - 至少 2 个同学院教师在线、1 个其他学院教师在线
  - 触发 `escalate` 后
  - 只有同学院在线教师收到 `escalation_notify`
  - payload 包含：`conv_id / student_id / title / status / created_at`

### L3

- **需 TX / T2 在远端 165 手工验**
- 目标链路：
  - student `escalate`
  - 同学院 teacher 收到通知
  - teacher 用 `conv_id` 发起 `accept`
  - 会话房间收到 `teacher_serving` 的 `status_changed`
  - 形成“呼叫人工 -> 通知 -> 接单”闭环

## 远端 165 冒烟步骤（给 TX / T2）

远端基址：`http://192.168.100.165:8100`

### 0. 已知测试账号

根据当前种子数据，远端已验证可用账号里：

- 学生：`2024010001 / 2024010001`
- 教师：`T001 / liangshufeng`
- 管理员：`A001 / admin123`

**注意**：当前代码仓库种子数据里只明确存在 1 个教师账号 `T001`。若要完整验证“2 个同学院 + 1 个异学院教师”的 L2/L3，需要 TX/T2 在远端准备额外教师账号；否则只能完成部分冒烟。

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

#### 管理员 token（用于验证默认不接收通知）

```bash
curl -s -X POST "http://192.168.100.165:8100/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"staff_id":"A001","password":"admin123"}'
```

记为：

- `STUDENT_TOKEN`
- `TEACHER_TOKEN`
- `ADMIN_TOKEN`
- 如果远端还有额外教师，再记 `TEACHER2_TOKEN` / `OTHER_COLLEGE_TEACHER_TOKEN`

### 2. 建立教师 WS 监听

`escalation_notify` 走的是**用户级推送**，不是房间广播，所以教师连接后**不需要 join_room**。

#### 打开同学院教师连接

```text
ws://192.168.100.165:8100/ws?token=TEACHER_TOKEN
```

如果有第二个同学院教师：

```text
ws://192.168.100.165:8100/ws?token=TEACHER2_TOKEN
```

#### 打开管理员连接（应当收不到该通知）

```text
ws://192.168.100.165:8100/ws?token=ADMIN_TOKEN
```

#### 若远端有异学院教师，再打开异学院教师连接

```text
ws://192.168.100.165:8100/ws?token=OTHER_COLLEGE_TEACHER_TOKEN
```

### 3. 学生创建会话

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations" \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"r07-3 escalate smoke"}'
```

记录返回中的 `id` 为 `CONV_ID`。

### 4. 学生触发 escalate

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/escalate" \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

期望返回：

- `status = pending_teacher`

### 5. 观察教师 WS 收到通知

同学院教师连接应收到：

```json
{
  "type": "escalation_notify",
  "data": {
    "conv_id": 123,
    "student_id": 456,
    "title": "r07-3 escalate smoke",
    "status": "pending_teacher",
    "created_at": "2026-..."
  }
}
```

期望：

- **同学院教师收到**
- **管理员不收到**
- **异学院教师不收到**（若远端有该账号）

### 6. 教师根据 payload 直接接单

```bash
curl -s -X POST "http://192.168.100.165:8100/api/conversations/CONV_ID/accept" \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

期望返回：

- `status = teacher_serving`
- `teacher_id` 为当前教师 ID

### 7. 学生或教师加入会话房间，观察状态变更闭环

建立任一会话侧连接：

```text
ws://192.168.100.165:8100/ws?token=STUDENT_TOKEN
```

连接后发送：

```json
{"type":"join_room","data":{"conv_id":CONV_ID}}
```

在第 6 步接单成功后，应收到类似消息：

```json
{
  "type": "status_changed",
  "data": {
    "conv_id": 123,
    "status": "teacher_serving",
    "teacher_id": 789,
    "teacher_name": "梁淑芬"
  }
}
```

## 是否存在需要 T0 判断的问题

- **没有**
- 本次实现完全遵循默认立场：
  - 只同学院 `teacher` 收通知
  - `admin` 不参与通知对象
  - 离线教师忽略
  - 通知失败不阻塞 `escalate`
  - payload 保持最小稳定字段集

## 当前阶段状态

- `r07-3`：**已完成，代码 + 测试 + 报告齐备**
- `r07-2`：**尚未开始**，等待 TX / T0 基于本次阶段性交付继续指令

## 新发现的错误模式

- 暂无新增
