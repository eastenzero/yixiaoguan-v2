# TEB 启动包 — 3 分钟上手

> Task Evidence Board：文件驱动的、四层 AI 协作开发系统。

---

## 架构一览

```
TX  用户（人类决策者）        需求确认、重大决策、人工阻塞点、远端 push
 ↓
T0  Architect（最强模型）    需求理解、澄清歧义、架构设计、Bug 诊断
 ↓  输出需求 spec
T1  Coordinator（强模型）    任务分解、直接下发 T3、集成测试、二次验收
 ↓  输出任务文件，直接派发给 T3
T3  Executor（便宜模型）     写代码、跑自检、写执行报告
T3  Scout  （便宜模型）     只读侦察、信息收集、输出结构化摘要
 ↓  执行完毕，提交报告
T2  Reviewer（中等模型）     独立跑 L0-L2 验证、Scope 审计、输出验证报告
 ↓  验证报告上报 T1
```

> T0-T2 是纯指挥官——**绝对不写代码**。
> 在现有系统上开发/修 bug 时，T0-T2 **严格禁止自行读写项目文件**，必须通过 Kimi CLI 代理获取项目信息。

---

## 快速开始

### 1. 拷贝到新项目

将本文件夹内容拷贝到项目根目录的 `.teb/`，并创建空的 `.tasks/` 目录。

```
你的项目/
├── .teb/              ← 模板和提示词
├── .tasks/            ← 任务树（从空目录开始，随项目生长）
├── src/
└── ...
```

### 2. 新功能开发流程

1. **T0**：把 `prompts/t0-architect.md` 发给最强 AI，描述你的目标。它会澄清需求、识别地基模块、输出需求 spec。
2. **T1**：把需求 spec + `prompts/t1-coordinator.md` 发给强 AI。它会分解任务树、创建 `.tasks/` 下的任务文件，**直接下发给 T3 执行**。
3. **你审阅**：看一眼任务文件，确认 OK。
4. **T3**：按任务文件执行编码、自检、写报告。
5. **T2**：T3 完成后，T2 独立跑 L0-L2 验证，输出验证报告。
6. **验收**：T1 做二次验收（L3 语义判定），你做最终确认。

### 3. Bug 修复流程

1. **T0**：描述 bug 现象，T0 诊断根因，输出 `type: bugfix` 的任务文件（含复现步骤和根因分析）。
2. **后续同开发流程**：T1 分解修复任务（必须包含回归测试），直接下发 T3 执行，T2 验证。

---

## 文件速查

| 文件 | 谁用 | 用途 |
|------|------|------|
| `prompts/t0-architect.md` | 最强 AI | 需求理解、架构设计、Bug 诊断 |
| `prompts/t1-coordinator.md` | 强 AI | 任务分解、打包、二次验收 |
| `prompts/t2-reviewer.md` | 中等 AI | 独立验证 T3 执行结果 |
| `prompts/t3-executor.md` | 便宜 AI | 执行编码 |
| `prompts/t3-scout.md` | 便宜 AI | 只读侦察、信息收集 |
| `agents/t3-executor.yaml` | Kimi CLI | T3 执行模式的 agent 配置 |
| `agents/t3-scout.yaml` | Kimi CLI | T3 侦察模式的 agent 配置（无写权限） |
| `templates/_task.template.md` | T1 参考 | 任务文件标准格式 |
| `templates/_report.template.md` | T3 参考 | 执行报告标准格式 |
| `guides/verification-guide.md` | 你自己 | L0-L3 验证层级说明和示例 |
| `guides/git-strategy.md` | 你自己 | 什么时候 commit、分支策略、回滚 |
| `antipatterns.md` | 所有 AI | 错题本 |

## 核心理念

- **文件是真相，AI 的自述是幻觉**
- **面向目标状态，而非面向动作**
- **验证与执行分离**
- **地基优先，集成测试不可省**
- **错题本是免疫系统**
