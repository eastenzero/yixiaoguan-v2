---
id: "r06-5a-scout-dify-compose"
parent: "R06-5"
type: "feature"
status: "pending"
tier: "T3"
priority: "medium"
risk: "low"
foundation: true

scope:
  - "docs/design/dify-compose-baseline-report.md"

out_of_scope:
  - "services/**"
  - "apps/**"
  - "任何对 Dify 容器的修改"
  - "任何 docker-compose 文件的修改"
  - "重启 / 停止 / 启动 Dify 的任何操作"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"     # R06-5 章节
  - "docs/PROJECT-CONTEXT.md"                     # §3 远端服务器
  - "docs/PROJECT-SECRETS.md"                     # §3.1 165 SSH

done_criteria:
  L0: "docs/design/dify-compose-baseline-report.md 存在"
  L1: "报告列出 Dify docker-compose 文件的绝对路径和所有 services 列表"
  L2: "报告包含当前每个容器的 CPU / 内存占用（docker stats 快照）"
  L3: "报告末尾给出 '瘦身候选清单' + '风险点'，Executor 可据此起草瘦身任务"

depends_on: []
created_at: "2026-04-17"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-17 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-5a Scout · 摸清 165 服务器上 Dify 的 docker-compose 现状

> 目标状态：Executor 在起草瘦身任务前，已经知道当前 Dify 的 compose 文件位置、所有 services、每个服务的资源占用、服务之间的依赖关系。**本任务严格只读**。

## 背景

`R06-5` 目标是把 Dify 容器组的总内存从 ≥2.5GB 降到 ≤1.8GB，以便给 gateway + PG + Redis 留出资源。
瘦身前必须**准确掌握基线**，否则无法判断：

- 哪些服务必须保留（gateway 依赖）
- 哪些服务可以关闭（未使用）
- 哪些服务可以降级（降 worker 副本、降 PG 内存等）

## 必读上下文

1. `docs/requirements/R06-P0-quick-wins.md` § R06-5（父需求）
2. `docs/PROJECT-SECRETS.md` § 3.1（SSH 登录信息）
3. `docs/PROJECT-CONTEXT.md` § 3（远端服务器架构）

## Scout 执行步骤

### Step 1：登录 165 服务器

```bash
ssh easten@192.168.100.165
# 密码见 PROJECT-SECRETS.md §3.1
```

### Step 2：定位 Dify compose 文件

```bash
# 常见位置（逐一尝试，第一个匹配的即是）
ls -la /home/easten/dify/docker/docker-compose.yaml 2>/dev/null
ls -la /home/easten/dify/docker-compose.yaml 2>/dev/null
ls -la /opt/dify/docker/docker-compose.yaml 2>/dev/null
# 如果上面都没有，用 find
find / -name "docker-compose*.yaml" -path "*dify*" 2>/dev/null
```

记录结果：**Dify compose 文件绝对路径** = `___`

### Step 3：导出服务清单

```bash
cd <compose 所在目录>
docker compose ps --format json | jq -s 'map({name, service, state, health})'
# 若系统没装 jq，就用：
docker compose ps
```

记录所有 service 名、状态、对应容器 ID。

### Step 4：抓资源占用快照

```bash
# 等 30 秒让负载稳定
sleep 30
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

记录每个容器的 **CPU%** 和 **Memory usage / limit**。

### Step 5：读取 compose 文件内容

```bash
cat <compose 文件路径>
```

整份 YAML 贴到报告里（或摘要关键部分，最少要有 services 清单 + 每个服务的 image + environment + depends_on + ports）。

### Step 6：确认服务用途

对每个 service，识别其职责。参考清单：

| service | 典型职责 | 本项目必要性判断 |
|---------|---------|------------------|
| api | Dify 后端 API | **必须** |
| worker | 异步任务 worker | **必须**（副本可降） |
| web | Dify 前端 | **必须**（管理员用） |
| db / postgres | Dify 自己的 PG | **必须**（独立于 V2 gateway 的 PG） |
| redis | 缓存 | **必须** |
| weaviate | 向量库 | 看是否在用 |
| qdrant | 向量库（可能替代 weaviate） | 看是否在用 |
| nginx | 反代 | **必须**（或外层反代替代） |
| sandbox | 代码沙盒 | **可关**（V2 不用代码执行节点） |
| ssrf_proxy | SSRF 防护 | **可关**（内网部署） |
| plugin_daemon | 插件运行时 | **可关**（未用插件） |
| certbot | HTTPS 证书 | 视情况（内网可关） |

⚠️ **不要仅凭服务名猜，一定 cat compose 文件读 image 字段确认**。某些 service 名在不同版本 Dify 里含义不同。

### Step 7：识别依赖关系

```bash
docker compose config --services
docker compose config | grep -A 3 "depends_on"
```

画出简要依赖图（文字版即可）。

### Step 8：写产出报告

创建 `docs/design/dify-compose-baseline-report.md`：

```markdown
# Dify Docker Compose 基线报告（YYYY-MM-DD）

> 抓取者：T3 Kimi Scout
> 抓取环境：192.168.100.165
> 抓取时刻：系统负载稳定 30s 后

## 1. Compose 文件位置

- 绝对路径：...
- Dify 版本（从 image tag 推断）：...
- 最后修改时间：`stat -c %y <file>`

## 2. Services 清单

| Service | Image | 状态 | 容器 ID |
|---------|-------|-----|---------|
| ... | ... | ... | ... |

## 3. 资源占用快照（抓取时刻）

| 容器 | CPU% | Mem | Mem% |
|------|-----|-----|------|
| ... | ... | ... | ... |

**总计**：CPU = X%, Memory = X MB

## 4. 服务用途与必要性判断

（按 Step 6 的表格填写）

## 5. 依赖关系

（依赖图文字版）

## 6. 瘦身候选清单

### 6.1 建议关闭（高置信度）
- service-A：理由是 ...
- service-B：理由是 ...

### 6.2 建议降级（中置信度）
- service-C：可降 worker 副本从 N → 1
- service-D：可限 mem_limit 从 X → Y

### 6.3 保持不动
- service-E：核心，不能动
- ...

## 7. 风险点

- 如果关闭 X，可能影响 ...
- 如果降 Y，需要 ...
- Dify 某些版本的 weaviate/qdrant 切换可能需要 ...

## 8. Compose 文件全文

\`\`\`yaml
（粘贴或摘要关键部分）
\`\`\`
```

## 已知陷阱

- **不要 `docker compose down`**（会停所有服务）
- **不要 `docker compose up -d`**（会重建容器可能破坏数据）
- **不要改 `.env` 或 compose 文件**（Executor 的职责）
- **不要直接进入容器执行命令**，仅观察外部状态
- 若发现 Dify 容器有大量 `restarting` 或 `exited` 状态，**如实记录**但不要尝试修复
- `docker stats --no-stream` 抓的是**瞬时快照**，某些 worker 的瞬时内存可能低于平均值；报告中要注明"瞬时值"
- Dify 的 `db` / `postgres` 容器里装的是 **Dify 自己的数据库**，不是 V2 gateway 的 PG；别搞混

## 不做的事（out_of_scope）

- 不做任何 docker 容器的 start/stop/restart/rm
- 不编辑 compose 文件或 .env
- 不编辑 V2 仓的代码
- 不尝试"顺便修理"发现的异常

## 完成后

1. 产出 `docs/design/dify-compose-baseline-report.md`
2. 向 T1 回报文件路径
3. T0 或 T1 基于此报告起草 `.tasks/r06-5b-exec-dify-slim.md`
