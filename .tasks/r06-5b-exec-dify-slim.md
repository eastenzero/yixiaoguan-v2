---
id: "r06-5b-exec-dify-slim"
parent: "R06-5"
type: "ops"                                     # 运维操作，改 compose 并重启单服务
status: "completed"
tier: "T3"                                      # 可交 T3 Kimi 执行（165 本机）
priority: "high"
risk: "medium"                                  # 会停 sandbox 容器，需冒烟回归

scope:
  - "/home/easten/dev/dify-deploy/docker/docker-compose.yaml"   # 注释掉 sandbox 服务块
  - "/home/easten/dev/dify-deploy/docker/docker-compose.yaml.bak-YYYYMMDD"   # 备份
  - "services/gateway/tests/smoke_chat.sh"     # 若需要；已有则不新建
  - ".tasks/reports/r06-5b-exec-dify-slim_report.md"

out_of_scope:
  - "services/**"                               # 不改 gateway 代码
  - "apps/**"                                   # 不改前端
  - "Dify Chatflow 配置"                         # 这是 R06-3c 的范围
  - "Dify Dataset"                              # 这是 R06-2 的范围
  - "Dify 的 .env / 数据库"                      # 本任务 Round 1 不动
  - "关闭 ssrf_proxy / plugin_daemon / weaviate" # 不在本任务范围（风险高，独立任务）
  - "调整 db_postgres / redis 参数"              # 不在 Round 1 范围

context_files:
  - ".teb/antipatterns.md"
  - "docs/design/dify-compose-baseline-report.md"  # 基线 + 瘦身建议
  - "docs/requirements/R06-P0-quick-wins.md"       # R06-5 章节
  - "docs/PROJECT-SECRETS.md"                       # §3.1 165 SSH

done_criteria:
  L0: "/home/easten/dev/dify-deploy/docker/docker-compose.yaml.bak-YYYYMMDD 存在；compose 文件的 sandbox 服务块被注释"
  L1: "docker compose up -d 后 sandbox 容器消失；其余 10 个容器状态均为 Up(healthy)"
  L2: "docker stats --no-stream 快照显示 Dify 总内存 ≤ 1.8 GiB"
  L3: "gateway 的 /api/chat/send 发 3 条测试问题（greeting / kb_query / transfer）均正常返回"

depends_on: []                                   # 独立任务，不依赖 scout 之外的产出
created_at: "2026-04-20"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-20 TX 授权 T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-5b Executor · Dify 瘦身 Round 1（关闭 sandbox）

> 目标状态：通过关闭 Dify 的 `sandbox` 服务，把容器组总内存从 **~2.25 GiB** 降至 **~1.73 GiB**（预估回收 ~520 MiB），**一步达标** R06-5 的 ≤1.8 GB 目标。
>
> 本任务**只做 Round 1**（关 sandbox）。Round 2（ssrf_proxy + db_postgres 降参数）和 Round 3（plugin_daemon）属独立后续任务，不在此落地。

## 背景

`docs/design/dify-compose-baseline-report.md` § 6.1 高置信度建议：关闭 `sandbox`。

- 当前 sandbox 占 **522.9 MiB**（单个容器最大内存占用）
- V2 Chatflow（`deploy/dify/yixiaoguan-chatflow.yml`）**无** Code Execution 节点
- R06-3c（prompt patch 任务）也确认新版 prompt 不引入代码执行需求
- **关闭 sandbox 后**：预估回收 ~520 MiB，总量 ≈ 1.73 GiB，达标

**Round 2 和 Round 3 的风险**：
- ssrf_proxy 关闭需同步改 `.env` 才不破坏外部请求
- plugin_daemon 可能承载 Dify 1.13 的 tongyi/qwen 模型提供商插件，关掉风险高
- 在 Round 1 已达标的前提下，不在本任务中做

## 必读上下文

1. `docs/design/dify-compose-baseline-report.md`（完整基线 + 3 轮瘦身建议 + 风险点）
2. `docs/requirements/R06-P0-quick-wins.md` § R06-5
3. `docs/PROJECT-SECRETS.md § 3.1`（165 SSH）

## 前置准备

### 1. SSH 登录 165

```bash
ssh easten@192.168.100.165
```

### 2. 进入 compose 目录

```bash
cd /home/easten/dev/dify-deploy/docker
pwd   # 应显示 /home/easten/dev/dify-deploy/docker
ls docker-compose.yaml  # 确认存在
```

### 3. 确认 Dify 当前健康状态

```bash
docker compose ps
```

**必须全部 Up / healthy**。若有 restarting / exited 的容器，**停止本任务**，先处理异常再瘦身。

### 4. 拿到当前内存基线

```bash
sleep 30
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | tee /tmp/dify-stats-before.txt
```

把总内存记在报告里，作为"瘦身前基线"。

---

## Step 1 · 备份 compose 文件

```bash
cd /home/easten/dev/dify-deploy/docker
DATE=$(date +%Y%m%d)
cp docker-compose.yaml docker-compose.yaml.bak-$DATE
ls -la docker-compose.yaml.bak-$DATE
```

**验收 L0**：`docker-compose.yaml.bak-YYYYMMDD` 存在且与原文件大小一致。

---

## Step 2 · 注释 sandbox 服务块

用以下方式之一：

### 方式 A（推荐）：sed 精确注释

```bash
cd /home/easten/dev/dify-deploy/docker

# 先定位 sandbox 服务块起止行
grep -n '^  sandbox:' docker-compose.yaml
grep -n '^  ssrf_proxy:' docker-compose.yaml  # sandbox 的下一个服务，作为结束标记
```

假设 sandbox 在第 N1 行，ssrf_proxy 在第 N2 行，用 Python 脚本块级注释（比 sed 安全）：

```bash
python3 <<'PY'
import re, pathlib, shutil
p = pathlib.Path("docker-compose.yaml")
lines = p.read_text().splitlines(keepends=True)
out = []
in_block = False
for line in lines:
    if re.match(r'^  sandbox:\s*$', line):
        in_block = True
    elif re.match(r'^  [a-zA-Z_]', line) and in_block:
        in_block = False
    if in_block:
        out.append("# " + line if not line.startswith("#") else line)
    else:
        out.append(line)
p.write_text("".join(out))
print("done")
PY
```

### 方式 B：手工 vim

```bash
vim docker-compose.yaml
# :set number
# /^  sandbox:$
# 进入 visual 模式选中整个服务块（到下一个同缩进的服务名 ssrf_proxy 之前）
# :',.!sed 's/^/# /'
```

### 验证

```bash
grep -A 20 '^# *sandbox:' docker-compose.yaml
```

应看到 sandbox 整块被 `# ` 前缀注释。

---

## Step 3 · 应用变更

```bash
cd /home/easten/dev/dify-deploy/docker
docker compose up -d
```

**期望输出**：
- `docker-sandbox-1  Removed`（或 Stopped + Removed）
- 其他容器：`docker-api-1  Running`、`docker-worker-1  Running` 等（已 running 的保持不变）

⚠️ 若看到其他容器**意外重启**，**立即**：
```bash
cp docker-compose.yaml.bak-$DATE docker-compose.yaml
docker compose up -d
```

## Step 4 · 健康检查（关键）

### 4.1 容器列表

```bash
docker compose ps
```

**期望**：sandbox 消失，其他 10 个容器全部 Up / healthy。

### 4.2 等 60 秒让系统稳定，再抓内存快照

```bash
sleep 60
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | tee /tmp/dify-stats-after.txt
```

**验收 L2**：手工加总所有容器的 Mem Usage，应 **≤ 1.8 GiB**（≈1843 MiB）。

### 4.3 Dify Web 可达性

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.100.165:3000
```

应返回 `200` 或 `307/302`（跳登录页）。

---

## Step 5 · gateway 端冒烟（关键）

```bash
# 在 165 上
TOKEN=$(curl -s -X POST http://localhost:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"staff_id":"2024010001","password":"2024010001"}' | jq -r .access_token)

CONV=$(curl -s -X POST http://localhost:8100/api/conversations \
  -H "Authorization: Bearer $TOKEN" | jq -r .id)

# T1 greeting
curl -N -X POST http://localhost:8100/api/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"conv_id\":$CONV,\"content\":\"你好\"}" | head -30

# T2 kb_query
curl -N -X POST http://localhost:8100/api/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"conv_id\":$CONV,\"content\":\"怎么申请弘毅奖学金？\"}" | head -30

# T3 transfer
curl -N -X POST http://localhost:8100/api/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"conv_id\":$CONV,\"content\":\"我要转人工\"}" | head -30
```

**验收 L3**：
- T1 走 greeting，返回固定问候文本
- T2 走 kb_query，有 RAG 结果（可能调用模型失败则停）
- T3 走 transfer，返回固定转人工文本

### 5.1 关键：KB 检索仍能通

T2 的 RAG 回答证明 **weaviate + 模型调用** 路径没被 sandbox 关闭影响。若 T2 失败，立刻回滚：

```bash
cd /home/easten/dev/dify-deploy/docker
cp docker-compose.yaml.bak-$DATE docker-compose.yaml
docker compose up -d
```

---

## Step 6 · 产出报告

创建 `.tasks/reports/r06-5b-exec-dify-slim_report.md`，必含：

```markdown
# R06-5b 执行报告（YYYY-MM-DD）

## 1. 基线（瘦身前）
- 总内存：XXX MiB
- 容器数：11
- 时间戳：YYYY-MM-DD HH:MM:SS

## 2. 变更
- 动作：注释 docker-compose.yaml 的 sandbox 服务块
- 备份：docker-compose.yaml.bak-YYYYMMDD
- 执行命令：docker compose up -d

## 3. 瘦身后
- 总内存：XXX MiB
- 容器数：10
- 时间戳：...

## 4. 冒烟结果
| 测试 | 结果 |
|------|------|
| docker compose ps 健康 | ✅ |
| Dify Web 200 | ✅ |
| greeting | ✅ |
| kb_query | ✅ |
| transfer | ✅ |

## 5. 回收内存
- 预估：~520 MiB
- 实际：XXX MiB

## 6. 异常与观察
- ...
```

---

## Step 7 · 更新文档

### 7.1 `docs/design/dify-compose-baseline-report.md`
- 在 § 9 末尾追加"Round 1 已完成，总内存从 X → Y"
- 标注时间戳

### 7.2 `docs/requirements/R06-P0-quick-wins.md`
- R06-5 总览表状态：📋 → ✅（Round 1 已达标）
- 变更日志追加一行
- Round 2/3 说明：已达标，暂不做

---

## 回滚方案

### Level 1：Step 3 后容器异常
```bash
cp docker-compose.yaml.bak-$DATE docker-compose.yaml
docker compose up -d
```

### Level 2：冒烟失败（sandbox 其实有隐藏依赖）
- 同 Level 1
- 在报告中记录"sandbox 不可直接关闭，原因 = ..."
- 反馈 T0 重新评估瘦身策略（改做 Round 2 或 PG 参数调整）

### Level 3：长时间（1 天后）发现某些功能异常
- Level 1 恢复
- 记录哪类操作触发异常，回灌到基线报告的"风险点"

---

## 已知陷阱

| 陷阱 | 规避 |
|------|------|
| 注释时截断到下一个服务块 | 用 Python 脚本方式，按同缩进层级截断 |
| docker compose 重启整组容器 | `up -d` 只影响被改的服务；若看到全部重启，说明 compose 语法错 |
| sandbox 有隐藏依赖（Dify 工具节点调用） | 未预料到；Level 1 回滚，补 Round 调查 |
| 本任务不改 `.env` | sandbox 对应的 `SANDBOX_API_KEY` 等环境变量保留；不会因缺变量报错 |
| 没加 `profiles` 导致删除后其他部署触发异常 | sandbox 在原 compose 中没有 `profiles`，注释后它不再启动；其他部署用的是 `yixiaoguan-chatflow.yml` 的 Chatflow，不依赖 sandbox |
| Round 2/3 不该在本任务做 | 严格只做 Round 1；Round 2 需改 .env，Round 3 风险高 |

---

## 不做的事（out_of_scope）

- 不改 ssrf_proxy / plugin_daemon / weaviate
- 不改 Dify 的 `.env`
- 不改 gateway 代码或配置
- 不改 Dify Chatflow / Dataset
- 不做 PG 参数调整
- 不做 Redis maxmemory 限制
- 不尝试彻底删除 sandbox 容器数据卷

---

## 完成后

1. `.tasks/reports/r06-5b-exec-dify-slim_report.md` 入仓（通过 Mutagen 或 git push）
2. 更新 `docs/design/dify-compose-baseline-report.md` 和 R06 spec
3. 通知 T0 / T2：R06-5 Round 1 已达标；建议 Round 2/3 单独立任
4. 如 Round 1 失败且回滚成功，反馈 T0 重新评估
