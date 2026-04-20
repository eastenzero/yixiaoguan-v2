# TEB + Mutagen 远程开发工作流

> 适用项目：`yixiaoguan-v2`
> 
> 当前协作基线：
> - 项目已接入 `.teb/`
> - 项目已接入 `.tasks/`
> - 项目根目录已存在 `mutagen.yml`
> - 当前默认远端开发目标：`easten@192.168.100.165:/home/easten/dev/yixiaoguan-v2`

---

## 1. 目标

这套工作流用于解决两个问题：

1. **需求与执行分层**：用 TEB 管理需求、任务、执行、验证
2. **本地编辑 + 远端运行**：用 Mutagen 保持本地代码与 165 服务器同步

推荐模式是：

- **本地 IDE 写代码**
- **Mutagen 自动同步到 165**
- **165 服务器负责运行 gateway / 看日志 / 做联调**

---

## 2. 当前默认服务器角色

### 2.1 主开发 / 联调机

- `192.168.100.165`
- 用户：`easten`
- 项目目录：`/home/easten/dev/yixiaoguan-v2`
- 当前已确认：
  - `services/gateway` 在 `:8100` 运行
  - Dify 在 `:3000`
  - PostgreSQL / Redis 可用

### 2.2 后续可讨论的候选机器

- `64.90.13.65`
  - `Ubuntu 24.04`
  - `16 vCPU / 15Gi RAM`
  - 当前未安装 Docker
  - 已有 nginx 与代理类服务占部分端口

- `60.205.205.99`
  - `Alibaba Cloud Linux 3`
  - `2 vCPU / 1.8Gi RAM`
  - 已安装 Docker
  - 当前已有 1Panel / nginx / docker-proxy 等服务在跑

> 这两台服务器先作为后续部署讨论输入，当前 Mutagen 默认**不**指向它们。

---

## 3. 本地前置条件

## 3.1 安装 Mutagen

需要先在**本地开发机**安装 Mutagen，并确保 `mutagen` 命令可用。

安装完成后，可先验证：

```powershell
mutagen version
```

如果这里没有输出版本号，说明本地 Mutagen 还未安装好，先不要执行下面的启动命令。

## 3.2 确保本地可直连 165 服务器

先确认以下 SSH 命令可用：

```powershell
ssh easten@192.168.100.165
```

如果你本地已经配置免密，这一步会更顺畅。

---

## 4. 项目级 Mutagen 启动命令

## 4.1 推荐方式：使用项目配置文件启动

在项目根目录执行：

```powershell
mutagen project start
```

这会读取项目根的 `mutagen.yml`，按既定规则创建同步会话。

当前配置对应：

- 本地目录：项目根目录 `.`
- 远端目录：`easten@192.168.100.165:/home/easten/dev/yixiaoguan-v2`
- 同步模式：`two-way-resolved`

已忽略的内容包括：

- `services/gateway/.env`
- `deploy/.env`
- `venv`
- `services/gateway/venv`
- `node_modules`
- `dist`
- `build`
- `__pycache__`
- 各类测试缓存与日志文件

## 4.2 检查同步状态

```powershell
mutagen sync list
```

如果创建成功，应该能看到名为 `yixiaoguan-v2` 的同步会话。

## 4.3 强制把待同步内容推过去

```powershell
mutagen sync flush yixiaoguan-v2
```

适合在以下场景使用：

- 刚做完一批较大改动
- 你想确保远端已经拿到最新内容
- 远端准备重启服务前

## 4.4 暂停 / 恢复同步

```powershell
mutagen sync pause yixiaoguan-v2
mutagen sync resume yixiaoguan-v2
```

适合在以下场景使用：

- 临时不想把本地改动继续推到远端
- 正在清理目录或做大规模重构

## 4.5 结束项目同步

优先尝试：

```powershell
mutagen project terminate
```

如果你的本地 Mutagen 版本不支持 `project` 子命令，则直接终止会话：

```powershell
mutagen sync terminate yixiaoguan-v2
```

---

## 5. Fallback：不用项目配置文件时的直连命令

如果本地 Mutagen 版本对 `mutagen project start` 支持不完整，可以直接使用：

```powershell
mutagen sync create --name=yixiaoguan-v2 . easten@192.168.100.165:/home/easten/dev/yixiaoguan-v2
```

然后用以下命令检查：

```powershell
mutagen sync list
```

如果需要终止：

```powershell
mutagen sync terminate yixiaoguan-v2
```

> 这种方式能用，但不如项目配置文件方式稳定，因为忽略规则和默认行为不一定完全按 `mutagen.yml` 组织。

---

## 6. 远端运行与验证命令

## 6.1 登录 165 服务器

```bash
ssh easten@192.168.100.165
```

## 6.2 进入项目目录

```bash
cd /home/easten/dev/yixiaoguan-v2
```

## 6.3 检查同步是否到位

```bash
git status --short
ls -la
```

## 6.4 进入 gateway 目录

```bash
cd /home/easten/dev/yixiaoguan-v2/services/gateway
```

## 6.5 启动 gateway（手动模式）

```bash
source venv/bin/activate
PYTHONPATH=. python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

如果要后台跑：

```bash
source venv/bin/activate
PYTHONPATH=. nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log 2>&1 &
```

## 6.6 查看健康状态

```bash
curl -s http://localhost:8100/health
```

## 6.7 查看日志

```bash
tail -f /tmp/gw.log
```

---

## 7. TEB 推荐工作流

## 7.1 角色分工

- **T0 / Architect**
  - 澄清需求
  - 判断边界
  - 输出 spec 或 bug 根因

- **T1 / Coordinator**
  - 把 spec 拆成 `.tasks/` 任务文件
  - 排序优先级
  - 组织回归测试与验收

- **T3 / Scout**
  - 只读侦察
  - 查代码 / 查日志 / 查接口现状
  - 输出结构化事实摘要

- **T3 / Executor**
  - 写代码
  - 跑本地或远端自检
  - 输出执行报告

- **T2 / Reviewer**
  - 独立验证
  - Scope 审计
  - 回归检查

## 7.2 这套项目里最推荐的用法

### 阶段 A：先盘清楚，不急着改

1. 用 **T0** 明确需求和边界
2. 用 **T3 Scout** 做只读探查
3. 把结论沉淀到：
   - `docs/requirements/`
   - `docs/design/`
   - 或 `.tasks/`

### 阶段 B：开始执行前，先打开同步

在本地项目根执行：

```powershell
mutagen project start
```

然后确认：

```powershell
mutagen sync list
```

### 阶段 C：T1 拆任务，T3 开干

推荐约定：

- 每个相对独立的改动拆成一个 `.tasks/` 文件
- 不把“探查”、“实现”、“验证”混在一个任务里
- 涉及远端依赖时，优先让 **Scout** 先摸清现状

### 阶段 D：本地改，远端跑

推荐节奏：

1. 本地 IDE 修改代码
2. Mutagen 自动同步到 165
3. 远端启动或重启目标服务
4. 远端看日志 / 跑接口 / 做 smoke test
5. 记录结果回到 `.tasks/` 或 `docs/`

### 阶段 E：验证和归档

1. **T2 Reviewer** 独立检查结果
2. 补回归测试结论
3. 将最终状态记录到：
   - `.tasks/` 执行报告
   - `docs/` 设计文档
   - 或单独测试报告

---

## 8. 针对医小管 v2 的具体协作建议

## 8.1 哪些内容适合本地改

- FastAPI 路由
- schema / service 层逻辑
- 文档与脚本
- 前端页面和接口层

## 8.2 哪些内容适合远端验证

- `gateway` 联调
- `/health` 与依赖检查
- Dify 联通性
- PostgreSQL / Redis 真实运行态
- WebSocket / SSE
- smoke test

## 8.3 哪些文件不要通过 Mutagen 覆盖

当前已在配置里排除：

- `services/gateway/.env`
- `deploy/.env`
- 远端虚拟环境目录

建议继续保持这个原则：

- **本地写代码，远端保留运行态配置**
- 不要把本地临时 `.env` 覆盖到服务器

---

## 9. 常见问题

## 9.1 `mutagen project start` 报错怎么办

优先检查：

- 本地是否已安装 Mutagen
- 本地是否能 `ssh easten@192.168.100.165`
- 当前目录是否是项目根目录
- 项目根是否存在 `mutagen.yml`

如果仍不行，退回到：

```powershell
mutagen sync create --name=yixiaoguan-v2 . easten@192.168.100.165:/home/easten/dev/yixiaoguan-v2
```

## 9.2 远端代码没更新怎么办

先执行：

```powershell
mutagen sync flush yixiaoguan-v2
```

然后到远端检查：

```bash
cd /home/easten/dev/yixiaoguan-v2
git status --short
```

## 9.3 远端服务还是旧逻辑怎么办

同步完成不等于进程自动重启。

通常还需要：

- 重新启动 `uvicorn`
- 或重启对应容器 / 进程

---

## 10. 当前建议

推荐你以后默认按下面节奏工作：

1. **T0/T1 先产出任务和边界**
2. **本地执行 `mutagen project start`**
3. **本地 IDE 改代码**
4. **165 远端跑服务与验证**
5. **T2 做独立验证**
6. **把结果写回 `.tasks/` 或 `docs/`**

这套方式最适合当前项目，因为它兼顾了：

- 本地编辑体验
- 远端真实环境验证
- Dify / PG / Redis 的联调需要
- TEB 的任务驱动协作方式
