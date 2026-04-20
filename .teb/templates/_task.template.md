---
# ===== 必填字段 =====
id: ""                    # 任务唯一标识，如 "auth-login-api"
parent: ""                # 父任务 ID，顶层任务留空
type: "feature"           # feature / bugfix / integration-test
status: "pending"         # pending → in_progress → verify → done / failed / blocked
tier: "T3"                # T0=架构设计 T1=分解派发 T2=独立验证 T3=具体执行
priority: "medium"        # high / medium / low
risk: "medium"            # high / medium / low（high 优先安排人工审查）
foundation: false         # true = 地基模块，其他模块依赖它，必须优先完成

# ===== 作用域（防止 AI 越界）=====
scope:                    # 允许修改的文件/目录（白名单）
  - "src/example/file.ts"
out_of_scope:             # 禁止触碰的文件/目录（黑名单）
  - "src/unrelated/**"

# ===== 上下文（AI 开始前必须先读）=====
context_files:            # 开工前必须阅读的文件列表
  - ".teb/antipatterns.md"

# ===== 完成标准（面向目标状态，不是面向动作）=====
done_criteria:
  L0: ""                  # 存在性检查：文件/函数/导出是否存在
  L1: ""                  # 静态检查：编译/类型检查/lint 是否通过
  L2: ""                  # 运行时检查：指定的测试命令是否全部通过
  L3: ""                  # 语义检查：功能是否符合描述的目标状态（人工或强模型判定）

# ===== 可选字段 =====
depends_on: []            # 前置依赖任务 ID 列表
created_at: ""            # 格式：2026-04-03 20:41:30
completed_at: ""          # 格式同上
verified_by: ""           # "human" / "script" / "t2-reviewer" 等

# ===== Bugfix 专用（type: bugfix 时填写）=====
# reproduction_steps:     # 精确的复现步骤
#   - "步骤1"
#   - "步骤2"
# root_cause: ""          # T0 诊断的根因（具体到文件和逻辑）
# affected_modules: []    # 可能波及的模块
# regression_test: ""     # 修复后必须新增的回归测试描述

# ===== 打包信息（父任务用，T1 填写）=====
# batches:
#   - name: "batch-1"
#     tasks: ["task-a", "task-b"]
#     parallel: true
#   - name: "batch-2"
#     tasks: ["task-c"]
#     depends_on: "batch-1"
---

# [任务标题]

> 用一两句话描述**目标状态**——完成后世界应该变成什么样。
> 不要写"实现xxx"、"开发xxx"这种动作描述。

## 背景

> 为什么需要做这件事？它在更大的目标中扮演什么角色？

## 已知陷阱

> 从错题本或历史经验中提取的、与本任务相关的注意事项。
> 没有则写"暂无"。
