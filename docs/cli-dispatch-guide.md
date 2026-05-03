# CLI 派单工作流通用指南（Cascade ⇄ kimi / codex / opencode 协作）

> 适用：Cascade 当 PM，把具体编码任务派给 3 大 CLI 之一（或并行派多个）执行。
>
> 本文从 `codex-dispatch-guide.md` 演化而来，把 codex-only 的部分泛化为 CLI 三家的通用模式（kimi、codex、opencode）。
>
> 维护时间：2026-04-29

---

## 1. 为什么要 "Cascade 派单 → CLI 执行"

| 角色 | 强项 | 短板 |
|---|---|---|
| **Cascade**（chat） | 调研、决策、设计、协调跨仓 / 跨设备资源 | 单次写大量代码慢、长 prompt 易失焦、不擅长重复改动 |
| **CLI 工人**（kimi / codex / opencode） | 严格按 prompt 编码、精确 diff、自动跑测试、commit 规整 | 没有项目宏观视角、不会做远程部署 |

**最佳分工**：

- Cascade 调研代码 → 设计 sprint → 写 prompt → 派 CLI → 等结果 → push + 部署 + 冒烟验证
- CLI 收 prompt → 改代码 → 跑测试 → commit（不 push）→ 写 summary

**收益**：

- Cascade 不用占着 chat 流写 200 行代码（chat 流被中断风险高）
- CLI 在专属 sandbox 里写 + 测试，commit message 规范
- **可以并行**：Cascade 派完 N 个独立任务后做别的事（比如继续调研）
- **可以多 AI 比稿**：同一个任务派给 3 家 CLI，对比哪家审美 / 工艺更对，再选最好的
- 异步：Cascade 派完后做别的事，轮询拿回结果

---

## 2. CLI 工具一览

### 2.1 已确认安装路径

```powershell
$kimi  = "C:\Users\Administrator\.local\bin\kimi.exe"
$codex = "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
$opencode = "C:\Users\Administrator\AppData\Roaming\npm\opencode.cmd"
```

每次脚本开头**显式给完整路径**最稳，Cascade 的 `run_command` 经常解析不到 PATH。

### 2.2 一句话调用语法（非交互 / 一次性执行 / 自动批准权限）

| CLI | 一句话语法 | 备注 |
|---|---|---|
| **kimi** | `Get-Content $prompt -Raw -Encoding UTF8 \| & $kimi --print --yolo *> $log` | `--print` 即非交互模式，隐式开 `--yolo` 自动批准 |
| **codex** | `Get-Content $prompt -Raw -Encoding UTF8 \| & $codex exec --dangerously-bypass-approvals-and-sandbox -C "<cwd>" --output-last-message $sum *> $log` | `exec` 子命令是非交互；`--output-last-message` 写出最后总结到文件 |
| **opencode** | `Get-Content $prompt -Raw -Encoding UTF8 \| & $opencode run -m deepseek/deepseek-v4-pro --dangerously-skip-permissions *> $log` | `run` 子命令一次性执行；`-m provider/model` 选模型；`--dangerously-skip-permissions` 等同 yolo |

**opencode 模型挑选指北**：

- `deepseek/deepseek-v4-pro` —— DeepSeek 最强通用模型，性价比高
- `deepseek/deepseek-reasoner` —— 推理型，适合复杂判断（架构 / 算法）
- `anthropic/claude-sonnet-4-5` —— Claude 顶级，UI / 设计审美强（**做美化任务首选**）
- `openai/gpt-5.3-codex` —— Codex 类，写代码工艺高
- `google/gemini-3-pro` —— Gemini 顶级，调研 / 资料整理强

### 2.3 标准启动模板（任意一家 CLI 通用）

```powershell
# 通用骨架
$cli        = $kimi   # 或 $codex / $opencode
$logDir     = "<workspace>\.tasks"
$promptFile = "$logDir\<agent>-<sprint-name>-prompt.txt"
$logFile    = "$logDir\<agent>-<sprint-name>.log"
$summary    = "$logDir\<agent>-<sprint-name>-summary.txt"

Write-Output "starting <sprint> at $(Get-Date -Format 'HH:mm:ss')"

# 不同 CLI 的 invocation：
# Kimi:
Get-Content $promptFile -Raw -Encoding UTF8 | & $kimi --print --yolo *> $logFile
# Codex:
Get-Content $promptFile -Raw -Encoding UTF8 | & $codex exec --dangerously-bypass-approvals-and-sandbox -C "<repo>" --output-last-message $summary *> $logFile
# Opencode (DeepSeek):
Get-Content $promptFile -Raw -Encoding UTF8 | & $opencode run -m deepseek/deepseek-v4-pro --dangerously-skip-permissions *> $logFile

Write-Output "finished <sprint> at $(Get-Date -Format 'HH:mm:ss')"
```

**关键参数对应**：

| 概念 | kimi | codex | opencode |
|---|---|---|---|
| 非交互模式 | `--print` | `exec` | `run` |
| 自动批准 | `--yolo`（含在 --print 里） | `--dangerously-bypass-approvals-and-sandbox` | `--dangerously-skip-permissions` |
| 工作目录 | （从启动 cwd 取） | `-C <path>` 显式指 | `--dir <path>` 或启动 cwd |
| 模型选择 | `-m <model>` | （由账号 / 配置决定） | `-m provider/model` |
| 最终消息 | （手动 grep 日志） | `--output-last-message <file>` | （手动 grep 日志） |

---

## 3. Cascade 调用方式（在 `run_command` 里）

**关键设置**：

```jsonc
{
  "Blocking": false,           // 必须 false，否则 chat 卡到 CLI 完成
  "SafeToAutoRun": true,       // 写入 .tasks 目录是安全的
  "WaitMsBeforeAsync": 5000    // 等 5s 看 CLI 是否秒挂（如 prompt 路径错）
}
```

**为什么 `Blocking=false`**：单 sprint 通常 3-15 分钟，阻塞会让 chat 流挂死。非阻塞 + 主动轮询是关键。

**进度监控一行命令**（监控所有 3 家）：

```powershell
"kimi:$((Get-Process kimi -EA 0 | Measure-Object).Count) " +
"codex:$((Get-Process codex -EA 0 | Measure-Object).Count) " +
"opencode:$((Get-Process opencode -EA 0 | Measure-Object).Count) " +
"node:$((Get-Process node -EA 0 | Measure-Object).Count)"
```

`*procs:0` 即对应 CLI 完成。

---

## 4. Prompt 写法（最关键）

### 4.1 黄金法则

| 原则 | 例 |
|---|---|
| **明确目标 + 范围** | "重写 src/views/HomePage.vue，应用 DESIGN.md 视觉系统" |
| **列明输入文件路径** | "请先读：DESIGN.md / jade.css / LandingPage.vue（标杆）" |
| **列明输出文件路径** | "请把结果写到 src/views/HomePage.<agent>.vue（不要覆盖原文件）" |
| **明确不做什么** | "不要修改 router、main.js、其它 .vue 文件、demo/ 后端、references/、images/" |
| **明确技术栈约束** | "不要 npm install。沿用已有 GSAP / Lenis / Tailwind / Element Plus" |
| **写 Verify 步骤**（如适用） | "Verify: dev server 自动 HMR，看是否仍能 mount，仍能渲染列表" |
| **强调 Final state expected** | 最后总结期望（输出文件存在 / 编译过 / 没改其他文件） |
| **PowerShell quoting 警告** | "Windows PowerShell 环境，避免复杂 shell pipe + 多层引号转义" |

### 4.2 完整 Prompt 模板

```
任务：<一句话目标>。<工作量估算>。

## 背景
- <现状代码位置 + 行号 + 简述>
- <相关上下游>
- Goal: <一句话再说一次目标>

## 严格规则
- 不要 <负面清单 1>
- 不要 <负面清单 2>
- ...
- Windows PowerShell 环境，避免复杂 shell pipe 与多层引号转义

## 你必须读的输入文件
- <abs-path-1> —— 干什么用
- <abs-path-2> —— 干什么用

## 你必须输出的文件
- <abs-path-output> —— 干什么的

## 实施步骤
1. <动作 1>
2. <动作 2>
   ```
   <可选示例代码 / 数据格式>
   ```
3. ...

## Final state expected
- [ ] <文件存在>
- [ ] <编译过>
- [ ] <没改其他文件>

完成后请总结：
1. 你做了什么
2. 关键决策
3. 是否遇到阻塞 / 漏洞
```

### 4.3 反面案例（容易翻车）

❌ **太开放**："请帮我把首页做漂亮一点"
→ CLI 会乱选 API / 表结构 / 文件位置，需要返工

❌ **要求改既有 commit**：要求 amend / rebase 容易破坏 commit chain
→ **永远新建 commit / 新文件**

❌ **缺少 Verify**："改完即可"
→ CLI 不会主动验证

❌ **多 CLI 比稿但写到同一文件**：3 家 CLI 互相覆盖
→ **每家写到独立文件**（HomePage.kimi.vue / HomePage.codex.vue / HomePage.deepseek.vue）

### 4.4 文件命名约定

放 `.tasks/<agent>-<sprint>-prompt.txt`：

- `.tasks/kimi-strip-backend-prompt.txt`
- `.tasks/codex-video-tea-prompt.txt`
- `.tasks/opencode-homepage-reskin-prompt.txt`

对应日志：

- `.tasks/<agent>-<sprint>.log` —— stdout/stderr 全量
- `.tasks/<agent>-<sprint>-summary.txt` —— 最后总结（codex 自动写，其他需 grep）

---

## 5. 多 AI 比稿（A/B/C 测试同一任务）

> 这是单 CLI 派单的高阶用法：同一份 prompt 派给 N 个 CLI，对比谁做得最好。

### 5.1 适用场景

- **设计 / 美化**：每个 AI 审美不同，比稿后选最好的
- **架构方案**：要 3 个不同思路对比
- **性能优化**：3 家可能给出 3 种思路

### 5.2 做法

1. **准备 N 份独立的工作文件**：
   ```powershell
   Copy-Item src/views/HomePage.vue src/views/HomePage.kimi.vue
   Copy-Item src/views/HomePage.vue src/views/HomePage.codex.vue
   Copy-Item src/views/HomePage.vue src/views/HomePage.deepseek.vue
   ```

2. **写一份共享 prompt** `.tasks/homepage-reskin-prompt.txt`，里面用占位符或显式三个不同输出路径。

3. **派 3 个独立 CLI**，每个 CLI prompt 中写明它的目标文件：
   ```powershell
   # Kimi
   "${promptText}`n请把结果写到 src/views/HomePage.kimi.vue" | & $kimi --print --yolo *> $kimiLog
   # Codex
   "${promptText}`n请把结果写到 src/views/HomePage.codex.vue" | & $codex exec ... *> $codexLog
   # OpenCode
   "${promptText}`n请把结果写到 src/views/HomePage.deepseek.vue" | & $opencode run -m anthropic/claude-sonnet-4-5 ... *> $opencodeLog
   ```

4. **轮询等待**：直到 3 家 procs 全 = 0。

5. **Cascade 评审**：
   - diff 三个文件
   - 必要时跑 dev server 用临时路由分别预览
   - 选最好的提到主文件 `HomePage.vue`
   - 把另外两份归档或删除

### 5.3 模型 vs 任务匹配建议

| 任务类型 | 推荐 CLI / 模型 | 备注 |
|---|---|---|
| **设计 / 美化 / 视觉** | opencode + claude-sonnet-4-5 / kimi-k2-thinking | Claude 审美最强 |
| **复杂代码重构** | codex (gpt-5-codex) / opencode + deepseek-v4-pro | Codex 工艺高 |
| **资料 / 调研 / 整理** | kimi / opencode + gemini-3-pro | 长上下文友好 |
| **算法 / 优化** | opencode + deepseek-reasoner | 推理强 |
| **多语言 / 中文敏感** | kimi-k2 / opencode + claude | Kimi 母语 |
| **Web 抓取 / 网络任务** | kimi / opencode（不要 codex —— 倾向用纯代码方案） | Kimi 工具用得比 codex 灵活 |

---

## 6. 异步轮询等待机制

### 6.1 完整生命周期

```
Cascade                              CLI
  │                                     │
  ├─ run_command Blocking=false ──────▶ 进程启动
  │  WaitMsBeforeAsync=5000             │
  │                                     │
  │  (5s 内若 CLI 秒挂，立刻返回 error)  │
  │                                     │
  ├─ Start-Sleep N 秒                   │ <----- 关键
  │                                     │
  ├─ 检查 CLI 进程是否还在 ◀───────────  │
  │                                     │
  ├─ 没了 → 看 git log / 输出文件       │
  │                                     │
  └─ 还在 → 再等 N 秒                   │
```

### 6.2 等多久？经验值

| Sprint 类型 | 平均时长 | 第一次 Sleep 建议 |
|---|---|---|
| **改 1-2 文件 + 简单逻辑** | 2-5 min | `Start-Sleep -Seconds 180` |
| **改 1 模块 + 几个文件 + 跑测试** | 5-10 min | `Start-Sleep -Seconds 300` |
| **设计美化 + UI 重做** | 10-20 min | `Start-Sleep -Seconds 600` |
| **网络任务（下载 / 抓取）** | 5-30 min | `Start-Sleep -Seconds 600` |
| **大型 feature + 多文件** | 15-30 min | `Start-Sleep -Seconds 900` |

**策略**：第一次 sleep 一半时间 → 检查进程 → 没结束再 sleep 剩余 → 再检查。**不要一次 sleep 太长**（用户可能要插话）。

### 6.3 检查 CLI 是否完成（一行）

```powershell
"$(Get-Date -Format 'HH:mm:ss') | kimi:$((Get-Process kimi -EA 0 | Measure-Object).Count) codex:$((Get-Process codex -EA 0 | Measure-Object).Count) opencode:$((Get-Process opencode -EA 0 | Measure-Object).Count)"
```

### 6.4 完成后的标准验收

```powershell
# 1. 看新文件
Get-ChildItem <output-path> -EA 0

# 2. 看 summary（codex 有 --output-last-message，其他需 grep 日志最后几行）
Get-Content $summary -Encoding UTF8 -Raw         # codex
Get-Content $log -Tail 80 -Encoding UTF8         # 通用
```

---

## 7. 常见故障

### 7.1 CLI 启动直接挂掉

**症状**：5s 内进程消失，`procs:0`，log 里有 stack trace 或权限错误

**排查**：
1. 显示 prompt 路径是否正确（绝对路径）
2. log 文件是否能写（目录权限）
3. CLI 是否需要登录（`opencode auth`、`kimi login`）

### 7.2 PowerShell 引号嵌套失败

**症状**：调用 ssh / 远程 / 复杂正则时 0 输出

**解决**：
- 简化为单层引号
- 多层引号命令落到 .sh / .ps1 文件 + scp / dotsource
- 用 Python 脚本代替 shell pipe

### 7.3 网络抓取失败（反爬）

**症状**：Pexels / Pixabay / TLS handshake fail / 403

**解决**：
- 优先用反爬较弱的源（Mixkit / Wikipedia Commons / Coverr）
- 加 `-UserAgent "Mozilla/5.0"`
- 重试用不同模型（kimi 比 codex 在网络任务上更宽松）

### 7.4 CLI 漏看主仓最新提交

**症状**：派的改动接在过期 base 上 → 多 head / 冲突

**预防**：在 prompt 顶部写 "current HEAD = `<sha>`"，让 CLI 验证起点。

### 7.5 多 AI 比稿时输出冲突

**症状**：3 家 CLI 都写到同一文件，最后只剩最后一家的版本

**解决**：每家显式写到独立路径（HomePage.kimi.vue / HomePage.codex.vue / HomePage.deepseek.vue）。在 prompt 里写死。

### 7.6 yoga README 与实际不符（实战教训）

**症状**：CLI 完成后说"已下载视频"，但实际下载的内容与 README 描述不符（Kimi 抓 Pexels 时拿了错误结果集）

**预防**：
- 在 prompt 里加一条："写 README 时严格描述 **你实际下载的视频内容**，不要套用搜索 query"
- Cascade 收到后**抽检**至少一个文件验证（视频用 ffprobe / 图片用 PIL）

---

## 8. Cheat Sheet（速查）

### 启动新 sprint（kimi）

```powershell
$kimi = "C:\Users\Administrator\.local\bin\kimi.exe"
$prompt = ".tasks\kimi-<name>-prompt.txt"
$log = ".tasks\kimi-<name>.log"
Get-Content $prompt -Raw -Encoding UTF8 | & $kimi --print --yolo *> $log
# Blocking=false, WaitMsBeforeAsync=5000
```

### 启动新 sprint（codex）

```powershell
$codex = "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
$prompt = ".tasks\codex-<name>-prompt.txt"
$log = ".tasks\codex-<name>.log"
$sum = ".tasks\codex-<name>-summary.txt"
Get-Content $prompt -Raw -Encoding UTF8 | & $codex exec --dangerously-bypass-approvals-and-sandbox -C "<repo>" --output-last-message $sum *> $log
```

### 启动新 sprint（opencode + DeepSeek 或 Claude）

```powershell
$opencode = "C:\Users\Administrator\AppData\Roaming\npm\opencode.cmd"
$prompt = ".tasks\opencode-<name>-prompt.txt"
$log = ".tasks\opencode-<name>.log"
# 用 DeepSeek（性价比高）
Get-Content $prompt -Raw -Encoding UTF8 | & $opencode run -m deepseek/deepseek-v4-pro --dangerously-skip-permissions *> $log
# 或用 Claude（审美强）
Get-Content $prompt -Raw -Encoding UTF8 | & $opencode run -m anthropic/claude-sonnet-4-5 --dangerously-skip-permissions *> $log
```

### 等待 + 检查

```powershell
Start-Sleep -Seconds 300
"$(Get-Date -Format 'HH:mm:ss') | kimi:$((Get-Process kimi -EA 0).Count) codex:$((Get-Process codex -EA 0).Count) opencode:$((Get-Process opencode -EA 0).Count)"
```

---

## 9. 何时**不**要派 CLI

- **1 行改动**：直接用 `edit` 工具更快
- **超大重构**（>500 行）：拆成多个小 sprint
- **跨多个 repo / 多机协调**：CLI 不擅长，Cascade 自己做
- **prompt 写起来比代码还长**：直接 edit 更快
- **试错性探索**：CLI 是"执行者"，不是"探索者"

---

## 10. 持续改进

每完成一个 sprint，回顾：

- prompt 是否第一次就让 CLI 一次跑通？
- 是否有 CLI 误解 / 漏改 / 多改？
- 等待时间是否合理？
- 比稿时哪家审美 / 工艺胜出？为什么？
- 把新坑写到 §7 故障排除里，让团队不再踩第二遍。

---

**最后**：本工作流不是银弹，但比"Cascade 全程在 chat 里手写代码"快 3-5 倍，且 commit 历史清爽。

**核心心法**：

- **Cascade 当 PM，CLI 当工程师**
- **能并行就并行，能比稿就比稿**
- **审美交给 Claude，工艺交给 Codex，调研交给 Kimi**
