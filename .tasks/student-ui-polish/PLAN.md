# 学生端 UI 美化 — 执行 Plan

> 起始日期：2026-05-03
> 标杆：教师端（apps/teacher-app）已建立的 design token + global utility + shared component 体系
> 决议：v2 primary = `#5b21b6` (violet-800)，learn 自 `apps/student-app/src/styles/tokens.scss`

## Spec — 强约束

每页改造必须满足以下硬指标，否则不算完成：

1. **`<style scoped lang="scss">`** + **`@import '@/styles/tokens.scss';`** 必须有
2. **零 hard-coded hex**（除非该 hex 已经成为 token 中的常量；测试方法：grep `#[0-9a-fA-F]\{3,6\}` 应仅命中 token 文件）
3. **所有 spacing / radius / shadow / font-size / font-weight 必须用 token 变量**（`$space-*`、`$radius-*`、`$shadow-*`、`$font-size-*`、`$font-weight-*`），禁用 `rem` / hardcode `px` 数字（除 1px border 等微像素）
4. **顶栏统一**：使用新建的 `TopAppBar.vue` 组件（56px 高、blur backdrop、圆形 action button）
5. **入场动画**：可见 hero/section 至少标注 `animate-fade-up delay-N`，让首屏有节奏感
6. **微交互**：可点击卡片/按钮 `:active` 必须有视觉反馈（scale 0.96-0.98 或阴影变化）
7. **主色一致性**：禁止出现 `#630ed4` `#7c3aed` `#702ae1` 等旧 primary 色（应用 `$primary` / `$primary-hover` / `$primary-soft`）
8. **图标策略**：本轮先保留 `material-symbols-outlined` 字体类（教师端切 SVG 可作为 T1 单独工程），但必须确保字体已加载，loading 闪烁问题以 CSS `font-display: swap` + 占位 width/height 解决
9. **safe-area**：`padding-bottom` 必须考虑 `env(safe-area-inset-bottom)`，所有 fixed bar 同理 top

## Sprint 划分

### 阶段 0：地基（约束与共享设施）

- [x] **0.1** 写本 PLAN
- [x] **0.2** 创建 `apps/student-app/src/styles/global.scss`（复用教师端 utility class）
- [x] **0.3** `App.vue` 引入 `global.scss`，删除冗余 `theme.scss` 中过时变量
- [x] **0.4** 创建 `apps/student-app/src/components/TopAppBar.vue`（学生端版本，紫色 primary）
- [x] **0.5** 升级 `apps/student-app/src/components/CustomTabBar.vue`（token 化、active dot、:active 动效、Material Symbols FILL active 切换）
- [x] **0.6** 修正 `apps/student-app/src/uni.scss` 旧色板 + `pages.json` tabBar 旧色 + `index.html` 加 `viewport-fit=cover`

### 阶段 1：核心交互页（视觉冲击 P0）

- [x] **1.1** `pages/chat/index.vue` 全面重写 style → SCSS + token；
  - [x] 顶栏改用 TopAppBar
  - [x] welcome 空态：64×64 logo 渐变 + 旋转 -3deg + 双层 primary 阴影 + radial glow + animate-fade-up
  - [x] AI bubble 用 elevation 阴影 + 浅紫色边框替代左边框装饰
  - [x] typing/cursor 动画统一到 `global.scss` 的 `.typing-dots` / `.blink-cursor`
  - [x] citation 用 `$primary-soft` 背景 + cit-item :active 动效
  - [x] suggestion-chip 全 token + 紫色边/`$primary-soft` :active
  - [x] markdown 拆分 `.markdown-body` 基础 + `.markdown-body--rich` 富文本（code/blockquote/table）
  - [x] bottom-area 重新定位（坐在 tabbar 上方）+ input focus-within 紫色发光
  - [x] send-btn 渐变按钮 + :active 缩放
  - [x] inline-call-teacher pill + 紫色阴影；inline-call-done 用 `$success` alpha
- [x] **1.2** `pages/chat/history.vue` 全面重写
  - [x] 顶栏改 TopAppBar（show-back）
  - [x] empty 态：88×88 圆形紫色 wrap + filled icon + 引导文案
  - [x] 卡片改成 icon-wrap + body 双列结构，icon 5 色按状态切换
  - [x] status-badge 5 套 modifier（ai-serving / pending-teacher / teacher-serving / resolved / closed）+ status-dot
  - [x] 卡片 :active scale + 阴影增强
  - [x] animate-fade-up + delay-1..6 阶梯入场
  - [x] loading 用 `.typing-dots`；no-more 用居中 em-dash 文案
- [x] **1.3** `pages/login/index.vue` 提升到教师端品质
  - [x] 三层光晕 orb（白 / violet-400 / violet-300）+ 三色渐变背景（primary → primary-hover → violet-950）
  - [x] 玻璃态卡片：rgba(255,255,255,0.96) + backdrop-filter blur(40px) saturate(180%) + inset highlight
  - [x] logo 88×88 渐变 + 旋转 3deg + 双层紫色阴影 + 内 icon 反向旋转
  - [x] title 30px / 800 / letter-spacing -0.02em
  - [x] 标签 "学号 / STUDENT ID" 双语 + 全大写 + 11px / 0.10em letter-spacing
  - [x] input :focus-within 紫色边 + 4px 紫色发光环
  - [x] submit-btn pill + 渐变 + 双层紫色阴影 + :active 缩放
  - [x] 入场 animate-fade-up（卡片）+ delay-2（footer）
  - [x] footer 链接全大写 + 0.10em letter-spacing
  - 备注：未加"记住我"复选框（避免改登录逻辑），可作为后续可选增强

### 阶段 2：导航壳页（下次对话）

- [ ] **2.1** `pages/home/index.vue`（已较新但需 token 收敛 + 入场动画）
- [ ] **2.2** `pages/services/index.vue`（重灾区：删平行工具类、TopAppBar 替换、token 化）
- [ ] **2.3** `pages/profile/index.vue`（hero 渐变 token 化、settings icon 颜色 token 化、TopAppBar 替换）

### 阶段 3：教师端同步精进（下次对话或并行）

- [ ] **3.1** T1 — 教师端图标统一到 Material Symbols Outlined（删 28 个 SVG 组件）
- [ ] **3.2** T2 — `tokens.scss` 拆分（base + alias-teacher + alias-student）
- [ ] **3.3** T4 — 抽 layout token（`$layout-app-bar-height` `$layout-tab-bar-height`）
- [ ] **3.4** T3（可选）— dashboard stat 卡 4 色 vs 单色 A/B 用户决定

## 验证方式

每完成一个 sprint：
1. 启动 `apps/student-app` dev server（vite，默认 5173）
2. 浏览器手机视口（375×812 iPhone 11/12/13）逐页验证
3. 关键检查项：
   - 顶栏高度统一 56px
   - TabBar active 态有 dot
   - 主色全部 `#5b21b6`（开发者工具确认无 `#630ed4` 残留）
   - 入场动画流畅
   - :active 有视觉反馈

## Git 策略

- 本 sprint 在 `feature/student-ui-polish` 分支（新建）
- 每个 sprint 一次 commit，message 用 `feat(student-ui): ...`
- 阶段 0 完成后 push，阶段 1 完成后 push，方便回滚
