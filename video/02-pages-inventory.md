# 医小管 页面清单 · 教师端

> 第一稿 · 2026-05-11 · 仅 teacher-app，student-app 待补
> 探查脚本: `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/explore-teacher.mjs`
> 截图位置: `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/out/explore-teacher/`
> Viewport: 393×852 (iPhone 14 Pro 竖屏，与 student-app 一致)

---

## 摘要

teacher-app 是 UniApp H5 mobile-first 应用，**与 student-app 同栈、同viewport、同设计语言**。共 10 个路由，4 个 Tab，2 个 admin 隐藏页面，1 个数据看板。

**Demo 视频可用价值评估**：
- ⭐ **数据看板** (analytics) — 首屏 4 卡片 + 中段趋势/质量图 + 底部学院分布/时段热力图/AI 成本，**做产品片头/全屏镜头的最佳素材**
- ⭐ **知识库** (knowledge) — 高频待补卡片 + "去补充"按钮，演示"老师补充入库"流程的关键入口
- ⭐ **profile/dashboard** — 紫粉渐变 hero 卡，开场展示老师身份感
- ⚠️ **学生提问** (questions) — anjing 账号无工单数据，演示需要先造数据
- ⚪ **admin 页面** — 入门级表单 UI，不是 demo 重点

---

## 路由与 Tab Bar

### Tab Bar (4 个，按顺序)
1. **工作台** `/pages/dashboard/index`
2. **学生提问** `/pages/questions/index`
3. **知识库** `/pages/knowledge/index`
4. **我的** `/pages/profile/index`

### 非 Tab 页面
- **登录** `/pages/login/index`
- **提问详情** `/pages/questions/detail`
- **知识详情** `/pages/knowledge/detail`
- **数据看板** `/pages/analytics/index` ⭐
- **用户管理** `/pages/admin/users` (admin 权限)
- **批量导入** `/pages/admin/import` (admin 权限)

---

## 各页面详细描述

### 01-dashboard 工作台
- **顶栏**: 紫色图标 + "工作台" + 🔔(红点提醒)
- **Hero 卡片**: 紫粉渐变 + "下午好，安静 👋" + "今天有 0 条待处理提问" + 圆形头像位
- **快捷操作 chip 区** (横向滚动): 新建知识 / 发布通知 / 数据报告 (旁边还有更多)
- **4 数据卡片 2×2 网格**:
  - 紫色: 今日提问 0
  - 红色: ❗ 待处理 0
  - 绿色: 📖 知识条目 0
  - 橙色: ✓ 今日审批 0
- **待处理提问区** (空状态)
- **底部 Tab Bar**: 工作台(高亮) / 学生提问 / 知识库 / 我的

### 02-questions-list 学生提问
- **顶栏**: ← 学生提问 🔍
- **状态过滤 chip** (横向): 全部(active) / 待处理 / 处理中 / 已解决
- **列表**: 工单卡片 (anjing 暂无数据)
- **空状态**: "暂无工单"

### 03-knowledge-list 知识库
- **顶栏**: ← 知识库 ⊕(新建)
- **搜索栏**: "搜索待补问题..."
- **Tab**: 高频待补(active) / 我的知识
- **卡片** (每个含):
  - 顶部小标签: "高频待补" 紫色
  - 右上: "1 次命中" 紫色文字
  - 标题: 如 "你有意见反馈" / "我不要" / "我不要转人工"
  - 副标题: "最近出现于 1 天前"
  - 底部: 灰圆 + "样例会话 63" + **紫色"去补充"按钮**

### 04-profile 我的
- **顶栏**: ← 我的 ⚙️
- **大 Hero 卡**: 紫粉渐变圆角矩形 + 圆形头像 + "安静" + "高级讲师 / 学院 17" + "ID: anjing"
- **3 数据条**: 累计处理 156 / 本月审批 42 / 知识入库 28
- **系统设置**:
  - 通知提醒 (toggle on)
  - 声音提示 (toggle on)
  - AI 自动回复 (toggle off)
  - 修改密码 (跳转)

### 05-analytics 数据看板 ⭐⭐⭐
**首屏**:
- **顶栏**: ← 数据看板
- **时间过滤**: 近 7 天(active) / 近 30 天 / 全部
- **4 大数据卡片 2×2** (每个卡片有彩色顶边线):
  - 紫色 ↗11.2%: **847** 总提问
  - 蓝色 ↗6.9%: **73.2%** AI 解答率
  - 绿色 ↗21.8%: **12.4 分** 平均响应
  - 橙色: **6** 待处理
- **提问趋势柱状图**: 7 天双色堆叠 (总提问深紫 + AI 解答浅紫)，05-04 至 05-10
- **AI 质量分析**: 紫色圆环 68% 命中率 + 横向进度条 优(135) / 中(86) / 低(42)

**中段** (滚动 600px):
- 热门未解答 Top 5
- 还有图表

**底部** (滚动 1200px):
- **学院提问分布** 横向柱状图: 计算机院 186 / 管理院 142 / 文学院 98 / 医学院 87 / 外语院 76 / 艺术院 63
- **提问时段分布** 7×24 热力图: 周一到周日 × 24 小时，紫色深浅展示
- **AI 成本概览** "按当前周期统计": 12,456 总 Tokens / ¥0.01 总价格 / 1.4s 平均延迟 + 7 天细分 (2,694 / 916 / 1,981 / ...)

### 06-admin-users 用户管理 (admin 权限页)
- **顶栏**: ← 用户管理 👤+(添加)
- **搜索栏**: "搜索学号或姓名"
- **角色过滤**: 全部(active) / 学生 / 教师 / 管理员
- **复选框**: "显示为离访客 (0)"
- **统计**: 共 0 人
- **空状态**: "暂无用户" (anjing 看不到，可能需要 admin 账号)

### 07-admin-import 批量导入用户
- **顶栏**: ← 批量导入用户
- **导入格式说明** 蓝色提示卡:
  1. 请输入 JSON 格式的用户列表
  2. 每个用户包含 staff_id (学号) 和 name (姓名)
  3. 初始密码默认为学号，可后续重置
  4. 已存在的学号会自动跳过
- **用户角色**: 学生(active) / 教师
- **学院 ID** 文本框 (示例: 17)
- **班级 ID (可选)** 文本框
- **用户数据 (JSON)** 大 textarea (预填示例)
- **确认导入** 紫色大按钮

---

## 已确认的工程事实

### 1. **代码与学生端高度共用**
- centrifuge.ts 工具类一行不差: `@f:/Documents/code/yixiaoguan-v2/apps/teacher-app/src/utils/centrifuge.ts`
- 同样的频道命名 `conv:{convId}`
- 同样的事件类型 `new_message` / `status_changed` / `escalation_notify`

### 2. **实时对话已实现，代码层完备**
- 老师 detail.vue 监听 → 学生 chat/index.vue 收 teacher 消息
- 完整状态机: `ai_serving → pending_teacher → teacher_serving → resolved/closed`
- 演示需要造一个工单数据 (anjing 当前为空)

### 3. **演示障碍**
- ⚠️ anjing 账号无工单/无用户，无法直接录"学生呼叫 → 老师接单"完整闭环
- 解决方案 (待讨论):
  - **A. 本地起 dev 环境** (deploy/docker-compose) → 用 admin 批量导入学生 → 学生触发 escalation → anjing 接单
  - **B. 线上 mock** → 后端临时构造 pending_teacher 工单

---

## 探查脚本要点

`@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/explore-teacher.mjs`

关键技术点 (后期录制脚本可直接复用):
- **viewport**: `393×852` + `deviceScaleFactor: 3` + `isMobile: true` + `hasTouch: true` + iPhone UA
- **登录**: `page.locator('input[type="text"]').fill(...)` 直接定位真实 input (绕开 uni-input wrapper)
- **页面切换**: `page.goto('.../#/pages/xxx')` 完整 URL 触发 router (因 `window.uni.switchTab` 在 H5 编译产物里不暴露)
- **每页 settle**: 2.5s 等待 (UniApp tab 切换动画 + API 请求渲染)

---

## 待补充

- 📋 student-app 探查脚本 (改造后)
- 📋 admin 账号下的 admin 页面对比
- 📋 questions/detail 详情页 (需要先造工单)
- 📋 knowledge/detail 知识详情编辑页 (需要点"去补充"进入)
