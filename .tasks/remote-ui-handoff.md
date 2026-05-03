# 远端工作区交接文档 — 学生端 UI 美化

> 生成时间: 2026-05-04  
> 本文档供远端 Windows 电脑上的 AI 助手使用，快速上手学生端 UI 优化工作。

## 1. 项目概要

- **项目名**: 医小管 v2 (yixiaoguan-v2) — 高校智能问答 + 事务导办平台
- **当前 commit**: `e376e4d` (master)
- **技术栈**: uni-app (Vue 3 + Vite) + SCSS，H5 构建
- **框架**: `@dcloudio/uni-app 3.0.0-4080420251103001`
- **样式**: SCSS design tokens (`tokens.scss`)，MD3 Material Design 3 tonal palette
- **图标**: Material Symbols Outlined (wght 300)

## 2. 克隆 & 启动

有两个 Git remote 可选（内容完全一致）：

| Remote | URL | 适用场景 |
|--------|-----|---------|
| **Gitea (内网)** | `http://192.168.100.176:13000/easten/yixiaoguan-v2.git` | 内网机器，速度极快 |
| **GitHub** | `https://github.com/eastenzero/yixiaoguan-v2.git` | 外网机器 |

```bash
# 方式一：内网 Gitea（推荐，如果在同一局域网）
git clone http://192.168.100.176:13000/easten/yixiaoguan-v2.git

# 方式二：GitHub
git clone https://github.com/eastenzero/yixiaoguan-v2.git
```

### ⚠ 分支策略（必须遵守）

**不要在 master 上直接开发！** 另一端在 master 上做教师端工作，直接改 master 会冲突。

```bash
cd yixiaoguan-v2
git checkout -b ui/student-polish    # 创建专属分支
# ... 在这个分支上工作 ...
```

### 推送规则

```bash
# 推到 Gitea（内网）
git remote add gitea http://192.168.100.176:13000/easten/yixiaoguan-v2.git  # 如果用 GitHub clone 的
git push gitea ui/student-polish

# 或推到 GitHub
git remote add github https://github.com/eastenzero/yixiaoguan-v2.git      # 如果用 Gitea clone 的
git push github ui/student-polish
```

本机那边会在合适的时候 merge 你的分支到 master。

### 启动开发服务器

```bash
cd apps/student-app
npm install
npm run dev:h5
# 默认 http://localhost:5174
```

### API 代理

`vite.config.ts` 将 `/api` 和 `/ws` 代理到 `192.168.100.165:8100`（内网开发服务器）。  
如果远端无法访问该内网，可改为 HK 线上：
```ts
// vite.config.ts → proxy.target
target: 'https://yxg.xiaoguan.site'
```
测试账号: `staff_id=4124150001, password=4124150001`

## 3. 学生端文件结构

```
apps/student-app/src/
├── components/
│   ├── CustomTabBar.vue        ← 底部导航栏 (4 tabs: 首页/AI问答/服务/我的)
│   └── FeatureNoticeSheet.vue  ← 功能预告弹层
├── pages/
│   ├── home/index.vue          ← 首页 (bento card 入口)
│   ├── chat/index.vue          ← AI 聊天页 (Markdown 渲染, 来源弹层)
│   ├── chat/history.vue        ← 聊天历史
│   ├── services/index.vue      ← 事务导办 (外链卡片网格)
│   ├── login/index.vue         ← 登录页
│   └── profile/index.vue       ← 个人中心
└── styles/
    ├── tokens.scss             ← MD3 design tokens (与 teacher-app 共享)
    └── global.scss             ← 全局样式
```

## 4. Design Tokens 规范 (必读)

文件: `src/styles/tokens.scss` (327 行, 67 个 MD3 token)

### 核心规则 (来自 DESIGN.md)
1. **No-Line**: 禁止 `1px solid` 边框；层次用 `surface-container` tint 差异表达
2. **No-Shadow**: 阴影不作默认；仅 FAB/Nav 用紫色折射阴影 (`$shadow-nav`, `$elevation-*`)
3. **图标 wght 300**: 细腻高端笔画
4. **大半径**: `$radius-lg: 2rem`, `$radius-xl: 3rem`
5. **display-md**: 2.75rem, weight 800

### 常用 token
| 用途 | Token |
|------|-------|
| 主色 | `$primary: #5b21b6` |
| 页面背景 | `$background` |
| 卡片背景 | `$surface-container-lowest` |
| 正文色 | `$on-surface` |
| 次要文字 | `$on-surface-variant` |
| 卡片圆角 | `$radius-md` (1rem) |
| 标准间距 | `$space-1` ~ `$space-8` |

## 5. 教师端作为参考标杆

教师端 (`apps/teacher-app/`) 的 UI 已经较为成熟，可作为设计参考：
- `pages/dashboard/index.vue` — 数据看板 (占位符，待开发)
- `pages/questions/index.vue` — 问题列表 (成熟 UI)
- `pages/knowledge/index.vue` — 知识库管理 (成熟 UI)
- `pages/login/index.vue` — 登录页 (成熟 UI)

两端共享同一套 `tokens.scss`。

## 6. 优化目标

学生端功能已完成，但 UI 品质低于教师端。需要逐页优化：

| 优先级 | 页面 | 核心问题 |
|--------|------|---------|
| P0 | `chat/index.vue` | AI 聊天核心页面，Markdown 渲染样式、气泡布局、来源弹层需精修 |
| P0 | `home/index.vue` | 首页 bento 入口卡片，间距/配色需对齐 MD3 |
| P1 | `services/index.vue` | 事务导办，卡片网格布局需调整 |
| P1 | `CustomTabBar.vue` | 底部导航，图标/选中态需精修 |
| P2 | `login/index.vue` | 登录页，对齐教师端品质 |
| P2 | `profile/index.vue` | 个人中心 |
| P2 | `chat/history.vue` | 历史记录列表 |

## 7. 工作流约束

1. **在 `ui/student-polish` 分支上工作**（见第 2 节分支策略），**禁止直接改 master**
2. **只改 `apps/student-app/`**，不要动 teacher-app 或 services/gateway
3. 样式修改使用 `tokens.scss` 中的 token，不要硬编码颜色/尺寸
4. 每完成一个页面做一次 commit，commit message 格式: `fix(student-ui): <页面名> <改动摘要>`
5. 可以用 `npm run dev:h5` 实时预览 H5 效果
6. 定期 push 到远端（gitea 或 github），方便本机那边查看进度

## 8. Git 操作注意

- clone 来源决定了默认 remote 名（`origin`），可按需添加第二个 remote
- push 命令: `git push origin ui/student-polish`（或 `git push gitea/github ui/student-polish`）
- **不要 rebase master、不要 merge master**，分支合并由本机负责
- 如遇到 `tokens.scss` 需要改动，先与本机沟通，避免合并冲突

## 9. 已知问题

- `FeatureNoticeSheet.vue` 可能需要删除或重构（功能预告弹层，可能已不需要）
- `vite.config.ts` 的 proxy target 是内网 IP，远端可能无法访问，按第 2 节说明修改
- `type-check` 有预存的类型错误（非 UI 相关），可忽略
