# 副窗口任务 · T17 学生 + 教师端两个 UI Bug

> 2026-05-12 凌晨 主对话导演反馈
> 用户实看 demo 样板片后定位 2 个真 bug
> 修完后**主对话会单独派人重录** D1/D2/D3，所以这一轮**只修 UI，不重录**

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2
apps/student-app/
apps/teacher-app/
```

---

## Bug 1 · 启动时图标闪英文 ligature 名

### 现象

学生端 + 教师端在启动 / 路由切换的最初 2-3 秒，所有 Material Symbols 图标位置**显示英文 ligature 名**而不是图标本身。例如：
- `home`（应是首页图标）
- `chat_bubble`（应是对话气泡）
- `business`（应是事务图标）
- `person`（应是个人）
- `notifications`（应是铃铛）
- `history`、`grid_view`、`arrow_forward`、`open_in_new`、`school`、`book` 等

2-3 秒后才被字体加载完成的真图标取代。

### 视频证据

主对话样板片 `out/final-fast.mp4` 的 D1 段开头（约 49-51 秒整片时间戳，对应 D1 段 0-2s）—— 学生端 home 页面 tab bar 和 hero 卡片上全是英文 ligature 字符串。同 bug 在 D2 教师端启动时也出现。

### 期望

启动 / 路由切换时**不出现英文 ligature 占位**，要么直接显示真图标，要么显示空白占位（不显示 fallback 文字）。

### 影响范围

- 学生端 H5（`apps/student-app/`）
- 教师端 H5（`apps/teacher-app/`）
- 所有用 Material Symbols 字体的页面（home / chat / questions / detail / profile / dashboard / analytics / knowledge / services / 等）

---

## Bug 2 · Chat 列表新消息不自动滚到底

### 现象

学生端 chat 页面 + 教师端 detail 页面在收到 / 发出新消息时，**滚动条不自动跟到列表底部**。结果是新消息出现在屏幕外（被 composer 输入区或 viewport 顶部遮挡），需要用户手动下拉才能看见。

### 视频证据

主对话样板片 `out/final-fast.mp4` 的 D3 段（双端实时分屏）特别明显：
- 学生端：收到 3 条老师回复时，最新消息往往看不到，只能看到旧消息
- 教师端：发出 3 条回复 + 收到学生反问时，列表停在"接单时的位置"不动

历史录制的 `out/d1/student.webm` 和 `out/d2/teacher.webm` 也展示了同问题（更隐蔽，但能复现）。

### 期望

- 收到新消息（`new_message` Centrifugo 推送）→ chat 列表平滑滚到底
- 发出新消息（用户点 send 后本地 echo）→ 同上
- 只要新消息**有可能落到 viewport 外**，就必须 scroll
- 顺带做一些 message-in 入场动效（淡入 / 上滑 / 弹性，由你定）—— 让收发消息这件事**视觉上"有声有色"**而不是突然出现一坨字

### 影响范围

- 学生端 chat 页面（`apps/student-app/src/pages/chat/index.vue` 或类似路径）
- 教师端 detail 页面（`apps/teacher-app/src/pages/questions/detail.vue` 或类似路径）
- 任何走 Centrifugo `new_message` 推送链路的消息列表

---

## 不要做的事

- ❌ 不要重录 D1/D2/D3 webm（主对话单独派 Kimi 处理）
- ❌ 不要修改其他 UI（不在本任务范围 —— 头像 / 颜色 / 字体 / 布局都不许动）
- ❌ 不要触碰 gateway / Centrifugo / 后端代码（这两个 bug 都在前端）
- ❌ 不要改 router / login flow / 登录态（启动闪烁是字体问题，不是 token 问题）
- ❌ 不要 commit `.tmp/demo-video/` 下任何文件
- ❌ 不要改 Material Symbols 图标的图标名（"home" "chat_bubble" 这种 ligature 名是图标库标准，问题在加载策略不在命名）

---

## 必读 context

- 项目最近一次 UI 改动笔记（teacher-app SCSS 坑位 + uni-app 图片 / HMR 坑位） —— 主对话 memory `bc9ae6b1` 里有详细记录，副窗口可能没有访问权限，**如果你跑 vite dev 报 SCSS 错就过来问主对话**
- uni-app H5 编译特性 —— 主对话 memory `bd474a4a` 里有详细的"`<view>` → `uni-view`" / "`<input>` → `uni-input`" 等编译坑位记录
- 学生端登录账号：`4125150011/4125150011`，教师端：`anjing/Anjing@yxg2026`
- 165 dev 后端：`http://192.168.100.165:8100`（dev 模式 vite proxy 已配好）

---

## 验收清单

主对话验收会做：

### Bug 1（图标闪烁）
- 清缓存冷启动学生端 + 教师端
- 录屏前 5 秒 → 不出现 `home` / `chat_bubble` 等英文字符串
- 路由切换 5 次（home → chat → services → profile → home）→ 不出现闪烁
- 慢网络节流（Chrome DevTools → Slow 3G）→ 仍不出现闪烁（要么真图标，要么空白）

### Bug 2（自动滚动）
- 学生端 chat 页面打开一条对话，主对话用 `gen-narration` 之外的方式触发 5 条 new_message Centrifugo 推送 → 5 条全部进入 viewport
- 教师端 detail 页面快速发 5 条回复 → 5 条全部可见
- 验证 message-in 动效自然（不闪、不抖、不卡顿）

跑完了告诉主对话：
1. 改了哪些文件（路径列表）
2. Bug 1 修复方案的简要描述（一句话即可，比如"预加载字体" / "改成 SVG 图标" / "ligature 替换前隐藏" 等）
3. Bug 2 改了哪个滚动方法 + 加了什么动效
4. 验收时主对话该重点看 D1 段哪几秒、D3 段哪几秒
5. 是否引入新依赖（如某 npm 包）

---

## 卡壳怎么办

- 字体加载预热没效果（Material Symbols 仍然延迟） → 回报主对话，可能要换离线 SVG 图标方案
- chat 列表用了 uni-app `scroll-view` 组件，scrollTop 不响应 → 主对话 memory 里有 uni-app 编译坑位线索，回报主对话协查
- vite dev server 起不来 / SCSS 编译错 → 主对话 memory `bc9ae6b1` 详细列了 4 个坑位（@use vs @import / `<image>` 改写 / HMR 卡死 / Cascade 截图 cache），回报主对话
- 任何超 60 分钟卡壳 → 立刻回报
