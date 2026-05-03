# 上线前 UI 预期管理改造 — 执行计划

## 决策记录
- `openAiQuestion`: 自动发送（利用现有 `chat_init_query` localStorage 机制）
- 能力标签: 仅 `建设中` 角标，不标 `外部系统` / `AI 可问`
- 老师回复实时展示: 已跑通，本轮跳过

---

## Step 1: 创建共享工具函数
**文件**: `apps/student-app/src/composables/useServiceNavigation.ts`
- [x] `openAiQuestion(question)` — setStorageSync('chat_init_query') + switchTab('/pages/chat/index')
- [x] `openExternal(url)` — H5: window.open / 非H5: navigateTo webview
- [x] `showComingSoon(featureName, suggestedQuestion?)` — uni.showModal 弹层 + "问问医小管" 按钮

## Step 2: 改造学生端事务导办页 (`services/index.vue`)
- [x] 顶栏 "服务大厅" → "服务指南"
- [x] Hero "校园服务中心" → "校园服务指南"
- [x] Hero "便捷办事 · 智慧生活" → "常见事务 · 流程咨询 · 入口导航"
- [x] 校园服务 grid 点击行为批量替换:
  - 空教室申请 → openAiQuestion('我想申请空教室，办理流程是什么？')
  - 我的申请 → showComingSoon('我的申请', '我想查看或跟进自己的校园事务申请，应该去哪里？')
  - 接诉即办 → openAiQuestion('我想反馈校园问题或投诉建议，应该怎么提交？')
  - 校医院 → openAiQuestion('校医院就诊流程和开放时间是什么？')
  - 班车查询 → openAiQuestion('班车时刻表在哪里查询？')
  - 更多 → openAiQuestion('医小管可以帮我做什么？')
  - 网上报修 / 校园网: 保留 openUrl (已有 url)
- [x] 学业 section "学生课表" → openAiQuestion('学生课表在哪里查看？')
- [x] 个人 section "个人日程" → showComingSoon(...)
- [x] 个人 section "我的提问" → navigateTo chat/history
- [x] "统一消息平台" → showComingSoon(...)

## Step 3: 改造学生端首页 (`home/index.vue`)
- [x] Bento "校园服务" 描述 "一站式办事入口" → "流程咨询与入口导航"
- [x] 扩充 tags 为 8-10 个常见问题快捷问
- [x] 通知横幅: 假数据 "你有 3 条未读通知" → 用真实 unread summary，0 条时隐藏
- [x] (可选) 增加"最近提问/继续咨询"区块 — 用 listConversations 拉最近 3 条

## Step 4: 改造学生端"我的"页 (`profile/index.vue`)
- [x] 统计卡: 硬编码 "128" → 真实会话数（或改为"查看记录"）
- [x] 统计卡: "12 我的申请" → 改为"我的咨询"并用真实数据或弱化为无数字
- [x] 学期进度卡: 假数据 → 移除或弱化为纯装饰(不显示具体数字)
- [x] AI 助手卡: 假预览文本 → 改为通用引导文案
- [x] settings 行为: 意见反馈 → openAiQuestion, 帮助中心 → openAiQuestion, 其他保留 showComingSoon
- [x] studentMeta: 硬编码 "临床医学系" → 从 userStore 取真实学院

## Step 5: 改造教师端工作台 (`dashboard/index.vue`)
- [x] "新建知识" → switchTab 到知识库 tab
- [x] "发布通知" → showComingSoon 弹层
- [x] "数据报告" → showComingSoon 弹层
- [x] "系统设置" → showComingSoon 弹层 或灰显

## Step 6: UI 冒烟验证
- [x] 学生端每个服务入口点击有反馈
- [x] 教师端每个快捷入口点击有反馈
- [x] AI 快捷问能进入问答并自动发送
- [x] 首页通知显示真实数据
- [x] "我的"页无明显假数据
- [x] 控制台无新增业务错误
