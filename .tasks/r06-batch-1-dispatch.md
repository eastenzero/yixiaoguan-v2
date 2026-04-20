---
id: "r06-batch-1-dispatch"
parent: "R06"
type: "dispatch"                    # 非标准任务文件；是 T1 派发清单
status: "ready"
tier: "T1"
priority: "high"
risk: "low"

scope:
  - "本文件本身"                    # 派发清单不改代码

out_of_scope:
  - "services/**"
  - "apps/**"

context_files:
  - "docs/requirements/R06-P0-quick-wins.md"
  - ".tasks/r06-2-scout-kb-source.md"
  - ".tasks/r06-3a-scout-dify-prompt.md"
  - ".tasks/r06-5a-scout-dify-compose.md"
  - "docs/PROJECT-SECRETS.md"

created_at: "2026-04-20"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-20 TX 授权，T0 代 T1 起草本派发清单。
> T1 审阅后可直接采用、局部调整、或完全重写。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06 batch-1 派发清单（3 个 Scout 任务）

> **目的**：告诉 TX（或 T1）怎么把 3 份 Scout 任务文件真正交给 T3 Kimi 去跑，以及每个任务应在哪台机器执行。
>
> **不替代** `.tasks/r06-*-scout-*.md` 本身，这三份文件是 Kimi 要读的 prompt。

---

## 0. 三个 Scout 的机器归属

| 任务 | 运行机器 | 原因 |
|------|---------|------|
| `r06-2-scout-kb-source` | **本地 Windows**（或提前把 kb-pipeline 同步到 165） | 要读 `../../kb-pipeline/04-output/` 里的 960 条原始文件 |
| `r06-3a-scout-dify-prompt` | **任意有浏览器的机器**（推荐 Windows 本地 Kimi） | 用 Kimi 浏览器工具登录 `http://192.168.100.165:3000` |
| `r06-5a-scout-dify-compose` | **165 本机** | 要 `docker compose ps` / `docker stats` / 读 compose 文件 |

---

## 1. 前置检查（TX 做，≤3 分钟）

### 1.1 确认 Kimi CLI 可用

- 本地 Windows：`kimi --version`（如未装，见 `docs/PROJECT-CONTEXT.md`）
- 165 服务器：`ssh easten@192.168.100.165 'kimi --version'`（记忆中 165 上是 v1.31.0）

### 1.2 确认 kb-pipeline 仓路径

- 本地 Windows：`C:\Users\Administrator\Documents\code\kb-pipeline` 是否存在
- 若要在 165 跑 r06-2 Scout，先确认 `ssh 165 'ls -la ~/dev/kb-pipeline 2>/dev/null || echo NO'`
- **默认策略**：r06-2 在 **本地 Windows 跑**，产出文件通过 Mutagen 自动同步到 165

### 1.3 确认 V2 仓当前工作区无未提交改动

```powershell
cd C:\Users\Administrator\Documents\code\yixiaoguan-v2
git status
```

若有未提交改动先提交或 stash，避免 Scout 产出与现存修改混在一起。

---

## 2. Scout 派发命令

> **约定**：每个 Scout 都用 `kimi --print -p <task-file>` 非交互执行；
> Kimi 产出文件直接写入 V2 仓的 `docs/design/`，通过 Mutagen 或 git 同步。

### 2.1 r06-2 · KB 数据源侦察（本地 Windows）

```powershell
cd C:\Users\Administrator\Documents\code\yixiaoguan-v2
kimi --print -p .tasks\r06-2-scout-kb-source.md
```

**预期产出**：`docs/design/kb-source-scout-report.md`

**注意**：任务文件里用的是相对路径 `../../kb-pipeline/...`；
Kimi 在 V2 仓根跑时相对路径会指向 `C:\Users\Administrator\Documents\code\kb-pipeline`，符合预期。

---

### 2.2 r06-3a · Dify prompt 抓取（本地 Windows，浏览器）

**注入 Dify 账号密码到环境变量**（避免 Kimi 读 SECRETS 文件时走冤枉路）：

```powershell
$env:DIFY_EMAIL = "easten_zero@qq.com"
$env:DIFY_PASSWORD = "<见 PROJECT-SECRETS.md §2.1>"
$env:DIFY_WEB_URL = "http://192.168.100.165:3000"

cd C:\Users\Administrator\Documents\code\yixiaoguan-v2
kimi --print -p .tasks\r06-3a-scout-dify-prompt.md
```

**预期产出**：
- `docs/design/dify-current-prompt.md`
- `docs/design/dify-current-config.md`

**注意**：
- Kimi 浏览器工具可能需要手动完成验证码；若 Kimi 报"无法登录"立即停，由 TX 手动贴 prompt 到 Kimi 对话里
- **严格只读**：Kimi 不能在 Dify 里点任何"保存 / 发布"按钮

---

### 2.3 r06-5a · Dify compose 基线（在 165 跑）

Kimi 需要在 165 本机运行，因为任务里有大量 `docker` 命令。

```powershell
# 本地 Windows 远程触发
ssh easten@192.168.100.165

# 在 165 shell 里：
cd ~/dev/yixiaoguan-v2
kimi --print -p .tasks/r06-5a-scout-dify-compose.md
```

**预期产出**：`docs/design/dify-compose-baseline-report.md`（通过 Mutagen 自动回流到本地 Windows）

**注意**：
- Kimi 在 165 上可能没有 `jq`，任务文件里已给出 `docker compose ps` fallback
- 如果 Kimi 尝试执行 `docker compose down/up/restart`，**人工 Ctrl-C 打断**

---

## 3. 并行执行策略

- **2.1 和 2.2** 可在同一台本地 Windows 上**串行**跑（两者都用 Kimi，建议先 2.1 再 2.2）
- **2.3** 在 165 上跑，**可与 2.1 / 2.2 完全并行**
- **总耗时估算**：30–60 分钟

---

## 4. 验收（TX 做）

Scout 跑完后，TX 或 T0 检查每份产出是否满足对应任务文件里的 `done_criteria`：

| Scout | 检查文件 | L0 检查 | L2 检查 |
|-------|---------|--------|---------|
| r06-2 | `docs/design/kb-source-scout-report.md` | 文件存在非空 | 至少 4 章节 + "推荐 Executor 做法"段 |
| r06-3a | `docs/design/dify-current-prompt.md` + `dify-current-config.md` | 两份都存在 | 有完整 system prompt + 节点模型/温度表 |
| r06-5a | `docs/design/dify-compose-baseline-report.md` | 文件存在 | 含 services 清单 + docker stats 快照 + 瘦身候选 |

---

## 5. batch-1 通过后，触发 batch-3（依赖 Scout 产出）

batch-3 任务由 T0（或 T1）**在 Scout 产出到齐后**起草，当前只有 `r06-4a-exec-gateway-inputs.md` 已预先就位（它不依赖任何 Scout）。

batch-3 剩余两份待起草：

- `.tasks/r06-2-exec-kb-migrate.md`（依赖 r06-2 Scout 报告）
- `.tasks/r06-5b-exec-dify-slim.md`（依赖 r06-5a Scout 报告）

R06-3' 的审阅任务（`.tasks/r06-3b-review-prompt.md`）会由 T0 自己起草（同时提交）。

---

## 6. 异常与回滚

| 场景 | 处理 |
|------|------|
| Kimi 报 Dify 登录失败 | 停 Scout 2.2，TX 手动登录抓 prompt 粘贴到文档 |
| Kimi 在 165 上企图改 compose 文件 | 立即 Ctrl-C；检查 `git diff`，必要时 `git checkout -- .` |
| kb-pipeline 路径不匹配 | 改任务文件里的相对路径，或在 Kimi 对话里纠正 |
| 产出文件名冲突已有文件 | Kimi 应追加时间戳；若覆盖，用 `git restore --staged` 恢复 |

---

## 7. 完成后

1. 3 份 Scout 产出文件 **全部进入 V2 仓并提交**（`git add docs/design/ && git commit -m "R06 batch-1 scout reports"`）
2. 在本文件末尾追加 **执行记录**（时间 / 耗时 / 产出路径 / 异常）
3. 通知 T0 进入 batch-3 Executor 任务起草阶段

---

## 执行记录

| 日期 | 任务 | 机器 | 耗时 | 产出 | 状态 |
|------|-----|-----|-----|-----|-----|
| — | r06-2 | — | — | — | 待执行 |
| — | r06-3a | — | — | — | 待执行 |
| — | r06-5a | — | — | — | 待执行 |
