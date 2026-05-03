# UI 优化计划

> 创建: 2026-05-04
> 状态: 进行中

## 优先级 1: 自定义 Dialog 组件 (AppDialog)

**目标**: 替换 `uni.showModal`，统一弹窗风格为 MD3

**组件**: `components/AppDialog.vue`
**Composable**: `composables/useDialog.ts`

**设计规范**:
- 圆角卡片 (`$radius-lg`) + 毛玻璃遮罩
- 动画: 缩放淡入 + 遮罩渐显
- 两种模式:
  - `alert` — 单按钮（知道了）
  - `confirm` — 双按钮（取消/确认）
- 通过 composable 调用: `useDialog().confirm({ title, content })` → Promise

**替换清单** (2处):
- [ ] `profile/index.vue:183` — 关于医小管 (alert)
- [ ] `profile/index.vue:206` — 退出登录确认 (confirm)

**复杂度**: 低
**状态**: ⬜ 待开发

---

## 优先级 2: 自定义 Toast 组件 (AppToast)

**目标**: 替换 `uni.showToast`，统一提示风格

**组件**: `components/AppToast.vue`
**Composable**: `composables/useToast.ts`

**设计规范**:
- 顶部滑入小条，MD3 配色
  - success: 绿色
  - error: 红色
  - info: 紫色 (primary)
- Material Symbols 图标
- 自动 2 秒消失

**替换清单** (8处):
- [ ] `login/index.vue:72` — 请输入学号 (error)
- [ ] `login/index.vue:75` — 请输入密码 (error)
- [ ] `login/index.vue:88` — 登录成功 (success)
- [ ] `login/index.vue:93` — 登录失败 (error)
- [ ] `chat/index.vue:427` — 创建会话失败 (error)
- [ ] `chat/index.vue:465` — 发送失败 (error)
- [ ] `chat/index.vue:601` — 已呼叫老师 (success)
- [ ] `chat/index.vue:604` — 呼叫失败 (error)
- [ ] `home/index.vue:228` — 即将上线 (info)
- [ ] `home/index.vue:243` — 功能开发中 (info)

**复杂度**: 中
**状态**: ⬜ 待开发

---

## 优先级 3: 其他 UI 优化

| 项目 | 复杂度 | 状态 |
|------|--------|------|
| "关于"弹窗内容丰富化 (Logo + 版本 + 描述) | 低 | ⬜ |
| Coming Soon Sheet 优化 (加预期提示) | 极低 | ⬜ |
| 首页常用服务可自定义 | 高 | ⬜ 后续 |
| 深色模式 | 中 | ⬜ 后续 |
| 离线/弱网 Empty State | 中 | ⬜ 后续 |
| Profile 头像上传 | 中 | ⬜ 后续 |

---

## 已完成

- [x] 事务导办服务对接 (2026-05-04)
- [x] 首页问候语动态化 (2026-05-04)
- [x] border-bottom 幽灵类名清理 (2026-05-04)
