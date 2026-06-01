# tx-new 上传差异审计清单（2026-05-14）

## 0. 当前结论

- **不建议直接整仓打包覆盖服务器**：本地包含演示视频、AE、录屏、BI/wall 实验、部署脚本、dev proxy 等大量非生产内容；服务器仓库自身也有未提交配置/BI 文件，需要保留。
- **可以先做低风险小包**：只上传新项目图标并重建学生端/教师端 H5。
- **后端建议分批上传**：analytics 时间修复、知识条目列表、会话学生姓名字段、实时推送修复都属于可上传候选，但应按批次验证，不要和视频/演示素材混在一起。
- **学生端免登录是当前服务器的有意配置**：tx-new `.env` 里 `pilot_mode_enabled=true`，前端自动调用 `/api/auth/pilot-anonymous`，不是异常。

## 1. 服务器基线

- **服务器**：`tx-new` / `82.156.129.75`
- **部署仓库**：`/home/easten/dev/yixiaoguan-v2`
- **服务器仓库分支/提交**：`master @ 6e5f434`
- **Gateway systemd**：`yixiaoguan-gateway.service`
- **Gateway 工作目录**：`/home/easten/dev/yixiaoguan-v2/services/gateway`
- **学生端静态目录**：`/var/www/yixiaoguan/student`
- **教师端静态目录**：`/var/www/yixiaoguan/teacher`
- **pilot 开关**：`pilot_mode_enabled=true`
- **服务器当前 favicon**：仍是旧版，SHA256 `b489baef...`

## 2. 本地图标改动（已完成，未部署）

### 已修改文件

- `medical_graduation_logo_clean_editable.svg`
  - 删除灰色整幅背景和中心背景光晕。
  - 描述从 pale grey background 改为 transparent background。
- `apps/student-app/src/static/favicon.svg`
  - 替换为透明背景、裁切为 `512x512 viewBox="520 160 640 640"` 的项目图标。
- `apps/teacher-app/src/static/favicon.svg`
  - 同学生端。
- `apps/student-app/src/pages/login/index.vue`
  - 登录页 Logo 从 Material Symbols `school` 改为 `/static/favicon.svg`。
- `apps/teacher-app/src/pages/login/index.vue`
  - 登录页 Logo 从 `IconGraduationCap` 改为 `/static/favicon.svg`。
  - 移除未使用的 `IconGraduationCap` import。

### 建议

- **建议上传**：是。
- **风险**：低。只影响浏览器 favicon 和登录页品牌图标。
- **注意**：需要重新 build H5，不能只传源码；`dist` 当前未更新。

## 3. 本地相对服务器已提交差异（服务器缺少）

本地当前分支：`fix/realtime-user-channel-push @ afd2f83`。
服务器 `6e5f434` 是本地 HEAD 的祖先，本地比服务器多 21 个提交。

### A. 实时推送修复

代表文件：

- `services/gateway/app/services/centrifugo_client.py`
- `services/gateway/app/routers/actions.py`
- `services/gateway/app/routers/conversations.py`
- `services/gateway/app/services/conversation_service.py`
- `services/gateway/tests/test_notify_conversation_parties.py`

内容：

- Centrifugo v6 JSON-RPC API 修复。
- `new_message` / `status_changed` 推送到会话频道和用户频道。
- 学生/教师页面不必停留在当前 conv 订阅页才能收到部分实时事件。

建议：

- **建议上传**：是，但作为独立后端批次。
- **风险**：中。涉及实时链路，应部署后做学生/教师双端冒烟。
- **注意**：服务器当前内测中，建议避开高峰，先备份并可回滚。

### B. 教师端 UI polish / avatar / FOUT 防御

代表文件：

- `apps/teacher-app/src/components/UserAvatar.vue`
- `apps/teacher-app/src/components/TopAppBar.vue`
- `apps/teacher-app/src/pages/dashboard/index.vue`
- `apps/teacher-app/src/pages/questions/index.vue`
- `apps/teacher-app/src/pages/questions/detail.vue`
- `apps/teacher-app/src/pages/admin/users.vue`
- `apps/teacher-app/src/pages/admin/import.vue`
- `apps/teacher-app/src/pages/profile/index.vue`
- `apps/teacher-app/src/utils/icons-ready.ts`
- `apps/teacher-app/index.html`
- `apps/teacher-app/src/main.ts`

内容：

- 教师端多页面视觉优化。
- 用户头像组件。
- Material Symbols 字体加载前隐藏，避免英文 ligature 闪屏。

建议：

- **建议上传**：看你是否接受新 UI。建议先本地或测试环境完整看一遍。
- **风险**：中。页面范围广，可能影响教师内测体验。

### C. 学生端 UI / chat 细节

代表文件：

- `apps/student-app/index.html`
- `apps/student-app/src/main.ts`
- `apps/student-app/src/pages/chat/index.vue`
- `apps/student-app/src/pages/chat/history.vue`
- `apps/student-app/src/stores/user.ts`
- `apps/student-app/src/utils/icons-ready.ts`

内容：

- 学生端 Material Symbols FOUT 防御。
- 聊天页滚动/底部 spacer 等体验修复。
- pilot 用户跳过实时连接，减少无意义 WS 报错噪音。

建议：

- **建议上传**：可以，但建议和学生端 H5 重建一起做。
- **风险**：中低。需重点验证免登录进入首页、AI 问答、历史记录。

### D. Vite dev proxy 改动

代表文件：

- `apps/student-app/vite.config.ts`
- `apps/teacher-app/vite.config.ts`

内容：

- dev server proxy 指向 `192.168.100.165:8100`。
- `/centrifugo` 指向本地 SSH tunnel `127.0.0.1:18000`。

建议：

- **不作为生产上传重点**。Vite `server.proxy` 不影响 H5 production build，但容易误导后续开发。
- **建议后续清理**：最终合并前改回更通用的开发配置，或用环境变量控制。

### E. 演示视频 / AE / Remotion / 文档

代表文件/目录：

- `video/01-tech-feasibility.md` 等 video 文档。
- `.tasks/ae-theme/*`
- `.tasks/demo-video-*`
- `.tasks/kimi-prompt-*`
- `.tasks/realtime-fix-postmortem-20260511.md`

建议：

- **不需要上传到服务器运行环境**。
- 可以提交到代码仓库留档，但不应参与生产部署包。

## 4. 本地未提交源码差异（当前工作区）

### A. analytics 时间修复

文件：

- `services/gateway/app/routers/analytics.py`

内容：

- `_period_range()` 返回 naive UTC datetime，避免 asyncpg 绑定 tz-aware datetime 到 `TIMESTAMP WITHOUT TIME ZONE` 导致 500。

建议：

- **建议上传**：是。
- **风险**：低。
- **验证**：`GET /api/analytics?period=7d`、`30d`、`all` 不再 500。

### B. 知识条目列表 API

文件：

- `services/gateway/app/routers/knowledge.py`
- `services/gateway/app/schemas/knowledge.py`
- `services/gateway/app/services/knowledge_service.py`
- `services/gateway/tests/test_knowledge_entries_list.py`（未跟踪）

内容：

- 新增 `GET /api/v1/knowledge/entries`。
- teacher 看自己提交的知识条目，admin 看全部。
- 支持 title 搜索、分页。

建议：

- **建议上传**：如果教师端知识库页面要显示真实条目，建议上传。
- **风险**：中低。不涉及数据库迁移，但要跑后端测试和真实账号冒烟。

### C. 会话学生/教师姓名字段

文件：

- `services/gateway/app/schemas/conversation.py`
- `services/gateway/app/services/conversation_service.py`
- `apps/teacher-app/src/pages/dashboard/index.vue`
- `apps/teacher-app/src/pages/questions/index.vue`
- `apps/teacher-app/src/pages/questions/detail.vue`

内容：

- `ConversationResponse` 增加 `student_name` / `teacher_name`。
- service 层批量查 users.name 附加到 conversation 实例。
- 教师端优先展示学生姓名，fallback 到 `学号 {id}`。

建议：

- **建议上传**：可以上传，解决教师端“学号 X”展示不友好。
- **风险**：中低。多一次批量 user 查询，需验证列表/详情性能和接口兼容。

### D. 视频文档修订

文件：

- `video/04-script-plan.md`
- `video/README.md`
- `video/05-progress-checkpoint.md`（未跟踪）
- `video/08-narration-v2.md`（未跟踪）

建议：

- **不上传到服务器运行环境**。
- 可提交仓库留档。

## 5. 本地未跟踪大类

### 应排除生产部署

- `.tmp/**`
- `.tasks/*ui-audit*/**` 截图
- `.tasks/ae-theme/**` AE 脚本/报告（除非做视频资产管理）
- `.tmp/demo-video/**` 录屏、webm、png、Remotion 临时工程
- `teacher-dashboard.png`

### 需单独决定

- `services/bi-evidence/`
- `services/bi-evidence-v1-legacy/`
- `services/wall-standalone/`
- `scripts/wall_export.py`
- `deploy/systemd/yxg-wall-export.*`
- `services/gateway/sql/*`

这些像 BI 展示墙/数据导出能力，不属于学生端/教师端主应用。若要上线，应单独作为一个小项目审核、部署、验收。

## 6. 服务器独有未提交内容（必须保护）

服务器仓库 `status --short`：

- `M deploy/centrifugo-config.json`
- `?? scripts/wall_export.py`
- `?? services/bi-evidence/`
- `?? services/gateway/sql/`

`deploy/centrifugo-config.json` 差异：

- 服务器增加了：
  - `http://82.156.129.75`
  - `http://82.156.129.75:81`

建议：

- **不要用本地文件直接覆盖服务器的 `deploy/centrifugo-config.json`**，否则可能丢掉 IP 访问白名单。
- 如果要规范化，应把这部分配置纳入正式提交，而不是留在服务器脏工作区。

## 7. 学生端免登录评估

当前机制：

- 后端：`POST /api/auth/pilot-anonymous`。
- 服务器开关：`pilot_mode_enabled=true`。
- 前端：`App.vue onLaunch -> userStore.init() -> tryPilotLogin()`。
- 请求层：遇到 401 会再次尝试 pilot login。
- pilot 用户：`staff_id = pilot:{device_id}`，角色是 `student`，没有真实 college/class。
- 本地后续改动：pilot 用户跳过实时连接，减少 WS 报错噪音。

判断：

- **内测阶段合理**：降低访问门槛，适合公开链接/二维码试用。
- **主要风险**：匿名用户会消耗 Dify/模型调用成本；真实学生登录路径被弱化；pilot 用户数据可能污染统计。
- **当前服务器已经有配套过滤**：admin 用户列表过滤 pilot 用户，埋点有 `is_pilot`，部分统计/数据可区分。

建议策略：

1. **短期继续保留当前机制**：不要现在改掉，避免影响内测入口。
2. **上线前切换策略**：将 `pilot_mode_enabled=false`，恢复学生账号登录。
3. **如果要兼顾真实登录和游客体验**：做独立游客入口更清晰，例如：
   - `https://yxg.xiaoguan.site/guest` 或 `https://guest.xiaoguan.site`
   - 游客入口自动 pilot login。
   - 主学生入口保留正式登录。

## 8. 推荐上传批次

### 批次 0：只换图标（最稳）

包含：

- `apps/student-app/src/static/favicon.svg`
- `apps/teacher-app/src/static/favicon.svg`
- `apps/student-app/src/pages/login/index.vue`
- `apps/teacher-app/src/pages/login/index.vue`
- 可选：`medical_graduation_logo_clean_editable.svg` 作为源素材留档。

操作：

- build 学生端 H5。
- build 教师端 H5。
- 上传到 `/var/www/yixiaoguan/student` 和 `/var/www/yixiaoguan/teacher`。
- 不重启 gateway。

### 批次 1：后端低风险修复

包含：

- `analytics.py` naive datetime 修复。
- `knowledge entries` API。
- `conversation student_name/teacher_name` 字段和 service 查询。

操作：

- 跑后端测试。
- 上传 gateway 代码。
- 重启 `yixiaoguan-gateway.service`。
- 验证 analytics / knowledge entries / conversations。

### 批次 2：前端体验更新

包含：

- 教师端 UI polish。
- 学生端 FOUT/聊天体验修复。
- 新图标若未在批次 0 上传，也一起包含。

操作：

- build 两端 H5。
- 替换 `/var/www/yixiaoguan/student`、`/var/www/yixiaoguan/teacher`。
- 验证学生免登录、AI 问答、教师登录、工单列表、工单详情、知识库。

### 批次 3：实时推送修复

包含：

- Centrifugo v6 publish/broadcast 修复。
- user channel 推送。
- 前端全局事件 fanout。

操作：

- 后端 + 两端前端一起部署。
- 做学生/教师双端实时聊天冒烟。
- 观察 Centrifugo 日志和 gateway 日志。

## 9. 当前不建议做的事

- 不建议直接把本地整个工作区 rsync 到服务器。
- 不建议把 `.tmp`、录屏产物、AE/Remotion 临时工程上传到服务器。
- 不建议覆盖服务器未提交的 Centrifugo 配置。
- 不建议现在关闭 `pilot_mode_enabled`，除非你决定内测入口改回登录。
