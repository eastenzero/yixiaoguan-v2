# 医小管 v2 — 三轨并行推进总规划

> 制定时间: 2026-05-04 03:45 UTC+8
> 状态: 待确认后执行

---

## 整体态势

经过 Cascade + DeepSeek 双线审计，教师端整体完成度 **65%**。
当前有三个独立工作流可以并行推进：

---

## 轨道 A：账号角色隔离（致命 Bug 修复）

**优先级**: 🔴 P0
**预估工时**: 0.5 天
**依赖**: 无

### 任务清单

1. **后端**: `auth.py` 登录接口增加 `expected_role` 参数
   - 学生端传 `expected_role="student"`
   - 教师端传 `expected_role=["teacher", "admin"]`
   - 不匹配返回 403 + 明确提示（如"教师账号请使用教师端登录"）
2. **前端-学生端**: `student-app/src/api/auth.ts` 登录时传 `expected_role: "student"`
3. **前端-教师端**: `teacher-app/src/api/auth.ts` 登录时传 `expected_role: "teacher"`
4. **前端双端**: `getMe()` 后二次校验角色，不匹配则清 token + 提示
5. **测试**: 验证 admin 无法登录学生端、学生无法登录教师端

---

## 轨道 B：引入 Centrifugo 替换手写 WebSocket

**优先级**: 🟡 P1
**预估工时**: 3-5 天
**依赖**: 无

### 任务清单

1. **部署 Centrifugo**
   - HK 服务器 Docker 部署 Centrifugo
   - 配置 JWT 认证（复用现有 JWT secret）
   - nginx 反代 `/centrifugo/connection/websocket`

2. **后端改造**
   - 新增 `services/centrifugo_client.py` — HTTP API 发布消息到 Centrifugo
   - 修改 `routers/conversations.py` — 发消息后调用 Centrifugo publish（替代 ws_manager broadcast）
   - 修改 `services/state_machine.py` — 状态变更后 publish 到 Centrifugo
   - `routers/ws.py` + `services/ws_manager.py` 标记废弃，保留兼容期

3. **前端改造**
   - 引入 `centrifuge-js` 包
   - 重写 `utils/websocket.ts` → `utils/centrifuge.ts`
   - 频道命名: `conv:{conv_id}` 与现有 room 模型对应
   - 保留断线恢复、心跳由 Centrifugo SDK 自动管理

4. **验证**
   - 端到端测试: 学生发消息 → 教师实时收到
   - 断线恢复测试: 断网 → 恢复 → 消息自动补发
   - 压力测试: 多会话并发

---

## 轨道 C：知识库数据融合与补全

**优先级**: 🟡 P1
**预估工时**: 2-3 天
**依赖**: DeepSeek 审计报告

### 数据现状

| 版本 | 来源 | 条目数 | Dify Dataset | 检索命中率 |
|------|------|--------|-------------|-----------|
| V1 旧 KB | yixiaoguan/knowledge-base/entries/ | 874 | 旧 `ec072e85-...` (内网 165) | 未测试 |
| V2 新 KB (W2+W3) | kb-pipeline/04-output/merged/ | 800 | `global-kb-v2` `4db0c819-...` (内网 165) | 92.6% |
| V2 最终版 (W1+W2+W3) | kb-pipeline/04-output/final-merged/ | 835 | Dify 总量 994 条 | **97.3%** |
| **线上 HK** | — | ? | `c2363fef-...` (DIFY_GLOBAL_DATASET_ID) | ? |

### 关键问题

1. **线上 HK 的 Dataset (`c2363fef-...`) 与 kb-pipeline 产出的 Dataset (`4db0c819-...`) ID 不同** — 需要确认线上用的是哪套数据
2. **V1 旧 KB (874 条) 是否有 V2 未覆盖的内容** — 等 DeepSeek 审计报告
3. **kb-pipeline 最终产出 994 条（含 W1）是否已全部入库线上** — 需要核实

### 任务清单（待 DeepSeek 审计后细化）

1. **核实线上 Dify Dataset 内容** — SSH 到 HK 服务器查看
2. **V1 独有内容评估** — 基于 DeepSeek 审计结果决定是否融合
3. **如需融合**: 按 KB-SPEC v2.0 规范转换 V1 独有条目 → 去重 → 入库
4. **后端知识管理端点补全** (DeepSeek 发现的 P0):
   - `GET /api/v1/knowledge/entries` — 条目列表
   - `GET /api/v1/knowledge/entries/{id}` — 条目详情
   - `POST /api/v1/knowledge/entries/{id}/offline` — 下线条目
5. **UnansweredQuestion 写入机制** — 学生提问拒答时写入 unanswered_questions 表

---

## 并行执行策略

```
时间轴 ──────────────────────────────────────→

轨道 A (角色隔离):  ████ 0.5天 → 完成 ✓
                          可由 CLI 工人(codex/kimi)执行

轨道 B (Centrifugo):  ██████████████ 3-5天
                          Cascade 设计 → DeepSeek/Codex 编码

轨道 C (知识库):       ██ DeepSeek审计 → ████████ 融合+补全 2-3天
                          DeepSeek 审计(已派发) → Cascade 决策 → CLI 执行
```

### 建议分工

| 任务 | 执行者 | 模型建议 |
|------|--------|----------|
| 轨道 A 编码 | Codex 或 Kimi | codex: `codex exec` |
| 轨道 B 设计 | Cascade | — |
| 轨道 B 编码 | OpenCode | `deepseek/deepseek-v4-pro` |
| 轨道 C 审计 | OpenCode | `deepseek/deepseek-v4-pro` (**已派发**) |
| 轨道 C 融合 | OpenCode + Cascade | — |

---

## 附录：DeepSeek 已派发任务

| 任务 | Prompt 文件 | Log 文件 | 状态 |
|------|-------------|----------|------|
| 教师端功能审计 | `.tasks/opencode-teacher-recon-prompt.txt` | `.tasks/opencode-teacher-recon.log` | ✅ 完成 |
| 知识库数据审计 | `.tasks/opencode-kb-data-audit-prompt.txt` | `.tasks/opencode-kb-data-audit.log` | 🔄 执行中 |
