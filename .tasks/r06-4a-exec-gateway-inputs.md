---
id: "r06-4a-exec-gateway-inputs"
parent: "R06-4A"
type: "feature"
status: "done"
tier: "T3"
priority: "high"
risk: "medium"
foundation: false

scope:
  - "services/gateway/app/routers/chat.py"           # 改 inputs 字段
  - "services/gateway/app/models/user.py"            # 加 relationship（仅在必要时）
  - "services/gateway/app/models/__init__.py"        # 若需要
  - "services/gateway/alembic/versions/*.py"         # 新建 migration（仅在需要加 campus 字段时）
  - "services/gateway/tests/test_chat_inputs.py"     # 新增或更新单测
  - ".tasks/reports/r06-4a-exec-gateway-inputs_report.md"

out_of_scope:
  - "apps/**"                                        # 不动 UniApp 前端
  - "Dify Chatflow 配置"                             # 这是 R06-4B 的范围
  - "services/gateway/app/routers/auth.py"           # 不改登录逻辑
  - "services/gateway/app/routers/kb.py"             # 不改 KB 路由
  - "services/gateway/app/routers/teacher*.py"       # 不改教师端路由
  - "数据库其他表结构"                                # 只允许加 campus 字段到 colleges 表

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"         # R06-4 章节
  - "docs/requirements/R05-KB-增强需求.md"            # R05-3 原需求
  - "services/gateway/app/routers/chat.py"
  - "services/gateway/app/models/user.py"

done_criteria:
  L0: "chat.py 的 dify_client.chat_stream(inputs={...}) 里不再有 college_id / student_name，改为 college_name + campus + class_id"
  L1: "pytest services/gateway/tests/test_chat_inputs.py 通过；mypy / ruff 通过"
  L2: "curl 发送一条消息，gateway 日志显示 inputs 字典包含正确的 college_name 和 class_id 字符串（非 ID）"
  L3: "用两个不同学院的测试账号各发一条消息，gateway 日志里 inputs.college_name 分别是两个不同的学院名"

depends_on: []
created_at: "2026-04-17"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-17 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-4A Executor · Gateway 把 college_name / campus / class_id 传给 Dify

> 目标状态：`chat.py` 发给 Dify 的 `inputs` 字典从当前的 `{college_id, student_name}` 改为 `{college_name, campus, class_id}`，为 R06-4B 在 Dify 侧注入学生上下文 prompt 做好数据基础。

## 背景

当前代码 `services/gateway/app/routers/chat.py:114-122`：

```python
async for event in dify_client.chat_stream(
    query=query,
    user_id=str(user.id),
    conversation_id=conv.dify_conversation_id,
    inputs={
        "college_id": str(user.college_id or ""),
        "student_name": user.name or "",
    },
):
```

问题：
1. `college_id` 是**数字 ID**，Dify prompt 里引用 `{{college_id}}` 拿到的是 `"5"` 而不是"临床与基础医学院"，无法用于人读的 prompt 注入
2. 缺 `campus`（校区信息）
3. 缺 `class_id`（班级信息）
4. `student_name` 实际不用（Dify 内置 user_id 已足够标识用户，name 是 PII 不应外发）

## 必读上下文

1. `docs/requirements/R06-P0-quick-wins.md` § R06-4 / R06-4A
2. `services/gateway/app/models/user.py`（当前 User / College / Class 模型）
3. `services/gateway/app/routers/chat.py`（当前实现）

## 现状分析（T0 已摸过）

### User / College / Class 模型现状

查看 `services/gateway/app/models/user.py:23-58`：

- `College` 表：`id`, `name`，**没有 campus 字段**
- `Class` 表：`id`, `name`, `college_id`, `grade_year`
- `User` 表：`college_id` (FK), `class_id` (FK)

**但 User 模型没有定义到 College/Class 的 relationship**（只有 `bindings`），所以 `user.college` 会报 AttributeError。

### 三个 inputs 字段的来源

| 目标字段 | 数据来源 | 陷阱 |
|---------|---------|------|
| `college_name` | `user.college_id` → query `colleges.name` | User 没 relationship，需 join 或额外 query |
| `campus` | **当前表结构无此字段** | 需方案决策（见下方） |
| `class_id` | `user.class_id` → query `classes.name` | 同样需要 join；字段命名易混：传的是**人读名**还是数据库 ID？ |

### campus 字段方案选择

**三选一**，执行前先**咨询 T0 或 TX 决定**：

| 方案 | 做法 | 优劣 |
|------|-----|------|
| **A. 加字段 + migration** | `College` 表加 `campus: str`，写 Alembic migration，初始化数据 | 彻底解决，但增大 scope（数据迁移 + 字段维护） |
| **B. 硬编码映射** | 代码里维护 `{college_name: campus}` 字典 | 快但难维护，学校校区变动即失效 |
| **C. 暂传空字符串** | 传 `campus=""`，留 TODO | 最轻，但 Dify prompt 端拿到空值要做容错 |

**T0 默认推荐：C**（当前阶段项目复杂度不值得 A 的维护成本；B 有硬编码风险）
- R06-4B 的 Dify prompt 要写 `如果 campus 为空，则省略"{campus}"部分`
- 在 `docs/design/` 新开一个 `TODO-campus-field.md` 追踪后续

**如果 T1 或 TX 决定方案 A**，Scope 要加：
- `alembic/versions/xxxx_add_campus_to_colleges.py`
- `scripts/backfill_campus.py`（或类似）

## Executor 执行步骤

### Step 1：选定 campus 方案

在 `.tasks/reports/r06-4a-exec-gateway-inputs_report.md` 开头明确写：
> **我选择方案 X，理由是 ...**

（推荐 C，除非 T1/TX 另有指示）

### Step 2：给 User 模型加 relationship

编辑 `services/gateway/app/models/user.py`：

```python
class User(Base):
    # ... 现有字段保留 ...

    bindings: Mapped[List["UserBinding"]] = relationship(back_populates="user")
    college: Mapped[Optional["College"]] = relationship(lazy="selectin")
    class_: Mapped[Optional["Class"]] = relationship(
        foreign_keys=[class_id], lazy="selectin"
    )
```

注意：
- 字段名用 `class_`（避免 Python 关键字冲突）
- `lazy="selectin"` 避免 N+1 问题
- 不要破坏现有的 bindings relationship

### Step 3：修改 chat.py 的 inputs 构造

找到 `services/gateway/app/routers/chat.py` 中 `_stream_ai_response` 函数，改：

```python
# 旧
inputs={
    "college_id": str(user.college_id or ""),
    "student_name": user.name or "",
},

# 新
inputs={
    "college_name": user.college.name if user.college else "",
    "campus": "",  # 方案 C：TODO
    "class_id": user.class_.name if user.class_ else "",
},
```

**若方案 A**，`campus` 改为 `user.college.campus if user.college else ""`。

### Step 4：写/更新单测

创建 `services/gateway/tests/test_chat_inputs.py`（或扩展已有 test_chat.py）：

```python
# 核心断言：
# 1. 构造一个 User 带 college + class_
# 2. 调用 _stream_ai_response 逻辑（或抽一个 build_dify_inputs 纯函数单测）
# 3. 断言返回的 inputs 字典 key 集合 == {"college_name", "campus", "class_id"}
# 4. 断言 college_name 是字符串且等于 college.name
# 5. 断言 class_id 是字符串且等于 class_.name
```

**建议抽出**：`chat.py` 里把 `inputs={...}` 改为调用一个 `build_dify_inputs(user)` 纯函数，便于单测。

### Step 5：手工验证

1. 启动 gateway：`cd services/gateway && python -m app.main`
2. 用两个不同学院的测试账号（见 PROJECT-SECRETS.md §6）登录获 token
3. 各发一条消息到 `POST /chat/messages`
4. 查看 gateway 日志，确认 inputs 输出正确

### Step 6：写执行报告

在 `.tasks/reports/r06-4a-exec-gateway-inputs_report.md` 写：

- 选择的方案（A/B/C）
- 改动文件清单
- 测试运行输出
- 发现的新陷阱 → 回传 antipatterns
- 遗留 TODO（如 campus 字段后续）

## 已知陷阱

- User 模型**目前没有 college/class relationship**，直接 `user.college.name` 会 AttributeError。必须先加 relationship 或用 SQL join。
- 如果数据库里**某些 User 的 college_id 为 NULL**（测试账号可能如此），必须处理空值，否则报错。
- Dify 的 inputs 只接受 **字符串**（不接受 None 或 int），空值必须转为 `""`。
- `student_name` 字段删掉后，如果 Dify Chatflow 里有 `{{student_name}}` 变量引用会导致 Dify 报错。**建议先在 Dify 确认没有引用再删，或先保留 student_name 字段做灰度**。
  - 💡 **安全做法**：inputs 字典同时包含新旧字段（`college_id` 和 `college_name` 共存），R06-4B 做完后再删 `college_id`。
- Dify `inputs` 字段在 Chatflow 里需要**预先声明变量**，gateway 传入未声明的变量会被丢弃。需要 TX 在 Dify UI 里先声明 `college_name` / `campus` / `class_id`（这是 R06-4B 的范围）。
- Alembic migration 必须在**pg 已有数据**的情况下安全执行，带默认值或 nullable=True。

## 不做的事（out_of_scope）

- 不改 Dify Chatflow（R06-4B 的范围）
- 不改 UniApp 前端
- 不改其他 router（auth / kb / teacher）
- 不改 User 其他字段
- 不改数据库其他表
- 不做性能优化或重构

## 回滚方案

- Git revert 本次改动即可
- 若写了 Alembic migration，`alembic downgrade -1`

## 完成后

- PR 描述或报告里链到本任务 ID（r06-4a-exec-gateway-inputs）
- T2 会独立审 L0-L2
- TX 做 R06-4B（在 Dify UI 加变量声明 + 注入上下文 prompt）
- 全部完成后跑 s3-deploy-test.md 冒烟
