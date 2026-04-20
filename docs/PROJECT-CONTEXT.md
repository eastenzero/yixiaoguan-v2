# 医小管 v2 — 项目上下文档案

> **用途**：一站式了解本项目的架构、仓库布局、基础设施、协作规范。
> **读者**：T0 / T1 / T3 / TX（用户）—— 每次进入项目前先读本文。
> **维护**：T0 主导；任何环境变更、仓库变更、协作方式调整都应更新此文件。
> **最近更新**：2026-04-17 首版

---

## 一、项目定位一句话

> **医小管 v2** = 基于 Dify Chatflow 的校园 AI 助手，FastAPI 单体 + UniApp 双端；
> **KB 仓（kb-pipeline）** 是 v2 的数据生产线；
> **v1 仓（yixiaoguan）** 已冻结，仅供资料参考。

---

## 二、仓库全景

| 简称 | 绝对路径（本地） | 角色 | Git 状态 |
|------|-----------------|-----|----------|
| **V2 仓** | `C:\Users\Administrator\Documents\code\yixiaoguan-v2` | 开发主战场（当前项目） | 活跃 |
| **KB 仓** | `C:\Users\Administrator\Documents\code\kb-pipeline` | 知识库生产线（数据/研究） | 活跃 |
| **V1 仓** | `C:\Users\Administrator\Documents\code\yixiaoguan` | 已冻结归档（含 v1 KB 原始 731 条） | 只读 |

### 2.1 V2 仓内部结构速览

```
yixiaoguan-v2/
├─ services/gateway/        # FastAPI 单体（:8100）
│  ├─ app/
│  │  ├─ routers/           # auth / chat / conversations / actions / ws
│  │  ├─ models/            # user / conversation / knowledge / kb_entry
│  │  ├─ schemas/
│  │  ├─ services/          # dify_client / state_machine / ws_manager
│  │  └─ utils/
│  ├─ alembic/              # 数据库迁移
│  ├─ .env（gitignored）
│  └─ requirements.txt
├─ apps/
│  ├─ student-app/          # UniApp 学生端（Vue 3）
│  └─ teacher-app/          # UniApp 教师端（Vue 3）
├─ scripts/                 # 运维脚本（含 migrate_kb.py）
├─ deploy/                  # Docker Compose 部署配置
├─ docs/                    # 产品/设计/规范（← 本文件所在处）
│  ├─ requirements/         # R01-R05 需求体系
│  ├─ design/               # dev-plan / dify-chatflow / teb-mutagen / DEPLOYMENT-PLAN
│  ├─ PROJECT-CONTEXT.md   ← 你正在看
│  └─ PROJECT-SECRETS.md   ← 敏感凭据（gitignored）
├─ .teb/                    # TEB 协作框架配置
├─ .tasks/                  # T1 生成的任务文件（当前为空）
└─ mutagen.yml              # 远端同步配置
```

### 2.2 KB 仓 vs V2 仓职责边界

| 内容类型 | 归属仓 | 说明 |
|---------|-------|------|
| KB 原始材料、清洗脚本 | **KB 仓** | 数据生产，不进 V2 |
| 教程 Markdown、截图素材 | **KB 仓** | 源文件；V2 前端通过 HTTP/CDN 消费 |
| KB-SPEC / KB-TEMPLATE | **KB 仓** | V2 `docs/README.md` 交叉引用，不重复存放 |
| 问卷设计、覆盖盲区分析 | **KB 仓** | 研究资料 |
| FastAPI 代码、UniApp 代码 | **V2 仓** | 应用代码 |
| Dify Chatflow DSL（若导出） | **V2 仓**（`docs/design/`） | 设计资产 |
| 部署方案、开发计划、需求 | **V2 仓**（`docs/`） | 应用开发决策 |

---

## 三、服务器与网络

### 3.1 主开发/联调机（165 eastern）

| 字段 | 值 |
|------|-----|
| IP | `192.168.100.165` |
| 用户 | `easten` |
| 项目目录 | `/home/easten/dev/yixiaoguan-v2` |
| 访问方式 | `ssh easten@192.168.100.165` |
| 同步方式 | Mutagen 从本地 ↔ 165（见 §五） |

### 3.2 服务端口一览

| 服务 | 端口 | 启动方式 |
|------|-----|---------|
| Gateway (FastAPI) | `:8100` | `uvicorn app.main:app`（见 §六） |
| Dify（Web + API） | `:3000`（Web）/ `:5001`（内部 API） | Docker Compose |
| PostgreSQL | `:5432` | 系统服务 |
| Redis | `:6379` | 系统服务 |

### 3.3 候选部署机器（未启用）

| IP | OS | 资源 | 当前状态 |
|----|----|----|---------|
| `64.90.13.65` | Ubuntu 24.04 | 16 vCPU / 15 GiB | 未装 Docker，nginx 占端口 |
| `60.205.205.99` | Alibaba Cloud Linux 3 | 2 vCPU / 1.8 GiB | 已装 Docker + 1Panel |

> 详见 `docs/design/teb-mutagen-remote-dev.md` §2.2。

---

## 四、敏感凭据

⚠️ **所有 API Key、密码、SSH 私钥等敏感信息存放在 `docs/PROJECT-SECRETS.md`，该文件已被 `.gitignore` 排除**。

如文件不存在或需要补全，联系 TX（用户）。

---

## 五、TEB 协作规范（速查）

### 5.1 角色表

| 角色 | 定位 | 允许动作 |
|------|-----|---------|
| **TX**（用户） | 决策者 | 需求确认、重大决策、远端 push、Dify UI 操作 |
| **T0**（Architect） | 最强模型 | 需求理解、架构设计、Bug 诊断、**输出 spec** |
| **T1**（Coordinator） | 强模型 | 任务分解、生成 `.tasks/`、直接派发 T3、集成测试 |
| **T3 Executor** | 便宜模型 | 写代码、跑自检、写执行报告 |
| **T3 Scout** | 便宜模型 | 只读侦察、信息收集（**无写权限**） |
| **T2**（Reviewer） | 中等模型 | 独立验证 L0-L2、Scope 审计 |

### 5.2 关键约束

- **T0-T2 绝对不写代码** — 代码类改动统一由 T3 Executor 执行
- **T0-T2 可以读写文档类文件**（`docs/` / `.tasks/` / `.teb/` 下的 Markdown）
  - ⚠️ 2026-04-17 TX 放宽约束：长上下文模型（Claude Sonnet 等）可自主读写文档
  - 短上下文模型（如 Kimi CLI 的小模型）仍需走 Scout 代理
- **T0-T2 读代码用于验证 spec 准确性**是允许的（非修改）
- 面向**目标状态**，非面向动作
- **文件是真相**，AI 的自述是幻觉

### 5.3 任务流程

```
TX 提需求
  ↓
T0 输出 spec（放 docs/requirements/）
  ↓
T1 拆成 .tasks/ 下的任务文件
  ↓
T3 Executor 执行 + 写报告
  ↓
T2 独立验证 L0-L2
  ↓
T1 二次验收 L3
  ↓
TX 最终确认
```

### 5.4 验收层级

| 层级 | 判定方式 | 示例 |
|------|---------|------|
| L0 | 存在性 | 文件/函数/接口是否存在 |
| L1 | 静态 | 编译/类型/lint 通过 |
| L2 | 运行时 | 测试命令全过 |
| L3 | 语义 | 功能是否符合目标（人工/强模型判定） |

> 完整规范：`.teb/README.md` 和 `docs/design/teb-mutagen-remote-dev.md`。

### 5.5 T3 工具矩阵

本项目有 3 类 T3 工具可选，按任务特性匹配：

| 工具 | 角色 | 特殊能力 | 适用场景 | 配置位置 |
|------|-----|---------|---------|---------|
| **Kimi CLI**（默认） | Scout / Executor | **浏览器调用**、文件读写、命令行 | 绝大多数任务；需浏览器的任务（如读 Dify UI） | `.teb/agents/t3-*.yaml` |
| **Python + DeepSeek** | Executor | 廉价 API | 批量 LLM 调用（上千次） | TX 维护 |
| **Python + 阿里云百炼** | Executor | 多模型负载均衡 | A/B 评测、模型对比 | TX 维护 |

**默认使用 Kimi CLI**，除非任务明确需要其他工具的特殊能力。

### 5.6 Kimi 浏览器能力的典型用途

- 登录 Dify Web 控制台抓取 Chatflow 节点配置 / system prompt
- 抓取第三方服务的 UI 状态作为验证辅助
- 触发需要 UI 操作的工作流（TX 授权后）

**注意**：涉及敏感操作（如删除数据、修改生产配置）必须由 TX 亲自执行，不要通过浏览器让 T3 做。

---

## 六、Mutagen 同步工作流（速查）

### 6.1 本地侧启动

```powershell
# 在 V2 仓根目录
mutagen project start
mutagen sync list
```

### 6.2 常用命令

| 场景 | 命令 |
|------|------|
| 强制推送本地到远端 | `mutagen sync flush yixiaoguan-v2` |
| 暂停同步 | `mutagen sync pause yixiaoguan-v2` |
| 恢复同步 | `mutagen sync resume yixiaoguan-v2` |
| 终止同步 | `mutagen project terminate` |

### 6.3 不同步的文件（已在 `mutagen.yml` 忽略）

- `services/gateway/.env` · `deploy/.env`
- `venv/` · `node_modules/`
- `dist/` · `build/` · `__pycache__/`
- 各类缓存和日志

> 完整文档：`docs/design/teb-mutagen-remote-dev.md`。

---

## 七、服务启动命令速查（远端 165）

### 7.1 Gateway

```bash
cd /home/easten/dev/yixiaoguan-v2/services/gateway
source ../../venv/bin/activate
# 前台
PYTHONPATH=. python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
# 后台
PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &
```

### 7.2 健康检查与日志

```bash
curl -s http://localhost:8100/health
tail -f /tmp/gw.log
```

### 7.3 Alembic 迁移

```bash
cd /home/easten/dev/yixiaoguan-v2/services/gateway
PYTHONPATH=. alembic revision --autogenerate -m "描述"
PYTHONPATH=. alembic upgrade head
```

---

## 八、技术栈

| 层 | 选型 | 备注 |
|---|------|------|
| 后端 | **FastAPI + SQLAlchemy (async) + Alembic** | Python 单体 |
| AI 引擎 | **Dify self-hosted** | 4 分支 Chatflow（chitchat / kb_query / transfer / 其他） |
| 数据库 | **PostgreSQL 15+** | 主存储 |
| 缓存 | **Redis 7+** | 会话/缓存 |
| 学生端 | **UniApp + Vue 3** | 微信小程序 + H5 双编译 |
| 教师端 | **UniApp + Vue 3 + Element Plus** | 同上 |
| 向量库 | Dify 内置（通义千问 embedding） | 不单独管理 |
| 同步 | **Mutagen** | 本地 ↔ 165 |
| 协作 | **TEB 框架** | `.teb/` + `.tasks/` |

---

## 九、进度与里程碑

| 阶段 | 状态 | 关键产出 |
|------|-----|---------|
| S1 | ✅ 完成 | FastAPI 脚手架、基础 auth |
| S2 | ✅ 完成（2026-04 中旬） | WebSocket + 状态机 + 工单后端 + 教师介入 |
| S3 | 🔄 进行中 | Dify 联调 + KB 迁移（v1 731 条） + 部署冒烟测试 |
| S4 | 📋 待规划 | R04/R05 需求（见下） |

### R04/R05 活跃需求（2026-04-14 TX 确认）

| ID | 需求 | 优先级 | 依赖 |
|----|------|-------|------|
| R04-N1 | Dify Chatflow 加用户上下文 | P1 | 无 |
| R04-N2 | KB 从 731 扩到 1000+（KB 仓产出） | P1 | KB 仓 W1 完成（已完成，960 条） |
| R05-1 | Top 10 图文教程 | P1 | 截图 + 前端卡片 |
| R05-2 | 高频无答案统计 | P2 | Gateway 新表 |
| R05-3 | 学院/班级个性化 prompt | P1 | Dify prompt 微调 |
| R05-4 | 教师定制通知 | P2 | 新表 + 拦截 + UI |

---

## 十、相关文档索引

### 产品与需求

| 文档 | 位置 | 说明 |
|------|------|------|
| 需求总索引 | `docs/README.md` | R01-R05 导航 |
| R01 既有意向 | `docs/requirements/R01-...md` | v1 基线 |
| R02 师生对话 | `docs/requirements/R02-...md` | 核心产品需求 |
| R03 开发前确认 | `docs/requirements/R03-...md` | ⚠️ 部分过时 |
| R04 v2 新增 | `docs/requirements/R04-v2-新增需求.md` | 活跃 |
| R05 KB 增强 | `docs/requirements/R05-KB-增强需求.md` | 活跃 |
| R06 P0 Quick Wins | `docs/requirements/R06-P0-quick-wins.md` | T0 刚下发 |

### 设计与架构

| 文档 | 位置 | 说明 |
|------|------|------|
| v2 开发计划 | `docs/design/dev-plan-v2.md` | 总体架构、历史决策 |
| Dify Chatflow 设计 | `docs/design/dify-chatflow-design.md` | 4 分支现状 |
| TEB + Mutagen | `docs/design/teb-mutagen-remote-dev.md` | 协作框架 |
| 部署与资源 | `docs/design/DEPLOYMENT-PLAN.md` | ← 从 KB 仓迁入 |
| 165 服务器侦察 | `docs/server-recon-2026-04-15.md` | 资源摸底 |

### KB 仓相关（跨仓引用）

| 文档 | 位置 | 说明 |
|------|------|------|
| KB 规范 | `../kb-pipeline/KB-SPEC.md` | 12 分类体系、字段定义 |
| KB 模板 | `../kb-pipeline/KB-TEMPLATE.md` | 3 示例 |
| W1 最终报告 | `../kb-pipeline/04-output/W1-FINAL-REPORT.md` | 960 条 KB 基线 |
| 覆盖盲区 | `../kb-pipeline/.task/COVERAGE-GAPS.md` | 盲区与过度覆盖 |
| 问卷方案 | `../kb-pipeline/.task/SURVEY-PLAN.md` | 学生需求问卷 |

### TEB 协作资料

| 文档 | 位置 |
|------|------|
| TEB 总说明 | `.teb/README.md` |
| 任务模板 | `.teb/templates/_task.template.md` |
| 报告模板 | `.teb/templates/_report.template.md` |
| 错题本 | `.teb/antipatterns.md` |

---

## 十一、常见问题

### Q1. 新对话/新 AI 实例加入时应该读什么？

**按顺序**：
1. 本文件（PROJECT-CONTEXT）
2. `.teb/README.md`（协作规范）
3. 当前任务相关的 `docs/requirements/R*.md`
4. 任务涉及的 `docs/design/*.md`

### Q2. API Key 从哪拿？

见 `docs/PROJECT-SECRETS.md`（gitignored）。

### Q3. Dify 账号密码？

见 `docs/PROJECT-SECRETS.md`。

### Q4. 远端服务挂了怎么办？

1. `ssh easten@192.168.100.165`
2. `tail -100 /tmp/gw.log` 看错误
3. `pkill -f uvicorn` 再重启（见 §七）

### Q5. 本地改动没到 165？

```powershell
mutagen sync flush yixiaoguan-v2
```

如还不行，先 `mutagen sync list` 看会话状态。

### Q6. Dify Chatflow 如何修改？

Dify 是 UI 驱动，无法从代码改。由 **TX（用户）手动操作** Dify Web 控制台：
- URL：`http://192.168.100.165:3000`
- 账号密码：见 `PROJECT-SECRETS.md`

---

## 十二、变更日志

| 日期 | 变更 | 作者 |
|------|-----|-----|
| 2026-04-17 | 首版创建 | T0 |
| 2026-04-17 | §5.2 TEB 约束更新：长上下文 T0 放宽自主读写；新增 §5.5/5.6 T3 工具矩阵 + Kimi 浏览器能力 | T0 |

---

*保持本文件为"入口文档" — 每次项目状态变化都应及时更新，避免后续 AI 或新成员读错信息。*
