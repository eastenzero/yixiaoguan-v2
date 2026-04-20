# 192.168.100.165 服务器探查报告（2026-04-15）

## 目的

确认以下信息，便于后续继续 S2 回归测试与远程协作开发：

- `yixiaoguan-v2` 与旧 `yixiaoguan` 在 165 服务器上的实际目录
- 当前实际运行中的后端服务归属
- `Dify`、数据库、Redis 等依赖的在线状态
- 远程协作工具线索（用户口述 `mutagent`，推断为 `Mutagen`）

## 探查方式

通过以下入口登录服务器：

```bash
ssh easten@192.168.100.165
```

## 关键结论

### 1. SSH 可用，用户为 `easten`

已确认可以通过 `ssh easten@192.168.100.165` 正常连接服务器。

### 2. 服务器上同时存在两套项目

在 `/home/easten/dev` 下确认存在：

- `/home/easten/dev/yixiaoguan-v2`
- `/home/easten/dev/yixiaoguan`

这说明：

- **旧项目** `yixiaoguan` 仍然保留并且部分服务仍在运行
- **新项目** `yixiaoguan-v2` 已部署到同一台服务器，并有独立服务在运行

### 3. 当前 `yixiaoguan-v2` 的 FastAPI gateway 正在运行

已确认以下信息：

- 进程工作目录：`/home/easten/dev/yixiaoguan-v2/services/gateway`
- 启动命令：`python -m uvicorn app.main:app --host 0.0.0.0 --port 8100`
- 监听端口：`8100`

这说明当前 `8100` 对应的是：

- **新项目 `yixiaoguan-v2` 的 FastAPI 单体 gateway**

### 4. `yixiaoguan-v2` gateway 当前健康状态正常

远程检查结果：

```json
{"status":"ok","version":"2.0.0","checks":{"postgres":"ok","redis":"ok","dify":"ok"}}
```

说明以下依赖在当前运行态下均可访问：

- PostgreSQL
- Redis
- Dify

### 5. `yixiaoguan-v2` gateway 的实际环境变量

服务器上的 `services/gateway/.env` 内容显示：

- `database_url=postgresql+asyncpg://yxg:yxg_v2_pass@localhost:5432/yixiaoguan_v2`
- `redis_url=redis://:Yx%40Redis2026!@localhost:6379/1`
- `dify_api_url=http://localhost:3000/v1`
- 已配置 `dify_api_key`
- 已配置 dataset 相关 key/id

这与用户补充的环境信息一致：

- **Dify 跑在 165 服务器的 3000 端口**

### 6. 旧项目 `yixiaoguan` 仍在运行

已确认：

- `8080` 端口仍可返回 `200`
- 服务器上存在 Java 进程 `java -jar app.jar`
- `/home/easten/dev/yixiaoguan/deploy/.env` 仍然存在

结合旧项目文档，可以判断：

- `8080` 基本对应旧项目 `yixiaoguan/services/business-api`
- 旧项目链路尚未完全下线

### 7. 当前服务器是“双轨并存”状态

当前服务器上至少有以下关键端口在线：

- `3000`：Dify
- `5432`：PostgreSQL
- `6379`：Redis
- `8080`：旧项目 `yixiaoguan` 的业务后端
- `8100`：新项目 `yixiaoguan-v2` 的 FastAPI gateway

这意味着后续排查和测试必须明确区分：

- **旧项目接口链路**
- **v2 gateway 链路**

否则很容易混淆。

## 运行方式观察

### 1. `yixiaoguan-v2` gateway 当前看起来是手动启动的

根据进程信息，当前 `8100` 上的 gateway 是直接通过：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

启动的。

未在本次探查中确认到它由 systemd、docker compose 或 supervisor 托管。

### 2. 日志文件存在于 `/tmp/gw.log`

探查时读取到了 `/tmp/gw.log`，其中包含：

- `/api/auth/login`
- `/api/auth/me`
- `/api/conversations`
- `/api/conversations/{id}/escalate`
- WebSocket `/ws?token=...`

说明：

- `gateway` 已被实际访问和测试过
- 师生会话、升级教师、WebSocket 相关路径都在使用中

### 3. 旧项目存在独立开发启动脚本

服务器上有：

- `/home/easten/dev/start-dev.sh`

该脚本明确服务于：

- `/home/easten/dev/yixiaoguan`

并会启动：

- PostgreSQL / Redis（docker）
- Spring Boot 后端 `:8080`
- `ai-service :8000`
- teacher-web `:5173`
- student-app `:5174`

因此：

- 这个脚本是**旧项目开发环境脚本**
- **不是 `yixiaoguan-v2` gateway 的启动方式**

## Mutagen 线索

### 1. 用户提到的 `mutagent` 高概率是 `Mutagen`

外部资料与服务器痕迹都指向：

- 正确名称应为 **`Mutagen`**
- 它是一个常见的远程开发文件同步/端口转发工具

常见用途包括：

- 本地目录与远程 Linux 目录实时同步
- 基于 SSH 的开发协作
- 配合本地 IDE 编辑、远端运行服务

### 2. 服务器上存在 `Mutagen` 使用痕迹

已确认：

- 存在目录：`/home/easten/.mutagen`
- 存在测试目录：`/home/easten/dev/mutagen-test`
- `~/.mutagen/caches/` 下有缓存文件

这说明该服务器**很可能曾经使用过 Mutagen**。

### 3. 当前 shell 中未发现 `mutagen` 命令

探查结果：

- `command -v mutagen` 无输出

说明可能存在以下情况之一：

- Mutagen 曾经安装过，但当前 PATH 中不可用
- Mutagen 是在另一端机器（例如本地开发机）安装的，服务器端仅留下 agent/cache 痕迹
- 当前环境还未完成 shell 初始化，导致命令不可见

### 4. 对当前任务的帮助判断

Mutagen 对以下场景可能有帮助：

- 将本地 `yixiaoguan-v2` 与远程 `/home/easten/dev/yixiaoguan-v2` 做增量同步
- 避免频繁手动上传文件
- 保持本地 IDE 与远程运行环境协同

但就本次探查来看：

- **当前继续 S2 测试并不依赖 Mutagen**
- 它更像是后续优化远程协作流程的候选方案

## 对后续开发的直接影响

### 1. 之前的关键阻塞已解除

现在已经明确：

- 目标服务器可登录
- `yixiaoguan-v2` 的真实路径已确认
- `gateway` 正在运行且健康检查通过
- Dify / PG / Redis 均在线

因此后续可以直接基于 `165` 服务器继续：

- S2 smoke test
- 接口排障
- 运行日志核对
- WebSocket 联调

### 2. 后续操作时必须显式区分两套后端

建议在所有记录和命令中明确写出目标：

- `yixiaoguan-v2 gateway (:8100)`
- `yixiaoguan old business-api (:8080)`

避免把旧项目接口误当成 v2 接口。

### 3. 如果要继续做自动化或远程协作，建议补齐以下信息

建议未来补充并沉淀：

- `yixiaoguan-v2` 的正式启动脚本或 systemd service
- `gateway` 日志的固定落盘位置
- 是否有统一的部署入口
- 是否需要恢复/正式启用 `Mutagen`
- 本地仓库与服务器仓库的同步约定

## 建议的下一步

### 立即可做

- 基于 `http://192.168.100.165:8100` 继续执行 S2 13 步 smoke test
- 对照 `/tmp/gw.log` 记录测试过程
- 将结果补充到单独的测试报告中

### 适合后续沉淀

- 为 `yixiaoguan-v2` 新增一份专门的远程运行说明
- 补充一份服务器协作说明文档，明确：
  - SSH 登录方式
  - 仓库路径
  - 关键端口
  - 旧/新项目边界
  - 是否使用 Mutagen

## 附：本次探查得到的关键路径

- SSH：`ssh easten@192.168.100.165`
- 新项目：`/home/easten/dev/yixiaoguan-v2`
- 新 gateway：`/home/easten/dev/yixiaoguan-v2/services/gateway`
- 旧项目：`/home/easten/dev/yixiaoguan`
- 旧部署目录：`/home/easten/dev/yixiaoguan/deploy`
- gateway 日志：`/tmp/gw.log`
- Mutagen 痕迹：`/home/easten/.mutagen`
- Mutagen 测试目录：`/home/easten/dev/mutagen-test`
