# Dify Docker Compose 基线报告（2026-04-20）

> 抓取者：T3 Kimi Scout  
> 抓取环境：192.168.100.165（本机直接执行，无需 SSH）  
> 抓取时刻：系统负载稳定 30s 后  
> 报告状态：✅ 已完成

---

## 1. Compose 文件位置

| 项 | 值 |
|---|---|
| **绝对路径** | `/home/easten/dev/dify-deploy/docker/docker-compose.yaml` |
| **所在目录** | `/home/easten/dev/dify-deploy/docker` |
| **Dify 版本**（从 image tag 推断） | `1.13.3`（`langgenius/dify-api:1.13.3`、`langgenius/dify-web:1.13.3`） |
| **最后修改时间** | `2026-04-13 15:13:41 +0800` |
| **文件总长度** | 1670 行 |
| **文件属性** | 由 `generate_docker_compose` 自动生成（头部注释说明） |

---

## 2. Services 清单

### 2.1 当前运行中的服务（`docker compose ps`）

| Service | Image | 状态 | 容器 ID | 暴露端口 |
|---------|-------|------|---------|----------|
| api | `langgenius/dify-api:1.13.3` | Up 6 days (healthy) | `2c862ce71483` | 5001/tcp |
| db_postgres | `postgres:15-alpine` | Up 6 days (healthy) | `23abc54c3a77` | 5432/tcp |
| nginx | `nginx:latest` | Up 6 days | `7c65b4b66919` | 0.0.0.0:3000→80, 0.0.0.0:3443→443 |
| plugin_daemon | `langgenius/dify-plugin-daemon:0.5.3-local` | Up 6 days | `6efbb2e37d96` | 0.0.0.0:5003→5003 |
| redis | `redis:6-alpine` | Up 6 days (healthy) | `37515d1478b4` | 6379/tcp |
| sandbox | `langgenius/dify-sandbox:0.2.14` | Up 6 days (healthy) | `63f51442379d` | — |
| ssrf_proxy | `ubuntu/squid:latest` | Up 6 days | `164b85384963` | 3128/tcp |
| weaviate | `semitechnologies/weaviate:1.27.0` | Up 6 days | `967363eb2ebd` | — |
| web | `langgenius/dify-web:1.13.3` | Up 6 days | `6b5de7fdefa1` | 3000/tcp |
| worker | `langgenius/dify-api:1.13.3` | Up 6 days | `81c82298742d` | 5001/tcp |
| worker_beat | `langgenius/dify-api:1.13.3` | Up 6 days | `ab6f84b5d515` | 5001/tcp |

**当前活跃容器数**：**11 个**

### 2.2 Compose 中定义但未运行的服务（带 `profiles`，未激活）

| Service | Image | Profile | 说明 |
|---------|-------|---------|------|
| init_permissions | `busybox:latest` | — | 一次性权限初始化容器，已完成 |
| db_mysql | `mysql:8.0` | `mysql` | 未使用 |
| certbot | `certbot/certbot` | `certbot` | 未使用 |
| qdrant | `langgenius/qdrant:v1.8.3` | `qdrant` | 未使用 |
| oceanbase | `oceanbase/oceanbase-ce:4.3.5-lts` | `oceanbase` | 未使用 |
| seekdb | `oceanbase/seekdb:latest` | `seekdb` | 未使用 |
| couchbase-server | build `./couchbase-server` | `couchbase` | 未使用 |
| pgvector | `pgvector/pgvector:pg16` | `pgvector` | 未使用 |
| vastbase | `vastdata/vastbase-vector` | `vastbase` | 未使用 |
| pgvecto-rs | `tensorchord/pgvecto-rs:pg16-v0.3.0` | `pgvecto-rs` | 未使用 |
| chroma | `ghcr.io/chroma-core/chroma:0.5.20` | `chroma` | 未使用 |
| iris | `containers.intersystems.com/intersystems/iris-community:2025.3` | `iris` | 未使用 |
| oracle | `container-registry.oracle.com/database/free:latest` | `oracle` | 未使用 |
| etcd / minio / milvus-standalone | — | `milvus` | Milvus 向量库全家桶，未使用 |
| opensearch / opensearch-dashboards | — | `opensearch` | 未使用 |
| opengauss | `opengauss/opengauss:7.0.0-RC1` | `opengauss` | 未使用 |
| myscale | `myscale/myscaledb:1.6.4` | `myscale` | 未使用 |
| matrixone | `matrixorigin/matrixone:2.1.1` | `matrixone` | 未使用 |
| elasticsearch / kibana | — | `elasticsearch` | 未使用 |
| unstructured | `downloads.unstructured.io/unstructured-io/unstructured-api:latest` | `unstructured` | 未使用 |

---

## 3. 资源占用快照（抓取时刻）

> ⚠️ 注：以下数值为 **`docker stats --no-stream`** 的**瞬时值**，部分 worker 的瞬时内存可能低于峰值平均值。

| 容器名 | Service | CPU% | Mem Usage / Limit | Mem% |
|--------|---------|------|-------------------|------|
| docker-api-1 | api | 0.09% | 432.4 MiB / 15.51 GiB | 2.72% |
| docker-worker-1 | worker | 0.42% | 481.3 MiB / 15.51 GiB | 3.03% |
| docker-worker_beat-1 | worker_beat | 0.00% | 296.4 MiB / 15.51 GiB | 1.87% |
| docker-web-1 | web | 0.00% | 106.1 MiB / 15.51 GiB | 0.67% |
| docker-db_postgres-1 | db_postgres | 1.34% | 159.8 MiB / 15.51 GiB | 1.01% |
| docker-redis-1 | redis | 0.34% | 9.207 MiB / 15.51 GiB | 0.06% |
| docker-sandbox-1 | sandbox | 0.00% | 522.9 MiB / 15.51 GiB | 3.29% |
| docker-plugin_daemon-1 | plugin_daemon | 0.25% | 193 MiB / 15.51 GiB | 1.22% |
| docker-ssrf_proxy-1 | ssrf_proxy | 0.02% | 22.84 MiB / 15.51 GiB | 0.14% |
| docker-nginx-1 | nginx | 0.00% | 9.141 MiB / 15.51 GiB | 0.06% |
| docker-weaviate-1 | weaviate | 0.77% | 73.4 MiB / 15.51 GiB | 0.46% |

**Dify 容器组内存总计**：

```
api          432.4 MiB
worker       481.3 MiB
worker_beat  296.4 MiB
web          106.1 MiB
db_postgres  159.8 MiB
redis          9.2 MiB
sandbox      522.9 MiB
plugin_daemon 193.0 MiB
ssrf_proxy    22.8 MiB
nginx          9.1 MiB
weaviate      73.4 MiB
-----------------------------
合计       ≈ 2,306 MiB  ≈  2.25 GiB
```

> 目标值（R06-5）：≤ 1.8 GB，当前差距约 **~500 MiB**。

---

## 4. 服务用途与必要性判断

| Service | Image | 典型职责 | 本项目必要性判断 | 置信度 |
|---------|-------|---------|------------------|--------|
| api | `langgenius/dify-api:1.13.3` | Dify 后端 API | **必须** | 高 |
| worker | `langgenius/dify-api:1.13.3` | Celery 异步任务 worker | **必须** | 高 |
| worker_beat | `langgenius/dify-api:1.13.3` | Celery Beat 定时任务调度 | **保留**（清理/调度任务依赖） | 中 |
| web | `langgenius/dify-web:1.13.3` | Dify 前端控制台 | **必须**（管理员用） | 高 |
| db_postgres | `postgres:15-alpine` | Dify 自有 PostgreSQL | **必须**（独立于 V2 gateway 的 PG） | 高 |
| redis | `redis:6-alpine` | 缓存 / Celery Broker | **必须** | 高 |
| nginx | `nginx:latest` | 反向代理（:3000→web, :3443→ssl） | **必须**（或外层反代替代） | 高 |
| weaviate | `semitechnologies/weaviate:1.27.0` | 向量数据库 | **必须**（`.env` 中 `VECTOR_STORE=weaviate`，确认在用） | 高 |
| sandbox | `langgenius/dify-sandbox:0.2.14` | 代码执行沙盒 | **可关**（V2 Chatflow 无代码执行节点） | 高 |
| ssrf_proxy | `ubuntu/squid:latest` | SSRF 防护代理 | **可关**（内网部署，但需同步移除 api/worker 的 `SSRF_PROXY_*` 环境变量） | 中 |
| plugin_daemon | `langgenius/dify-plugin-daemon:0.5.3-local` | 插件运行时 | **可关**（未使用自定义插件；但 Dify 1.13 部分模型提供商可能通过插件加载，需验证） | 中 |

> **重要发现**：
> - `.env` 中明确设置 `VECTOR_STORE=weaviate`，weaviate 是**当前活跃向量库**，不可直接关闭。
> - worker 当前仅 **1 个副本**，已无副本可降。
> - db_postgres 当前 `shared_buffers=128MB`（从 compose 文件 `command` 参数读取），有下调空间。

---

## 5. 依赖关系

### 5.1 简要依赖图（文字版）

```
                    ┌─────────────┐
                    │   nginx     │
                    │  (反向代理)  │
                    └──────┬──────┘
                           │ depends_on
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
      ┌────────┐     ┌────────┐      ┌─────────┐
      │  web   │     │  api   │      │  plugin │
      │(前端)  │     │(后端API)│      │ _daemon │
      └────────┘     └───┬────┘      └────┬────┘
                         │                │
              ┌─────────┼─────────┐      │ depends_on (optional)
              │         │         │      │
              ▼         ▼         ▼      ▼
        ┌────────┐ ┌────────┐ ┌──────┐ ┌──────────┐
        │ worker │ │worker_b│ │ redis│ │db_postgres│
        │        │ │ eat    │ │      │ │ (optional)│
        └───┬────┘ └───┬────┘ └──┬───┘ └──────────┘
            │          │         │
            └──────────┴─────────┘
                         │
              ┌─────────┼─────────┐
              │         │         │
              ▼         ▼         ▼
         ┌────────┐ ┌──────┐ ┌────────┐
         │sandbox │ │ssrf_ │ │weaviate│
         │(沙盒)  │ │proxy │ │(向量库)│
         └───┬────┘ └──┬───┘ └────────┘
             │         │
             └─────────┘
           sandbox 通过 HTTP_PROXY/HTTPS_PROXY
           使用 ssrf_proxy 访问外网
```

### 5.2 关键依赖说明

- **nginx** → `depends_on: [api, web]`（严格依赖，nginx 配置中 upstream 指向这二者）
- **api / worker / worker_beat** → `depends_on: init_permissions(已完成), db_postgres(healthy, optional), redis(started)`
- **plugin_daemon** → `depends_on: db_postgres(healthy, optional), db_mysql(healthy, optional)`
- 注意：`db_mysql`、`oceanbase`、`seekdb` 在 `depends_on` 中被声明，但它们带有 `profiles` **并未实际运行**；`required: false` 确保缺失时不会阻塞启动。

---

## 6. 瘦身候选清单

### 6.1 建议关闭（高置信度）

| Service | 当前内存 | 预估回收内存 | 理由 |
|---------|---------|-------------|------|
| **sandbox** | 522.9 MiB | ~520 MiB | V2 Chatflow 无"代码执行"节点；`deploy/dify/yixiaoguan-chatflow.yml` 中未见 Code 节点。关闭后不影响对话、RAG、知识库。 |

> 关闭方式：从 compose 文件中移除 `sandbox` 服务定义，或注释掉。

### 6.2 建议关闭（中置信度，需验证）

| Service | 当前内存 | 预估回收内存 | 理由与风险 |
|---------|---------|-------------|-----------|
| **ssrf_proxy** | 22.8 MiB | ~23 MiB | 内网部署，SSR F 风险可控。但 api/worker 环境变量中设置了 `SSRF_PROXY_HTTP_URL=http://ssrf_proxy:3128`，若直接关闭容器而保留环境变量，外部 HTTP 请求（如工具节点、网页抓取）会报连接失败。需**同步清空 `.env` 中的 `SSRF_PROXY_HTTP_URL` / `SSRF_PROXY_HTTPS_URL`**。 |
| **plugin_daemon** | 193 MiB | ~190 MiB | 当前未安装任何自定义插件。但 Dify 1.13 将部分模型提供商（如 tongyi/qwen）迁移到了插件架构；若 plugin_daemon 缺失，可能导致模型加载失败。建议在**测试环境**先关闭并跑通冒烟测试后再决定。 |

### 6.3 建议降级（中置信度）

| Service | 当前配置 | 建议调整 | 预估效果 |
|---------|---------|---------|---------|
| **db_postgres** | `shared_buffers=128MB` | 调至 `64MB` | 回收 ~64 MiB |
| **db_postgres** | `effective_cache_size=4096MB` | 调至 `1024MB` | 仅影响查询规划器，不直接省内存 |
| **redis** | 无 `maxmemory` 限制 | 追加 `maxmemory 256mb` + `maxmemory-policy allkeys-lru` | 防爆上限，当前仅 9 MiB，空间不大 |

> **worker 副本数**：当前已为 **1 个**，无法继续缩减。

### 6.4 保持不动

| Service | 理由 |
|---------|------|
| api | 核心服务，不可动 |
| worker | 核心服务，处理知识库索引/异步任务，不可动 |
| worker_beat | 负责定时清理任务、工作流调度；贸然关闭可能导致数据堆积 |
| web | 管理员控制台入口，必须保留 |
| db_postgres | Dify 自有数据库，必须保留 |
| redis | 缓存 + Celery Broker，必须保留 |
| nginx | :3000 入口反代，必须保留（或移至宿主机 nginx，但属于架构改动） |
| weaviate | `.env` 中 `VECTOR_STORE=weaviate` 且 Dataset/KB 检索依赖它；关闭需先迁移向量数据至 qdrant/pgvector 或切换内置存储 |

---

## 7. 风险点

1. **sandbox 关闭风险**：极低。V2 Chatflow（`deploy/dify/yixiaoguan-chatflow.yml`）中无 Code Execution 节点，确认不受影响。

2. **ssrf_proxy 关闭风险**：中。若仅停容器而不改 `.env`，api/worker 的 `SSRF_PROXY_HTTP_URL` 指向无效地址，可能导致：
   - HTTP Request 工具节点失败
   - 网页抓取（JinaReader/Firecrawl）失败
   - 外部 API 调用失败  
   **必须同步修改 `.env`**。

3. **plugin_daemon 关闭风险**：中高。Dify 1.13 的插件化程度较高，tongyi/qwen 模型可能通过 plugin_daemon 加载。关闭后若出现 `模型不可用` 或 `plugin_daemon 连接失败`，需立即回滚。

4. **weaviate 不可直接关闭**：当前 `.env` 中 `VECTOR_STORE=weaviate`，且 Dify Global Dataset（KB）的数据存储在 weaviate 中。若强行关闭，KB 检索将完全失效。**如需关闭 weaviate，必须先**：
   - 将向量数据迁移至 qdrant（或 pgvector）
   - 修改 `.env` 中 `VECTOR_STORE` 指向新后端
   - 重新索引所有文档
   这是一个**数据迁移任务**，不在本次瘦身 POC 的简易范围内。

5. **PG 参数调整风险**：`shared_buffers` 从 128MB 降到 64MB 对轻量负载影响极小，但需重启 `db_postgres` 容器生效；重启期间 Dify 短暂不可用（约 10-20 秒）。

6. **worker_beat 不建议关闭**：虽然它占用 296 MiB，但负责：
   - `ENABLE_CHECK_UPGRADABLE_PLUGIN_TASK=true`（插件更新检查）
   - `ENABLE_WORKFLOW_SCHEDULE_POLLER_TASK=true`（工作流定时触发）
   - 各类清理任务（消息清理、数据集队列监控等，当前部分已关闭）
   若确认所有 `ENABLE_*_TASK` 均已关闭且不需要定时调度，可再评估。

---

## 8. Compose 文件关键摘要

以下仅摘要当前**活跃服务**的关键配置。完整 1670 行 YAML 见原文件 `/home/easten/dev/dify-deploy/docker/docker-compose.yaml`。

```yaml
services:
  api:
    image: langgenius/dify-api:1.13.3
    environment:
      MODE: api
      SERVER_WORKER_AMOUNT: 1
      CELERY_WORKER_AMOUNT: 4
      DB_TYPE: postgresql
      VECTOR_STORE: weaviate
      SSRF_PROXY_HTTP_URL: http://ssrf_proxy:3128
      SSRF_PROXY_HTTPS_URL: http://ssrf_proxy:3128
    depends_on:
      - db_postgres
      - redis

  worker:
    image: langgenius/dify-api:1.13.3
    environment:
      MODE: worker
      CELERY_WORKER_AMOUNT: 4
    depends_on:
      - db_postgres
      - redis

  worker_beat:
    image: langgenius/dify-api:1.13.3
    environment:
      MODE: beat
    depends_on:
      - db_postgres
      - redis

  web:
    image: langgenius/dify-web:1.13.3

  db_postgres:
    image: postgres:15-alpine
    command: >
      postgres -c max_connections=100
               -c shared_buffers=128MB
               -c work_mem=4MB
               -c maintenance_work_mem=64MB
               -c effective_cache_size=4096MB

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass difyai123456

  weaviate:
    image: semitechnologies/weaviate:1.27.0
    profiles: [weaviate]

  sandbox:
    image: langgenius/dify-sandbox:0.2.14
    environment:
      API_KEY: dify-sandbox
      ENABLE_NETWORK: true
      HTTP_PROXY: http://ssrf_proxy:3128

  ssrf_proxy:
    image: ubuntu/squid:latest

  plugin_daemon:
    image: langgenius/dify-plugin-daemon:0.5.3-local
    environment:
      SERVER_PORT: 5002

  nginx:
    image: nginx:latest
    ports:
      - "3000:80"
      - "3443:443"
    depends_on:
      - api
      - web
```

---

## 9. 执行建议（供 r06-5b Executor 参考）

### Round 1：关闭 sandbox（预估回收 ~520 MiB）

1. 备份原 compose：`cp docker-compose.yaml docker-compose.yaml.bak`
2. 注释/删除 `sandbox` 服务块
3. `docker compose up -d`（仅 sandbox 会被移除）
4. 跑 `s3-deploy-test.md` 的 10 步冒烟测试
5. 若通过 → 当前内存可从 ~2.25 GB 降至 ~1.73 GB（**已达标 ≤1.8GB**）

### Round 2（可选）：关闭 ssrf_proxy + 下调 PG shared_buffers

- 若 Round 1 后已达标，Round 2 仅为进一步余量。
- 同步修改 `.env`：清空 `SSRF_PROXY_HTTP_URL` / `SSRF_PROXY_HTTPS_URL`
- 修改 db_postgres command：`shared_buffers=64MB`

### Round 3（不建议在本轮做）：plugin_daemon

- 风险较高，建议单独作为一个带冒烟测试的任务处理。

---

## 10. Round 1 执行记录（2026-04-20）

> 执行者：T3 Executor（Kimi CLI）
> 任务文件：`.tasks/r06-5b-exec-dify-slim.md`
> 详细报告：`.tasks/reports/r06-5b-exec-dify-slim_report.md`

- **动作**：注释 docker-compose.yaml 的 `sandbox` 服务块（987–1010 行）
- **备份**：`docker-compose.yaml.bak-20260420`
- **结果**：
  - 容器数：11 → 10
  - 瞬态内存：~2306 MiB → ~1433 MiB
  - 稳态估算：~1700–1800 MiB（**已达标 ≤ 1.8 GiB**）
  - 冒烟测试：greeting / kb_query（含 RAG sources）/ transfer 全部通过
- **结论**：Round 1 成功达标。Round 2（ssrf_proxy + PG 参数）和 Round 3（plugin_daemon）因已达标且风险收益比不足，暂不做。

---

*报告结束。Round 1 已由 T3 Executor 于 2026-04-20 完成并验证。*
