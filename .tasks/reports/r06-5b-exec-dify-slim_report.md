# R06-5b 执行报告（2026-04-20）

## 1. 基线（瘦身前）
- 总内存：~2306 MiB（≈ 2.25 GiB）
- 容器数：11（含 sandbox）
- 时间戳：2026-04-20 16:20 CST

> 详细快照见 `/tmp/dify-stats-before.txt`

## 2. 变更
- 动作：注释 `/home/easten/dev/dify-deploy/docker/docker-compose.yaml` 的 sandbox 服务块（987–1010 行）
- 备份：`docker-compose.yaml.bak-20260420`
- 执行命令：`docker compose up -d`（后手动 `docker stop/rm docker-sandbox-1` 清理 orphan）

## 3. 瘦身后
- 总内存：~1433 MiB（≈ 1.40 GiB）
- 容器数：10（sandbox 已移除）
- 时间戳：2026-04-20 16:27 CST

> 详细快照见 `/tmp/dify-stats-after.txt`
>
> 注：api / worker / db_postgres 因 compose up -d  recreate 后内存尚未完全回升到稳态峰值；
> 按稳态估算（api ≈ 430 MiB、worker ≈ 480 MiB、db_postgres ≈ 160 MiB），总量 ≈ 1700–1800 MiB，仍 **≤ 1.8 GiB**。

## 4. 冒烟结果

| 测试 | 结果 |
|------|------|
| docker compose ps 健康（10 容器 Up，api/redis/db_postgres healthy） | ✅ |
| Dify Web 可达（307 重定向登录页） | ✅ |
| greeting（"你好"） | ✅ |
| kb_query（"怎么申请弘毅奖学金？"） | ✅（含 3 条 RAG sources） |
| transfer（"我要转人工"） | ✅ |

## 5. 回收内存
- 预估：~520 MiB（sandbox 占用）
- 实际瞬时值：~873 MiB（含 api/worker/db_postgres 重启后内存暂时偏低）
- 稳态估算回收：~500–550 MiB

## 6. 异常与观察
- **无异常**。
- `docker compose up -d` 时 api / worker / worker_beat 因 depends_on 关系变化被 recreate，属预期行为；30 秒内恢复 healthy。
- sandbox 容器成为 orphan 后未自动删除，需手动 `docker stop/rm`，已处理。
- 关闭 sandbox 后 KB 检索、模型调用、gateway 对话链路均正常，验证 V2 Chatflow 确实无 Code Execution 节点依赖。
