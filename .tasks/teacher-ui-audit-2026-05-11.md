# 教师端 UI 审计 — 2026-05-11

> 范围：`apps/teacher-app` 全部 11 个路由的真实运行截图 + 代码审计。
> 标杆：`apps/student-app/src/styles/tokens.scss`（MD3 tonal palette、8pt grid、大半径、no-line/no-shadow）。
> 后端：165 dev (`http://192.168.100.165:8100`)，`fix/realtime-user-channel-push` 分支。

## 截图清单

由 `.tmp/demo-video/teacher-audit-capture.mjs` 跑出，输出目录 `before/` 和 `after/`。
393×852 视口（iPhone 14 Pro），`deviceScaleFactor=2`，`fullPage: true`。

| # | 路由 | 文件 | 高度 | 备注 |
|---|------|------|------|------|
| 01 | `/pages/login/index` | `before/01-login.png` | 1704 | 未登录态（独立 ctx） |
| 02 | `/pages/dashboard/index` | `before/02-dashboard.png` | 1804 | 工作台（teacher） |
| 03 | `/pages/questions/index` | `before/03-questions-list.png` | 6324 | 工单列表（全部） |
| 04 | `/pages/questions/index` | `before/04-questions-list-pending.png` | 1804 | 工单列表（待处理 tab） |
| 05 | `/pages/questions/detail?id=N` | `before/05-questions-detail.png` | 1704 | 工单详情（teacher_serving） |
| 06 | `/pages/knowledge/index` | `before/06-knowledge-list.png` | 1804 | 知识库列表 |
| 07 | `/pages/knowledge/detail?id=1` | `before/07-knowledge-detail.png` | 1704 | 知识详情 |
| 08 | `/pages/profile/index` | `before/08-profile.png` | 2278 | 个人中心 |
| 09 | `/pages/analytics/index` | `before/09-analytics.png` | 3968 | 数据看板 |
| 10 | `/pages/admin/users` | `before/10-admin-users.png` | 1704 | 用户管理（teacher token，403 后空态） |
| 11 | `/pages/admin/import` | `before/11-admin-import.png` | 1704 | 批量导入 |

⚠️ 跑前提：student dev `:3001` + teacher dev `:5301` 已起，SSH tunnel `localhost:18000 → 165:8000` 已开。
重新跑：`node .tmp/demo-video/teacher-audit-capture.mjs before|after`

## 现状评分（基于源码 + 视觉对照）

| 文件 | 评分 | 主要问题 | 优先级 |
|------|------|---------|--------|
| `pages/admin/import.vue` | **D 级** | `<style scoped>` 不带 `lang="scss"`，无法用 token；通篇硬编码 (`#702ae1` `#9333ea` `#fff` `#e2e8f0` `#3b82f6` `#16a34a` `#dc2626` …)；色号是 v1/Tailwind 大杂烩，非 MD3 | P0 |
| `pages/admin/users.vue` | **D 级** | 同上：`<style scoped lang="scss">` 但内部仍大量硬编码（`#702ae1` v1 主色、`#191c1e` `#94a3b8` `#64748b` 等 Tailwind 灰阶、`#ede9fe` `#dcfce7` `#fef3c7` `#fee2e2` 等 Tailwind 容器色）；与全站 MD3 tonal 系完全脱节 | P0 |
| `components/TopAppBar.vue` | **B 级** | 主体已对齐 token，但图标颜色硬编码 `#2f2e32`、加号按钮硬编码 `#702ae1`（v1 主色）。导致点开 add 按钮的颜色与全站 `#5b21b6` 不一致 | P0 |
| `pages/profile/index.vue` | **B 级** | 三张卡片用了硬编码假数据 `156 / 42 / 28`；接入用户 store 后改成真实计数（或退化为占位文案）；`high 级讲师` 也是写死 | P1 |
| `pages/dashboard/index.vue` | **A- 级** | 整体对齐 token，但工单卡里 `.status-dot.status-0/1/2/3` 选择器与模板绑定的字符串状态名（`pending_teacher` 等）不匹配，状态点永远透明；学生用 `学生 #{{student_id}}` 而不是用真名 | P1 |
| `pages/questions/index.vue` | **A- 级** | 同上：`学生 #{{student_id}}` 缺真名；`AI 匹配度 80%` 是写死的兜底值 (`item.confidence` 后端从未返回) | P1 |
| `pages/questions/detail.vue` | **A 级** | 较完整；学生信息卡仍用 `学生 #{{student_id}}`；`接单/已解决/已关闭/teacher_serving` 状态完整。可读性 OK | P2 |
| `pages/knowledge/index.vue` | **A 级** | 完整对齐 token；`reject-reason-inline` 用了硬编码 `rgba(239, 68, 68, 0.08)` 应改 `rgba($error, 0.08)` | P2 |
| `pages/knowledge/detail.vue` | **A 级** | `reject-banner` 用了硬编码 `rgba(239, 68, 68, 0.08)`；其他对齐 | P2 |
| `pages/analytics/index.vue` | **A 级** | 整体好；ring 渐变 `conic-gradient(#5b21b6 …, #ede9fe …)` 写死，但这是图表色，可接受 | P3 |
| `pages/login/index.vue` | **A 级** | 紫色光晕 + 玻璃卡片，已对齐 MD3；无明显问题 | — |
| `components/BottomNavBar.vue` | **A 级** | 共享标杆，无问题 | — |
| `components/FeatureNoticeSheet.vue` | **A 级** | 共享，无问题 | — |

## 设计约束（from `student-app/src/styles/tokens.scss`）

> 这些规则在 `tokens.scss` 顶部已写明，作为本次 polish 的硬约束。

- **No-Line**：禁 1px solid 边框；层次靠 surface-container-lowest / -low / -high tonal tint 差异。
- **No-Shadow-As-Default**：阴影只用 `$shadow-fab` `$shadow-nav` `$elevation-1/2/3`，且必须是紫色折射 `rgba(91, 33, 182, ...)`，禁中性灰 `rgba(0,0,0,...)`。
- **MD3 Radius**：`$radius-md=1rem` 默认；`$radius-lg=2rem` 主力；pill = `$radius-full=9999px`。
- **8pt grid**：`$space-1` ... `$space-12`；硬编码 `padding: 0.625rem` 这种碎片值要换成 `$space-3` (12px) 等就近档。
- **Type scale**：`$display-md=2.75rem/800` `$title-lg=22px/700` `$body-md=14px/400` `$label-md=12px/500`。
- **图标 wght 300**：`.material-symbols-outlined` 全局规则已设。

---

## Sprint 计划

### Sprint A（P0 — 最粗糙）

1. **`pages/admin/users.vue`** — `<style scoped lang="scss">` 全量重写为 token 引用；保留布局结构和数据逻辑。
2. **`pages/admin/import.vue`** — `<style scoped lang="scss">` 全量重写；同上。
3. **`components/TopAppBar.vue`** — 把 IconArrowLeft/IconSearch/IconSettings/IconEdit 的 `#2f2e32` 改 `var(--md-on-surface)` 或 SCSS 变量；IconPlus 的 `#702ae1` 改 `#5b21b6`（或 token 桥接 var）。

### Sprint B（P1 — 数据 / 可信度）

4. **`pages/profile/index.vue`** — 卸掉硬编码假统计 `156/42/28`，挂接用户 store 派生值；当前没有真后端 API 时退化为更克制的展示。
5. **`pages/dashboard/index.vue`** — 修 `.status-dot/.status-text` 选择器，对齐到真实 status 字符串；显示学生姓名而非 `student_id`。
6. **`pages/questions/index.vue`** — 显示真实学生姓名；删除 `AI 匹配度 80%` 兜底假值（后端无字段时直接隐藏该 section）。

### Sprint C（P2/P3 — 优雅）

7. **`pages/knowledge/index.vue` / `detail.vue`** — `rgba(239,68,68,...)` → `rgba($error, ...)`。
8. **`pages/analytics/index.vue`** — ring `conic-gradient` 用 SCSS 变量。
9. **`questions/detail.vue`** — 学生姓名替换。

---

每个 Sprint 完成后跑：

```bash
# 1. 重新截图
node .tmp/demo-video/teacher-audit-capture.mjs after

# 2. 实时推送回归
node .tmp/demo-video/test-realtime-v7.mjs   # T1+T2+T3 必须 PASS
```

> 实时推送修复（`fix/realtime-user-channel-push` 分支）若被波及任何一行后端代码即拦截，禁止合并。

---

## 变更日志（追加）

### 2026-05-11 Sprint A + B 完成

| 文件 | 变更 | before | after |
|------|------|--------|-------|
| `components/TopAppBar.vue` | 去掉硬编码 `#2f2e32` `#702ae1`；图标 currentColor + `color: $on-surface / $primary`；玻璃 bg 用 `rgba($surface-container-lowest, 0.8)` | — | — |
| `pages/admin/users.vue` | `<style scoped lang="scss">` 内全量 token 化：tailwind 灰 → on-surface tier、白底 → surface-container-lowest + `$elevation-1`、1px solid 边框 → no-line tonal、role badges 用 MD3 secondary/success/warning container | `before/10-admin-users.png` (42 KB) | `after/10-admin-users.png` (46 KB) |
| `pages/admin/import.vue` | `<style scoped>` → `lang="scss"` + 全量 token 化：blue tips → `$secondary-container`、白底输入 → `$surface-container-low`、submit pill + `$gradient-cta`、`#bbf7d0` border → no-line | `before/11-admin-import.png` (110 KB) | `after/11-admin-import.png` (119 KB) |
| `pages/dashboard/index.vue` | 修 `.status-dot/.status-text` 选择器：`.status-0/1/2/3` → `.status-pending_teacher / teacher_serving / ai_serving / resolved / closed`（对齐 `ConversationStatus` enum 字符串）；卡片以 `question.title` 为 headline，`学号 {id}` demote 到 chip；移除标题二次渲染 | `before/02-dashboard.png` | `after/02-dashboard.png` |
| `pages/profile/index.vue` | 卸掉硬编码假统计 `156/42/28`；接入 `listConversations(status=resolved)` / `listConversations()` / `getKnowledgeEntries()` 三个 read-only API 派生 `累计处理 / 参与工单 / 知识条目`；`onMounted + onShow` 触发刷新 | `before/08-profile.png` 显示 156/42/28 | `after/08-profile.png` 显示 0/17/0（真值） |
| `pages/questions/index.vue` | 把假的 `AI 匹配度 80%` 条件渲染：`v-if="typeof item.confidence === 'number' && item.confidence > 0"`；`学生 #N · title · 时间` → `学号 N · 时间`，标题不再二次重复 | `before/03-questions-list.png` (515 KB, 重复气泡撑高) | `after/03-questions-list.png` (372 KB, -28%) |
| `pages/questions/detail.vue` | `学生 #` → `学号` | — | — |
| `pages/knowledge/index.vue` | `rgba(239, 68, 68, 0.08)` → `rgba($error, 0.08)`；px → token (`$space-3` `$radius-md`) | — | — |
| `pages/knowledge/detail.vue` | 同上 | — | — |
| `pages.json` | `tabBar.selectedColor: #702ae1` (v1) → `#5b21b6` (v2 primary)；CustomTabBar 已用 v2 主色，但 fallback 路径需对齐 | — | — |

### 回归测试

跑了 `node .tmp/demo-video/test-realtime-v7.mjs`（2026-05-11 20:55 UTC+8）：

```
[result] T1 (teacher UI 发 → student UI 实时收): PASS
[result] T2 (student UI 发 → teacher UI 实时收): PASS
[result] T3 (再一轮 teacher → student): PASS
[info] student frames=7, teacher frames=3
[verify] stu user# hits=2, tea user# hits=0
[summary] T1=true T2=true T3=true
```

UI 重构未波及实时推送修复 (`fix/realtime-user-channel-push` 分支)；后端代码未触碰。

### 仍未处理（P2 及以下，留给后续）

- `pages/analytics/index.vue`：metric-card chart palette 仍有硬编码（`#5b21b6` `#8b5cf6` `#2563eb` `#7c3aed` 等）。这些是图表色，不影响 UI 一致性，但理想情况应该走 SCSS 变量。
- 学生姓名展示：当前所有页面仍是 `学号 {id}` 而不是真名，因为 `/api/conversations` 响应 schema 不含 `student_name`。**修这条需要后端加 join**，不在 `fix/realtime-user-channel-push` 分支允许改动范围内。等内测结束 merge master 后单开一个小 sprint 处理。
- `pages/profile/index.vue` 的 `高级讲师 / 学院 17` 仍是占位文案，`学院 {id}` 应该展示真实学院名（同样要后端 schema 补字段或在前端调 `/api/colleges/{id}`）。

---

## 2026-05-11 Phase 3 · demo 数据灌库（seed-demo-data.py）

### 新增工具

`services/gateway/scripts/seed-demo-data.py` — Faker zh_CN 驱动的 demo 数据 seed 脚本。

#### 保护栏
- `APP_ENV=prod` / `APP_ENV=production` → 立刻退出
- gateway host 命中 prod 黑名单（`xiaoguan.site`、`130814.xyz`、`64.90.13.65`、`60.205.205.99`、`82.156.129.75`）→ 立刻退出
- gateway host 不在 DEV 白名单（`192.168.*`、`127.0.0.1`、`localhost`、`10.*`）→ 立刻退出
- 所有写入数据以 `[demo]` 前缀作为可追溯 marker，`cleanup-sql` 严格匹配 marker 回滚
- 无 `--confirm` 时所有写入模式默认 dry-run

#### 模式
| mode | 路径 | 描述 |
|------|------|------|
| `conv` | HTTP API | 创建 `conversation` + `messages`，走真实状态机（escalate/accept/resolve），默认分布 20% ai_serving / 15% pending_teacher / 25% teacher_serving / 40% resolved |
| `kb-sql` | stdout SQL | 生成 `unanswered_questions` + `kb_suggestions`（含 pending global + approved class/college 混合）的 INSERT 语句 |
| `cleanup-sql` | stdout SQL | 生成 `[demo]%` 精准匹配的 DELETE 语句（messages → convs → kb → UQ 顺序，避开 FK） |
| `list-sql` | stdout SQL | 只读 COUNT + 抽样 |

#### 一键回滚
```bash
python -c "import subprocess,sys; out = subprocess.check_output([sys.executable, 'services/gateway/scripts/seed-demo-data.py', 'cleanup-sql']); open('.tmp/cleanup.sql', 'wb').write(out)"
scp .tmp\cleanup.sql easten@192.168.100.165:/tmp/cleanup.sql
ssh easten@192.168.100.165 "docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2 < /tmp/cleanup.sql"
```

### Seed 结果（165 dev）

| 实体 | 前 | seed 后 | 新增 |
|-----|----|--------|------|
| conversations | 74 | 133 | **+59**（其中 resolved 23, teacher_serving 15, pending_teacher 9, ai_serving 12） |
| messages | 377 | 638 | +261 |
| kb_suggestions | 5 | 30 | **+25**（pending 7 + approved 18） |
| unanswered_questions | 10 | 18 | +8 |

### Seed 后视觉确认（`.tasks/teacher-ui-audit-2026-05-11/after-seed/` 和 `after-seed-admin/`）

**teacher (anjing) 视角**：
- `02-dashboard.png`：今日提问 65、待处理 5；`待处理提问` 列表有 `[demo] 党课报名什么时候开始 · 学号 19`、`[demo] 选课系统什么时候开放 · 学号 32` 等 4+ 条实数据，每条卡片正确显示红色 `待处理` dot + text（Sprint B 修复生效）
- `03-questions-list.png`（全部 tab）+ `04-questions-list-pending.png`（待处理 tab, badge 5）：列表饱满，滚动区展示 8+ 张卡片，无多余的 `AI 匹配度 80%` 假进度条，`学号 NN · 4分钟前` 两行布局干净
- `08-profile.png`：统计 `0 / 17 / 0`（累计处理 / 参与工单 / 知识条目）— 取自真实 API；非测试老师工单多时会显示真实数

**admin (A001) 视角**：
- `10-admin-users.png`（485 KB vs teacher 的 46 KB）：admin 可见全部用户列表，pill 过滤器正常
- `06-knowledge-list.png`（452 KB vs teacher 的 203 KB）：admin 看到 7 条 `[demo]%` pending global kb_suggestions（Sprint B 目标达成）

### Phase 3 realtime 回归（seed 完成后）

```
[result] T1 (teacher UI 发 → student UI 实时收): PASS
[result] T2 (student UI 发 → teacher UI 实时收): PASS
[result] T3 (再一轮 teacher → student): PASS
[summary] T1=true T2=true T3=true
```

跑 seed-demo-data.py 不影响实时推送。`fix/realtime-user-channel-push` 分支功能完整。

### Phase 3 已知限制

1. **知识列表页 GET /api/v1/knowledge/entries 不存在**：前端 `getKnowledgeEntries` 回落到本地缓存或空。seed 的 KB 只有通过 admin 的 `/reviews/pending` 在 `admin-knowledge-review` 路径可见。列表页补数据需后端增加 `@router.get("/entries")`，超出本次 UI sprint 范畴。
2. **`pilot:*` 测试号被过滤**：防止污染。真正的学生帐号 password === staff_id 约定。
3. **`13800000002` 账号 login 失败**：手机号格式的遗留测试账号密码与 staff_id 不同，seed 脚本会 skip + 继续。
4. **偶发 `conv NN accept 403`**：个别 conv 因 role/权限边界 accept 失败，已 warn 跳过，不影响其他条目成功 seed。

### 启动 / 清理速查

```powershell
# Windows PowerShell · 灌 60 条 conversation
python services\gateway\scripts\seed-demo-data.py conv --count 60 --confirm

# 灌 25 条 KB（走 SSH pipe）
python -c "import subprocess,sys; out = subprocess.check_output([sys.executable, 'services/gateway/scripts/seed-demo-data.py', 'kb-sql', '--kb-count', '25']); open('.tmp/seed-kb.sql', 'wb').write(out)"
scp .tmp\seed-kb.sql easten@192.168.100.165:/tmp/seed-kb.sql
ssh easten@192.168.100.165 "docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2 < /tmp/seed-kb.sql"

# 演示结束清理
python -c "import subprocess,sys; out = subprocess.check_output([sys.executable, 'services/gateway/scripts/seed-demo-data.py', 'cleanup-sql']); open('.tmp/cleanup.sql', 'wb').write(out)"
scp .tmp\cleanup.sql easten@192.168.100.165:/tmp/cleanup.sql
ssh easten@192.168.100.165 "docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2 < /tmp/cleanup.sql"
```

---

---

## 2026-05-11 Phase 4 · 头像 (UserAvatar 组件)

### 病根（为什么之前是空灰圆）

- `pages/profile/index.vue`：96×96 大 `.avatar-placeholder` 空灰圆
- `pages/dashboard/index.vue` 欢迎 banner：64×64 `.avatar-placeholder` 空灰圆
- `pages/questions/detail.vue` 学生卡：56×56 `.avatar-placeholder` 空灰圆
- `pages/questions/index.vue` 列表：标题首字母 + 5 色轮换 → 属于唯一能打的方案，但和其他地方不统一
- 后端 `UserInfo.avatar_url` schema 已有，但从未被写入 → 永远 null

### 新增组件 `@/Users/easten/projects/yixiaoguan-v2/apps/teacher-app/src/components/UserAvatar.vue`

三级兜底策略：

1. **最优先**：`props.avatarUrl`（如果未来后端填充了头像 CDN URL，直接用）
2. **兜底**：[DiceBear 9.x `notionists-neutral`](https://api.dicebear.com/9.x/notionists-neutral/svg) SVG API，按 `staff_id` 作为 seed，每个人一张确定性生成的独特卡通头像，背景走 MD3 tonal 调色板的渐变（`ddd6fe,fbcfe8,c4e0c9,ffe1cc,d4e4fb`）
3. **最底**：离线 / DNS 挂 / 请求失败时，显示姓名首字母 + 基于 seed hash 的 5 色 MD3 tonal 容器色（primary-container / secondary-container / tertiary-container / primary-soft / tertiary-soft）

**实现要点**：
- 用 `<view>` + `background-image: url(...)` 而不是 `<img>` 或 uni 的 `<image>`（前者 uni-app 模板编译器会改写，后者 SVG content-type 处理有毛病）
- JS 侧 `new Image()` 预加载，`onload` 成功才翻 `imageLoaded=true`，避免空容器闪烁；`onerror` 兜底回 initial
- SCSS 不写 `@use`（uni-app-vite plugin 自动把 `uni.scss` @import 注入在 style block 开头，`@use must be first` 会报 "must be written before any other rules"），直接依赖全局已注入的 tokens

### 改动的 4 处调用点

| 页面 | size | seed | 替换前 |
|------|------|------|--------|
| `pages/profile/index.vue` hero | 88px | `staff_id`（例：`anjing`） | 空灰圆 |
| `pages/dashboard/index.vue` 欢迎 banner | 56px（带 ring） | `staff_id` | 空灰圆 |
| `pages/questions/detail.vue` 学生卡 | 56px | `student_id` | 空灰圆 + 绿色在线点（点保留） |
| `pages/questions/index.vue` 列表 | 44px | `student_id` | 首字母 + 5 色轮换（用 title 首字母，不稳定） |

### 视觉确认（`.tasks/teacher-ui-audit-2026-05-11/after-avatar/`）

- `08-profile.png` (299 KB)：`anjing` 的 DiceBear 卡通头像 on top of purple hero gradient，非常干净、有辨识度
- `02-dashboard.png` (266 KB)：欢迎 banner 右侧 `anjing` 头像，56px + 白色 2px ring，和紫色 banner 对比强烈
- `03-questions-list.png` (574 KB)：每条 question card 左侧一张独特 DiceBear 头像（按 `student_id` 种子），瞬间从"一堆灰圆"变成"一群真实学生"
- `05-questions-detail.png` (135 KB)：学生信息卡头像 + 在线点（保留）

### 修复过程中的技术坑

1. **SCSS `@use` 失败**：dart-sass 要求 `@use` 必须在所有其他 rule 之前；uni-app-vite 会把 uni.scss 的 `@import` 自动注入到每个 style block 开头，破坏这个约束。结论：本项目所有 `.vue` 必须用 `@import`，或直接不写（tokens 已全局注入）。
2. **HMR "卡住"假象**：上面那个 SCSS 错误导致整个 UserAvatar.vue 一直编译失败，页面 DOM 保持在 error overlay 状态；Playwright 截图是错误遮罩，文件大小恒定 163 KB。kill + 重启 dev server，第一次 full reload 才拿到真的错误日志，然后修 SCSS 就好了。
3. **uni-app `<image>` vs `<img>`**：uni-app H5 模板编译会把 `<img>` 改写为 `<image>` 组件；后者对 SVG 的 content-type / referrer 处理有边缘 case，很多情况下不渲染。最稳方案：`<view style="background-image: url(...)">`，模板编译器碰不着背景图。

### Phase 4 回归

```
[result] T1 (teacher UI 发 → student UI 实时收): PASS
[result] T2 (student UI 发 → teacher UI 实时收): PASS
[result] T3 (再一轮 teacher → student): PASS
[summary] T1=true T2=true T3=true
```

引入 UserAvatar 组件 + dev server 重启后，实时推送链路仍完整。

---

## 2026-05-11 Phase 5 · 收尾遮挡修复

### 问题

1. **教师端 `pages/questions/detail.vue` `teacher_serving` 状态下，最后一条系统/教师消息被底部 reply action-bar 遮挡**
   - reply mode 的 action-bar 实际高度 = `16 + 80(input min) + 12(gap) + 48(buttons) + 16+safe-area = ~200-230px`
   - 原 `.main-content { padding-bottom: 160px }` 不够，scroll 到底时最后一条消息被压住一半
2. **教师端 `pages/questions/index.vue` 待处理 tab 右上角红色 badge 被剪掉**
   - badge `top: -4px` 凸出 tab 顶部 4px
   - 父级 `.filter-section` 是 `<scroll-view scroll-x>`，scroll-x 容器默认在顶沿做了裁切，badge 凸出部分被切
3. **`apps/student-app/src/pages/chat/index.vue` 同款 input bar 遮挡（防御性）**
   - bottom-area 实际高 ≈ 5.1rem（padding 1.5 + input-wrapper 3.625），原 `.bottom-spacer` 4.5rem 差 0.6rem，最后一条 system message 边缘可能被压

### 修复

| 文件 | 改动 |
|------|------|
| `pages/questions/detail.vue` | `.main-content { padding-bottom: 160px }` → `calc(240px + env(safe-area-inset-bottom))` |
| `pages/questions/detail.vue` | `.action-bar` 去掉 `backdrop-filter: blur(20px)` + `rgba(...,0.95)` 半透明，改为 `$surface-container-lowest` 100% 不透明 + 顶部 `box-shadow` 做分层（避免 scroll content 经过 fixed action-bar 区域被磨砂遮挡） |
| `pages/questions/index.vue` | `.filter-section` 加 `padding-top: 8px`（覆盖 badge top:-4px 凸出 + 2px ring） |
| `apps/student-app/src/pages/chat/index.vue` | `.bottom-spacer` 高度 4.5rem → 5.5rem |

### Frosted glass 取舍说明

原 `.action-bar` 用了 `backdrop-filter: blur(20px) saturate(180%)` + `rgba($surface-container-lowest, 0.95)` 实现 iOS 17 / MD3 风格的"frosted glass" — 这种效果当 fixed bar 浮在静态页面上时很漂亮，但**当下方有可滚动 chat content 经过这一区域时**，blur 会让正在经过的气泡内容看起来"被磨砂遮挡"，给人"有一层东西位于顶层"的负面观感。聊天 UI（WeChat / iMessage / Material Chat）几乎一致地用纯不透明背景 + 顶部 shadow 来分层，原因正是这个。本项目其他 nav bar（如 TopAppBar / BottomNavBar）静态页面下保留 frosted glass 没问题。

### 视觉确认

- `04-questions-list-pending.png` (281 KB)：badge 红圆「9」完整显示在紫色 tab 右上角，带白色 ring
- `05-questions-detail.png` (131 KB)：底部 "请输入回复内容..." textarea + "仅回复" / "回复并解决" 按钮全可见，且最后一条教师消息可正常滚动到底部不被压

### Phase 5 回归

```
[result] T1 (teacher UI 发 → student UI 实时收): PASS
[result] T2 (student UI 发 → teacher UI 实时收): PASS
[result] T3 (再一轮 teacher → student): PASS
```

### Demo 截图前的"学号多样化"建议

当前"处理中" tab 反复出现学号 18 的原因：`test-realtime-v7.mjs` 和 `teacher-audit-capture.mjs` 都用固定 `staff_id=4125150011`（user_id=18）创建测试 conv，这些 conv 留在 `teacher_serving` 状态。Demo / 正式截图前建议：

```bash
# 1. 清掉之前 capture / realtime 测试残留的 [demo] [ui-audit] [v7-rN] 标记 conv
python services/gateway/scripts/seed-demo-data.py cleanup-sql | \
  ssh easten@192.168.100.165 'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'

# 2. 重新灌 60 条多样化 conv (random.choice 学生池, 各种状态分布)
python services/gateway/scripts/seed-demo-data.py conv --count 60 --confirm

# 3. 这时候 "处理中" / "待处理" tab 就会是 19/32/50/9/34/30/45/47 这种多样化学号
```

---

## 总结

### ✓ 已完成

- **Sprint A**: TopAppBar / admin/users / admin/import 全量 token 化
- **Sprint B**: dashboard 状态类选择器对齐 enum / profile 真实 API 统计 / questions 去假 confidence / knowledge rgba / pages.json tabBar v2 primary / 学号 文案统一
- **Phase 3 Seed**: 59 convs / 25 KB / 8 UQ 入 165 dev，全部带 `[demo]` marker
- **Phase 4 Avatar**: UserAvatar 公用组件 + DiceBear `notionists-neutral` + hash 首字母三级 fallback，替换 4 处灰圆
- **Phase 5 遮挡修复**: detail.vue padding-bottom 160→240px / questions/index 加 padding-top 8px / student chat spacer 4.5→5.5rem
- **截图对比**: before + after + after-seed + after-seed-admin + after-avatar + after-avatar-admin 共 6 套 66 张截图，都存于 `.tasks/teacher-ui-audit-2026-05-11/`
- **Realtime 回归**: 四轮 T1+T2+T3 全 PASS，`fix/realtime-user-channel-push` 未受影响

### ⚠︎ 未完成（留给后续）

- analytics chart palette 硬编码清理（P2）
- 前端展示真实 `student_name` / `college_name`（需后端 schema 补字段，P1）
- 缺失的 `GET /api/v1/knowledge/entries` 端点（需后端增 route，P1）
- 后端加 `POST /api/users/me/avatar` 允许教师上传真实头像，填入 `avatar_url` 字段（当前 UserAvatar 的档位 1 / "最优先"分支已预留好）（P2）
- 演示环境如果断外网，DiceBear 拉不到会降级到首字母 fallback，外网恢复或把 SVG 预缓存/内置静态图都可以进一步兜底（P3）


