---
id: "r06-3b-review-prompt"
parent: "R06-3'"
type: "review"
status: "pending"                   # 等 r06-3a 产出后 T0 启动
tier: "T0"                          # T0 自己做的审阅任务
priority: "high"
risk: "low"

scope:
  - "docs/design/dify-prompt-review.md"       # 本次审阅的产出
  - "可能追加的 R06-3c 任务文件（若结论是需补强）"

out_of_scope:
  - "services/**"
  - "apps/**"
  - "任何 Dify 的写操作"            # 若判定需改 prompt，由 TX 手动贴 Dify UI，不由本任务执行
  - "修改已有 scout 报告文件"        # 只读 r06-3a 的产出，不改

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"   # R06-3 / R06-3' 章节
  - "docs/design/dify-current-prompt.md"        # r06-3a 的主要产出
  - "docs/design/dify-current-config.md"        # r06-3a 的附带产出
  - ".tasks/r06-3a-scout-dify-prompt.md"        # 抓取方法与范围

done_criteria:
  L0: "docs/design/dify-prompt-review.md 存在"
  L1: "文件包含：对现状 prompt 的逐节点评估 + 差异对照表 + 结论（通过 / 需补强）"
  L2: "若结论为需补强，有对应的 `.tasks/r06-3c-exec-prompt-patch.md` 文件或 TX UI 操作清单"
  L3: "TX 审阅后确认 '可据此推进 R06-4B 与 batch-4' 或 '需先补强再推进'"

depends_on:
  - "r06-3a-scout-dify-prompt"        # 强依赖：没有 Scout 产出就没法审阅
created_at: "2026-04-20"
---

# R06-3b Review · T0 审阅 Dify 现有 prompt 是否需补强

> 目标状态：基于 r06-3a 抓回来的 Dify 现状 prompt，T0 给出**明确判定**——
> **(A)** 现状已符合 R06-3 设计意图，直接进入 R06-4B / batch-4；
> **(B)** 需要补强，产出**具体改动清单**并由 TX 或新建 `r06-3c` 任务落地。
>
> 这是 R06-3'（"审阅模式"）的核心闭环动作。

## 背景

2026-04-17 TX 口头告知"Dify 主 LLM 节点**已有**由 AI 早期写入的 system prompt"，V2 仓内无记录。
因此把 R06-3 原来的"注入人设 prompt"任务改为 **R06-3'**：

1. `r06-3a` 由 T3 Kimi Scout 抓回现状到 `docs/design/dify-current-prompt.md`（本任务**输入**）
2. **`r06-3b`（本任务）** T0 对照 R06-3 原设计意图，判断现状是否够用
3. 若够用：无需动作，更新 R06 spec 把 R06-3' 标为 ✅
4. 若不够用：新建 `r06-3c` 任务（TX 手动贴 Dify，或由新 T3 执行）

## 必读输入

- `docs/design/dify-current-prompt.md`（r06-3a 产出；必须存在非空）
- `docs/design/dify-current-config.md`（r06-3a 产出；辅助）
- `docs/requirements/R06-P0-quick-wins.md` § R06-3（原设计意图，含人设 / 边界 / 拒答 / RAG 引用格式）
- `docs/requirements/R04-v2-新增需求.md` 与 `R05-KB-增强需求.md`（学生上下文需求，与 R06-3 有交叉）

## 审阅步骤

### Step 1：读 r06-3a 产出，结构化记录

把 `dify-current-prompt.md` 中每个 LLM 节点的 prompt 摘出，按以下表格整理到本任务产出里：

| 节点 | 模型 | 温度 | system prompt 摘要 | 用户消息模板 |
|------|-----|-----|-------------------|-------------|
| ... | ... | ... | ... | ... |

### Step 2：对照 R06-3 原设计意图

R06-3 原文要求 prompt 至少包含以下要素：

1. **人设**：医学院新生辅助 AI / 医小管
2. **能力边界**：能答什么、不能答什么
3. **RAG 引用格式**：引用 `{{#context#}}` 时如何标注来源
4. **拒答策略**：超纲问题（医疗诊断、违法、个人隐私、无 KB 证据）如何回答
5. **转人工触发**：学生明确要求找老师 / AI 连续 2 轮无答案 → 如何引导

对每个要素，给出评级：

| 要素 | 现状满足程度 | 证据（摘录） | 缺口 |
|------|------------|------------|-----|
| 人设 | ✅ 有 / ⚠️ 部分 / ❌ 无 | prompt 中 "..." | ... |
| 能力边界 | ... | ... | ... |
| RAG 引用格式 | ... | ... | ... |
| 拒答策略 | ... | ... | ... |
| 转人工触发 | ... | ... | ... |

### Step 3：结合 R05 个性化需求（前瞻）

R06-4A/B 会让 gateway 传新的学生上下文字段（`college_name` / `campus` / `class_id`）。
检查现状 prompt **是否已使用** `{{#inputs.college_name#}}` 等变量：

- 如果现状已用旧字段名（如 `{{#inputs.college_id#}}` / `{{#inputs.student_name#}}`）→ **R06-4B 必须改 prompt**，本次审阅在结论里标明
- 如果现状完全没有用学生上下文变量 → R06-4B 是"新增注入"而非"修改"
- 如果现状用的变量名与 R06-4A 的新字段名**不一致** → 建议把 R06-4A 和本审阅产出**强绑定**，先定字段名再改 gateway

### Step 4：结论与动作

得出以下之一：

- **A. 通过（无需改动）**
  - 现状 prompt 已覆盖 R06-3 全部要素
  - R06-4B 只需"新增"学生上下文变量引用，不冲突
  - 动作：把 R06 spec 中 R06-3' 标 ✅，加变更日志

- **B. 需局部补强**
  - 列出**具体要改的行 / 段 / 变量名**
  - 不新建大任务，用 `r06-3c-exec-prompt-patch.md`（TX 手动贴 Dify UI）收尾
  - 注明每项改动对应的 R06 要素

- **C. 需重写**
  - 现状 prompt 与 R06-3 设计分歧过大
  - 起草完整的新 prompt 文本（放进 `docs/design/dify-prompt-target-v2.md`）
  - 在 `r06-3c-exec-prompt-patch.md` 中给 TX 明确的"整段替换"指引

### Step 5：产出文件

创建 `docs/design/dify-prompt-review.md`，必含章节：

```markdown
# Dify Prompt 审阅报告（YYYY-MM-DD）

> 审阅者：T0
> 依据：docs/design/dify-current-prompt.md（r06-3a Scout 产出）
> 对照：docs/requirements/R06-P0-quick-wins.md § R06-3

## 1. 现状摘要
（Step 1 的表）

## 2. 要素覆盖评估
（Step 2 的表）

## 3. 与 R06-4 的字段名一致性检查
（Step 3 的结论）

## 4. 审阅结论
- 分级：A 通过 / B 局部补强 / C 重写
- 理由：...
- 对后续任务的影响：
  - R06-4B 是否受阻：...
  - batch-4 是否可启动：...

## 5. 补强动作（若结论 != A）
- 新建 `.tasks/r06-3c-exec-prompt-patch.md`（或直接在本文件末尾给 TX UI 操作清单）
- 动作 1：...
- 动作 2：...

## 6. 变更建议传递
- 需回灌到 R06 spec 的内容：...
- 需回灌到 R04/R05 的内容：...
```

## 已知陷阱

- r06-3a Scout 可能抓不全（prompt 被截断 / 变量没展开），若发现，**先退回 Scout 补抓**再审阅，不要盲判
- 现状 prompt 如果是早期 AI 写的，可能有废弃变量名（如 `{{#student_id#}}` 这种旧 schema），需与当前 gateway 对账
- 不要在审阅报告里**直接把密钥 / SSH / 账号**写进去（SECRETS 文件外不保留任何敏感信息）
- 如果 Dify 有 "草稿 / 已发布" 两份 prompt 且内容不一致，以 **已发布** 为准，草稿的差异单独记录

## 不做的事（out_of_scope）

- 不登录 Dify
- 不改 Dify 任何节点
- 不改 V2 仓的代码（`services/` / `apps/`）
- 不起草 R06-4B 的 TX 操作清单（那是 batch-4 的 R06-4B 自己的职责，本审阅只判断"是否受阻"）
- 不起草新 Scout 任务（如果需要补抓，回流到 r06-3a 说明）

## 完成后

1. 产出 `docs/design/dify-prompt-review.md`
2. 若结论为 B / C，同时产出 `.tasks/r06-3c-exec-prompt-patch.md`
3. 更新 `docs/requirements/R06-P0-quick-wins.md`：
   - 变更日志追加一行
   - 根据结论把 R06-3' 标为 ✅ / 🟡（待补强）
4. 通知 T1 启动 batch-4（若 R06-4B 未受阻）
