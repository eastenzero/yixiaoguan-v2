# Visual Diff Report — Stitch 设计稿 vs 当前实现

> 生成日期：2026-04-27
> 范围：12 个 v2 上线 scope 内的页面（教师端 7 + 学生端 5）
> 评分维度：结构 / 配色 / 字体 / 组件，每项 0-3 分，单页满分 12

## 总览

| 端 | 页面 | 结构 | 配色 | 字体 | 组件 | 总分 | 主要差距 |
|----|------|------|------|------|------|------|----------|
| 教师端 | login | 3 | 3 | 2 | 2 | 10/12 | 自定义 SVG 图标替代 Material Symbols |
| 教师端 | dashboard | 3 | 3 | 2 | 2 | 10/12 | 头像为占位符，自定义图标 |
| 教师端 | knowledge_base | 2 | 3 | 2 | 2 | 9/12 | 含额外审核/待补工作流，卡片信息密度更高 |
| 教师端 | knowledge_detail | 2 | 3 | 2 | 2 | 9/12 | 纯文本渲染，缺图片/步骤/引用块 |
| 教师端 | question_list | 3 | 3 | 2 | 2 | 10/12 | 头像为字母占位，缺真实头像 |
| 教师端 | question_detail | 3 | 3 | 2 | 2 | 10/12 | 缺快捷回复 chips，自定义图标 |
| 教师端 | profile_settings | 3 | 3 | 2 | 2 | 10/12 | 头像占位，自定义图标 |
| 学生端 | login_page | 3 | 3 | 2 | 3 | 11/12 | 近乎 1:1，仅字体未加载 Manrope |
| 学生端 | home_page | 1 | 2 | 2 | 1 | 6/12 | 缺失搜索条、标签、Bento 网格、服务列表、通知横幅 |
| 学生端 | ai_chat_page | 3 | 2 | 2 | 2 | 9/12 | 缺追问 chips，部分颜色硬编码 |
| 学生端 | chat_history | 1 | 2 | 2 | 1 | 6/12 | 缺失汇总 Hero、筛选器、头像堆叠、FAB |
| 学生端 | profile_page | 1 | 2 | 2 | 1 | 6/12 | 缺失统计卡、Bento 学期进度/AI 卡片、设置分组 |

平均总分：教师端 **9.7/12**，学生端 **7.6/12**。

## 通用观察（应用到所有页面的共性问题）

1. **两端主色不统一**：教师端 stitch 使用 `#702ae1`，学生端 stitch 使用 `#630ed4`；当前实现已分别跟随，但跨端视觉一致性弱。
2. **字体族缺失 Manrope**：stitch 全量指定 `font-family: Manrope, PingFang SC, sans-serif`；当前实现依赖系统默认或 PingFang SC，未加载 Web Font，导致字重和字间距差异。
3. **图标体系分裂**：教师端使用自定义 SVG 图标组件（`@/components/icons/`），学生端混用 `material-symbols-outlined` 与部分自定义图标；stitch 统一使用 Material Symbols Outlined（wght 300/400，FILL 0/1）。
4. **学生端缺乏 design token 体系**：教师端有完整的 `theme.scss`（MD3 语义化变量），学生端 `theme.scss` 仅 38 行且未在所有页面导入，大量颜色硬编码（如 `#f8fafc`、`#0f172a`）。
5. **圆角体系不一致**：stitch 统一使用 `rounded-xl`/`rounded-2xl`/`rounded-3xl`（16px/24px/48px）；学生端部分卡片仅 `0.75rem`（12px），与设计的"大圆角"语言不符。

## 设计令牌（design tokens）建议

基于 stitch 设计稿，提议沉淀统一的 v2 design system tokens：

```scss
// 主色（建议以教师端 #702ae1 为基准，学生端归一化）
$primary: #702ae1;
$primary-dim: #6411d5;
$primary-container: #b28cff;
$on-primary: #f8f0ff;

// 中性表面
$bg-page: #faf5fb;        // 教师端
$bg-page-student: #f7f9fb; // 学生端（可保留差异）
$bg-card: #ffffff;
$surface-container-low: #f4eff5;
$surface-container: #ebe7ed;
$border: #afacb1;

// 文本
$text-primary: #2f2e32;
$text-secondary: #5d5b5f;
$text-muted: #78767b;

// 圆角
$radius-sm: 12px;
$radius-md: 16px;
$radius-lg: 24px;
$radius-xl: 32px;
$radius-full: 9999px;

// 阴影（紫色调多层）
$shadow-card: 0 1px 3px rgba(112,42,225,0.06), 0 4px 8px -2px rgba(112,42,225,0.08);
$shadow-elevated: 0 4px 12px rgba(112,42,225,0.10), 0 16px 40px -8px rgba(112,42,225,0.16);

// 间距
$space-page: 20px;
$space-section: 32px;

// 字体
$font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

## 教师端逐页

### 1. login_screen → apps/teacher-app/src/pages/login/index.vue

- **得分**：10/12（结构 3 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - 背景：`bg-gradient-to-br from-primary-fixed-dim via-primary to-primary-dim`
  - 主色：`#702ae1`
  - 关键元素：光晕圆 orb、玻璃态登录卡片（`bg-surface-container-lowest/95 backdrop-blur-2xl`）、Material Symbols 图标、渐变按钮、记住我 checkbox、其他登录方式
- **当前实现**：
  - 完全复现了渐变背景与光晕圆装饰
  - 使用 SCSS 变量 `$primary`/`$surface-container-lowest`，与设计 token 一致
  - 登录按钮使用 `$gradient-btn`，阴影与圆角匹配
- **差距**：
  - 自定义 SVG 图标（`IconGraduationCap`、`IconUser` 等）替代了 Material Symbols，视觉 weight 和风格略不同
  - 未加载 Manrope 字体，依赖系统默认
  - 验证码区域在 v2 已隐藏，与设计（无验证码）一致
- **建议改动**（按工作量从小到大）：
  - [小] 全局注入 Manrope 字体（CDN 或本地 woff2）
  - [中] 将常用图标替换为 `material-symbols-outlined` 字体图标或统一图标组件库
  - [大] 无（本页已高度还原）

### 2. dashboard → apps/teacher-app/src/pages/dashboard/index.vue

- **得分**：10/12（结构 3 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - TopAppBar：白色模糊背景 + 通知红点
  - Welcome Banner：渐变紫卡片 + 头像 + 装饰光晕
  - Quick Actions：横向滚动 pill 按钮（新建知识/发布通知/数据报告/系统设置）
  - Statistics：2×2 网格，4 种浅色背景（紫/红/绿/琥珀）
  - Pending Questions：卡片列表，含学生姓名、院系标签、时间、状态点、箭头
- **当前实现**：
  - 结构完全对齐：顶栏 → 欢迎横幅 → 快捷操作 → 统计 → 提问列表 → 底部导航
  - 颜色使用 `$gradient-hero`、`$secondary-container/30`、`$error-container/10` 等，与 stitch 一一对应
- **差距**：
  - 头像为纯色占位符（`avatar-placeholder`），无真实图片或默认头像
  - 快捷操作使用自定义 SVG 图标
  - 提问卡片中院系标签数据未绑定真实院系，显示为对话标题
- **建议改动**：
  - [小] 头像区域接入默认头像或首字母头像
  - [中] 统一图标体系
  - [中] 补充学生院系/专业字段到卡片展示

### 3. knowledge_base → apps/teacher-app/src/pages/knowledge/index.vue

- **得分**：9/12（结构 2 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - 顶栏：返回 + "知识库"标题 + 圆形添加按钮（`bg-primary/10 text-primary rounded-full`）
  - 搜索栏：`bg-surface-container` 大圆角输入框
  - 分类标签：pill 形状，激活态为 `bg-primary text-on-primary`
  - 知识卡片：`rounded-3xl p-6`，含分类标签（彩色 pill）、状态点、标题、摘要、作者头像、时间
- **当前实现**：
  - 基础结构（搜索、标签、卡片列表）对齐
  - 卡片圆角 `24px`、阴影 `$elevation-1` 匹配
  - 但存在大量业务扩展 UI：高频待补 composer、AI 润色抽屉、管理员审核按钮（通过/驳回）
- **差距**：
  - 卡片内嵌的 composer（去补充/预览/提交）是业务新增，视觉较重，打断设计节奏
  - 管理员审核视图（`isAdmin && activeCategory === 0`）在设计稿中无对应
  - 缺少真实作者头像
- **建议改动**：
  - [中] 将 composer / 润色抽屉改为底部 sheet 或独立页面，减轻卡片负担
  - [小] 统一卡片内的操作按钮为设计稿的轻量链接样式
  - [小] 补充头像占位策略

### 4. knowledge_detail → apps/teacher-app/src/pages/knowledge/detail.vue

- **得分**：9/12（结构 2 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - Hero：分类标签 + 状态标签 + 大标题（`text-3xl md:text-4xl font-extrabold`）+ 作者行
  - Body：可包含首图（`aspect-video rounded-xl`）、H3 标题、编号步骤列表（带圆形序号）、引用块（左边框 + 浅色背景）
  - Bottom Action Bar：`下线`（outline）+ `编辑`（primary gradient）
- **当前实现**：
  - Hero 区域结构对齐，颜色正确
  - Bottom Action Bar 结构与样式均匹配
  - 但正文仅渲染纯文本（`<text class="content-text">{{ entry.content }}</text>`）
- **差距**：
  - 正文无富文本渲染：缺失图片、H3、有序列表、引用块样式
  - 存在 `reject-banner`（驳回原因）业务扩展，设计稿无对应
  - 标题字号 `30px` 接近设计，但未响应式放大到 `text-4xl`
- **建议改动**：
  - [大] 接入 Markdown / RichText 渲染器，支持图片、列表、引用块
  - [小] 将驳回 banner 调整为轻量提示条，避免打断阅读

### 5. question_list → apps/teacher-app/src/pages/questions/index.vue

- **得分**：10/12（结构 3 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - 顶栏：返回 + "学生提问" + 搜索图标
  - Filter Tabs：pill 形状（全部/待处理/处理中/已解决）
  - 卡片：学生头像（圆形真实照片）、姓名、专业·时间、状态 badge、问题摘要、`line-clamp-2`、AI 匹配度进度条
- **当前实现**：
  - 结构完全对齐
  - AI 匹配度进度条（`ai-confidence`）已还原，含绿/琥珀/红三色阈值
  - 状态 badge 颜色与文本样式匹配
- **差距**：
  - 头像使用彩色圆形 + 首字母（`avatarColors` 数组），非真实头像
  - 学生姓名为 `学生 #{{ id }}`，非真实姓名
  - 专业/院系信息缺失
  - 自定义 `IconBrain` 替代 Material Symbols `psychology`
- **建议改动**：
  - [小] 接入学生头像与真实姓名/院系数据
  - [小] 统一图标

### 6. question_detail → apps/teacher-app/src/pages/questions/detail.vue

- **得分**：10/12（结构 3 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - 学生信息卡：头像 + 在线绿点 + 姓名 + 状态 badge
  - 聊天区：学生消息（紫色圆角气泡右对齐）、AI 消息（白底带红色左边框 + AI 头像）、系统消息（居中灰色 pill）
  - 底部：待处理时显示大号渐变「接单处理」按钮；处理中时显示快捷回复 chips + 输入框 + 发送按钮
- **当前实现**：
  - 聊天结构完全对齐，气泡配色与圆角匹配
  - AI 消息白底 + 左边框（`border-left: 4px solid $error` 在设计中为装饰，实现使用了 `$error` 色系，但设计稿 AI 气泡左边框为 `border-error/20` + 红色指示条）
  - 底部状态机（待处理/处理中/已解决/已关闭）完整
- **差距**：
  - 缺快捷回复 chips（设计稿中的「已为您查询 / 请到XX部门 / 核对缴费号」pill 按钮）
  - 系统消息样式为居中 badge，但颜色略浅
  - 自定义图标替代 Material Symbols
- **建议改动**：
  - [中] 补充快捷回复 chips（可配置常用语）
  - [小] 统一图标

### 7. profile_settings → apps/teacher-app/src/pages/profile/index.vue

- **得分**：10/12（结构 3 / 配色 3 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - Hero：渐变紫卡片 + 大头像（带白边）+ 姓名 + 职称/院系 + ID badge（`bg-white/20 backdrop-blur-md rounded-full`）
  - Stats：3 列网格（累计处理/本月审批/知识入库）
  - Settings：分组列表，带白色圆形图标底 + toggle switch / chevron
  - Logout：红色文字按钮，带图标
- **当前实现**：
  - 结构完全对齐
  - Hero 渐变使用 `$gradient-hero`，装饰光晕使用 `glow-1/glow-2`
  - Toggle switch 为自定义实现，样式与 design 一致
- **差距**：
  - 头像为占位符
  - 设置项中的图标使用自定义 SVG
  - 统计数值为写死（156/42/28），未绑定真实数据
- **建议改动**：
  - [小] 接入真实统计数据 API
  - [小] 头像与图标统一

## 学生端逐页

### 8. login_page → apps/student-app/src/pages/login/index.vue

- **得分**：11/12（结构 3 / 配色 3 / 字体 2 / 组件 3）
- **stitch 设计要点**：
  - 背景：`linear-gradient(135deg, #5B21B6 0%, #8B5CF6 100%)`
  - 卡片：`bg-surface-container-lowest rounded-[24px]` 白色卡片，带大阴影
  - 表单：学号/密码/验证码（带图片验证码），图标使用 Material Symbols
  - 按钮：渐变圆角大按钮
- **当前实现**：
  - 近乎 1:1 还原，直接使用 `linear-gradient(135deg, #5b21b6, #8b5cf6)`
  - 使用 `material-symbols-outlined` 图标，与 stitch 一致
  - 卡片圆角 `1.5rem`、阴影、footer 结构均匹配
- **差距**：
  - 未加载 Manrope 字体
  - 验证码区域在 v2 逻辑中可能未启用，但 DOM 结构保留
- **建议改动**：
  - [小] 注入 Manrope 字体
  - [小] 清理未启用验证码的占位样式

### 9. home_page → apps/student-app/src/pages/home/index.vue

- **得分**：6/12（结构 1 / 配色 2 / 字体 2 / 组件 1）
- **stitch 设计要点**：
  - 顶栏：`医小管` 品牌名 + 通知铃铛（带红点）
  - 问候语：`下午好，林同学` + `智慧校园助理` 大标题
  - AI 搜索条：大圆角 pill，左侧紫色图标容器 + 输入框 + 「提问」按钮
  - 横向标签：`奖学金政策 / 选课指南 / 图书馆开放 / 校园卡充值`
  - Bento 网格：2×2，大卡片「AI 智能助手」+ 两个小卡片「空教室预约」「我的申请」
  - 常用服务：列表（教务管理/图书馆/学生邮箱/学校官网），带 chevron
  - 通知横幅：`bg-primary/5` 紫色轻量提示条
  - 底部导航：活跃项为紫色 pill 背景
- **当前实现**：
  - 极简布局：仅问候语 → hero 卡片「问 AI 助手」→ 快捷提问列表 → 最近对话
  - 无顶栏品牌/通知，无搜索条，无标签，无 Bento，无服务列表，无通知横幅
  - 底部使用 `CustomTabBar`
- **差距**：
  - 缺失 6+ 个设计区块，整体信息架构完全不同
  - 背景色 `#f8fafc` 接近设计 `#f7f9fb`，但缺少 surface 层级变化
  - 快捷提问为简单白色卡片列表，非设计的搜索+标签+Bento 组合
- **建议改动**：
  - [大] **按 stitch 设计稿重构首页**：补全顶栏、搜索 pill、标签、Bento Grid、服务列表、通知横幅
  - [中] 统一底部导航为设计稿的 pill 高亮样式
  - [小] 接入真实最近对话与通知数据

⚠️ 用户已报告该页存在「首页被篡改」问题。本次 visual diff 已识别 6 处与设计稿明显不一致的区块，可能与篡改相关：
1. 缺失顶部品牌栏与通知入口
2. 缺失 AI 搜索输入条（设计的核心交互入口）
3. 缺失横向热点标签
4. 缺失 Bento 风格功能网格（AI 助手/空教室/我的申请）
5. 缺失「常用服务」快捷链接列表
6. 缺失未读通知横幅

### 10. ai_chat_page → apps/student-app/src/pages/chat/index.vue

- **得分**：9/12（结构 3 / 配色 2 / 字体 2 / 组件 2）
- **stitch 设计要点**：
  - 顶栏：返回箭头 + `医小管` 紫色标题 + 历史图标
  - 用户消息：`editorial-gradient` 紫色气泡，右对齐，圆角 `rounded-t-xl rounded-bl-xl`
  - AI 消息：白色气泡，左对齐，`border-l-4 border-primary`，含 AI 头像 + "Medical Assistant" label
  - 引用：「参考资料」卡片，`bg-surface-container-low rounded-lg`
  - 追问：底部 3 个轻量 pill 按钮（`bg-primary/5 hover:bg-primary/10`）
  - 输入区：大圆角输入框 + 紫色圆形发送按钮
- **当前实现**：
  - 顶栏、气泡布局、AI header、引用卡片、输入区均高度还原
  - 用户气泡使用相同渐变（`#630ed4 → #7c3aed`）
  - AI 气泡白底 + 左边框（`border-left: 0.25rem solid #630ed4`）
  - 引用卡片（`citations`）结构匹配
- **差距**：
  - 缺失追问 chips（`如何在线预约？/还有其他讲座吗？/综合楼怎么走？`）
  - 部分颜色硬编码（`#f7f9fb`、`#191c1e`、`#94a3b8`），未使用共享 token
  - AI header 标签为 "MEDICAL ASSISTANT"（大写），设计为 "Medical Assistant"（首字母大写）
  - 未加载 Manrope
- **建议改动**：
  - [中] 补充追问 chips（根据上下文动态生成或配置）
  - [小] 颜色值迁移到 `theme.scss` token
  - [小] 字体统一

### 11. chat_history → apps/student-app/src/pages/chat/history.vue

- **得分**：6/12（结构 1 / 配色 2 / 字体 2 / 组件 1）
- **stitch 设计要点**：
  - 顶栏：返回 + "对话历史" + 搜索按钮
  - Hero 汇总卡：`bg-gradient-to-br from-primary to-primary-container`，含本月对话数 + 解决率
  - 筛选器：「最近记录」标题 + 「全部状态」下拉
  - 卡片：左侧图标容器 + 标题/时间 + 状态 badge；底部头像堆叠（用户+AI）+ 消息数 + chevron
  - FAB：右下角紫色渐变圆形 `+` 按钮
- **当前实现**：
  - 极简列表：顶栏（无搜索）→ 对话卡片（仅标题 + 状态 badge + 时间）
  - 无 Hero 汇总、无筛选器、无头像堆叠、无消息数、无 FAB
- **差距**：
  - 信息密度极低，缺失设计的上下文（头像、消息数、分类图标）
  - 状态 badge 颜色硬编码，未使用 token
  - 卡片圆角 `0.75rem`（12px），设计为 `rounded-lg`（16px）
- **建议改动**：
  - [大] 补全 Hero 汇总卡、筛选器、FAB
  - [中] 丰富卡片内容：接入头像、消息数、分类图标
  - [小] 统一圆角与颜色 token

### 12. profile_page → apps/student-app/src/pages/profile/index.vue

- **得分**：6/12（结构 1 / 配色 2 / 字体 2 / 组件 1）
- **stitch 设计要点**：
  - 顶栏：返回 + "我的" + 通知铃铛（红点）
  - Hero：渐变紫卡片 + 真实头像（带 verified 徽章）+ 姓名 + 专业/年级 + 认证标签
  - 统计：2 列（问答历史/我的申请），带图标容器
  - Bento 网格：学期进度卡（含百分比进度条）+ AI 助手卡（含最近对话摘要 + 按钮）
  - 设置：分组列表（消息通知/系统设置/意见反馈/帮助中心/关于），带圆形图标 + chevron
  - 底部：退出登录 + Version 文本
- **当前实现**：
  - 极简：渐变头部（仅头像图标 + 姓名 + 学号）→ 信息卡片（3 行文本）→ 退出登录
  - 无顶栏、无统计、无 Bento、无设置分组、无版本号
- **差距**：
  - 缺失 5+ 核心区块，与设计风格差异最大
  - 信息卡片使用简单白底列表，无图标容器
  - 退出登录为白底红边框按钮，设计为 `bg-error/10 text-error` 轻量按钮
- **建议改动**：
  - [大] 按 stitch 重构：补全顶栏、统计卡、Bento 网格、设置分组
  - [中] 接入真实学期进度与 AI 最近对话数据
  - [小] 统一按钮与颜色样式

## 推荐 UI 精修任务清单

### Sprint 1（共性优化，影响所有页面）
- [P0] 沉淀 `apps/_shared/styles/tokens.scss`，定义统一 design tokens（两端共享主色、圆角、阴影、字号）
- [P0] 学生端全面替换硬编码颜色为共享 token，教师端已较好，仅需微调
- [P1] 统一图标体系：评估在两端统一使用 `material-symbols-outlined` 字体图标（减少自定义 SVG 维护成本）
- [P1] 全局加载 Manrope 字体（通过 CDN 或本地静态资源），统一字重与字间距
- [P1] 统一卡片圆角为 `$radius-lg: 24px`（学生端当前多为 12-16px）

### Sprint 2（逐页精修）
- [P0] **学生端 home**（首页篡改修复 + 设计对齐）— 缺失 6 大区块，需按 stitch 重构
- [P0] **学生端 profile** — 缺失统计/Bento/设置分组，需大幅补充
- [P0] **学生端 chat_history** — 补全 Hero 汇总、筛选器、FAB、丰富卡片
- [P1] 教师端 knowledge_detail — 接入富文本渲染（Markdown），支持图片、列表、引用块
- [P1] 教师端 knowledge_base — 优化 composer 交互，减轻卡片视觉负担
- [P1] 学生端 ai_chat — 补充追问 chips
- [P2] 其它 7 页（按总分从高到低，均为小修：图标统一、头像接入、字体加载）

预计工作量：Sprint 1 ≈ 1-2 天；Sprint 2 ≈ 4-6 天（学生端 3 个大改页面占主要工作量）。
