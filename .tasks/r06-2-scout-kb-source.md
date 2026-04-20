---
id: "r06-2-scout-kb-source"
parent: "R06-2"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "low"
foundation: true                    # Executor 依赖此 Scout 的产出

scope:
  - "docs/design/kb-source-scout-report.md"   # 仅允许创建此产出文件

out_of_scope:
  - "services/**"                   # 不动代码
  - "apps/**"
  - "../kb-pipeline/**"             # 不改 KB 仓，只读
  - "scripts/migrate_kb.py"         # Executor 任务才会改

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"    # 第 R06-2 章节
  - "docs/PROJECT-CONTEXT.md"                    # 第 §2 仓库全景

done_criteria:
  L0: "docs/design/kb-source-scout-report.md 存在"
  L1: "报告中至少包含 4 个章节：文件位置、数据格式、字段映射、数量清点"
  L2: "报告末尾有明确的 '推荐 Executor 做法' 段落，列出迁移脚本的 3 条关键改动"
  L3: "T0 或 T1 审阅后判定'可据此起草 Executor 任务'"

depends_on: []
created_at: "2026-04-17"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-17 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-2 Scout · 摸清 KB 仓 960 条最终产出的位置和格式

> 目标状态：Executor 在起草迁移脚本前，**已知**KB 仓 960 条数据的精确位置、文件格式、字段名、与 v1 KB 的差异映射。**不**在此任务中动任何代码。

## 背景

`R06-2` 要把 Dify 全局 dataset 从 v1 的 731 条替换为 KB 仓 W1 产出的 960 条。
当前 `services/gateway/scripts/migrate_kb.py` 的 `--entries-dir` 参数指向的是 v1 的路径（`~/dev/yixiaoguan/knowledge-base/entries`，按 `KB-*.md` 命名的单文件模式）。

KB 仓的 W1 产出格式未知，可能是：
- 按文件目录组织（类似 v1，但路径不同）
- 按汇总 JSONL 文件组织
- 按主题/学院分组的多目录
- 含元数据 `catalog.json` / `index.json`

必须先摸清，否则 Executor 没法写脚本。

## 必读上下文

在开工前读以下文件：

1. `docs/requirements/R06-P0-quick-wins.md` § R06-2（本任务的父需求）
2. `docs/PROJECT-CONTEXT.md` § 2.2（KB 仓 vs V2 仓职责边界）
3. `../../kb-pipeline/KB-SPEC.md`（v2 KB 字段规范）
4. `../../kb-pipeline/04-output/W1-FINAL-REPORT.md`（W1 产出总览）
5. `../../kb-pipeline/04-output/` 目录的实际文件列表

## Scout 执行步骤

### Step 1：定位产出

1. `ls -la ../../kb-pipeline/04-output/` 记录所有文件和子目录
2. 识别出哪些是 "960 条 KB 的最终交付物"（可能有多个候选）
3. 如有多个候选，对照 `W1-FINAL-REPORT.md` 确认**正式的入库数据源**

### Step 2：抓格式

1. 对每个疑似交付物，抽取前 3 条样本
2. 记录：
   - 文件格式（.md / .jsonl / .json / .csv）
   - 单条数据的 schema（字段名 + 类型 + 示例值）
   - 命名规则（如 KB-001-xxx.md）
   - 是否有前言元数据（YAML frontmatter 等）

### Step 3：数量清点

1. 确认条目数是否真的是 960（±5 可接受）
2. 若不是，找出实际数量并记录原因

### Step 4：字段映射分析

对比 v1（731 条）和 v2（960 条）的字段差异：

| v1 字段 | v2 字段 | 是否一致 | 转换规则 |
|---------|--------|---------|---------|
| title | ? | ? | ? |
| category | ? | ? | ? |
| content | ? | ? | ? |
| original_source | ? | ? | ? |
| tags | ? | ? | ? |
| ...（补充所有字段） | | | |

参考 `services/gateway/app/models/kb_entry.py` 看 PG 表结构。

### Step 5：类别体系映射

KB 仓用 **12 分类体系**（见 KB-SPEC.md），v1 可能不是 12 个。对照：

- 列出 v1 的分类集合
- 列出 v2 的 12 个分类
- 给出 mapping 表（若 v1 没有对应分类则标"丢弃"）

## 产出格式

创建 `docs/design/kb-source-scout-report.md`，必须包含以下章节：

```markdown
# KB 仓 960 条数据源侦察报告

## 1. 文件位置
- 主产出路径：...
- 次要产出（若有）：...

## 2. 数据格式
- 文件类型：.md / .jsonl / ...
- 单条 schema：...
- 命名规则：...

## 3. 字段映射（v1 → v2）
| v1 | v2 | 转换 |
|----|-----|-----|
...

## 4. 分类体系映射
| v1 类别 | v2 类别 |
|---------|--------|
...

## 5. 数量清点
- 预期：960
- 实际：...
- 差异原因：...

## 6. 样本展示
给出 3 条完整样本（含所有字段）

## 7. 推荐 Executor 做法
1. 迁移脚本应调整 --entries-dir 为 ...
2. 脚本需增加 ... 的字段转换逻辑
3. 分类字段需要 mapping 层，建议独立函数
4. 其他注意事项...
```

## 已知陷阱

- KB 仓可能有多个 "final" 版本文件，不要挑错
- `04-output/` 可能有实验性产出，要识别出**正式交付的 960 条**
- 某些字段可能在 JSONL 里叫 `source_url`，在 MD 里叫 `original_source`，注意一致性
- 如果 KB 仓 960 条的单条长度远大于 v1（v1 可能是小条目，v2 可能是聚合后的大文档），这会影响 Dify dataset 的存储策略
- 不要因为好奇去改 KB 仓的任何文件，严格只读

## 不做的事（out_of_scope）

- 不要动 `scripts/migrate_kb.py`（那是 Executor 的任务）
- 不要真的调 Dify API（那是 Executor 的任务）
- 不要清 PG 数据（那是 Executor 的任务）
- 不要读 / 写 `services/` 和 `apps/` 下的代码
- 不要修改 KB 仓的任何文件

## 完成后

把 `docs/design/kb-source-scout-report.md` 的**路径**回传给 T1。T0 会基于此报告起草 `.tasks/r06-2-exec-kb-migrate.md`。
