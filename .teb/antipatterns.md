# 错题本（AI Anti-Patterns）

> **规则**：每次任务开始前，执行 AI 必须阅读此文件。
> **维护者**：指挥官（你）。执行 AI 不直接修改此文件，而是在 `_report.md` 中报告新发现的模式，由你统一追加。

---

## 使用方法

1. 执行 AI 在 `_report.md` 的"新发现的错误模式"章节报告新坑
2. 你审阅后，把有价值的条目追加到下面
3. 格式：**现象** → **正确做法**

---

## 已知模式

### AP-001：T0 越权起草 `.tasks/` 文件

- **现象**：T0（Architect）在输出 `docs/requirements/R0X-*.md` 需求 spec 后，顺手在 `.tasks/` 下创建带完整 YAML frontmatter + done_criteria + step-by-step 的任务文件。
- **违反原则**：TEB 规范中 T0 只负责**需求 spec**，**任务分解与派发**是 T1 Coordinator 的专属职责。T0 越权会削弱 T1 的独立审查，若 T1 使用的模型与 T0 不同，格式冲突还会造成派发混乱。
- **正确做法**：
  1. T0 在 spec 文档的"交给 T1 的建议"章节用**自然语言**描述子任务目标、边界、依赖，**不写** YAML frontmatter、不写 step-by-step、不写 L0-L3 done_criteria
  2. `.tasks/` 目录下的文件一律由 T1 创建
  3. 若因特殊原因（如紧急冲刺、TX 口头授权）T0 必须代劳，**强制要求**：
     - 文件正文开头添加 `Meta：T0 代劳起草` 块
     - 在父需求 spec 文档中明确列出代劳清单和原因
     - 把此次例外录入本文件（见 2026-04-17 记录）
- **首发记录**：2026-04-17，R06 P0 Quick Wins 冲刺期间，TX 授权 T0 代写 4 份 `.tasks/` 文件。相关文件：
  - `.tasks/r06-2-scout-kb-source.md`
  - `.tasks/r06-3a-scout-dify-prompt.md`
  - `.tasks/r06-5a-scout-dify-compose.md`
  - `.tasks/r06-4a-exec-gateway-inputs.md`

---

<!-- 示例格式：
### AP-00X：...
- **现象**：...
- **正确做法**：...
-->
