# Codex 派单工作流（Cascade ⇄ Codex 协作指南）

> 适用场景：windsurf Cascade 作为"项目经理 + 部署工程师"，把具体编码任务派给 OpenAI Codex（CLI 版）执行，全程异步轮询。
>
> 本文档基于 2026-04-28 实战 7 commits（P1-1 学生端通知 + P0-2 Lite 拒答优化）总结。

---

## 1. 为什么要 "Cascade 派单 → Codex 执行"

| 角色 | 强项 | 短板 |
|---|---|---|
| **Cascade**（chat） | 调研、决策、设计、协调多个上下文（远程 165 / GitHub / 文档） | 单次写大量代码慢、长 prompt 易失焦、难做大量重复改动 |
| **Codex**（CLI） | 严格按 prompt 执行编码、精确 diff、自动跑测试、commit 规整 | 没有项目宏观视角、不会做远程部署、不擅长跨仓决策 |

**最佳分工**：
- Cascade 调研代码 → 设计 sprint → 写 prompt → 派 codex → 等结果 → push + 部署 165 + 冒烟验证
- Codex 收 prompt → 改代码 → 跑测试 → commit（不 push）→ 写 summary

**收益**：
- Cascade 不用占着 chat 流写 200 行代码（chat 流被中断风险高）
- Codex 在专属 sandbox 里写 + 测试，commit message 规范
- 异步：Cascade 派完后做别的事（比如继续调研），轮询拿回结果

---

## 2. 启动 Codex 的标准命令骨架

### 2.1 工具路径（一次性确认）

```powershell
$codex = "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
```

> Windows 上 Codex CLI 由 `npm install -g @openai/codex` 安装，命令名是 `codex.cmd`。Cascade 的 `run_command` 经常解析不到 PATH，**显式给完整路径**最稳。

### 2.2 标准启动模板

```powershell
$codex      = "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
$logDir     = "<worktree>\.tasks"
$promptFile = "$logDir\codex-<sprint-name>-prompt.txt"   # 输入 prompt
$logFile    = "$logDir\codex-<sprint-name>.log"          # codex stdout/stderr 全量
$summaryFile= "$logDir\codex-<sprint-name>-summary.txt"  # codex 最终 message

Write-Output "starting <sprint-name> at $(Get-Date -Format 'HH:mm:ss')"
Get-Content $promptFile -Raw | & $codex exec `
    --dangerously-bypass-approvals-and-sandbox `
    -C "<absolute-project-path>" `
    --output-last-message $summaryFile `
    *> $logFile
Write-Output "finished <sprint-name> at $(Get-Date -Format 'HH:mm:ss')"
```

**关键参数**：

| 参数 | 作用 |
|---|---|
| `exec` | 非交互模式（一次性执行 prompt 即退出，不开 REPL） |
| `--dangerously-bypass-approvals-and-sandbox` | 跳过 codex 的人工 confirm 提示，让它自动写文件 + 跑命令 |
| `-C <path>` | 指定 codex 的工作根目录（**必须是绝对路径**） |
| `--output-last-message <file>` | 把 codex 最后一条总结消息写到指定文件，便于后续 grep |
| `Get-Content -Raw \| & $codex` | 用 stdin pipe 喂入 prompt（避免 PowerShell 把 prompt 当成命令行参数转义） |
| `*> $logFile` | 把 stdout + stderr 全部重定向到日志（防止刷屏 + 留证） |

### 2.3 调用方式（在 Cascade 的 `run_command` 里）

**关键设置**：

```jsonc
{
  "Blocking": false,           // 必须 false，否则 chat 卡到 codex 完成
  "SafeToAutoRun": true,       // 写入 .tasks 目录是安全的
  "WaitMsBeforeAsync": 10000   // 等 10s 看 codex 是否秒挂（如 prompt 文件路径错误）
}
```

**为什么 `Blocking=false`**：codex 一次 sprint 通常 3-15 分钟，阻塞会让 Cascade chat 流挂死，用户无法插话。非阻塞 + 主动轮询是关键。

---

## 3. Prompt 写法（最关键的环节）

### 3.1 黄金法则

| 原则 | 例 |
|---|---|
| **明确 commit 数量** | "Make exactly TWO new commits on top of HEAD (`<sha>`)" |
| **每个 commit 列明具体文件 + 改动** | "Edit `services/gateway/app/services/refusal.py`: add function `is_refusal(answer, sources)` ..." |
| **明确不做什么** | "Do NOT modify, rebase, squash, or amend existing commits. Do not push." |
| **写出 Verify 步骤** | "Verify: `python -m pytest tests/test_refusal.py -q` -> all pass" |
| **指定 commit message 字面值** | `Commit message: "feat(refusal): detect AI refusal in gateway + tag message metadata"` |
| **强调 Final state expected** | 最后一段总结期望（HEAD 上有 N 个新 commit / 测试全过 / 不 push） |

### 3.2 完整 Prompt 模板

```
P0-2 lite: <一句话目标>。<工作量估算>。

Strict rules:
- Do NOT modify, rebase, squash, or amend any existing commits.
- Make exactly TWO new commits on top of current HEAD (<sha>).
- Do not push.
- When invoking shell commands on Windows PowerShell, AVOID complex regex with pipes
  and double-quote escaping. Use simple commands or read files directly.

Background:
- <现状代码位置 + 行号 + 简述>
- <相关上下游>
- Goal: <一句话再说一次目标>

============================================================
COMMIT 1: <commit 标题>
Commit message: "<commit message 字面值>"
============================================================

1.1 <动作 1，具体到文件路径 + 函数 + 字段名>

    <可选：示例代码 / 数据格式>

1.2 <动作 2 ...>

1.3 Verify:
    cd services/gateway
    python -m pytest tests/<test>.py -q
    -> all pass

    ruff check <文件列表>

1.4 Commit message: "<再次重复 commit message 字面值>"

============================================================
COMMIT 2: <commit 标题>
Commit message: "<commit message 字面值>"
============================================================

<同上>

============================================================
Final state expected:
- HEAD has exactly 2 NEW commits on top of <base-sha>
- <测试结果>
- <linter 结果>
- No push, no amend
- No existing commits modified
```

### 3.3 反面案例（容易翻车的写法）

❌ **太开放**：

> "请帮我加一下未读功能"

→ Codex 会乱选 API 名 / 表结构 / 文件位置，需要返工。

❌ **要求改既有 commit**：

> "在 commit `abc123` 上加一个文件"

→ 要求 amend / rebase 容易破坏 commit chain。**永远新建 commit**。

❌ **缺少 Verify**：

> "改完 commit 即可"

→ Codex 不会主动跑测试，可能 break。

❌ **commit message 模糊**：

> "Commit message: about unread"

→ 不规范，无法被 git log 一眼看懂。

### 3.4 Prompt 文件命名约定

放 `.tasks/codex-<sprint-shortname>-prompt.txt`，例：
- `.tasks/codex-p1-1-unread-prompt.txt`
- `.tasks/codex-fix-alembic-prompt.txt`
- `.tasks/codex-refusal-prompt.txt`

对应日志和 summary 同名：
- `.tasks/codex-<sprint>-prompt.txt`（输入）
- `.tasks/codex-<sprint>.log`（codex 全量 stdout/stderr）
- `.tasks/codex-<sprint>-summary.txt`（codex 最后总结消息）

---

## 4. 异步轮询等待机制（重头戏）

### 4.1 完整生命周期

```
Cascade                           Codex
  │                                 │
  ├─ run_command Blocking=false ───▶ 进程启动
  │  WaitMsBeforeAsync=10000        │
  │                                 │
  │  (10s 内若 codex 秒挂，立刻返回 error，避免无效等待)
  │                                 │
  ├─ Start-Sleep N 秒                │ <----- 关键
  │                                 │
  ├─ 检查 codex 进程是否还在 ◀─────── │
  │                                 │
  ├─ 没了 → 看 git log + summary     │
  │                                 │
  └─ 还在 → 再等 N 秒                │
```

### 4.2 等多久？经验值

| Sprint 类型 | 平均时长 | 第一次 Sleep 建议 |
|---|---|---|
| **改 1 行 + 跑测试**（如 alembic 修复） | 1-3 min | `Start-Sleep -Seconds 180` |
| **后端 1 service + 测试 + 1 commit** | 3-5 min | `Start-Sleep -Seconds 300` |
| **前端 + 后端 + 测试 + 2 commits** | 5-12 min | `Start-Sleep -Seconds 420` |
| **大型 feature + 多文件** | 10-20 min | `Start-Sleep -Seconds 600` |

**策略**：第一次 sleep 一半时间 → 检查进程 → 没结束再 sleep 剩余 → 再检查。**不要一次 sleep 太长**（用户可能要插话）。

### 4.3 检查 codex 是否完成

```powershell
Start-Sleep -Seconds 240
"now: $(Get-Date -Format 'HH:mm:ss')"
"codex procs: $((Get-Process codex -EA 0 | Measure-Object).Count)"
```

- `codex procs: 0` → 完成
- `codex procs: 1` → 还在跑，继续等

### 4.4 完成后的标准验收

```powershell
# 1. 看新 commits
git -C "<repo>" log --oneline -5

# 2. 看 codex 总结
$sf = "<.tasks-summary-file>"
Get-Content $sf -Encoding UTF8 -Raw

# 3. spot check 关键改动（grep / Read 文件）
```

**Summary 文件最关键**：codex 会自报 "我做了 A、B、C，验证 D 通过"。如果 summary 提到测试失败 / build 失败，立刻看 .log 详情。

---

## 5. 验收 → Push → 部署 → 冒烟

### 5.1 标准 5 步流程

```
1. git log -5             检查新 commits
2. 读 summary 文件        看 codex 自报的验证结果
3. spot check 关键文件    防止 codex 编造（不常见但可能）
4. git push               推 GitHub
5. ssh 远程 + 同步 + 重启  部署到 165
6. curl 冒烟              验证生产 API
```

### 5.2 PowerShell push 的坑

PowerShell 把 `git push` 的 stderr 当成 error 红字打印（即便成功），但 `Everything up-to-date` 或 `<old>..<new>  master -> master` 表示成功。**忽略 exit code，看输出文本**。

```powershell
git -C "<repo>" push github master 2>&1
# 即使 exit 1，看到 "<old>..<new>  master -> master" 就是成功
```

### 5.3 远程部署 + ssh 引号地狱

PowerShell 的引号转义 + ssh 远端 bash 的引号嵌套是双重灾难。**最稳的写法**：

**A. 简单命令**（一行 bash 内）：
```powershell
ssh easten@192.168.100.165 "git -C /home/x/repo log --oneline -5"
```

**B. 带变量替换**（用 PS 双引号 + bash 单引号）：
```powershell
$tok = "<token>"
ssh easten@192.168.100.165 "curl -sf -H 'Authorization: Bearer $tok' http://localhost:8100/health"
```

**C. 多行复杂 bash**：写到本地 .sh → scp 上去 → ssh 跑：
```powershell
$lines = @(
  "#!/bin/bash"
  "TOK='<token>'"
  "curl -s -H `"Authorization: Bearer `$TOK`" http://x | python3 -m json.tool"
)
$tmpf = "$env:TEMP\verify.sh"
$lines -join "`n" | Set-Content -Encoding ascii -NoNewline -Path $tmpf
scp -q $tmpf easten@192.168.100.165:/tmp/verify.sh
ssh easten@192.168.100.165 "bash /tmp/verify.sh"
```

**D. 远端 nohup 启动服务**（避免 SSH 关闭被 SIGHUP）：
```powershell
ssh easten@host "cd /path && setsid nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 < /dev/null & disown"
```
关键：`setsid` + `< /dev/null` + `disown` 三件套。

---

## 6. 常见故障 + 解决方案

### 6.1 Alembic Multiple heads

**症状**：`ERROR Multiple head revisions are present`

**根因**：本地误以为 latest mig 是 `X`，但远端主仓另有更新的 mig `Y`，于是新 mig 接在 `X` 上，造成分叉。

**解决**：
1. `alembic heads` 查所有 head
2. 派 codex 单独写一个 1-line fix commit：把分叉那个 mig 的 `down_revision` 改成另一支的 head
3. 不 amend、不 rebase，新加 commit 是最干净的

### 6.2 PowerShell 引号嵌套失败

**症状**：ssh 命令看似执行但 0 输出

**解决**：
- 简化为单层引号
- 把多层引号的命令落到 .sh 文件 + scp
- 用 `Get-Content $cmdFile -Raw \| ssh host bash` 形式

### 6.3 Codex 在 prompt 里乱写 Windows 命令

**症状**：codex 跑 PowerShell 的 grep + 引号转义失败

**解决**：在 prompt 顶部加：
> "When invoking shell commands on Windows PowerShell, AVOID complex regex with pipes
> and double-quote escaping. Use simple commands or read files directly."

让 codex 用 Python 脚本 / 直接 Read 文件代替 shell pipe。

### 6.4 远程 nohup 启动后被 SIGHUP

**症状**：ssh 跑 `nohup uvicorn ... &` 后立即查 `ps`，看到进程在；但 ssh 退出后进程也死了。

**根因**：nohup 不挡 SIGHUP，bash session 关闭时仍传给子进程。

**解决**：`setsid nohup ... < /dev/null & disown`

### 6.5 Codex 漏看主仓最新 mig

**症状**：派的 mig 接在过期 base 上 → 多 head

**预防**：在 Cascade 派单前，手动 `git log --oneline -10` 看 GitHub 最新 sha + 在 prompt 写 "on top of HEAD (`<sha>`)"，让 codex 验证起点。

### 6.6 用户 Windows worktree mode 的注意事项

Cascade 在 worktree 里看到的代码 ≠ 主仓 HEAD。**始终 `git -C <main-repo>` 查主仓状态**，不要被 worktree 当前 branch 误导。

---

## 7. Cheat Sheet（速查）

### 启动新 sprint

```powershell
# 1. 写 prompt
$prompt = "<.tasks>\codex-<name>-prompt.txt"
# (用 write_to_file 工具创建)

# 2. 启动 codex
$codex = "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
$log   = "<.tasks>\codex-<name>.log"
$sum   = "<.tasks>\codex-<name>-summary.txt"
Get-Content $prompt -Raw | & $codex exec --dangerously-bypass-approvals-and-sandbox -C "<repo>" --output-last-message $sum *> $log
# Blocking=false, WaitMsBeforeAsync=10000
```

### 等待 + 检查

```powershell
Start-Sleep -Seconds 300
"codex procs: $((Get-Process codex -EA 0 | Measure-Object).Count)"
git -C "<repo>" log --oneline -5
Get-Content "<.tasks>\codex-<name>-summary.txt" -Raw
```

### 部署 165

```powershell
git -C "<repo>" push github master 2>&1
ssh easten@192.168.100.165 "cd /home/easten/dev/yixiaoguan-v2 && git fetch github && git reset --hard github/master"
ssh easten@192.168.100.165 "cd /home/easten/dev/yixiaoguan-v2/services/gateway && source venv/bin/activate && alembic upgrade head"
ssh easten@192.168.100.165 "pkill -f 'uvicorn app.main' ; sleep 2 ; cd /home/easten/dev/yixiaoguan-v2/services/gateway && source venv/bin/activate && setsid nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 < /dev/null & disown"
Start-Sleep -Seconds 5
ssh easten@192.168.100.165 "curl -sf http://localhost:8100/health"
```

---

## 8. 一次完整 Sprint 范例（P0-2 Lite 拒答优化）

| 阶段 | 时长 | 动作 |
|---|---|---|
| 调研 | 5 min | Cascade 用 code_search + grep 找现状代码（前端 isRefusalMsg 已实现，后端缺） |
| 设计 | 3 min | Cascade 决定：新建 `refusal.py` + 修 chat.py + 前端加 sticky CTA |
| 写 prompt | 5 min | Cascade 用 write_to_file 创建 `.tasks/codex-refusal-prompt.txt`（含 2 个 commit 的详细规约） |
| 派 codex | 0 min | run_command Blocking=false |
| 等待 | 12 min | Start-Sleep 10min → 看 codex procs=0 → 看 summary（7 测试过 + ruff 过 + build 过） |
| Push | 1 min | git push github master |
| 部署 | 2 min | ssh 165 fetch + reset + alembic + setsid nohup uvicorn |
| 冒烟 | 1 min | curl /health + spot check 后端代码 grep refusal |
| 总计 | **~30 min** | 2 commits、22 关键词、7 测试、前后端联动 |

---

## 9. 何时不要派 codex

- **1 行改动**：直接用 `edit` 工具更快
- **超大重构**（>500 行）：拆成多个小 sprint
- **跨多个 repo / 多机协调**：codex 不擅长，Cascade 自己做
- **prompt 写起来比代码还长**：直接 edit 更快
- **试错性探索**：codex 是"执行者"，不是"探索者"

---

## 10. 持续改进

每完成一个 sprint，回顾：
- prompt 是否第一次就让 codex 一次跑通？
- 是否有 codex 误解 / 漏改 / 多改？
- 等待时间是否合理？
- 部署有没有遇到新坑？

把新坑写到 §6 故障排除里，让团队不再踩第二遍。

---

**最后**：本工作流不是银弹，但比"Cascade 全程在 chat 里手写代码"快 3-5 倍，且 commit 历史清爽。核心心法是：**Cascade 当项目经理，Codex 当工程师，异步并行**。
