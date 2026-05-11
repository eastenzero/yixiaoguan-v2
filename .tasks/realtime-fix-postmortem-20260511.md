# 实时推送修复 · 复盘日志

**日期**: 2026-05-11
**分支**: `fix/realtime-user-channel-push`
**提交**: `429b6c6` + `07d98e6`（已 push 到 gitea + github）
**部署**: 192.168.100.165 dev 服务器（内测期间不动 prod TX）
**验证**: Playwright e2e `test-realtime-v6.mjs` — T1 + T2 + T3 全部 PASS，user# + conv: 双频道推送实证

---

## 1. 问题陈述

### 用户报告
> "学生端聊天页面收不到老师的实时回复，必须刷新页面才能看到新消息。"

### 表面症状
| 场景 | 之前的表现 |
|---|---|
| 学生在 `chat/index.vue` 详情页 | 老师发消息后 UI **不更新** |
| 学生在 `chat/history.vue` 列表 | 列表 `updated_at` **不刷新** |
| 学生在 `home/index.vue` 首页 | 不知道老师已经回复 |
| 教师端 `questions/index.vue` 列表 | 学生 escalate 后老师**看不到新工单**（除非刷新）|

### 演进史
- v1（基线）: 单进程 in-memory dict WebSocket，"一步一卡"
- v2（centrifugo 集成）: 引入 Centrifugo v6 容器作为 pub/sub bus，gateway 通过 HTTP API 推送
- 集成后曾经 "看似工作过"，但实际只是**legacy ws conv room 路径**在跑，Centrifugo 路径**从来没真正生效过**

---

## 2. 排查过程（时间线）

### 第一层猜测（错的）
最初认为是**前端订阅频道不全**：学生端只订阅了 `conv:{id}`，老师推到 `conv:{id}` 时学生不在 chat 详情页就漏。

→ 改方案：让后端推 `conv:{id}` + `user#{student_id}` + `user#{teacher_id}`，前端 store 全局监听 `user#` 频道。

### 第二层猜测（部分对）
写 helper `notify_conversation_parties` 后跑 e2e，T1 看似 PASS，但 WS frame 抓到的 publication **不带 `channel` 字段**。

```json
{"type":"new_message","data":{...}}   ← legacy ws raw frame
```

应该长这样：
```json
{"push":{"channel":"user#18","pub":{"data":{...}}}}   ← Centrifugo frame
```

说明：**Centrifugo 完全没在工作**，前端能收到只是因为 chat 页 join_room 走 legacy ws conv room 兜底。

### 第三层（真 root cause）
直接 curl 165 上的 Centrifugo HTTP API 测试：

```bash
# gateway 代码用的端点（v3 旧风格）
curl -X POST http://127.0.0.1:8000/api/publish \
  -H "X-API-Key: ..." -d '{"channel":"user#18","data":{...}}'
→ 400 Bad Request

# Centrifugo v6 实际接受的端点
curl -X POST http://127.0.0.1:8000/api \
  -H "X-API-Key: ..." \
  -d '{"method":"publish","params":{"channel":"user#18","data":{...}}}'
→ {"result":{}}
```

**Centrifugo v6 `centrifugo/centrifugo:v6` 容器移除了 per-method REST 端点 `/api/publish` 和 `/api/broadcast`，统一为 `POST /api` + JSON-RPC body。**

`services/gateway/app/services/centrifugo_client.py` 的 `publish()` / `broadcast()` 一直在打废弃端点 → 400 Bad Request → except 兜住返 `False` → **静默失败，无人知晓**。

---

## 3. 多层 root cause 总结

| 层 | 问题 | 影响 |
|---|---|---|
| **L0（最深）** | Centrifugo client 用 v3 旧端点，v6 已废弃 | **整个 Centrifugo 推送链路从集成以来从未真正工作过** |
| L1 | 后端只推 `conv:{id}`，没推 `user#` 频道 | 学生不在 chat 详情页时收不到（即使 L0 修了也漏）|
| L2 | 学生端 store 没全局监听，只在 chat 页订阅 | 离开 chat 页后即使 push 到达也没人处理 |
| L3 | history / home 等页面没事件总线订阅 | 收到 push 也不会刷新这些页面的 UI |
| L4 | 教师端 questions / dashboard 也只订阅 legacy ws | 教师端看不到学生 escalate（同样的 root cause）|

**修复必须从最深的 L0 开始，否则上面所有补丁都是在错误的基础上叠加。**

---

## 4. 修复内容

### 4.1 Backend `429b6c6` — 频道路由 + 5 endpoint 重构

**新增** `services/gateway/app/services/conversation_service.py`:
```python
async def notify_conversation_parties(conv, event_type, data, *, actor_id=None):
    """
    永远推 conv:{conv.id}（兼容详情页订阅者）
    推 user#{student_id} 当 student 不是 actor
    推 user#{teacher_id} 当 teacher 已接单且不是 actor
    legacy ws 永远只推 conv room（保持向后兼容）
    """
```

**改 5 个 endpoint** 改用 helper：
- `app/routers/actions.py` 的 escalate / accept / resolve / close
- `app/routers/conversations.py` 的 send_message + reactivate

**新增 5 个单测** `services/gateway/tests/test_notify_conversation_parties.py`，覆盖：
- 学生发消息：只推 conv（不重复推自己）
- 老师 escalate：推 conv + user#{student}
- 老师 accept：推 conv + user#{student}
- 老师发消息：推 conv + user#{student}
- close：推 conv + 双方 user#

### 4.2 Backend `07d98e6` — Centrifugo v6 API 修复（真 root cause）

`services/gateway/app/services/centrifugo_client.py`:

```python
# 之前（v3 风格，v6 下 400 Bad Request）
resp = await client.post(
    f"{self.api_url}/api/publish",
    json={"channel": channel, "data": data},
    headers={"X-API-Key": self.api_key, ...},
)

# 修复（v6 JSON-RPC 风格）
resp = await client.post(
    f"{self.api_url}/api",
    json={"method": "publish", "params": {"channel": channel, "data": data}},
    headers={"X-API-Key": self.api_key, ...},
)
# 加 body-level error 检查（v6 可能 200 OK with error in body）
body = resp.json() if resp.content else {}
if "error" in body:
    logger.error("Centrifugo publish error body: %s", body["error"])
    return False
```

`broadcast()` 同样从 `/api/broadcast` 改为 `/api` + `{"method":"broadcast","params":{...}}`。

### 4.3 Frontend — 学生端 store 全局监听

`apps/student-app/src/stores/user.ts`:
```ts
function attachGlobalRealtimeListeners(token: string) {
  // 监听 wsManager + centrifugeManager 两条通道
  // 用 payload 指纹（type + msg.id 或 type + conv.id + status）去重
  // fanout 到 uni event bus: uni.$emit('rt:new_message' | 'rt:status_changed', payload)
}
```

→ 任意页面通过 `uni.$on('rt:new_message', handler)` 即可订阅，不再耦合具体 ws 实例。

### 4.4 Frontend — 各页面订阅事件总线

| 文件 | 改动 |
|---|---|
| `apps/student-app/src/pages/chat/index.vue` | 改成 `uni.$on('rt:new_message')`（替代直接 ws 订阅，避免重复） |
| `apps/student-app/src/pages/chat/history.vue` | 加 `uni.$on('rt:new_message')` + `uni.$on('rt:status_changed')` 触发 `loadData(true)` |
| `apps/teacher-app/src/pages/questions/index.vue` | 加 `centrifugeManager` 订阅（兼容 user# 频道）|
| `apps/teacher-app/src/pages/dashboard/index.vue` | 同上 |

---

## 5. 验证证据

### 5.1 单元测试

```
$ python -m pytest tests/ -q
====== 66 passed in 1.01s ======
```

新增 5 个 `notify_conversation_parties` 单测全部 PASS，原有测试无回归。

### 5.2 e2e Playwright 测试

`test-realtime-v6.mjs` 跑在 dev 环境（student :3001 + teacher :5301，proxy → 165:8100，Centrifugo 走 SSH tunnel `localhost:18000` → 165:8000）：

```
[ws-evt] ← {"push":{"channel":"user#18","pub":{"data":{"type":"new_message",...}}}}
[ws-evt] ← {"push":{"channel":"conv:70","pub":{"data":{"type":"new_message",...}}}}

[verify] user# channel hits=1, conv: hits=1
[result] T1 (chat 实时收 teacher msg): PASS
[result] T2 (history 自动刷新 = uni.$on 触发 loadData): PASS
[result] T3 (home 不报错 during push): PASS, errs=0
[summary] T1=true T2=true T3=true
```

**双频道（user#18 + conv:70）publication frame 实拍记录**，证明 Centrifugo 路径首次真正端到端跑通。

### 5.3 直接 curl 验证 Centrifugo

```bash
# 在 165 上
curl -X POST http://127.0.0.1:8000/api \
  -H "Authorization: apikey b5ad74fa94c7b7ef87382e89b3ce2009" \
  -d '{"method":"broadcast","params":{"channels":["conv:65","user#18"],"data":{...}}}'

→ {"result":{"responses":[{"result":{"offset":7,"epoch":"QTTM"}},{"result":{}}]}}
```

---

## 6. 部署状态

### 165 dev 服务器（已部署）
- ✅ `/home/easten/dev/yixiaoguan-v2` working tree 与 `gitea/fix/realtime-user-channel-push` 一致
- ✅ `centrifugo_client.py` v6 fix 已生效
- ✅ `yixiaoguan-gateway.service` 已 `sudo systemctl restart`
- ✅ health: `{"status":"ok","postgres":"ok","redis":"ok","dify":"ok"}`
- ✅ Centrifugo `centrifugo/centrifugo:v6` 容器（127.0.0.1:8000）正常运行

### TX prod（**未部署 — 内测期不动**）
- 内测期间产线代码保持现状
- 等内测结束 + 数据采集完成后，merge `fix/realtime-user-channel-push` 进 master，再走部署流程
- 部署只需：`git pull` + `sudo systemctl restart yixiaoguan-gateway.service`，prod nginx 已配 `/centrifugo/` → `127.0.0.1:8000` 反代（看 `deploy/nginx-centrifugo.conf`）

---

## 7. 未提交的临时改动（演示用，**不要 commit 进 master**）

| 文件 | 临时改动 | 用途 |
|---|---|---|
| `apps/student-app/vite.config.ts` | `/api`、`/ws` proxy 指 `192.168.100.165:8100`；`/centrifugo` proxy 指 `127.0.0.1:18000` 并 `rewrite: path => path.replace(/^\/centrifugo/, '')` | 本地 dev 演示 |
| `apps/teacher-app/vite.config.ts` | 同上 | 本地 dev 演示 |
| SSH tunnel `ssh -N -L 18000:127.0.0.1:8000 easten@192.168.100.165` | 本地 18000 → 165 上 127.0.0.1:8000 | 因为 165 上 Centrifugo 只 bind loopback，dev 机直连不到 |

**演示完毕后清理**：
```bash
# 1. revert vite.config.ts
git checkout apps/student-app/vite.config.ts apps/teacher-app/vite.config.ts
# 2. kill SSH tunnel
# 在 PowerShell 找 PID 后 Stop-Process
netstat -ano | findstr LISTENING | findstr ":18000"
Stop-Process -Id <PID>
```

---

## 8. 关键经验教训

### 8.1 静默失败 + except 兜底是隐性高危
原 `centrifugo_client.py` 的 `except Exception: return False` 把 400 Bad Request 吃掉，没有 alert，没有指标，没有任何健康检查能发现 publish 全军覆没。

**改进建议**：
- publish/broadcast 失败时**升级日志级别**到 ERROR + 加 metric counter
- 加一个启动时自检：实际发一条到 `__healthcheck__` 频道，失败则启动告警

### 8.2 第三方组件升级要做 contract test
v6 容器是 docker pull 拉下来的，但客户端代码没跟进 API 变更。**改进建议**：
- 在 `tests/test_centrifugo_integration.py` 加一个真实 HTTP 调用的 contract test（用 testcontainers 起 v6 容器）
- 集成到 CI 里，v 版本变更必跑

### 8.3 e2e 验证要看 WS 协议层证据
之前误以为 T1 PASS 就是修复成功，但实际上 frame 里没有 `"channel":"user#"` 字段，全是 legacy ws raw frame。**修测试断言时要看协议层细节**，不能只看 UI。

### 8.4 多层 bug 要从最深层开始修
本次有 5 层互相叠加的问题（L0-L4），如果先改 L1-L4 不动 L0，所有上层修复都"看似工作"但实际仍是在 legacy ws 兜底。**找到真 root cause 之后再回过头看上面的修复，每一层都还是必要的**（user# 频道路由 + store 全局监听 + 各页面事件总线订阅都是独立价值），但**修复链路的有效性依赖 L0 修好**。

---

## 9. 后续追踪

- [ ] 内测结束、数据收集完成后，PR 合并 `fix/realtime-user-channel-push` → master
- [ ] prod TX 部署 + 学生手机验证
- [ ] 给 `centrifugo_client.py` 加 contract test（testcontainers + v6 镜像）
- [ ] 加启动自检 publish 到 `__healthcheck__` 频道
- [ ] 撤销 `vite.config.ts` 临时改动 + 关闭 SSH tunnel（演示完成后）

---

## 附录 A — 完整文件清单

```
services/gateway/app/services/centrifugo_client.py        # v6 JSON-RPC API（核心）
services/gateway/app/services/conversation_service.py     # notify_conversation_parties helper
services/gateway/app/routers/actions.py                   # 4 endpoint 改用 helper
services/gateway/app/routers/conversations.py             # send_message + reactivate
services/gateway/tests/test_notify_conversation_parties.py # 5 个新单测
apps/student-app/src/stores/user.ts                       # 全局 listener + uni 事件总线 fanout
apps/student-app/src/pages/chat/index.vue                 # 改用 uni.$on
apps/student-app/src/pages/chat/history.vue               # 加 uni.$on 自动刷新
apps/teacher-app/src/pages/questions/index.vue            # centrifugeManager 订阅
apps/teacher-app/src/pages/dashboard/index.vue            # centrifugeManager 订阅
```

## 附录 B — Playwright e2e 脚本

```
.tmp/demo-video/test-realtime-v6.mjs    # 主要 e2e（T1 + T2 + T3）
.tmp/demo-video/test-realtime-v4.mjs    # 教师端 escalate push 专项
.tmp/demo-video/test-realtime-v5.mjs    # 学生端接收专项（早期版本）
.tmp/demo-video/diag-student-centrifugo.mjs       # 学生端 Centrifugo 连接诊断
.tmp/demo-video/diag-prod-student-centrifugo.mjs  # prod 环境对照诊断
.tmp/demo-video/test-cfg-publish.json   # curl 直测 Centrifugo publish payload
.tmp/demo-video/test-cfg-broadcast.json # curl 直测 broadcast payload
.tmp/demo-video/out/realtime-v6/        # 最近一次 e2e 截图 + ws-frames.json + timeline.log
```
