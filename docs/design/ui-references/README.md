# UI 设计参考

> 来源：stitch.itcss.org 根据产品描述生成的 HTML 原型
> 用途：作为两端 UniApp 实现的视觉与交互参考；**非可直接编译的代码**
> 添加日期：2026-04-27

## 目录结构

```
docs/design/ui-references/
├── README.md                这份文档
├── GAP-ANALYSIS.md          stitch 设计稿 vs 当前实现的差距分析
├── teacher-app-stitch/      教师端 UI 原型（HTML + 截图）
│   └── stitch_/             原始 stitch 输出目录
├── student-app-stitch/      学生端 UI 原型（HTML + 截图）
│   └── stitch_yixiaoguan_campus_assistant/
└── _archives/               原始 zip（建议 .gitignore）
```

## 教师端页面清单（teacher-app-stitch/）

每个页面目录下包含 `code.html`（可浏览器打开预览）和 `screen.png`（截图）。

| 文件 | 页面标题 | 用途 |
|------|---------|------|
| `login_screen/code.html` | 教师工作台-登录 | 教师登录入口 |
| `dashboard/code.html` | 工作台 | 教师首页（待处理任务、新建知识入口） |
| `knowledge_base/code.html` | 知识库 | 知识库列表 |
| `knowledge_detail/code.html` | 知识详情 | 单条知识查看/编辑 |
| `question_list/code.html` | 学生提问 | 待答疑问题列表 |
| `question_detail/code.html` | 提问详情 | 单条问题答疑界面 |
| `profile_settings/code.html` | 我的 | 教师个人中心 |
| `yixiaoguan_teacher_app_prd.html` | PRD 文档 | 设计师附带的 PRD（参考用） |

## 学生端页面清单（student-app-stitch/）

每个页面目录下包含 `code.html`（可浏览器打开预览）和 `screen.png`（截图）。

| 文件 | 页面标题 | 用途 |
|------|---------|------|
| `login_page/code.html` | 登录 | 学生登录 |
| `home_page/code.html` | 智慧校园助理 | 学生首页 |
| `services_page/code.html` | 服务大厅 | 各类申请入口聚合 |
| `ai_chat_page/code.html` | AI 问答 | 主聊天界面 |
| `chat_history/code.html` | 对话历史 | 历史会话列表 |
| `my_questions/code.html` | 我的提问 | 学生发起的提问列表 |
| `my_applications/code.html` | 我的申请 | 学生发起的申请列表 |
| `application_detail/code.html` | 申请详情 | 单条申请的详细界面 |
| `classroom_booking_form/code.html` | 空教室预约 | 表单页 |
| `knowledge_detail/code.html` | 知识库详情 | 学生侧查看知识 |
| `pdf_viewer/code.html` | PDF 预览 | 文档查看 |
| `profile_page/code.html` | 我的 | 学生个人中心 |

## 设计师 PRD

`teacher-app-stitch/stitch_/yixiaoguan_teacher_app_prd.html` 是设计师附的产品描述文档，开发参考用。

## 使用约定

- 直接在浏览器打开任一 HTML 即可预览设计；**不要直接 import 到 UniApp**
- 提取**配色、间距、字号、组件结构**到 UniApp 代码
- 截图（PNG）可作为视觉对比的 baseline
- 当前实现路径：`apps/teacher-app/src/pages/`、`apps/student-app/src/pages/`
- 差距详见 `GAP-ANALYSIS.md`

## 历史

| 日期 | 来源 | 备注 |
|------|------|------|
| 2026-04-27 | 用户提供 stitch 输出 zip | 原始 zip 在 `_archives/`；本次修正了目录命名与内容的错位 |
