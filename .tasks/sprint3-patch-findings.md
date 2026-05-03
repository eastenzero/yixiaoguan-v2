# Sprint 3 Patch — 探查发现与修复计划

> 探查日期: 2026-05-03
> 范围: 版本一致性 + UI 修补 (chat 来源卡片、学生端 UI 对齐、事务导办链接)

## 1. 版本一致性诊断

### 三端 Git 状态

| 环境 | HEAD commit | 分支 | 冲突标记 | 说明 |
|------|------------|------|---------|------|
| **本地** (Windows) | `ca957f5` master | master | **有** (4处 main.py, 各1处 chat.py/chat.vue/dashboard.vue) | Mutagen worktree 同步引入 |
| **UB** (192.168.100.165 easten) | `d4fd3ef` master | master | **有** (同本地) | 落后本地 6 commit |
| **HK** (64.90.13.65 root) | `ca957f5` master | master | **无** (已手动解决) | dirty 文件未 commit |

### 冲突来源

Mutagen 在主仓 `F:/Documents/code/yixiaoguan-v2/` 和 worktree `C:/Users/Administrator/.windsurf/worktrees/yixiaoguan-v2/yixiaoguan-v2-d990a10b/` 之间双向同步时产生冲突标记。

### 受影响文件 (dirty working tree)

| 文件 | committed (HEAD) | worktree 新增内容 | HK 状态 |
|------|-----------------|-----------------|---------|
| `services/gateway/app/main.py` | 无 admin router | admin_router 挂载 | 已用 worktree 版本 (82行, 含 admin) |
| `services/gateway/app/routers/chat.py` | 基础 chat_send | R10 建议问题 + analytics | 已用 worktree 版本 |
| `services/gateway/app/services/dify_client.py` | — | 更新 | 已用 worktree 版本 |
| `apps/student-app/src/pages/chat/index.vue` | 625行 | 690行 (suggestions, 来源弹层等) | 已用 worktree 版本 |
| `apps/student-app/src/utils/sse.ts` | — | 更新 | 已用 worktree 版本 |
| `apps/teacher-app/src/pages/dashboard/index.vue` | 613行 | 771行 (admin 区块) | 已用 worktree 版本 |
| `apps/teacher-app/src/pages/login/index.vue` | — | 更新 | 已用 worktree 版本 |
| `apps/teacher-app/src/pages.json` | — | admin 页面路由 | 已用 worktree 版本 |

### 解决策略

以 HK 的已解决版本为准（worktree 新功能版本）→ 本地 resolve → commit → push → 同步 UB。

---

## 2. 学生端知识来源卡片

### 现状

- 来源点击 → `sourcePopup` 底部弹层, 固定 `max-height: 60vh`
- 弹层内容: `<text>{{ sourcePopup.content }}</text>` — **纯文本**, 不渲染 Markdown
- **无拖拽/全屏展开功能**, 无 touch 手势
- 设计稿中来源卡片带 `open_in_new` 图标和下划线链接

### 需修复

- [ ] 弹层内容改用 `v-html="renderMarkdown(content)"` 渲染 Markdown
- [ ] 添加 touch drag 手势: 弹层高度从 40vh → 100vh 可拖拽
- [ ] 拖拽到顶部时吸附全屏显示, 向下拖拽可收回/关闭

---

## 3. 学生端 UI 向教师端看齐

### 现状

- Design tokens (`tokens.scss`) 两端已完全统一 ✅
- 学生端 chat 页面在 worktree 版本中使用硬编码颜色 (`#630ed4`, `#7c3aed`) 而非 token 变量
- 教师端 dashboard 的 Material Design 3 风格组件(stat cards, question cards, admin cards)更精致

### 需修复

- [ ] chat 页面 `<style>` 中硬编码颜色替换为 `$token` 变量
- [ ] 对照教师端走查学生端各页面视觉一致性

---

## 4. 事务导办 (services) 页面

### 现状

`apps/student-app/src/pages/services/index.vue` — 6 个占位卡片, 全部 `@click="comingSoon"` → toast "即将上线"

### 设计稿要求 (stitch services_page)

**快捷入口**: 校主页、信息门户、服务大厅、统一消息平台
**校园服务**: 空教室申请、我的申请、网上报修、接诉即办、校园网、校医院、班车查询
**查询服务**: 学生课表、成绩查询、图书馆、学生邮箱
**个人**: 个人日程、我的提问

### V1 项目已有链接 (提取自 `C:\Users\Administrator\Documents\code\yixiaoguan`)

**来源文件**: `apps/student-app/src/pages/services/index.vue` + `apps/student-app/src/pages/home/index.vue`

#### 快捷入口 / 校园服务

| 服务项 | 类型 | URL / 路由 | 备注 |
|--------|------|-----------|------|
| 空教室申请 | 内部路由 | `/pages/apply/classroom` | V2 暂无此页面 |
| 我的申请 | 内部路由 | `/pages/apply/status` | V2 暂无此页面 |
| 网上报修 | 外链 | `https://metc.sdfmu.edu.cn/info/1073/1954.htm` | |
| 接诉即办 | 企业微信 | — | toast: "请在山一大企业微信中使用" |
| 校园网 | 外链 | `http://vpnportal.sdfmu.edu.cn` | |
| 校医院 | 无 | — | 暂无链接 |
| 班车查询 | 企业微信 | — | toast: "请在山一大企业微信中使用" |
| 更多 | 无 | — | 占位 |

#### 常用服务 / 查询服务 (home + services)

| 服务项 | URL | 备注 |
|--------|-----|------|
| 信息门户 | `http://portal.sdfmu.edu.cn` | home bento 卡片 |
| 教务管理系统 | `http://jwc.sdfmu.edu.cn` | home 常用服务 |
| 成绩查询 | `http://jwc.sdfmu.edu.cn` | services 学业区 |
| 图书馆 | `http://202.194.232.127/index.html` | |
| 学生邮箱 | `https://mail.sdfmu.edu.cn/` | |
| 学校官网 | `https://www.sdfmu.edu.cn` | home 常用服务 |

#### V1 的 openUrl 实现

```ts
function openUrl(url: string) {
  window.open(url, '_blank')
}
```

#### V1 的 wechatOnly 提示

```ts
function wechatOnlyToast() {
  uni.showToast({ title: '请在山一大企业微信中使用', icon: 'none', duration: 2000 })
}
```

### 需修复

- [ ] 按设计稿重做页面布局 (hero banner, 分区 grid)
- [ ] 绑定上述实际 URL (外链用 `window.open`; 企业微信用 toast; 内部路由暂 "即将上线")
- [ ] 无外链的项留 "功能开发中" 但样式需灰显区分
- [ ] home 页面的常用服务也要同步绑定链接 (当前全部是 toast)

---

## 5. 修复优先级

| # | 任务 | 优先级 | 依赖 |
|---|------|--------|------|
| F0 | 解决冲突标记 & 统一代码 (以 HK worktree 版本为准) | P0 | — |
| F1 | 来源弹层 Markdown 渲染 + 拖拽全屏 | P1 | F0 |
| F2 | 学生端 chat 硬编码颜色 → token 变量 | P1 | F0 |
| F3 | 事务导办页面重做 + 链接绑定 | P1 | F0, v1 链接参考 |
| F4 | 前端重新构建并部署到 HK | P0 | F0-F3 |

---

## 6. 执行流程

1. 本地 resolve 冲突 (取 HK/worktree 版本) → commit
2. 逐项修复 F1-F3
3. 本地验证 (dev server preview)
4. git push → HK pull → npm build → 重启 gateway
5. UB 同步 (git pull)
